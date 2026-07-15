"""§5.2 S1 unit classifier — regex heuristics merged with a cheap LLM pass.

Usage: ``await classify_units(brand, units, client=..., usage=...)`` or
``await run_classifier(brand, units, work_dir, ...)``.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Sequence, cast

from shared.llm import Usage

from .. import settings
from ..contracts import (
    SCHEMA_VERSION,
    EntityKind,
    RunVariant,
    SourceUnit,
    UnitLabel,
    UnitLabelName,
    write_jsonl,
)
from .prompts import load_prompt
from .runner import DEFAULT_CACHE_ROOT, CacheContext, LLMClient, complete_json_cached

STAGE_VERSION = "1.0.0"
PROMPT_UNIT_CLASSIFIER = "unit_classifier"
_NEIGHBOR_RADIUS = 2

_VALID_LABELS: frozenset[str] = frozenset(
    {
        "value",
        "normative",
        "conditional",
        "verbatim",
        "asset_ref",
        "structural",
        "example",
        "narrative",
        "noise",
    }
)
_VALID_YIELDS: frozenset[str] = frozenset(
    {
        "token_primitive",
        "token_semantic",
        "rule",
        "asset",
        "subtype",
        "template",
    }
)
_REQUIRED_LOCK_LABELS: frozenset[str] = frozenset({"value", "normative", "verbatim"})

_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_DIM_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:px|pt|em|rem|%)(?!\w)", re.IGNORECASE)
_RATIO_RE = re.compile(r"\b\d+\s*:\s*\d+\b")
_RGB_RE = re.compile(
    r"\brgb\s*\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)",
    re.IGNORECASE,
)
_FONT_WEIGHT_NUM_RE = re.compile(
    r"\b(?:font-weight|weight)\s*:?\s*\d{1,4}\b",
    re.IGNORECASE,
)
_MULTI_RADIUS_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:px|pt|em|rem|%)"
    r"(?:\s+\d+(?:\.\d+)?\s*(?:px|pt|em|rem|%))+(?!\w)",
    re.IGNORECASE,
)
_NORMATIVE_RE = re.compile(
    r"\b(must|never|always|only|do not|don't|required|reserved|max(?:imum)?|min(?:imum)?|"
    r"at least|at most|exactly|prohibited|avoid)\b",
    re.IGNORECASE,
)
_CONDITIONAL_RE = re.compile(
    r"\b(if|when|on (?:light|dark)|desktop|mobile|print|unless|except)\b",
    re.IGNORECASE,
)
_VERBATIM_KEYWORD_RE = re.compile(
    r"\b(verbatim|exact(?:ly as shown)?|word[- ]for[- ]word|as written)\b",
    re.IGNORECASE,
)
_QUOTED_SPAN_RE = re.compile(r'"([^"]+)"|\'([^\']+)\'|“([^”]+)”|‘([^’]+)’')


class ClassifierResponseError(ValueError):
    """LLM classifier output failed validation for a batch or unit."""

    def __init__(
        self,
        message: str,
        *,
        batch_index: int | None = None,
        unit_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.batch_index = batch_index
        self.unit_id = unit_id


def heuristic_labels(unit: SourceUnit) -> list[UnitLabelName]:
    """Pure regex detectors; result is sorted, deduped, and becomes ``heuristic_locked``."""
    text = unit.text
    found: set[UnitLabelName] = set()

    has_value = bool(
        _HEX_RE.search(text)
        or _DIM_RE.search(text)
        or _RATIO_RE.search(text)
        or _RGB_RE.search(text)
        or _FONT_WEIGHT_NUM_RE.search(text)
        or _MULTI_RADIUS_RE.search(text)
    )
    contentful = unit.kind not in {"blank", "heading"}
    has_normative = contentful and bool(_NORMATIVE_RE.search(text))
    has_conditional = contentful and bool(_CONDITIONAL_RE.search(text)) and (
        has_value or has_normative
    )
    has_verbatim = contentful and (
        bool(_VERBATIM_KEYWORD_RE.search(text)) or _quoted_span_has_eight_words(text)
    )

    if has_value:
        found.add("value")
    if has_normative:
        found.add("normative")
    if has_conditional:
        found.add("conditional")
    if has_verbatim:
        found.add("verbatim")

    if unit.kind == "blank":
        found.add("noise")
    elif unit.kind == "heading":
        found.add("structural")
        if not (has_value or has_normative or has_conditional or has_verbatim):
            found.add("noise")

    return sorted(found)


def _quoted_span_has_eight_words(text: str) -> bool:
    for match in _QUOTED_SPAN_RE.finditer(text):
        span = next(group for group in match.groups() if group is not None)
        if len(span.split()) >= 8:
            return True
    return False


def _sort_units(units: Sequence[SourceUnit]) -> list[SourceUnit]:
    return sorted(units, key=lambda unit: (unit.doc_ref, unit.ordinal))


def _units_by_doc_ref(units: Sequence[SourceUnit]) -> dict[str, list[SourceUnit]]:
    grouped: dict[str, list[SourceUnit]] = {}
    for unit in units:
        grouped.setdefault(unit.doc_ref, []).append(unit)
    for doc_ref in grouped:
        grouped[doc_ref] = sorted(grouped[doc_ref], key=lambda item: item.ordinal)
    return grouped


def _target_batches(units: Sequence[SourceUnit], batch_size: int) -> list[list[SourceUnit]]:
    ordered = _sort_units(units)
    return [ordered[index : index + batch_size] for index in range(0, len(ordered), batch_size)]


def _neighbor_window(
    units_by_doc: dict[str, list[SourceUnit]],
    target: SourceUnit,
    *,
    radius: int = _NEIGHBOR_RADIUS,
) -> list[SourceUnit]:
    doc_units = units_by_doc[target.doc_ref]
    index = next(idx for idx, unit in enumerate(doc_units) if unit.unit_id == target.unit_id)
    start = max(0, index - radius)
    end = min(len(doc_units), index + radius + 1)
    return doc_units[start:end]


def _batch_context_units(
    targets: Sequence[SourceUnit],
    units_by_doc: dict[str, list[SourceUnit]],
) -> list[SourceUnit]:
    seen: set[str] = set()
    context: list[SourceUnit] = []
    for target in targets:
        for unit in _neighbor_window(units_by_doc, target):
            if unit.unit_id in seen:
                continue
            seen.add(unit.unit_id)
            context.append(unit)
    return sorted(context, key=lambda unit: (unit.doc_ref, unit.ordinal))


def _render_classify_units(
    context_units: Sequence[SourceUnit],
    target_ids: set[str],
    locked_by_id: dict[str, list[UnitLabelName]],
) -> str:
    parts: list[str] = []
    for unit in sorted(context_units, key=lambda item: (item.doc_ref, item.ordinal)):
        if parts and not parts[-1].endswith("\n"):
            parts.append("\n")
        role = "TARGET" if unit.unit_id in target_ids else "context"
        locked = locked_by_id.get(unit.unit_id) or []
        locked_suffix = f" locked={','.join(locked)}" if locked else ""
        parts.append(f"[{unit.unit_id}] ({unit.kind}) {role}{locked_suffix} {unit.text}")
    return "".join(parts)


def _merge_label(
    unit: SourceUnit,
    locked: list[UnitLabelName],
    llm_row: dict[str, Any],
    *,
    batch_index: int | None = None,
) -> UnitLabel:
    try:
        llm_labels = _coerce_label_list(llm_row.get("labels"), field="labels")
        expected_yield = _coerce_yield_list(
            llm_row.get("expected_yield"),
            field="expected_yield",
        )
        required_value = llm_row.get("required")
        if not isinstance(required_value, bool):
            raise ClassifierResponseError(
                f"invalid required: expected boolean, got {required_value!r}"
            )
        confidence = _coerce_confidence(llm_row.get("confidence"))
    except ClassifierResponseError as exc:
        raise ClassifierResponseError(
            f"batch {batch_index}: unit {unit.unit_id!r}: {exc}",
            batch_index=batch_index,
            unit_id=unit.unit_id,
        ) from exc

    if unit.kind == "blank":
        required = False
    elif set(locked) & _REQUIRED_LOCK_LABELS:
        required = True
    else:
        required = required_value

    return UnitLabel(
        schema_version=SCHEMA_VERSION,
        unit_id=unit.unit_id,
        labels=sorted(set(llm_labels) | set(locked)),
        expected_yield=expected_yield,
        required=required,
        heuristic_locked=sorted(set(locked)),
        confidence=confidence,
    )


def _coerce_label_list(raw: Any, *, field: str) -> list[UnitLabelName]:
    if not isinstance(raw, list):
        raise ClassifierResponseError(f"invalid {field}: expected list, got {type(raw).__name__}")
    out: list[UnitLabelName] = []
    for item in raw:
        if not isinstance(item, str) or item not in _VALID_LABELS:
            raise ClassifierResponseError(f"invalid {field} entry: {item!r}")
        label = cast(UnitLabelName, item)
        out.append(label)
    return sorted(set(out))


def _coerce_yield_list(raw: Any, *, field: str) -> list[EntityKind]:
    if not isinstance(raw, list):
        raise ClassifierResponseError(f"invalid {field}: expected list, got {type(raw).__name__}")
    out: list[EntityKind] = []
    for item in raw:
        if not isinstance(item, str) or item not in _VALID_YIELDS:
            raise ClassifierResponseError(f"invalid {field} entry: {item!r}")
        kind = cast(EntityKind, item)
        out.append(kind)
    return sorted(set(out))


def _coerce_confidence(raw: Any) -> float:
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        raise ClassifierResponseError(f"invalid confidence: {raw!r}")
    value = float(raw)
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ClassifierResponseError(f"confidence out of range: {value}")
    return value


def _parse_batch_response(
    raw: Any,
    *,
    target_ids: set[str],
    batch_index: int,
) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        raise ClassifierResponseError(
            f"batch {batch_index}: expected object response, got {type(raw).__name__}",
            batch_index=batch_index,
        )
    rows = raw.get("units")
    if not isinstance(rows, list):
        raise ClassifierResponseError(
            f"batch {batch_index}: missing units list",
            batch_index=batch_index,
        )

    parsed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ClassifierResponseError(
                f"batch {batch_index}: unit row must be an object",
                batch_index=batch_index,
            )
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str):
            raise ClassifierResponseError(
                f"batch {batch_index}: unit row missing unit_id",
                batch_index=batch_index,
            )
        if unit_id not in target_ids:
            raise ClassifierResponseError(
                f"batch {batch_index}: unexpected unit_id {unit_id!r}",
                batch_index=batch_index,
                unit_id=unit_id,
            )
        if unit_id in parsed:
            raise ClassifierResponseError(
                f"batch {batch_index}: duplicate unit_id {unit_id!r}",
                batch_index=batch_index,
                unit_id=unit_id,
            )
        parsed[unit_id] = row

    missing = sorted(target_ids - set(parsed))
    if missing:
        raise ClassifierResponseError(
            f"batch {batch_index}: missing unit_id {missing[0]!r}",
            batch_index=batch_index,
            unit_id=missing[0],
        )
    return parsed


async def classify_units(
    brand: str,
    units: list[SourceUnit],
    *,
    client: LLMClient,
    usage: Usage,
    variant: RunVariant | None = None,
    model: str | None = None,
    cache_root: Path | None = None,
    prompts_dir: Path | None = None,
    batch_size: int = 40,
) -> list[UnitLabel]:
    """Classify every unit; heuristics lock labels the LLM cannot remove."""
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")

    resolved_variant = variant or RunVariant(
        run_id="classify",
        model=model or settings.CLASSIFY_MODEL,
        temperature=0.0,
        replicate=0,
    )
    if model is not None and variant is not None and variant.model != model:
        resolved_variant = resolved_variant.model_copy(update={"model": model})

    locked_by_id = {unit.unit_id: heuristic_labels(unit) for unit in units}
    units_by_doc = _units_by_doc_ref(units)
    template = load_prompt(PROMPT_UNIT_CLASSIFIER, prompts_dir)
    ctx = CacheContext(
        brand=brand,
        variant=resolved_variant,
        prompt_name=PROMPT_UNIT_CLASSIFIER,
        template=template,
        content_hash="",
        cache_root=cache_root or DEFAULT_CACHE_ROOT,
    )

    llm_by_id: dict[str, tuple[int, dict[str, Any]]] = {}
    for batch_index, targets in enumerate(_target_batches(units, batch_size)):
        target_ids = {unit.unit_id for unit in targets}
        context_units = _batch_context_units(targets, units_by_doc)
        rendered = template.render(
            brand=brand,
            units=_render_classify_units(context_units, target_ids, locked_by_id),
        )
        raw = await complete_json_cached(
            client,
            ctx,
            rendered.system,
            rendered.user,
            usage,
        )
        rows = _parse_batch_response(raw, target_ids=target_ids, batch_index=batch_index)
        llm_by_id.update((unit_id, (batch_index, row)) for unit_id, row in rows.items())

    labels = [
        _merge_label(
            unit,
            locked_by_id[unit.unit_id],
            llm_by_id[unit.unit_id][1],
            batch_index=llm_by_id[unit.unit_id][0],
        )
        for unit in _sort_units(units)
    ]
    return labels


async def run_classifier(
    brand: str,
    units: list[SourceUnit],
    work_dir: Path,
    *,
    client: LLMClient,
    usage: Usage,
    variant: RunVariant | None = None,
    model: str | None = None,
    cache_root: Path | None = None,
    prompts_dir: Path | None = None,
    batch_size: int = 40,
) -> list[UnitLabel]:
    """Classify units and write ``work_dir/unit_labels.jsonl``."""
    labels = await classify_units(
        brand,
        units,
        client=client,
        usage=usage,
        variant=variant,
        model=model,
        cache_root=cache_root,
        prompts_dir=prompts_dir,
        batch_size=batch_size,
    )
    write_jsonl(work_dir / "unit_labels.jsonl", labels)
    return labels
