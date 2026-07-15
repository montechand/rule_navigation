"""§5.5 S4 ensemble reconciliation — pure merge over K verified runs.

Public handoff:
- ``build_verified_run``: raw ``RunOutput`` → S3-verified boundary input.
- ``semantic_match_key``: normalized path + resolved default canon (WP-11 compatible).
- ``reconcile_ensemble``: pure K-run merge.
- ``write_candidates``: atomic, stale-safe candidate artifacts.
"""

from __future__ import annotations

import copy
import itertools
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from indexing_v2 import settings
from indexing_v2.cascade.guards import normalize_guard
from indexing_v2.contracts import (
    SCHEMA_VERSION,
    Conflict,
    ExtractionMeta,
    Finding,
    SourceUnit,
    UnitLabel,
    atomic_write_json,
    stable_hash,
)
from indexing_v2.extraction.align import is_concrete_value_field
from indexing_v2.extraction.normalize import normalize_value
from indexing_v2.extraction.provenance import ProvenanceResult, verify_entities
from indexing_v2.extraction.runner import RunOutput

STAGE_VERSION = "1.2.0"

EntityKindBucket = Literal[
    "token_primitive",
    "token_semantic",
    "asset",
    "subtype",
    "template",
    "rule",
]


class SemanticResolutionError(ValueError):
    """A semantic default contains a missing or cyclic ``$ref`` chain."""


class RuleGroupMappingError(ValueError):
    """A rule group id maps to conflicting source document references."""


class VerifiedRunInput(BaseModel):
    """One S3-verified extraction run (WP-07 output + provenance)."""

    schema_version: str = SCHEMA_VERSION
    output: RunOutput
    provenance: ProvenanceResult


class EnsembleResult(BaseModel):
    """Merged active candidates plus conflicts, findings, and full S3 provenance."""

    schema_version: str = SCHEMA_VERSION
    champion_run: str
    tokens_primitive: list[dict[str, Any]] = Field(default_factory=list)
    tokens_semantic: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    subtypes: list[dict[str, Any]] = Field(default_factory=list)
    templates: list[dict[str, Any]] = Field(default_factory=list)
    rule_groups: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    rule_group_doc_refs: dict[str, str] = Field(default_factory=dict)
    relations_by_group: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    conflicts: list[Conflict] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    provenance: ProvenanceResult = Field(default_factory=ProvenanceResult)


@dataclass(frozen=True, slots=True)
class _Occurrence:
    run_id: str
    kind: EntityKindBucket
    entity: dict[str, Any]
    catalog: Mapping[str, dict[str, Any]]
    group_id: str | None = None


@dataclass(frozen=True, slots=True)
class _EntityGroup:
    kind: EntityKindBucket
    occurrences: tuple[_Occurrence, ...]
    raw_occurrences: tuple[_Occurrence, ...]
    group_id: str | None = None

    @property
    def support(self) -> int:
        return len(self.occurrences)


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _occurrence_sort_key(item: _Occurrence) -> tuple[str, str]:
    return (str(item.entity.get("id", "")), _json_key(item.entity))


def _scope(entity: Mapping[str, Any]) -> str:
    raw = entity.get("scope")
    return str(raw) if raw is not None else "global"


def _element_path(entity: Mapping[str, Any]) -> str:
    paths = entity.get("element_paths")
    if isinstance(paths, list) and paths:
        raw = sorted(str(path) for path in paths)[0]
    else:
        selector = entity.get("selector")
        selector_path = selector.get("element_path") if isinstance(selector, dict) else None
        raw = str(entity.get("element_path") or entity.get("key") or selector_path or "")
    return normalize_value("string", raw).canon


def _default_raw(entity: Mapping[str, Any]) -> Any:
    value = entity.get("value")
    return value.get("default") if isinstance(value, dict) else value


def build_token_catalog(output: RunOutput) -> dict[str, dict[str, Any]]:
    """Return the deterministic per-run token id catalog used for semantic ``$ref`` resolution."""
    catalog: dict[str, dict[str, Any]] = {}
    tokens = [*output.primitive_tokens, *output.semantic_tokens]
    for token in sorted(tokens, key=lambda item: (str(item.get("id", "")), _json_key(item))):
        token_id = str(token.get("id", ""))
        if not token_id:
            continue
        candidate = copy.deepcopy(token)
        previous = catalog.get(token_id)
        if previous is not None and _json_key(previous) != _json_key(candidate):
            raise SemanticResolutionError(f"duplicate token id {token_id!r} has differing definitions")
        catalog[token_id] = candidate
    return catalog


