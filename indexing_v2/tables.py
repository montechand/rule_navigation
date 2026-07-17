"""E2 token_table: deterministic table detection, compilation, and injection.

Design-bible tables (typography scales, palettes, gradient sets, spacing/radius
scales, canvas spec-lists) are compiled WITHOUT any LLM in the hot path:

- ``detect_table_blocks(units)`` finds markdown tables (contiguous ``table_row``
  runs, split on header/separator rows) and spec-lists (>=3 consecutive
  ``list_item`` units in label-colon-value shape).
- ``compile_table_block(block, brand)`` emits a ``BrandTokenTable``-shaped dict,
  per-atom row tokens (evidence quote = the exact cell substring, so s3
  value-verification passes trivially), and one deterministic umbrella binding
  rule whose effect carries every row token.

Because compilation is pure and deterministic, the umbrella rule is
byte-identical across ensemble runs and survives s4 with support = K — the
consensus problem that LLM-partitioned table blobs can never win is bypassed
by construction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from indexing_v2.contracts import SourceUnit, slugify

TABLES_VERSION = "tables-v1"

_SEPARATOR_RE = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")
_SPEC_LIST_RE = re.compile(r"^\s*(?:\d+\.|[-*])?\s*.{2,80}?[:—→]\s*.*[\d#].*", re.DOTALL)
_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
_DIM_RE = re.compile(r"\b(\d+(?:\.\d+)?)(px|pt|em|rem|in|\")\b")
_PCT_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*%")
_WEIGHT_RE = re.compile(
    r"\b(ExtraBold|SemiBold|Semibold|Bold|Medium|Regular|Light)\b"
)
_FONT_RE = re.compile(r"\b(Nunito Sans|Agenda|Aptos|Verdana|Helvetica|Arial)\b")

_TYPE_SHORT = {
    "typography_scale": "type",
    "color_palette": "color",
    "gradient_set": "grad",
    "spacing_scale": "space",
    "radius_scale": "radius",
    "canvas_spec": "canvas",
    "component_spec": "comp",
}

_COLUMN_ROLES = {
    "name": "name",
    "level": "name",
    "token": "name",
    "gradient": "name",
    "item": "name",
    "hex": "value",
    "value": "value",
    "stops": "value",
    "rgb": "value",
    "cmyk": "surface_print",
    "pantone": "surface_print",
    "print": "surface_print",
    "digital / email": "surface_digital",
    "digital": "surface_digital",
    "email": "surface_digital",
    "word / ppt / excel fallback": "fallback",
    "fallback": "fallback",
    "usage": "usage",
    "use here": "usage",
    "use": "usage",
}


@dataclass(frozen=True)
class RawTableBlock:
    """A detected table before compilation."""

    doc_ref: str
    heading_path: tuple[str, ...]
    kind: str  # "table" | "spec_list"
    header: tuple[str, ...]
    rows: tuple[tuple[str, tuple[str, ...]], ...]  # (unit_id, cells)
    row_texts: tuple[str, ...]  # verbatim unit text per row (evidence quotes)


@dataclass
class CompiledTable:
    table: dict[str, Any]
    row_tokens: list[dict[str, Any]] = field(default_factory=list)
    umbrella_rule: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _split_table_cells(text: str) -> list[str]:
    stripped = text.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _detect_markdown_tables(units: Sequence[SourceUnit]) -> list[RawTableBlock]:
    blocks: list[RawTableBlock] = []
    run: list[SourceUnit] = []

    def _flush(run_units: list[SourceUnit]) -> None:
        if len(run_units) < 3:
            return
        # A row immediately followed by a |---| separator is a header; each
        # header starts a new table within the contiguous run.
        header: tuple[str, ...] | None = None
        rows: list[tuple[str, tuple[str, ...]]] = []
        row_texts: list[str] = []

        def _emit() -> None:
            if header is not None and rows:
                blocks.append(
                    RawTableBlock(
                        doc_ref=run_units[0].doc_ref,
                        heading_path=tuple(run_units[0].heading_path),
                        kind="table",
                        header=header,
                        rows=tuple(rows),
                        row_texts=tuple(row_texts),
                    )
                )

        for index, unit in enumerate(run_units):
            if _SEPARATOR_RE.match(unit.text):
                continue
            is_header = index + 1 < len(run_units) and _SEPARATOR_RE.match(
                run_units[index + 1].text
            )
            if is_header:
                _emit()
                header = tuple(_split_table_cells(unit.text))
                rows = []
                row_texts = []
            elif header is not None:
                rows.append((unit.unit_id, tuple(_split_table_cells(unit.text))))
                row_texts.append(unit.text)
        _emit()

    prev: SourceUnit | None = None
    for unit in units:
        if unit.kind == "table_row":
            if run and prev is not None and (
                unit.doc_ref != run[0].doc_ref
                or tuple(unit.heading_path) != tuple(run[0].heading_path)
            ):
                _flush(run)
                run = []
            run.append(unit)
        else:
            if run:
                _flush(run)
                run = []
        prev = unit
    if run:
        _flush(run)
    return blocks


def _detect_spec_lists(units: Sequence[SourceUnit]) -> list[RawTableBlock]:
    blocks: list[RawTableBlock] = []
    run: list[SourceUnit] = []

    def _flush(run_units: list[SourceUnit]) -> None:
        matching = [unit for unit in run_units if _SPEC_LIST_RE.match(unit.text)]
        if len(matching) < 3:
            return
        rows: list[tuple[str, tuple[str, ...]]] = []
        row_texts: list[str] = []
        for unit in matching:
            label, value = _split_spec_item(unit.text)
            rows.append((unit.unit_id, (label, value)))
            row_texts.append(unit.text)
        blocks.append(
            RawTableBlock(
                doc_ref=matching[0].doc_ref,
                heading_path=tuple(matching[0].heading_path),
                kind="spec_list",
                header=("item", "value"),
                rows=tuple(rows),
                row_texts=tuple(row_texts),
            )
        )

    for unit in units:
        if unit.kind == "list_item":
            if run and (
                unit.doc_ref != run[0].doc_ref
                or tuple(unit.heading_path) != tuple(run[0].heading_path)
            ):
                _flush(run)
                run = []
            run.append(unit)
        else:
            if run:
                _flush(run)
                run = []
    if run:
        _flush(run)
    return blocks


def _split_spec_item(text: str) -> tuple[str, str]:
    body = re.sub(r"^\s*(?:\d+\.|[-*])\s*", "", text.strip())
    for sep in (":", "—", "→"):
        idx = body.find(sep)
        if 0 < idx <= 80:
            return body[:idx].strip().strip("*").strip(), body[idx + len(sep):].strip()
    return body[:60].strip(), body


def detect_table_blocks(units: Sequence[SourceUnit]) -> list[RawTableBlock]:
    """Find markdown tables and spec-lists; deterministic document order."""
    blocks = [*_detect_markdown_tables(units), *_detect_spec_lists(units)]
    ordinals = {unit.unit_id: unit.ordinal for unit in units}
    blocks.sort(key=lambda block: (block.doc_ref, ordinals.get(block.rows[0][0], 0)))
    return blocks


# ---------------------------------------------------------------------------
# Classification (heuristic; no LLM in the hot path)
# ---------------------------------------------------------------------------

def classify_table_type(block: RawTableBlock) -> str:
    heading = " ".join(block.heading_path).lower()
    header = " ".join(block.header).lower()
    all_cells = " ".join(
        cell for _, cells in block.rows for cell in cells
    )
    hex_rows = sum(
        1 for _, cells in block.rows if any(_HEX_RE.search(cell) for cell in cells)
    )
    if "gradient" in heading or "gradient" in header or (
        "→" in all_cells and hex_rows >= max(1, len(block.rows) // 2)
        and "stops" in header
    ):
        return "gradient_set"
    if "hex" in header or hex_rows >= max(2, (2 * len(block.rows)) // 3):
        return "color_palette"
    if (
        "typograph" in heading
        or "type scale" in heading
        or "font" in heading
        or "level" in header
    ):
        return "typography_scale"
    if "radius" in heading or "corner" in heading:
        return "radius_scale"
    if any(word in heading for word in ("spacing", "padding", "margin", "rhythm")):
        return "spacing_scale"
    if any(word in heading for word in ("canvas", "grid", "layout", "structure")):
        return "canvas_spec"
    if block.kind == "spec_list":
        return "component_spec"
    return "other.table"


# ---------------------------------------------------------------------------
# Per-atom cell parsing
# ---------------------------------------------------------------------------

def _extract_atoms(cell: str, *, column_role: str | None) -> list[tuple[str, str, str]]:
    """Split a composite cell into (atom_name, token_type, exact_substring).

    Every returned substring appears verbatim in the cell (and hence in the
    unit text), so provenance value-verification passes per-atom.
    """
    atoms: list[tuple[str, str, str]] = []
    hexes = _HEX_RE.findall(cell)
    for index, match in enumerate(hexes):
        name = "color" if len(hexes) == 1 else f"color_{index + 1}"
        atoms.append((name, "color", match))
    dims = [m.group(0) for m in _DIM_RE.finditer(cell)]
    dim_names: list[str] = []
    if len(dims) == 1:
        dim_names = ["size"]
    elif len(dims) == 2:
        dim_names = ["size", "line_height"]
    else:
        dim_names = [f"dim_{index + 1}" for index in range(len(dims))]
    for name, match in zip(dim_names, dims):
        atoms.append((name, "dimension", match))
    for index, m in enumerate(_PCT_RE.finditer(cell)):
        name = "pct" if index == 0 else f"pct_{index + 1}"
        atoms.append((name, "number", m.group(0)))
    weight = _WEIGHT_RE.search(cell)
    if weight:
        atoms.append(("weight", "font_weight", weight.group(0)))
    font = _FONT_RE.search(cell)
    if font:
        atoms.append(("font", "font", font.group(0)))
    if not atoms and cell and column_role in {"value", "surface_print", "surface_digital", "fallback"}:
        atoms.append(("value", "other", cell))
    return atoms


def _column_role(name: str) -> str | None:
    return _COLUMN_ROLES.get(name.strip().lower())


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------

def _row_key(cells: Sequence[str], used: set[str]) -> str:
    base = slugify(re.sub(r"[*_`]", "", cells[0] if cells else "row")) or "row"
    key = base
    n = 2
    while key in used:
        key = f"{base}_{n}"
        n += 1
    used.add(key)
    return key


def _render_markdown(block: RawTableBlock) -> str:
    lines = ["| " + " | ".join(block.header) + " |"]
    lines.append("|" + "---|" * len(block.header))
    for _, cells in block.rows:
        padded = list(cells) + [""] * (len(block.header) - len(cells))
        lines.append(
            "| " + " | ".join(cell.replace("\n", " ").strip() for cell in padded) + " |"
        )
    return "\n".join(lines)


def compile_table_block(block: RawTableBlock, brand: str) -> CompiledTable:
    """Deterministically compile one block into table + row tokens + umbrella rule."""
    table_type = classify_table_type(block)
    type_short = _TYPE_SHORT.get(table_type, "tbl")
    heading = block.heading_path[-1] if block.heading_path else block.doc_ref
    name_slug = slugify(re.sub(r"\[.*?\]", "", heading)) or slugify(block.doc_ref)
    table_id = f"ttab_{brand}_{name_slug}"

    columns = [
        {"name": header_cell, "role": _column_role(header_cell), "unit_hint": None}
        for header_cell in block.header
    ]

    row_tokens: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    used_keys: set[str] = set()
    used_token_ids: set[str] = set()
    all_unit_ids: list[str] = []

    for (unit_id, cells), row_text in zip(block.rows, block.row_texts):
        row_key = _row_key(cells, used_keys)
        all_unit_ids.append(unit_id)
        cell_map: dict[str, Any] = {}
        token_ids: list[str] = []
        for col_index, cell in enumerate(cells):
            col_name = (
                block.header[col_index]
                if col_index < len(block.header)
                else f"col_{col_index + 1}"
            )
            cell_map[col_name] = cell
            role = _column_role(col_name)
            if role == "name":
                continue
            for atom_name, token_type, substring in _extract_atoms(cell, column_role=role):
                suffix = atom_name if len(cells) <= 2 or role in {None, "value"} else (
                    f"{slugify(col_name)}_{atom_name}"
                )
                token_id = f"tok_{brand}_{type_short}_{row_key}_{suffix}"
                if token_id in used_token_ids:
                    continue
                used_token_ids.add(token_id)
                token_ids.append(token_id)
                row_tokens.append(
                    {
                        "id": token_id,
                        "entity_kind": "token_primitive",
                        "kind": "primitive",
                        "token_type": token_type,
                        "key": f"{type_short}.{row_key}.{suffix}",
                        "value": {
                            "default": substring,
                            "default_evidence": {
                                "unit_ids": [unit_id],
                                "quotes": [substring],
                            },
                            "variants": None,
                        },
                        "aliases": [cells[0].strip().strip("*").strip()] if cells else [],
                        "evidence": {"unit_ids": [unit_id], "quotes": [substring]},
                        "compiled_by": TABLES_VERSION,
                    }
                )
                assignments.append(
                    {
                        "element_path": f"{type_short}.{row_key}.{suffix}",
                        "token_id": token_id,
                        "linked_by": f"{TABLES_VERSION}:table",
                    }
                )
        rows.append(
            {
                "row_key": row_key,
                "unit_id": unit_id,
                "cells": cell_map,
                "token_ids": token_ids,
            }
        )

    rule_slug = f"{name_slug}_table_binding"
    rule_id = f"rule_{brand}_{rule_slug}"
    rendered = _render_markdown(block)
    rule_text = (
        f"The {heading} table is a closed, brand-approved set; every row binds "
        f"its listed values exactly as specified. Do not invent or alter rows.\n\n"
        f"{rendered}"
    )
    umbrella_rule = {
        "id": rule_id,
        "slug": rule_slug,
        "rule_class": "assembly",
        "constraint_type": "binding",
        "selector": {"element_path": None},
        "effect": {"assignments": assignments},
        "rule_text": rule_text,
        "intent": f"Bind the {heading} table values verbatim.",
        "hardness": "strong_default",
        "evidence": {
            "unit_ids": list(all_unit_ids),
            "quotes": [text.strip("\n") for text in block.row_texts],
        },
        "token_ids": sorted(used_token_ids),
        "compiled_by": TABLES_VERSION,
    }

    table = {
        "id": table_id,
        "entity_kind": "token_table",
        "brand_id": brand,
        "table_type": table_type,
        "name": heading,
        "columns": columns,
        "rows": rows,
        "scope": "global",
        "applies_when": None,
        "variant_of": None,
        "umbrella_rule_id": rule_id,
        "doc_ref": block.doc_ref,
        "source": "design_bible",
        "status": "active",
        "version": 1,
        "evidence": {
            "unit_ids": list(all_unit_ids),
            "quotes": [text.strip("\n") for text in block.row_texts],
        },
        "compiled_by": TABLES_VERSION,
    }
    return CompiledTable(table=table, row_tokens=row_tokens, umbrella_rule=umbrella_rule)


def compile_brand_tables(brand: str, units: Sequence[SourceUnit]) -> list[CompiledTable]:
    """Detect and compile every table block; collision-free across blocks.

    Table/rule ids are uniquified with ``_2``/``_3`` suffixes in document order.
    Row-token ids that collide across tables are deduplicated: the same value
    (e.g. Brand Blue's hex appearing in two palette tables) reuses the first
    minted token; a conflicting value is renamed so no id is ever ambiguous.
    """
    compiled: list[CompiledTable] = []
    seen_table_ids: set[str] = set()
    token_values: dict[str, str] = {}
    for block in detect_table_blocks(units):
        item = compile_table_block(block, brand)
        table_id = str(item.table["id"])
        n = 2
        while table_id in seen_table_ids:
            table_id = f"{item.table['id']}_{n}"
            n += 1
        if table_id != item.table["id"]:
            item = _remap_ids(item, {
                str(item.table["id"]): table_id,
                str(item.umbrella_rule["id"]): str(item.umbrella_rule["id"]) + table_id[len(str(item.table["id"])):],
                **{
                    str(token["id"]): str(token["id"]) + table_id[len(str(item.table["id"])):]
                    for token in item.row_tokens
                },
            })
        seen_table_ids.add(table_id)

        rename: dict[str, str] = {}
        deduped_tokens: list[dict[str, Any]] = []
        for token in item.row_tokens:
            token_id = str(token["id"])
            value = str((token.get("value") or {}).get("default"))
            existing = token_values.get(token_id)
            if existing is None:
                token_values[token_id] = value
                deduped_tokens.append(token)
                continue
            if existing == value:
                # Same value re-stated in another table: reuse the first token.
                continue
            fresh = token_id
            n = 2
            while fresh in token_values:
                fresh = f"{token_id}_{n}"
                n += 1
            rename[token_id] = fresh
            token_values[fresh] = value
            renamed = dict(token, id=fresh)
            renamed["key"] = f"{renamed['key']}_{fresh.rsplit('_', 1)[-1]}"
            deduped_tokens.append(renamed)
        item = CompiledTable(
            table=item.table,
            row_tokens=deduped_tokens,
            umbrella_rule=item.umbrella_rule,
        )
        if rename:
            item = _remap_ids(item, rename)
        compiled.append(item)
    return compiled


def _remap_ids(item: CompiledTable, mapping: dict[str, str]) -> CompiledTable:
    """Rewrite every occurrence of the mapped ids across the compiled trio."""

    def _walk(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: _walk(sub) for key, sub in value.items()}
        if isinstance(value, list):
            return [_walk(sub) for sub in value]
        if isinstance(value, str) and value in mapping:
            return mapping[value]
        return value

    return CompiledTable(
        table=_walk(item.table),
        row_tokens=[_walk(token) for token in item.row_tokens],
        umbrella_rule=_walk(item.umbrella_rule),
    )


# ---------------------------------------------------------------------------
# Injection helpers (used by the extraction runner)
# ---------------------------------------------------------------------------

def merge_row_tokens(
    existing: list[dict[str, Any]],
    compiled: Iterable[CompiledTable],
) -> list[dict[str, Any]]:
    """Append compiled row tokens, skipping ids the run already carries."""
    known = {str(token.get("id")) for token in existing}
    merged = list(existing)
    for item in compiled:
        for token in item.row_tokens:
            if str(token["id"]) not in known:
                known.add(str(token["id"]))
                merged.append(token)
    return merged


def table_row_token_ids(tables: Iterable[dict[str, Any]]) -> set[str]:
    """All token ids minted from rows of the given table dicts."""
    out: set[str] = set()
    for table in tables:
        for row in table.get("rows") or []:
            for token_id in row.get("token_ids") or []:
                out.add(str(token_id))
    return out


def resolve_literal_against_tables(
    literal: str,
    tables: Iterable[dict[str, Any]],
) -> str | None:
    """Return the row-token id whose cell contains ``literal`` verbatim, if any."""
    needle = literal.strip().lower()
    if not needle:
        return None
    for table in tables:
        for row in table.get("rows") or []:
            cells = row.get("cells") or {}
            for cell in cells.values():
                if isinstance(cell, str) and needle in cell.lower():
                    token_ids = row.get("token_ids") or []
                    if token_ids:
                        return str(token_ids[0])
    return None
