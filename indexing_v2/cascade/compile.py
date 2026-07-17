"""Cascade sheet materialization, dedupe, and query API (§5.10.3).

Usage: ``from indexing_v2.cascade.compile import compile_cascade, get_sheet``
"""

from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from indexing_v2.cascade.contexts import enumerate_contexts, observed_content_tag_combos
from indexing_v2.cascade.guards import normalize_guard
from indexing_v2.cascade.resolve import (
    RESIDUAL_AXES,
    ResolvedProperty,
    _resolved_property,
    collect_bindings,
    partial_eval_guard,
    resolve_element,
    specificity,
    specificity_without_id,
)
from indexing_v2.contracts import (
    SCHEMA_VERSION,
    Binding,
    ContextKey,
    Guard,
    atomic_write_json,
    stable_hash,
)
from indexing_v2.contracts import KBSnapshot
from shared import config
from shared.registries import get_registries
from shared.schemas import BrandRule, SECTION_TYPES

STAGE_VERSION = "1.0.0"

_CONTEXT_DEFAULTS = {
    "audience": "dtp_patient",
    "surface": "email",
    "campaign": "none",
    "theme": "none",
    "tags": [],
}
_CONTEXT_ALIASES = {"content_tags": "tags", "tag": "tags"}


class SheetContext(BaseModel):
    audience: str
    campaign: str
    surface: str
    tags: list[str] = Field(default_factory=list)
    theme: str


class GovernanceEntry(BaseModel):
    rule_id: str
    verdict: Optional[str] = None
    preferred_form: Optional[str] = None


class StructureBucket(BaseModel):
    cardinality: list[dict[str, Any]] = Field(default_factory=list)
    ordering: list[dict[str, Any]] = Field(default_factory=list)
    pairing: list[dict[str, Any]] = Field(default_factory=list)
    exclusivity: list[dict[str, Any]] = Field(default_factory=list)


class EmailRules(BaseModel):
    hard_constraints: list[str] = Field(default_factory=list)
    strong_defaults: list[str] = Field(default_factory=list)
    soft_guidance: list[str] = Field(default_factory=list)
    governance: list[GovernanceEntry] = Field(default_factory=list)
    structure: StructureBucket = Field(default_factory=StructureBucket)


class SectionRules(BaseModel):
    hard: list[str] = Field(default_factory=list)
    default: list[str] = Field(default_factory=list)
    guidance: list[str] = Field(default_factory=list)


class SectionSheet(BaseModel):
    rules: SectionRules = Field(default_factory=SectionRules)
    elements: dict[str, ResolvedProperty] = Field(default_factory=dict)


class CascadeSheet(BaseModel):
    schema_version: str = SCHEMA_VERSION
    context: SheetContext
    kb_hash: str
    email: EmailRules = Field(default_factory=EmailRules)
    sections: dict[str, SectionSheet] = Field(default_factory=dict)


class ContextIndexEntry(BaseModel):
    schema_version: str = SCHEMA_VERSION
    axes: SheetContext
    sheet_hash: str


class ContextIndex(BaseModel):
    schema_version: str = SCHEMA_VERSION
    kb_hash: str
    contexts: dict[str, ContextIndexEntry] = Field(default_factory=dict)


class ShadowedBinding(BaseModel):
    schema_version: str = SCHEMA_VERSION
    binding_key: str
    source_kind: str
    source_id: str
    element_path: str
    reason: Literal["shadowed"] = "shadowed"
    shadowed_by: list[str] = Field(default_factory=list)