def _resolve_ref_default(
    value: Any,
    catalog: Mapping[str, dict[str, Any]],
    *,
    entity_id: str,
    chain: tuple[str, ...] = (),
) -> Any:
    if not isinstance(value, dict) or "$ref" not in value:
        return value
    ref = str(value["$ref"])
    next_chain = (*chain, ref)
    if ref in chain:
        rendered = " -> ".join(next_chain)
        raise SemanticResolutionError(f"{entity_id}: cyclic $ref default: {rendered}")
    target = catalog.get(ref)
    if target is None:
        rendered = " -> ".join(next_chain)
        raise SemanticResolutionError(f"{entity_id}: missing $ref default: {rendered}")
    return _resolve_ref_default(
        _default_raw(target),
        catalog,
        entity_id=entity_id,
        chain=next_chain,
    )


def semantic_match_key(
    entity: Mapping[str, Any],
    token_catalog: Mapping[str, dict[str, Any]],
) -> tuple[str, str]:
    """Return ``(normalized element_path, resolved default canon)`` for WP-11 triage keys."""
    entity_id = str(entity.get("id", "<semantic>"))
    resolved = _resolve_ref_default(
        _default_raw(entity),
        token_catalog,
        entity_id=entity_id,
    )
    token_type = str(entity.get("token_type") or "unknown")
    canon = "" if resolved is None else normalize_value(token_type, resolved).canon
    return (_element_path(entity), canon)


def _primitive_match_key(entity: Mapping[str, Any]) -> tuple[str, str, str]:
    token_type = str(entity.get("token_type") or "unknown")
    raw = _default_raw(entity)
    canon = "" if raw is None else normalize_value(token_type, raw).canon
    return (token_type, canon, _scope(entity))


def _normalized_name(entity: Mapping[str, Any]) -> str:
    raw = entity.get("name") or entity.get("id") or ""
    return normalize_value("string", str(raw)).canon


def _asset_match_key(entity: Mapping[str, Any]) -> tuple[str, str]:
    asset_type = str(entity.get("asset_type") or entity.get("type") or "unknown")
    uri = entity.get("uri")
    if isinstance(uri, str) and uri.strip():
        return (asset_type, normalize_value("string", uri).canon)
    return (asset_type, _normalized_name(entity))


def _named_match_key(entity: Mapping[str, Any], fallback: str) -> tuple[str, str]:
    kind = str(entity.get("kind") or entity.get("instance_of") or fallback)
    return (kind, _normalized_name(entity))


def _rule_identity(rule: Mapping[str, Any]) -> tuple[str, str]:
    selector = rule.get("selector")
    path = selector.get("element_path") if isinstance(selector, dict) else ""
    return (str(rule.get("rule_class") or ""), normalize_value("string", str(path or "")).canon)


