"""§5.4.3 provenance verification and quarantine (S3).

Pure core: ``verify_entities`` and ``active_entities``. Thin I/O: ``write_provenance``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Union

from pydantic import BaseModel, Field

from indexing_v2 import settings
from indexing_v2.contracts import (
    SCHEMA_VERSION,
    EVIDENCE_PATHS,
    EntityKind,
    EvidenceSpan,
    ProvenanceRecord,
    SourceUnit,
    ValueCheck,
    Verification,
    atomic_write_json,
)

from .align import ValueVerificationResult, is_concrete_value_field, verify_value_path

STAGE_VERSION = "1.0.1"

_PATH_SEGMENT_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")
_VARIANT_VALUE_RE = re.compile(r"^value\.variants\[\d+\]\.value$")


class ProvenanceError(Exception):
    """Base error for provenance stage."""


class UnknownEntityKindError(ProvenanceError):
    """Raised when ``entities_by_kind`` contains an unrecognized kind key."""


EntitiesBucket = Union[Sequence[dict[str, Any]], Mapping[str, dict[str, Any]]]
EntitiesByKind = Mapping[str, EntitiesBucket]

_VERIFICATION_RANK: dict[Verification, int] = {
    "value_verified": 3,
    "span_verified": 2,
    "unverified": 1,
}


class QuarantineEntry(BaseModel):
    schema_version: str = SCHEMA_VERSION
    entity_id: str
    entity_kind: EntityKind
    reason: str


class ProvenanceResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    records_by_entity: dict[str, list[ProvenanceRecord]] = Field(default_factory=dict)
    by_unit: dict[str, list[str]] = Field(default_factory=dict)
    quarantine: list[QuarantineEntry] = Field(default_factory=list)


def _parse_path(path: str) -> list[str | int]:
    if path == "":
        return []
    segments: list[str | int] = []
    for part in path.split("."):
        while part:
            match = _PATH_SEGMENT_RE.match(part)
            if match is None:
                raise ProvenanceError(f"invalid field path: {path!r}")
            if match.group(1) is not None:
                segments.append(match.group(1))
                part = part[match.end() :]
            else:
                segments.append(int(match.group(2)))
                part = part[match.end() :]
    return segments


def _walk_path(root: Any, segments: Sequence[str | int]) -> Any:
    current: Any = root
    for segment in segments:
        if isinstance(segment, int):
            if not isinstance(current, list) or segment >= len(current):
                return None
            current = current[segment]
        elif isinstance(current, dict):
            if segment not in current:
                return None
            current = current[segment]
        else:
            return None
    return current


def _get_at_path(entity: dict[str, Any], field_path: str) -> Any:
    if field_path == "":
        return entity
    return _walk_path(entity, _parse_path(field_path))


def _path_exists(entity: dict[str, Any], field_path: str) -> bool:
    current: Any = entity
    for segment in _parse_path(field_path):
        if isinstance(segment, int):
            if not isinstance(current, list) or segment >= len(current):
                return False
            current = current[segment]
        elif isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            return False
    return True


def _evidence_keys_for_field(field_path: str) -> tuple[str, list[str]]:
    if field_path == "":
        return ("", ["evidence"])
    if field_path == "value.default":
        return ("value", ["default_evidence"])
    if _VARIANT_VALUE_RE.match(field_path):
        parent = field_path.rsplit(".", 1)[0]
        return (parent, ["evidence", "value_evidence"])
    if field_path == "governance.preferred_form":
        return ("governance", ["preferred_form_evidence"])
    if field_path in {"effect", "snippets", "body"}:
        return ("", [f"{field_path}_evidence"])
    if "." in field_path:
        parent, leaf = field_path.rsplit(".", 1)
        return (parent, [f"{leaf}_evidence"])
    return ("", [f"{field_path}_evidence"])


def _lookup_evidence(
    entity_id: str,
    entity: dict[str, Any],
    field_path: str,
) -> dict[str, Any] | None:
    parent_path, keys = _evidence_keys_for_field(field_path)
    parent = entity if parent_path == "" else _get_at_path(entity, parent_path)
    if not isinstance(parent, dict):
        return None
    for key in keys:
        if key not in parent:
            continue
        raw = parent[key]
        # ponytail: LLM schemas emit `| null` for optional evidence; treat null as absent.
        if raw is None:
            continue
        if not isinstance(raw, dict):
            field_label = field_path or "entity"
            raise ProvenanceError(
                f"malformed evidence for {entity_id}/{field_label}: {key} must be an object"
            )
        return raw
    return None


def _evidence_string_list(
    evidence: Mapping[str, Any],
    key: str,
    *,
    entity_id: str,
    field_path: str,
) -> list[str]:
    if key not in evidence:
        return []
    raw = evidence[key]
    field_label = field_path or "entity"
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ProvenanceError(
            f"malformed evidence for {entity_id}/{field_label}: {key} must be a list of strings"
        )
    return raw


def _expand_field_paths(entity: dict[str, Any], kind: EntityKind) -> list[str]:
    concrete: list[str] = []
    for pattern in EVIDENCE_PATHS[kind]:
        if "[*]" in pattern:
            prefix, suffix = pattern.split("[*]", 1)
            variants = _get_at_path(entity, prefix)
            if isinstance(variants, list):
                for index in range(len(variants)):
                    concrete.append(f"{prefix}[{index}]{suffix}")
            continue
        concrete.append(pattern)
    return concrete


def _token_type_for_field(field_path: str, entity: dict[str, Any]) -> str:
    if field_path == "governance.preferred_form":
        return "preferred_form"
    if field_path == "body":
        return "body"
    token_type = entity.get("token_type")
    return str(token_type) if token_type is not None else "unknown"


def _span_key(span: EvidenceSpan) -> tuple[Any, ...]:
    return (
        span.doc_ref,
        tuple(span.unit_ids),
        span.start,
        span.end,
        span.quote,
        span.match,
    )


def _merge_verification_results(
    results: Sequence[ValueVerificationResult],
) -> tuple[list[EvidenceSpan], ValueCheck, Verification, str | None]:
    spans: list[EvidenceSpan] = []
    seen: set[tuple[Any, ...]] = set()
    for result in results:
        key = _span_key(result.span)
        if key not in seen:
            seen.add(key)
            spans.append(result.span)
    spans.sort(
        key=lambda span: (
            span.doc_ref,
            span.start,
            span.end,
            span.quote,
            span.match,
            tuple(span.unit_ids),
        )
    )

    if not results:
        return spans, ValueCheck(status="fail", detail="no quotes"), "unverified", None

    best = max(results, key=lambda result: _VERIFICATION_RANK[result.verification])
    details = [result.detail for result in results if result.detail]
    merged_detail = details[0] if len(details) == 1 else (details[0] if details else None)

    statuses = {result.value_check.status for result in results}
    if "pass" in statuses:
        value_check = next(result.value_check for result in results if result.value_check.status == "pass")
    elif statuses == {"n/a"}:
        value_check = ValueCheck(status="n/a")
    else:
        value_check = next(
            result.value_check
            for result in results
            if result.value_check.status == "fail"
        )

    return spans, value_check, best.verification, merged_detail


def _record_for_path(
    *,
    entity_id: str,
    field_path: str,
    entity: dict[str, Any],
    units_by_id: Mapping[str, SourceUnit],
    fuzzy_min_ratio: float,
) -> ProvenanceRecord:
    raw_value = _get_at_path(entity, field_path) if field_path else entity
    if is_concrete_value_field(field_path) and raw_value is None:
        field_state = "null" if _path_exists(entity, field_path) else "absent"
        return ProvenanceRecord(
            entity_id=entity_id,
            field=field_path,
            spans=[],
            value_check=ValueCheck(
                status="n/a",
                detail=f"{field_path} is {field_state}; no concrete literal to verify",
            ),
            verification="unverified",
        )

    evidence = _lookup_evidence(entity_id, entity, field_path)
    quotes = (
        _evidence_string_list(
            evidence,
            "quotes",
            entity_id=entity_id,
            field_path=field_path,
        )
        if evidence is not None
        else []
    )
    unit_ids = (
        _evidence_string_list(
            evidence,
            "unit_ids",
            entity_id=entity_id,
            field_path=field_path,
        )
        if evidence is not None
        else []
    )

    is_structural_ref = isinstance(raw_value, dict) and "$ref" in raw_value
    if evidence is None or not quotes:
        field_label = field_path or "entity"
        return ProvenanceRecord(
            entity_id=entity_id,
            field=field_path,
            spans=[],
            value_check=ValueCheck(
                status="n/a" if is_structural_ref else "fail",
                detail=(
                    "structural $ref"
                    if is_structural_ref
                    else f"missing evidence for {field_label}"
                ),
            ),
            verification="unverified",
        )

    token_type = _token_type_for_field(field_path, entity)
    quote_results = [
        verify_value_path(
            field_path=field_path,
            token_type=token_type,
            raw_value=raw_value,
            quote=quote,
            units_by_id=units_by_id,
            cited_unit_ids=unit_ids,
            fuzzy_min_ratio=fuzzy_min_ratio,
        )
        for quote in quotes
    ]
    spans, value_check, verification, _ = _merge_verification_results(quote_results)
    return ProvenanceRecord(
        entity_id=entity_id,
        field=field_path,
        spans=spans,
        value_check=value_check,
        verification=verification,
    )


def _iter_entities(entities_by_kind: EntitiesByKind) -> list[tuple[EntityKind, dict[str, Any]]]:
    out: list[tuple[EntityKind, dict[str, Any]]] = []
    seen_ids: set[str] = set()
    for kind, bucket in entities_by_kind.items():
        if kind not in EVIDENCE_PATHS:
            raise UnknownEntityKindError(f"unknown entity kind: {kind!r}")
        entity_kind = kind
        if isinstance(bucket, Mapping):
            entities = list(bucket.values())
        else:
            entities = list(bucket)
        for entity in entities:
            if not isinstance(entity, dict):
                raise ProvenanceError(f"entity for kind {kind!r} must be a dict")
            entity_id = entity.get("id")
            if not isinstance(entity_id, str) or not entity_id:
                raise ProvenanceError(f"entity for kind {kind!r} missing string id")
            if entity_id in seen_ids:
                raise ProvenanceError(f"duplicate entity id: {entity_id}")
            seen_ids.add(entity_id)
            out.append((entity_kind, entity))
    out.sort(key=lambda item: (item[1]["id"], item[0]))
    return out


def _concrete_literal_records(records: Sequence[ProvenanceRecord]) -> list[ProvenanceRecord]:
    return [
        record
        for record in records
        if is_concrete_value_field(record.field) and record.value_check.status != "n/a"
    ]


def _record_failed(record: ProvenanceRecord) -> bool:
    return record.verification == "unverified" or record.value_check.status == "fail"


def _quarantine_reason(entity_id: str, records: Sequence[ProvenanceRecord]) -> str | None:
    concrete = _concrete_literal_records(records)
    if not concrete:
        return None
    if not all(_record_failed(record) for record in concrete):
        return None
    failed_fields = ", ".join(sorted(record.field for record in concrete))
    return f"{entity_id}: all concrete value paths unverified ({failed_fields})"


def _build_by_unit(records_by_entity: Mapping[str, Sequence[ProvenanceRecord]]) -> dict[str, list[str]]:
    index: dict[str, set[str]] = {}
    for entity_id in sorted(records_by_entity):
        for record in records_by_entity[entity_id]:
            if record.verification not in {"span_verified", "value_verified"}:
                continue
            for span in record.spans:
                if span.match == "failed":
                    continue
                for unit_id in span.unit_ids:
                    index.setdefault(unit_id, set()).add(entity_id)
    return {unit_id: sorted(index[unit_id]) for unit_id in sorted(index)}


def verify_entities(
    entities_by_kind: EntitiesByKind,
    units: Sequence[SourceUnit],
    *,
    fuzzy_min_ratio: float | None = None,
) -> ProvenanceResult:
    """Verify evidence for every entity path in ``EVIDENCE_PATHS``."""
    ratio = settings.FUZZY_MATCH_MIN_RATIO if fuzzy_min_ratio is None else fuzzy_min_ratio
    units_by_id = {unit.unit_id: unit for unit in units}

    records_by_entity: dict[str, list[ProvenanceRecord]] = {}
    quarantine: list[QuarantineEntry] = []

    for kind, entity in _iter_entities(entities_by_kind):
        entity_id = str(entity["id"])
        records = [
            _record_for_path(
                entity_id=entity_id,
                field_path=field_path,
                entity=entity,
                units_by_id=units_by_id,
                fuzzy_min_ratio=ratio,
            )
            for field_path in _expand_field_paths(entity, kind)
        ]
        records_by_entity[entity_id] = records
        reason = _quarantine_reason(entity_id, records)
        if reason is not None:
            quarantine.append(
                QuarantineEntry(
                    entity_id=entity_id,
                    entity_kind=kind,
                    reason=reason,
                )
            )

    return ProvenanceResult(
        records_by_entity=records_by_entity,
        by_unit=_build_by_unit(records_by_entity),
        quarantine=sorted(quarantine, key=lambda entry: entry.entity_id),
    )


def active_entities(
    result: ProvenanceResult,
    entities_by_kind: EntitiesByKind,
) -> dict[str, list[dict[str, Any]]]:
    """Return entities excluding quarantined ids; provenance records are unchanged."""
    quarantined = {entry.entity_id for entry in result.quarantine}
    active: dict[str, list[dict[str, Any]]] = {}
    for kind, bucket in entities_by_kind.items():
        if kind not in EVIDENCE_PATHS:
            raise UnknownEntityKindError(f"unknown entity kind: {kind!r}")
        if isinstance(bucket, Mapping):
            entities = list(bucket.values())
        else:
            entities = list(bucket)
        kept = [
            entity
            for entity in entities
            if isinstance(entity, dict) and str(entity.get("id", "")) not in quarantined
        ]
        if kept:
            active[kind] = kept
    return active


def write_provenance(result: ProvenanceResult, run_dir: Path) -> None:
    """Persist provenance artifacts under ``run_dir``."""
    provenance_dir = run_dir / "provenance"
    expected_files = {f"{entity_id}.json" for entity_id in result.records_by_entity}
    if provenance_dir.exists():
        for path in sorted(provenance_dir.glob("*.json")):
            if path.name != "_by_unit.json" and path.name not in expected_files:
                path.unlink()
    for entity_id in sorted(result.records_by_entity):
        records = result.records_by_entity[entity_id]
        atomic_write_json(
            provenance_dir / f"{entity_id}.json",
            [record.model_dump(mode="json") for record in records],
        )
    atomic_write_json(provenance_dir / "_by_unit.json", result.by_unit)
    atomic_write_json(
        run_dir / "quarantine.json",
        [entry.model_dump(mode="json") for entry in result.quarantine],
    )