def render_brand_sheets(snapshot: KBSnapshot) -> str:
    """Compact markdown for every always-injected global token table (E2).

    Global tables with no ``applies_when`` guard render unconditionally — this
    is the email-wide injection surface. Campaign-scoped or guarded tables are
    retrieval-gated and listed by reference only.
    """
    lines = [f"# Brand sheets — {snapshot.brand}", ""]
    gated: list[str] = []
    for table_id in sorted(snapshot.tables):
        table = snapshot.tables[table_id]
        if table.scope != "global" or table.applies_when:
            gated.append(f"- `{table.id}` ({table.table_type}, scope={table.scope})")
            continue
        lines.append(f"## {table.name} ({table.table_type})")
        lines.append("")
        header = [column.name for column in table.columns]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|" * len(header))
        for row in table.rows:
            cells = [
                str(row.cells.get(column.name, "")).replace("\n", " ").strip()
                for column in table.columns
            ]
            lines.append("| " + " | ".join(cells) + " |")
        if table.umbrella_rule_id:
            lines.append("")
            lines.append(f"Bound by `{table.umbrella_rule_id}`.")
        lines.append("")
    if gated:
        lines.append("## Context-gated tables (retrieval only)")
        lines.append("")
        lines.extend(gated)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def compile_cascade(snapshot: KBSnapshot, output_dir: Path, kb_hash: str) -> ContextIndex:
    """Write deterministic cascade sheets and the context index; remove stale sheets."""
    output_dir = Path(output_dir)
    sheets_dir = output_dir / "sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)

    if snapshot.tables:
        (output_dir / "brand_sheets.md").write_text(
            render_brand_sheets(snapshot), encoding="utf-8"
        )

    bindings = collect_bindings(snapshot)
    contexts = enumerate_contexts(snapshot)
    observed_tags = _observed_tags(snapshot)
    section_names = _section_names(snapshot)

    hash_to_payload: dict[str, dict[str, Any]] = {}
    index = ContextIndex(kb_hash=kb_hash)

    for ctx in contexts:
        sheet = _build_sheet(
            snapshot,
            ctx,
            kb_hash,
            bindings,
            section_names,
            observed_tags,
        )
        payload = sheet.model_dump(mode="json")
        dedupe_payload = {key: value for key, value in payload.items() if key != "context"}
        sheet_hash = stable_hash(dedupe_payload)
        hash_to_payload.setdefault(sheet_hash, payload)
        index.contexts[ctx.canonical()] = ContextIndexEntry(
            axes=sheet.context,
            sheet_hash=sheet_hash,
        )

    active_hashes = set(hash_to_payload)
    for stale in sheets_dir.glob("*.json"):
        if stale.stem not in active_hashes:
            stale.unlink()

    for sheet_hash, payload in sorted(hash_to_payload.items()):
        atomic_write_json(sheets_dir / f"{sheet_hash}.json", payload)

    atomic_write_json(output_dir / "contexts.json", index.model_dump(mode="json"))
    return index


def get_sheet(brand_or_root: str | Path, **axes: Any) -> CascadeSheet:
    """Load a sheet by brand or cascade root with default-filled email axes."""
    cascade_root = _resolve_cascade_root(brand_or_root)
    index_path = cascade_root / "contexts.json"
    if not index_path.exists():
        raise FileNotFoundError(f"missing cascade index: {index_path}")

    index = ContextIndex.model_validate(json.loads(index_path.read_text(encoding="utf-8")))
    context = _context_from_axes(axes, index)
    key = _context_key_from_sheet_context(context).canonical()
    entry = index.contexts.get(key)
    if entry is None:
        raise KeyError(f"no sheet for context {key}")

    sheet_path = cascade_root / "sheets" / f"{entry.sheet_hash}.json"
    if not sheet_path.exists():
        raise FileNotFoundError(f"missing sheet payload: {sheet_path}")

    sheet = CascadeSheet.model_validate(json.loads(sheet_path.read_text(encoding="utf-8")))
    if sheet.kb_hash != index.kb_hash:
        raise ValueError(
            f"kb_hash mismatch for {key}: index={index.kb_hash} sheet={sheet.kb_hash}"
        )
    if entry.sheet_hash != stable_hash(
        {k: v for k, v in sheet.model_dump(mode="json").items() if k != "context"}
    ):
        raise ValueError(f"sheet hash mismatch for context {key}")
    return sheet.model_copy(update={"context": entry.axes})


def analyze_shadowed_bindings(
    snapshot: KBSnapshot,
    bindings: Optional[list[Binding]] = None,
) -> list[ShadowedBinding]:
    """Bindings that never win any context×residual cell."""
    effective_bindings = bindings if bindings is not None else collect_bindings(snapshot)
    contexts = enumerate_contexts(snapshot)
    observed_tags = _observed_tags(snapshot)
    domains = _residual_domains(snapshot, observed_tags, effective_bindings)
    live, compatible, shadowers = _evaluate_residual_cells(
        effective_bindings,
        contexts,
        observed_tags,
        domains,
    )
    shadowed = [
        ShadowedBinding(
            binding_key=key,
            source_kind=binding.source_kind,
            source_id=binding.source_id,
            element_path=binding.element_path,
            shadowed_by=sorted(shadowers.get(key, set())),
        )
        for binding in effective_bindings
        if (key := _binding_key(binding)) in compatible and key not in live
    ]
    return sorted(shadowed, key=lambda item: (item.element_path, item.source_id))


def _build_sheet(
    snapshot: KBSnapshot,
    ctx: ContextKey,
    kb_hash: str,
    bindings: list[Binding],
    section_names: list[str],
    observed_tags: set[str],
) -> CascadeSheet:
    sheet_ctx = SheetContext(
        audience=ctx.audience,
        campaign=ctx.campaign,
        surface=ctx.surface,
        tags=list(ctx.content_tags),
        theme=ctx.theme,
    )
    email_rules = EmailRules()
    sections = {name: SectionSheet() for name in section_names}

    for rule in sorted(snapshot.rules.values(), key=lambda item: item.id):
        if not _rule_active_for_context(rule, ctx, observed_tags):
            continue
        _place_rule(rule, email_rules, sections)

    element_paths = sorted({binding.element_path for binding in bindings if binding.element_path != "*"})
    for path in element_paths:
        resolved = resolve_element(path, bindings, ctx, observed_tags=observed_tags)
        for section_name, section in sections.items():
            section_prop = _section_property(resolved, section_name)
            if section_prop.candidates:
                section.elements[path] = section_prop

    return CascadeSheet(context=sheet_ctx, kb_hash=kb_hash, email=email_rules, sections=sections)