def _claimed_unit_ids(entity: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            raw_ids = value.get("unit_ids")
            if isinstance(raw_ids, list):
                found.update(str(unit_id) for unit_id in raw_ids)
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(entity)
    return found


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def _output_entities(output: RunOutput) -> dict[EntityKindBucket, list[dict[str, Any]]]:
    return {
        "token_primitive": [copy.deepcopy(item) for item in output.primitive_tokens],
        "token_semantic": [copy.deepcopy(item) for item in output.semantic_tokens],
        "asset": [
            copy.deepcopy(item)
            for item in output.catalog_rest.get("assets", [])
            if isinstance(item, dict)
        ],
        "subtype": [
            copy.deepcopy(item)
            for item in output.catalog_rest.get("subtypes", [])
            if isinstance(item, dict)
        ],
        "template": [
            copy.deepcopy(item)
            for item in output.catalog_rest.get("templates", [])
            if isinstance(item, dict)
        ],
        "rule": [
            copy.deepcopy(rule)
            for group in output.rule_groups
            for rule in group.rules
            if isinstance(rule, dict)
        ],
    }


def _collect_occurrences(
    runs: Sequence[VerifiedRunInput],
    *,
    active_only: bool,
) -> dict[EntityKindBucket, list[_Occurrence]]:
    buckets: dict[EntityKindBucket, list[_Occurrence]] = {
        "token_primitive": [],
        "token_semantic": [],
        "asset": [],
        "subtype": [],
        "template": [],
        "rule": [],
    }
    for run in runs:
        run_id = run.output.variant.run_id
        catalog = build_token_catalog(run.output)
        quarantined = {entry.entity_id for entry in run.provenance.quarantine}
        entities = _output_entities(run.output)
        for kind in ("token_primitive", "token_semantic", "asset", "subtype", "template"):
            for entity in entities[kind]:
                if active_only and str(entity.get("id", "")) in quarantined:
                    continue
                buckets[kind].append(
                    _Occurrence(
                        run_id=run_id,
                        kind=kind,
                        entity=entity,
                        catalog=catalog,
                    )
                )
        for group in run.output.rule_groups:
            for rule in group.rules:
                if not isinstance(rule, dict):
                    continue
                entity = copy.deepcopy(rule)
                if active_only and str(entity.get("id", "")) in quarantined:
                    continue
                buckets["rule"].append(
                    _Occurrence(
                        run_id=run_id,
                        kind="rule",
                        entity=entity,
                        catalog=catalog,
                        group_id=group.group_id,
                    )
                )
    for kind in buckets:
        buckets[kind].sort(key=lambda item: (item.run_id, _occurrence_sort_key(item)))
    return buckets


def _collapse_per_run(items: Sequence[_Occurrence]) -> tuple[_Occurrence, ...]:
    by_run: dict[str, list[_Occurrence]] = {}
    for item in items:
        by_run.setdefault(item.run_id, []).append(item)
    return tuple(
        sorted(by_run[run_id], key=_occurrence_sort_key)[0]
        for run_id in sorted(by_run)
    )


def _generic_groups(
    occurrences: Sequence[_Occurrence],
    kind: EntityKindBucket,
) -> list[_EntityGroup]:
    keyed: dict[tuple[Any, ...], list[_Occurrence]] = {}
    for item in occurrences:
        if kind == "token_primitive":
            key: tuple[Any, ...] = _primitive_match_key(item.entity)
        elif kind == "asset":
            key = _asset_match_key(item.entity)
        elif kind == "subtype":
            key = _named_match_key(item.entity, "unknown")
        elif kind == "template":
            key = _named_match_key(item.entity, "template")
        else:
            raise ValueError(f"unsupported generic group kind: {kind}")
        keyed.setdefault(key, []).append(item)
    return [
        _EntityGroup(
            kind=kind,
            occurrences=_collapse_per_run(raw),
            raw_occurrences=tuple(sorted(raw, key=lambda item: (item.run_id, _occurrence_sort_key(item)))),
        )
        for _, raw in sorted(keyed.items())
    ]


def _semantic_groups(
    occurrences: Sequence[_Occurrence],
    champion_run: str,
) -> tuple[list[_EntityGroup], list[Conflict]]:
    by_path: dict[str, list[_Occurrence]] = {}
    for item in occurrences:
        path, _ = semantic_match_key(item.entity, item.catalog)
        by_path.setdefault(path, []).append(item)

    groups: list[_EntityGroup] = []
    conflicts: list[Conflict] = []
    for path in sorted(by_path):
        raw = sorted(by_path[path], key=lambda item: (item.run_id, _occurrence_sort_key(item)))
        selected = _collapse_per_run(raw)
        raw_by_canon: dict[str, list[_Occurrence]] = {}
        for item in raw:
            _, canon = semantic_match_key(item.entity, item.catalog)
            raw_by_canon.setdefault(canon, []).append(item)
        for left_canon, right_canon in itertools.combinations(sorted(raw_by_canon), 2):
            left = sorted(raw_by_canon[left_canon], key=_occurrence_sort_key)[0]
            right = sorted(raw_by_canon[right_canon], key=_occurrence_sort_key)[0]
            conflicts.append(
                Conflict(
                    kind="intra_token",
                    element_path=path,
                    a_id=str(left.entity.get("id", "")),
                    b_id=str(right.entity.get("id", "")),
                    overlap_guard={},
                    detail=(
                        f"semantic token path {path!r} has conflicting resolved defaults "
                        f"{left_canon!r} vs {right_canon!r}"
                    ),
                )
            )
        base = next(
            (item for item in selected if item.run_id == champion_run),
            selected[0],
        )
        _, chosen_canon = semantic_match_key(base.entity, base.catalog)
        kept = tuple(
            item
            for item in selected
            if semantic_match_key(item.entity, item.catalog)[1] == chosen_canon
        )
        kept_raw = tuple(
            item
            for item in raw
            if semantic_match_key(item.entity, item.catalog)[1] == chosen_canon
        )
        groups.append(
            _EntityGroup(
                kind="token_semantic",
                occurrences=kept,
                raw_occurrences=kept_raw,
            )
        )
    return groups, conflicts


def _rule_groups(occurrences: Sequence[_Occurrence]) -> list[_EntityGroup]:
    by_identity: dict[tuple[str, str, str], list[_Occurrence]] = {}
    for item in occurrences:
        rule_class, path = _rule_identity(item.entity)
        by_identity.setdefault((item.group_id or "", rule_class, path), []).append(item)

    groups: list[_EntityGroup] = []
    for identity in sorted(by_identity):
        pending = list(_collapse_per_run(by_identity[identity]))
        while pending:
            seed = pending.pop(0)
            seed_units = _claimed_unit_ids(seed.entity)
            matched = [seed]
            rest: list[_Occurrence] = []
            for item in pending:
                if _jaccard(seed_units, _claimed_unit_ids(item.entity)) >= 0.5:
                    matched.append(item)
                else:
                    rest.append(item)
            pending = rest
            groups.append(
                _EntityGroup(
                    kind="rule",
                    occurrences=tuple(sorted(matched, key=lambda item: item.run_id)),
                    raw_occurrences=tuple(sorted(matched, key=lambda item: item.run_id)),
                    group_id=identity[0],
                )
            )
    return groups


def _active_entity_ids(run: VerifiedRunInput) -> set[str]:
    quarantined = {entry.entity_id for entry in run.provenance.quarantine}
    return {
        str(entity.get("id", ""))
        for entities in _output_entities(run.output).values()
        for entity in entities
        if str(entity.get("id", "")) not in quarantined
    }


def _value_verified_rate(run: VerifiedRunInput) -> float:
    active_ids = _active_entity_ids(run)
    concrete = [
        record
        for entity_id in sorted(active_ids)
        for record in run.provenance.records_by_entity.get(entity_id, [])
        if is_concrete_value_field(record.field) and record.value_check.status != "n/a"
    ]
    if not concrete:
        return 0.0
    return sum(record.verification == "value_verified" for record in concrete) / len(concrete)


def _required_unit_coverage(run: VerifiedRunInput, labels: Sequence[UnitLabel]) -> float:
    required = {label.unit_id for label in labels if label.required}
    if not required:
        return 0.0
    active_ids = _active_entity_ids(run)
    covered = {
        unit_id
        for unit_id, entity_ids in run.provenance.by_unit.items()
        if unit_id in required and any(entity_id in active_ids for entity_id in entity_ids)
    }
    return len(covered) / len(required)


def _select_champion_run(
    runs: Sequence[VerifiedRunInput],
    labels: Sequence[UnitLabel],
) -> str:
    scored = [
        (
            _value_verified_rate(run),
            _required_unit_coverage(run, labels),
            run.output.variant.run_id,
        )
        for run in runs
    ]
    scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return scored[0][2]


def _champion_occurrence(
    group: _EntityGroup,
    champion_run: str,
) -> _Occurrence:
    return next(
        (item for item in group.occurrences if item.run_id == champion_run),
        group.occurrences[0],
    )


def _vote_key(present: bool, value: Any) -> str:
    return _json_key({"present": present, "value": value if present else None})


def _majority_field(
    group: _EntityGroup,
    field: str,
    champion: _Occurrence,
) -> tuple[bool, Any, float]:
    votes = [
        (field in item.entity, item.entity.get(field))
        for item in group.occurrences
    ]
    counts: Counter[str] = Counter(_vote_key(present, value) for present, value in votes)
    best_count = max(counts.values())
    tied = sorted(key for key, count in counts.items() if count == best_count)
    champion_key = _vote_key(field in champion.entity, champion.entity.get(field))
    chosen_key = champion_key if champion_key in tied else tied[0]
    chosen = json.loads(chosen_key)
    return bool(chosen["present"]), chosen["value"], best_count / len(votes)


def _is_evidence_key(key: str) -> bool:
    return key == "evidence" or key.endswith("_evidence")


def _merge_evidence(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    unit_counts: Counter[str] = Counter()
    quote_counts: Counter[str] = Counter()
    for item in items:
        unit_ids = item.get("unit_ids")
        if isinstance(unit_ids, list):
            unit_counts.update(str(unit_id) for unit_id in set(unit_ids))
        quotes = item.get("quotes")
        if isinstance(quotes, list):
            quote_counts.update(str(quote) for quote in set(quotes))
    return {
        "unit_ids": sorted(unit_counts, key=lambda unit_id: (-unit_counts[unit_id], unit_id)),
        "quotes": sorted(quote_counts, key=lambda quote: (-quote_counts[quote], quote)),
    }


def _merge_evidence_per_run(
    items: Sequence[tuple[str, Mapping[str, Any]]],
) -> dict[str, Any]:
    """Union duplicate emissions inside a run, then count citations once per run."""
    by_run: dict[str, list[Mapping[str, Any]]] = {}
    for run_id, evidence in items:
        by_run.setdefault(run_id, []).append(evidence)
    collapsed: list[dict[str, Any]] = []
    for run_id in sorted(by_run):
        unit_ids: set[str] = set()
        quotes: set[str] = set()
        for evidence in by_run[run_id]:
            raw_unit_ids = evidence.get("unit_ids")
            if isinstance(raw_unit_ids, list):
                unit_ids.update(str(unit_id) for unit_id in raw_unit_ids)
            raw_quotes = evidence.get("quotes")
            if isinstance(raw_quotes, list):
                quotes.update(str(quote) for quote in raw_quotes)
        collapsed.append({"unit_ids": sorted(unit_ids), "quotes": sorted(quotes)})
    return _merge_evidence(collapsed)


def _merge_top_level(
    base: dict[str, Any],
    group: _EntityGroup,
    champion: _Occurrence,
    *,
    protected: set[str],
) -> dict[str, float]:
    agreement: dict[str, float] = {}
    fields = sorted(
        {
            key
            for item in group.occurrences
            for key in item.entity
            if key not in protected
            and key not in {"id", "value", "aliases", "extraction_meta"}
            and not _is_evidence_key(key)
        }
    )
    for field in fields:
        present, value, ratio = _majority_field(group, field, champion)
        if present:
            base[field] = copy.deepcopy(value)
        else:
            base.pop(field, None)
        agreement[field] = ratio

    evidence_fields = sorted(
        {
            key
            for item in group.occurrences
            for key, value in item.entity.items()
            if _is_evidence_key(key) and isinstance(value, dict)
        }
    )
    for field in evidence_fields:
        evidence = [
            (item.run_id, cast(dict[str, Any], item.entity[field]))
            for item in group.raw_occurrences
            if isinstance(item.entity.get(field), dict)
        ]
        base[field] = _merge_evidence_per_run(evidence)
    return agreement


def _merge_aliases(
    base: dict[str, Any],
    raw_occurrences: Sequence[_Occurrence],
) -> None:
    aliases: set[str] = set()
    existing = base.get("aliases")
    if isinstance(existing, list):
        aliases.update(str(alias) for alias in existing)
    for item in raw_occurrences:
        raw_aliases = item.entity.get("aliases")
        if isinstance(raw_aliases, list):
            aliases.update(str(alias) for alias in raw_aliases)
        for field in ("key", "name"):
            alternate = item.entity.get(field)
            chosen = base.get(field)
            if isinstance(alternate, str) and alternate and alternate != chosen:
                aliases.add(alternate)
    if aliases:
        base["aliases"] = sorted(aliases)


def _majority_values(
    values_by_run: Mapping[str, Any],
    champion_run: str,
) -> tuple[Any, float]:
    counts: Counter[str] = Counter(_json_key(value) for value in values_by_run.values())
    best_count = max(counts.values())
    tied = sorted(key for key, count in counts.items() if count == best_count)
    champion_key = (
        _json_key(values_by_run[champion_run])
        if champion_run in values_by_run
        else ""
    )
    chosen_key = champion_key if champion_key in tied else tied[0]
    return json.loads(chosen_key), best_count / len(values_by_run)


def _guard_hash(variant: Mapping[str, Any]) -> str:
    return stable_hash(normalize_guard(variant.get("when")))


def _merge_variants(
    group: _EntityGroup,
    champion_run: str,
) -> tuple[list[dict[str, Any]] | None, dict[str, float], list[Conflict]]:
    candidates_by_guard_run: dict[
        str,
        dict[str, list[tuple[_Occurrence, dict[str, Any]]]],
    ] = {}
    saw_variants = False
    for item in group.raw_occurrences:
        value = item.entity.get("value")
        variants = value.get("variants") if isinstance(value, dict) else None
        if not isinstance(variants, list):
            continue
        saw_variants = True
        grouped: dict[str, list[dict[str, Any]]] = {}
        for variant in variants:
            if isinstance(variant, dict):
                grouped.setdefault(_guard_hash(variant), []).append(variant)
        for guard_hash, candidates in grouped.items():
            for candidate in candidates:
                candidates_by_guard_run.setdefault(guard_hash, {}).setdefault(
                    item.run_id,
                    [],
                ).append((item, candidate))

    if not saw_variants:
        return None, {}, []

    merged: list[dict[str, Any]] = []
    agreement: dict[str, float] = {}
    conflicts: list[Conflict] = []
    for guard_hash in sorted(candidates_by_guard_run):
        candidates_by_run = candidates_by_guard_run[guard_hash]
        entries = {
            run_id: sorted(
                candidates,
                key=lambda pair: (_occurrence_sort_key(pair[0]), _json_key(pair[1])),
            )[0]
            for run_id, candidates in candidates_by_run.items()
        }
        values = {run_id: variant.get("value") for run_id, (_, variant) in entries.items()}
        chosen_value, _ = _majority_values(values, champion_run)
        base_entry = entries.get(champion_run) or entries[sorted(entries)[0]]
        base = copy.deepcopy(base_entry[1])
        base["value"] = chosen_value
        evidence = [
            (run_id, cast(dict[str, Any], variant["evidence"]))
            for run_id, candidates in candidates_by_run.items()
            for _, variant in candidates
            if isinstance(variant.get("evidence"), dict)
        ]
        if evidence:
            base["evidence"] = _merge_evidence_per_run(evidence)
        distinct = sorted({_json_key(value) for value in values.values()})
        if len(distinct) > 1:
            left = entries[sorted(entries)[0]][0]
            right = entries[sorted(entries)[-1]][0]
            conflicts.append(
                Conflict(
                    kind="intra_token",
                    element_path=_element_path(group.occurrences[0].entity),
                    a_id=str(left.entity.get("id", "")),
                    b_id=str(right.entity.get("id", "")),
                    overlap_guard=normalize_guard(base.get("when")),
                    detail=f"variant guard {guard_hash} has conflicting values across runs",
                )
            )
        merged.append(base)
        agreement[f"value.variants[{guard_hash}]"] = len(entries) / group.support
    return merged, agreement, conflicts


def _confidence(
    support: int,
    runs: int,
    default_agreement: float,
) -> Literal["high", "medium", "low"]:
    if default_agreement <= 0.5:
        return "low"
    if support == runs:
        return "high"
    return "medium" if support > runs / 2 else "low"


def _merge_group(
    group: _EntityGroup,
    champion_run: str,
    runs: int,
) -> tuple[dict[str, Any], list[Conflict]]:
    champion = _champion_occurrence(group, champion_run)
    base = copy.deepcopy(champion.entity)
    protected = {"rule_text", "intent"} if group.kind == "rule" else set()
    agreement = _merge_top_level(base, group, champion, protected=protected)
    conflicts: list[Conflict] = []
    default_agreement = 1.0

    if group.kind in {"token_primitive", "token_semantic"}:
        values_by_run = {
            item.run_id: _default_raw(item.entity)
            for item in group.occurrences
        }
        chosen_default, default_agreement = _majority_values(values_by_run, champion_run)
        value = base.get("value")
        if not isinstance(value, dict):
            value = {}
            base["value"] = value
        value["default"] = chosen_default
        agreement["value.default"] = default_agreement
        default_evidence = [
            (
                item.run_id,
                cast(dict[str, Any], item.entity["value"]["default_evidence"]),
            )
            for item in group.raw_occurrences
            if isinstance(item.entity.get("value"), dict)
            and isinstance(item.entity["value"].get("default_evidence"), dict)
        ]
        if default_evidence:
            value["default_evidence"] = _merge_evidence_per_run(default_evidence)
        variants, variant_agreement, variant_conflicts = _merge_variants(group, champion_run)
        value["variants"] = variants
        agreement.update(variant_agreement)
        conflicts.extend(variant_conflicts)
        _merge_aliases(base, group.raw_occurrences)

    champion_units = _claimed_unit_ids(champion.entity)
    dissent = sorted(
        {
            unit_id
            for item in group.occurrences
            if item.run_id != champion_run
            for unit_id in _claimed_unit_ids(item.entity)
        }
        - champion_units
    )
    meta = ExtractionMeta(
        runs=runs,
        support=group.support,
        field_agreement=agreement,
        confidence=_confidence(group.support, runs, default_agreement),
        champion_run=champion_run,
        dissent_unit_ids=dissent,
    )
    base["extraction_meta"] = meta.model_dump(mode="json")
    return base, conflicts


def _verified_unit_ids(item: _Occurrence, runs_by_id: Mapping[str, VerifiedRunInput]) -> set[str]:
    provenance = runs_by_id[item.run_id].provenance
    entity_id = str(item.entity.get("id", ""))
    return {
        unit_id
        for unit_id, entity_ids in provenance.by_unit.items()
        if entity_id in entity_ids
    }


def _group_verified_unit_ids(
    group: _EntityGroup,
    runs_by_id: Mapping[str, VerifiedRunInput],
) -> set[str]:
    return {
        unit_id
        for item in group.raw_occurrences
        for unit_id in _verified_unit_ids(item, runs_by_id)
    }


def _is_value_verified(item: _Occurrence, runs_by_id: Mapping[str, VerifiedRunInput]) -> bool:
    entity_id = str(item.entity.get("id", ""))
    return any(
        record.verification == "value_verified"
        for record in runs_by_id[item.run_id].provenance.records_by_entity.get(entity_id, [])
    )


def _finding(item: _Occurrence, reason: str) -> Finding:
    entity_id = str(item.entity.get("id", ""))
    payload = {
        "entity_id": entity_id,
        "kind": item.kind,
        "run_id": item.run_id,
        "reason": reason,
    }
    return Finding(
        finding_id=f"f_ensemble_{stable_hash(payload)[:12]}",
        round=0,
        finding_type="fabrication",
        severity="minor",
        target_entity_id=entity_id,
        unit_ids=sorted(_claimed_unit_ids(item.entity)),
        description=reason,
        resolution="open",
    )


def _validate_runs(runs: Sequence[VerifiedRunInput]) -> list[VerifiedRunInput]:
    if not runs:
        raise ValueError("reconcile_ensemble requires at least one verified run")
    run_ids = [run.output.variant.run_id for run in runs]
    if any(not run_id.strip() for run_id in run_ids):
        raise ValueError("reconcile_ensemble requires non-empty run_ids")
    duplicates = sorted(run_id for run_id, count in Counter(run_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate run_ids: {', '.join(duplicates)}")
    return sorted(runs, key=lambda run: run.output.variant.run_id)


def _rule_group_handoff(
    runs: Sequence[VerifiedRunInput],
    champion_run: str,
) -> tuple[dict[str, str], dict[str, list[dict[str, Any]]]]:
    """Build group source mappings and champion-base/strict-majority relations.

    Relation rows are untyped dictionaries, so S4 never injects support metadata.
    Exact canonical JSON duplicates count once per run. Every champion row survives;
    a distinct nonchampion row survives only when present in a strict majority of
    runs that emitted the group.
    """
    doc_refs: dict[str, str] = {}
    relations: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    group_runs: dict[str, set[str]] = {}
    for run in runs:
        run_id = run.output.variant.run_id
        for group in sorted(
            run.output.rule_groups,
            key=lambda item: (item.group_id, item.doc_ref),
        ):
            existing = doc_refs.get(group.group_id)
            if existing is not None and existing != group.doc_ref:
                raise RuleGroupMappingError(
                    f"rule group {group.group_id!r} maps to conflicting doc_refs "
                    f"{existing!r} and {group.doc_ref!r}"
                )
            doc_refs[group.group_id] = group.doc_ref
            group_runs.setdefault(group.group_id, set()).add(run_id)
            per_run = relations.setdefault(group.group_id, {}).setdefault(run_id, {})
            for relation in group.relations:
                key = _json_key(relation)
                per_run.setdefault(key, copy.deepcopy(relation))

    merged: dict[str, list[dict[str, Any]]] = {}
    for group_id in sorted(doc_refs):
        by_run = relations.get(group_id, {})
        support: Counter[str] = Counter(
            key
            for run_id in sorted(by_run)
            for key in by_run[run_id]
        )
        champion_keys = set(by_run.get(champion_run, {}))
        denominator = len(group_runs[group_id])
        kept_keys = sorted(
            key
            for key, count in support.items()
            if key in champion_keys or count > denominator / 2
        )
        rows: list[dict[str, Any]] = []
        for key in kept_keys:
            if key in by_run.get(champion_run, {}):
                rows.append(copy.deepcopy(by_run[champion_run][key]))
                continue
            source_run = next(run_id for run_id in sorted(by_run) if key in by_run[run_id])
            rows.append(copy.deepcopy(by_run[source_run][key]))
        merged[group_id] = rows
    return dict(sorted(doc_refs.items())), merged


def reconcile_ensemble(
    runs: Sequence[VerifiedRunInput],
    units: Sequence[SourceUnit],
    labels: Sequence[UnitLabel],
    *,
    fuzzy_min_ratio: float | None = None,
) -> EnsembleResult:
    """Merge K verified runs; each run contributes at most one vote per entity group."""
    ordered_runs = _validate_runs(runs)
    runs_by_id = {run.output.variant.run_id: run for run in ordered_runs}
    runs_count = len(ordered_runs)
    champion_run = _select_champion_run(ordered_runs, labels)
    rule_group_doc_refs, relations_by_group = _rule_group_handoff(
        ordered_runs,
        champion_run,
    )
    active = _collect_occurrences(ordered_runs, active_only=True)
    all_occurrences = _collect_occurrences(ordered_runs, active_only=False)

    groups: list[_EntityGroup] = []
    conflicts: list[Conflict] = []
    for kind in ("token_primitive", "asset", "subtype", "template"):
        groups.extend(_generic_groups(active[kind], kind))
    semantic_groups, semantic_conflicts = _semantic_groups(
        active["token_semantic"],
        champion_run,
    )
    groups.extend(semantic_groups)
    groups.extend(_rule_groups(active["rule"]))
    conflicts.extend(semantic_conflicts)
    groups.sort(
        key=lambda group: (
            group.kind,
            group.group_id or "",
            _occurrence_sort_key(group.occurrences[0]),
        )
    )

    merged: dict[EntityKindBucket, list[dict[str, Any]]] = {
        "token_primitive": [],
        "token_semantic": [],
        "asset": [],
        "subtype": [],
        "template": [],
        "rule": [],
    }
    merged_rule_groups: dict[str, list[dict[str, Any]]] = {}
    findings: list[Finding] = []

    consensus_groups = [group for group in groups if group.support > 1]
    singleton_groups = [group for group in groups if group.support == 1]
    consensus_units = {
        unit_id
        for group in consensus_groups
        for unit_id in _group_verified_unit_ids(group, runs_by_id)
    }

    def materialize(group: _EntityGroup) -> None:
        entity, entity_conflicts = _merge_group(group, champion_run, runs_count)
        conflicts.extend(entity_conflicts)
        merged[group.kind].append(entity)
        if group.kind == "rule":
            merged_rule_groups.setdefault(group.group_id or "unknown", []).append(entity)

    for group in consensus_groups:
        materialize(group)

    required_ids = {label.unit_id for label in labels if label.required}
    for group in singleton_groups:
        item = group.occurrences[0]
        unique_required = (
            _group_verified_unit_ids(group, runs_by_id) & required_ids
        ) - consensus_units
        if _is_value_verified(item, runs_by_id) and unique_required:
            materialize(group)
        else:
            entity_id = str(item.entity.get("id", ""))
            findings.append(
                _finding(
                    item,
                    (
                        f"{entity_id}: singleton from run {item.run_id} rejected "
                        "(requires value_verified and a unique required-unit claim)"
                    ),
                )
            )

    active_keys = {
        (item.run_id, item.kind, str(item.entity.get("id", "")))
        for items in active.values()
        for item in items
    }
    seen_quarantined: set[tuple[str, EntityKindBucket, str]] = set()
    for items in all_occurrences.values():
        for item in items:
            key = (item.run_id, item.kind, str(item.entity.get("id", "")))
            if key in active_keys or key in seen_quarantined:
                continue
            seen_quarantined.add(key)
            findings.append(
                _finding(
                    item,
                    f"{key[2]}: quarantined S3 entity from run {item.run_id} rejected",
                )
            )

    for kind in merged:
        merged[kind].sort(key=lambda entity: str(entity.get("id", "")))
    for group_id in merged_rule_groups:
        merged_rule_groups[group_id].sort(key=lambda entity: str(entity.get("id", "")))

    entities_for_verify: dict[str, list[dict[str, Any]]] = {
        kind: entities for kind, entities in merged.items()
    }
    ratio = settings.FUZZY_MATCH_MIN_RATIO if fuzzy_min_ratio is None else fuzzy_min_ratio
    provenance = verify_entities(entities_for_verify, units, fuzzy_min_ratio=ratio)
    final_quarantined = {entry.entity_id for entry in provenance.quarantine}
    for kind in merged:
        merged[kind] = [
            entity
            for entity in merged[kind]
            if str(entity.get("id", "")) not in final_quarantined
        ]
    for group_id in list(merged_rule_groups):
        merged_rule_groups[group_id] = [
            rule
            for rule in merged_rule_groups[group_id]
            if str(rule.get("id", "")) not in final_quarantined
        ]
        if not merged_rule_groups[group_id]:
            del merged_rule_groups[group_id]

    conflicts.sort(
        key=lambda item: (item.kind, item.element_path or "", item.a_id, item.b_id, item.detail)
    )
    findings.sort(key=lambda item: item.finding_id)
    return EnsembleResult(
        champion_run=champion_run,
        tokens_primitive=merged["token_primitive"],
        tokens_semantic=merged["token_semantic"],
        assets=merged["asset"],
        subtypes=merged["subtype"],
        templates=merged["template"],
        rule_groups=dict(sorted(merged_rule_groups.items())),
        rule_group_doc_refs=rule_group_doc_refs,
        relations_by_group=relations_by_group,
        conflicts=conflicts,
        findings=findings,
        provenance=provenance,
    )


def build_verified_run(
    output: RunOutput,
    units: Sequence[SourceUnit],
    *,
    fuzzy_min_ratio: float | None = None,
) -> VerifiedRunInput:
    """Construct a verified run input from raw extraction output."""
    entities: dict[str, list[dict[str, Any]]] = {
        kind: bucket for kind, bucket in _output_entities(output).items()
    }
    ratio = settings.FUZZY_MATCH_MIN_RATIO if fuzzy_min_ratio is None else fuzzy_min_ratio
    provenance = verify_entities(entities, units, fuzzy_min_ratio=ratio)
    return VerifiedRunInput(output=output, provenance=provenance)


def write_candidates(result: EnsembleResult, work_dir: Path) -> None:
    """Persist active candidate artifacts under ``work_dir/candidates``."""
    candidates_dir = work_dir / "candidates"
    rules_dir = candidates_dir / "rules"
    quarantined = {entry.entity_id for entry in result.provenance.quarantine}
    tokens = sorted(
        [
            *[
                {**entity, "kind": "primitive"}
                for entity in result.tokens_primitive
                if str(entity.get("id", "")) not in quarantined
            ],
            *[
                {**entity, "kind": "semantic"}
                for entity in result.tokens_semantic
                if str(entity.get("id", "")) not in quarantined
            ],
        ],
        key=lambda entity: (str(entity.get("kind", "")), str(entity.get("id", ""))),
    )
    payload_by_name = {
        "tokens": tokens,
        "assets": [
            entity
            for entity in sorted(result.assets, key=lambda item: str(item.get("id", "")))
            if str(entity.get("id", "")) not in quarantined
        ],
        "subtypes": [
            entity
            for entity in sorted(result.subtypes, key=lambda item: str(item.get("id", "")))
            if str(entity.get("id", "")) not in quarantined
        ],
        "templates": [
            entity
            for entity in sorted(result.templates, key=lambda item: str(item.get("id", "")))
            if str(entity.get("id", "")) not in quarantined
        ],
    }
    expected_top = {f"{name}.json" for name in payload_by_name}
    if candidates_dir.exists():
        for path in sorted(candidates_dir.glob("*.json")):
            if path.name not in expected_top:
                path.unlink()
    for name, payload in payload_by_name.items():
        atomic_write_json(candidates_dir / f"{name}.json", payload)

    rule_payloads = {
        group_id: [
            rule
            for rule in rules
            if str(rule.get("id", "")) not in quarantined
        ]
        for group_id, rules in result.rule_groups.items()
    }
    rule_payloads = {
        group_id: rules
        for group_id, rules in rule_payloads.items()
        if rules
    }
    expected_rules = {f"{group_id}.json" for group_id in rule_payloads}
    if rules_dir.exists():
        for path in sorted(rules_dir.glob("*.json")):
            if path.name not in expected_rules:
                path.unlink()
    for group_id in sorted(rule_payloads):
        atomic_write_json(rules_dir / f"{group_id}.json", rule_payloads[group_id])