def _section_property(resolved: ResolvedProperty, section_name: str) -> ResolvedProperty:
    if section_name == "*":
        filtered = [c for c in resolved.candidates if "section" not in c.residual_guard]
    else:
        filtered = []
        for candidate in resolved.candidates:
            term = candidate.residual_guard.get("section")
            if term is not None and section_name not in term.values:
                continue
            residual = {
                axis: guard_term
                for axis, guard_term in candidate.residual_guard.items()
                if axis != "section"
            }
            filtered.append(candidate.model_copy(update={"residual_guard": residual}))
    return _resolved_property(resolved.element_path, filtered)


def _rule_active_for_context(rule: BrandRule, ctx: ContextKey, observed_tags: set[str]) -> bool:
    guards: list[Any] = [rule.applies_when]
    if rule.audience is not None:
        guards.append({"audience": rule.audience})
    if rule.content_types is not None:
        guards.append({"surface": rule.content_types})
    if rule.selector.section_types is not None:
        guards.append({"section": rule.selector.section_types})
    merged = normalize_guard(guards)
    residual = partial_eval_guard(merged, ctx, observed_tags)
    return residual is not None and all(term.values for term in residual.values())


def _place_rule(rule: BrandRule, email_rules: EmailRules, sections: dict[str, SectionSheet]) -> None:
    if rule.constraint_type == "binding":
        return
    if rule.governance and isinstance(rule.governance, dict):
        preferred = rule.governance.get("preferred_form")
        verdict = rule.governance.get("verdict")
        email_rules.governance.append(
            GovernanceEntry(
                rule_id=rule.id,
                verdict=str(verdict) if verdict is not None else None,
                preferred_form=str(preferred) if preferred is not None else None,
            )
        )

    structure_kind = rule.constraint_type
    if structure_kind in {"cardinality", "ordering", "pairing", "exclusivity"}:
        payload = dict(rule.effect or {})
        payload["rule_id"] = rule.id
        bucket = getattr(email_rules.structure, str(structure_kind))
        bucket.append(payload)

    if rule.evaluation_scope == "email":
        bucket_name = {
            "hard_constraint": "hard_constraints",
            "strong_default": "strong_defaults",
            "soft_guidance": "soft_guidance",
        }[rule.hardness]
        getattr(email_rules, bucket_name).append(rule.id)
        return

    target_sections = _rule_sections(rule, sections)
    bucket_name = {
        "hard_constraint": "hard",
        "strong_default": "default",
        "soft_guidance": "guidance",
    }[rule.hardness]
    for section_name in target_sections:
        bucket = getattr(sections[section_name].rules, bucket_name)
        bucket.append(rule.id)


def _rule_sections(rule: BrandRule, sections: dict[str, SectionSheet]) -> list[str]:
    section_types = rule.selector.section_types
    if section_types is None:
        return ["*"]
    if not section_types:
        return []
    out = [name for name in section_types if name in sections]
    return out or ["*"]


def _section_names(snapshot: KBSnapshot) -> list[str]:
    names = set(SECTION_TYPES)
    names.update(get_registries().section_types(snapshot.brand))
    for rule in snapshot.rules.values():
        for item in rule.selector.section_types or []:
            names.add(item)
    ordered = sorted(names)
    return ordered + ["*"]


def _observed_tags(snapshot: KBSnapshot) -> set[str]:
    return {
        tag
        for combo in observed_content_tag_combos(snapshot)
        for tag in combo
    }


def _residual_domains(
    snapshot: KBSnapshot,
    observed_tags: set[str],
    bindings: list[Binding],
) -> dict[str, list[str]]:
    domains: dict[str, set[str]] = {
        axis: set(values) for axis, values in snapshot.predicate_domains.items()
    }
    domains.setdefault("section", set()).update(
        name for name in _section_names(snapshot) if name != "*"
    )
    for axis in RESIDUAL_AXES:
        domains.setdefault(axis, set())
    for tag in observed_tags:
        domains[f"tag:{tag}"] = {"absent", "present"}
    for binding in bindings:
        for axis, term in binding.guard.items():
            if axis.startswith("tag:"):
                domains.setdefault(axis, set()).update(("absent", "present"))
            else:
                domains.setdefault(axis, set()).update(term.values)
    return {axis: sorted(values) for axis, values in sorted(domains.items())}


def _binding_key(binding: Binding) -> str:
    return f"{binding.source_kind}:{binding.source_id}:{binding.element_path}"


def _evaluate_residual_cells(
    bindings: list[Binding],
    contexts: list[ContextKey],
    observed_tags: set[str],
    domains: dict[str, list[str]],
) -> tuple[set[str], set[str], dict[str, set[str]]]:
    live: set[str] = set()
    compatible: set[str] = set()
    shadowers: dict[str, set[str]] = {}
    paths = sorted({binding.element_path for binding in bindings})
    for ctx in contexts:
        for path in paths:
            surviving: list[tuple[Binding, Guard]] = []
            for binding in bindings:
                if binding.element_path != path:
                    continue
                residual = partial_eval_guard(binding.guard, ctx, observed_tags)
                if residual is not None and all(term.values for term in residual.values()):
                    surviving.append((binding, residual))
            if not surviving:
                continue
            axes = sorted({axis for _, residual in surviving for axis in residual})
            cell_domains = [domains[axis] for axis in axes]
            for values in product(*cell_domains):
                cell = dict(zip(axes, values))
                active = [
                    binding
                    for binding, residual in surviving
                    if _guard_accepts(residual, cell)
                ]
                if not active:
                    continue
                active.sort(key=specificity, reverse=True)
                compatible.update(_binding_key(binding) for binding in active)
                top_rank = specificity_without_id(active[0])
                tied = [
                    binding
                    for binding in active
                    if specificity_without_id(binding) == top_rank
                ]
                tied_values = {
                    json.dumps(binding.value, sort_keys=True, ensure_ascii=False)
                    for binding in tied
                }
                winners = tied if len(tied_values) > 1 else [active[0]]
                live.update(_binding_key(binding) for binding in winners)
                winner_ids = {binding.source_id for binding in winners}
                winner_keys = {_binding_key(binding) for binding in winners}
                for binding in active:
                    if _binding_key(binding) in winner_keys:
                        continue
                    shadowers.setdefault(_binding_key(binding), set()).update(winner_ids)
    return live, compatible, shadowers


def _guard_accepts(guard: Guard, cell: dict[str, str]) -> bool:
    return all(cell.get(axis) in term.values for axis, term in guard.items())


def _resolve_cascade_root(brand_or_root: str | Path) -> Path:
    path = Path(brand_or_root)
    if path.exists():
        if (path / "contexts.json").is_file():
            return path
        if (path / "cascade").is_dir():
            return path / "cascade"
        return path
    return config.kb_dir(str(brand_or_root)) / "cascade"


def _context_from_axes(axes: dict[str, Any], index: ContextIndex) -> SheetContext:
    normalized: dict[str, Any] = {}
    for key, value in axes.items():
        if key not in _CONTEXT_DEFAULTS and key not in _CONTEXT_ALIASES:
            raise KeyError(f"unknown axis {key!r}")
        target = _CONTEXT_ALIASES.get(key, key)
        if target in normalized:
            raise ValueError(f"duplicate aliases for axis {target!r}")
        normalized[target] = value

    result = dict(_CONTEXT_DEFAULTS)
    for key, default in _CONTEXT_DEFAULTS.items():
        if key not in normalized:
            result[key] = list(default) if key == "tags" else default
            continue
        raw = normalized[key]
        if key == "tags":
            if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
                raise ValueError("tags must be a list of strings")
            result[key] = sorted(raw)
            continue
        if not isinstance(raw, str):
            raise ValueError(f"{key} must be a string")
        result[key] = raw
    context = SheetContext.model_validate(result)
    allowed = {
        "audience": sorted({entry.axes.audience for entry in index.contexts.values()}),
        "surface": sorted({entry.axes.surface for entry in index.contexts.values()}),
        "campaign": sorted({entry.axes.campaign for entry in index.contexts.values()}),
        "theme": sorted({entry.axes.theme for entry in index.contexts.values()}),
    }
    for axis, values in allowed.items():
        value = getattr(context, axis)
        if value not in values:
            raise ValueError(f"unknown value for {axis!r}: {value!r}; allowed={values}")
    tag_combos = sorted({tuple(entry.axes.tags) for entry in index.contexts.values()})
    if tuple(context.tags) not in tag_combos:
        raise ValueError(
            f"unknown value for 'tags': {context.tags!r}; "
            f"allowed={[list(combo) for combo in tag_combos]}"
        )
    return context


def _context_key_from_sheet_context(context: SheetContext) -> ContextKey:
    return ContextKey(
        audience=context.audience,
        surface=context.surface,
        campaign=context.campaign,
        theme=context.theme,
        content_tags=list(context.tags),
    )
