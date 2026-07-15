"""§5.6 S5 adversarial critic — findings, mechanical screen, patcher, re-verification.

Usage: ``await run_critic(brand, units, candidates, client=..., usage=..., work_dir=...)``.

WP-11 reuses ``apply_patch_to_candidates`` and ``triage_findings`` for the gap loop.
"""

from __future__ import annotations

import asyncio
import copy
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, Protocol, get_args

from pydantic import BaseModel, Field, ValidationError
from shared.llm import Usage

from .. import settings
from ..contracts import (
    SCHEMA_VERSION,
    EntityKind,
    Finding,
    FindingType,
    Patch,
    PatchOp,
    RunVariant,
    SourceUnit,
    atomic_write_json,
    slugify,
    stable_hash,
    write_jsonl,
)
from .provenance import (
    EntitiesByKind,
    ProvenanceError,
    ProvenanceResult,
    verify_entities,
)
from .prompts import load_prompt
from .runner import (
    DEFAULT_CACHE_ROOT,
    CacheContext,
    LLMClient,
    complete_json_cached,
    render_units,
)

STAGE_VERSION = "1.0.0"

PROMPT_CRITIC_CATALOG = "critic_catalog"
PROMPT_CRITIC_RULES = "critic_rules"

_MECHANICAL_TYPES = frozenset({"fabrication", "value_distortion"})
_FINDING_TYPES = frozenset(get_args(FindingType))
_CATALOG_KINDS: tuple[EntityKind, ...] = (
    "token_primitive",
    "token_semantic",
    "asset",
    "subtype",
    "template",
)
# ponytail: coarse char budget before splitting primitive tokens by token_type.
_MAX_CATALOG_CHARS = 120_000


class CriticError(Exception):
    """Base error for critic stage."""


class CriticResponseError(CriticError):
    """LLM critic output failed strict Finding validation."""

    def __init__(self, message: str, *, round_num: int | None = None) -> None:
        super().__init__(message)
        self.round_num = round_num


class UnknownCandidateBucketError(CriticError):
    """Raised when ``candidates`` is missing a required bucket key."""


class PatchApplicationError(CriticError):
    """Raised when a patch references missing entities or malformed payload."""


class CandidateAdapterError(CriticError):
    """Raised when ensemble candidates lack an explicit rule-group source mapping."""


class EnsembleCandidateSource(Protocol):
    """WP-09 fields consumed by ``CandidateSet.from_ensemble``."""

    champion_run: str
    tokens_primitive: list[dict[str, Any]]
    tokens_semantic: list[dict[str, Any]]
    assets: list[dict[str, Any]]
    subtypes: list[dict[str, Any]]
    templates: list[dict[str, Any]]
    rule_groups: dict[str, list[dict[str, Any]]]


PatchAuditStatus = Literal[
    "applied",
    "rejected_mechanical",
    "rejected_verification",
]


class PatchAuditRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    finding_id: str
    round: int
    op: PatchOp
    target_entity_ids: list[str] = Field(default_factory=list)
    before_hash: str
    after_hash: str | None = None
    status: PatchAuditStatus
    detail: str | None = None


class CandidateSet(BaseModel):
    """Typed stage boundary from WP-09 ensemble reconciler (K=1 champion output).

    Bucket keys match ``provenance.verify_entities`` entity kinds. Despite its legacy
    name, ``rules_by_doc_ref`` is keyed by opaque WP-09 group id; the separate
    ``rule_group_doc_refs`` map drives per-blob prompts. WP-09 persists these under
    ``work/candidates/{tokens,assets,subtypes,templates}.json`` and
    ``work/candidates/rules/{group_id}.json``.
    """

    schema_version: str = SCHEMA_VERSION
    token_primitive: list[dict[str, Any]] = Field(default_factory=list)
    token_semantic: list[dict[str, Any]] = Field(default_factory=list)
    asset: list[dict[str, Any]] = Field(default_factory=list)
    subtype: list[dict[str, Any]] = Field(default_factory=list)
    template: list[dict[str, Any]] = Field(default_factory=list)
    rules_by_doc_ref: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    rule_group_doc_refs: dict[str, str] = Field(default_factory=dict)
    champion_run_id: str = "r0"

    @classmethod
    def from_ensemble(
        cls,
        result: EnsembleCandidateSource,
        *,
        rule_group_doc_refs: Mapping[str, str] | None = None,
    ) -> CandidateSet:
        """Adapt WP-09 output without conflating group ids and source doc refs."""
        result_mapping = getattr(result, "rule_group_doc_refs", None)
        raw_mapping: Mapping[str, str] | None = rule_group_doc_refs
        if raw_mapping is None and isinstance(result_mapping, Mapping):
            if all(
                isinstance(group_id, str) and isinstance(doc_ref, str)
                for group_id, doc_ref in result_mapping.items()
            ):
                raw_mapping = result_mapping
        groups = {
            str(group_id): sorted(
                (copy.deepcopy(rule) for rule in rules),
                key=lambda rule: str(rule.get("id", "")),
            )
            for group_id, rules in sorted(result.rule_groups.items())
        }
        mapping = dict(sorted((raw_mapping or {}).items()))
        missing = sorted(set(groups) - set(mapping))
        if missing:
            raise CandidateAdapterError(
                f"missing doc_ref mapping for rule group {missing[0]!r}"
            )
        return cls(
            champion_run_id=result.champion_run,
            token_primitive=sorted(
                copy.deepcopy(result.tokens_primitive),
                key=lambda entity: str(entity.get("id", "")),
            ),
            token_semantic=sorted(
                copy.deepcopy(result.tokens_semantic),
                key=lambda entity: str(entity.get("id", "")),
            ),
            asset=sorted(
                copy.deepcopy(result.assets),
                key=lambda entity: str(entity.get("id", "")),
            ),
            subtype=sorted(
                copy.deepcopy(result.subtypes),
                key=lambda entity: str(entity.get("id", "")),
            ),
            template=sorted(
                copy.deepcopy(result.templates),
                key=lambda entity: str(entity.get("id", "")),
            ),
            rules_by_doc_ref=groups,
            rule_group_doc_refs={
                group_id: mapping[group_id]
                for group_id in sorted(groups)
            },
        )

    def to_entities_by_kind(self) -> dict[str, list[dict[str, Any]]]:
        rules = [
            rule
            for group_id in sorted(self.rules_by_doc_ref)
            for rule in sorted(
                self.rules_by_doc_ref[group_id],
                key=lambda item: str(item.get("id", "")),
            )
        ]
        return {
            "token_primitive": sorted(
                self.token_primitive,
                key=lambda item: str(item.get("id", "")),
            ),
            "token_semantic": sorted(
                self.token_semantic,
                key=lambda item: str(item.get("id", "")),
            ),
            "asset": sorted(self.asset, key=lambda item: str(item.get("id", ""))),
            "subtype": sorted(
                self.subtype,
                key=lambda item: str(item.get("id", "")),
            ),
            "template": sorted(
                self.template,
                key=lambda item: str(item.get("id", "")),
            ),
            "rule": rules,
        }


class CriticResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    candidates: CandidateSet
    findings: list[Finding]
    audit: list[PatchAuditRecord]
    rounds_completed: int


def _critic_variant(champion_run_id: str = "r0") -> RunVariant:
    return RunVariant(
        run_id=champion_run_id,
        model=settings.CRITIC_MODEL,
        temperature=0.0,
        replicate=0,
    )


def _bucket_for_kind(kind: EntityKind) -> str:
    if kind == "rule":
        return "rules_by_doc_ref"
    return kind


def _entity_list(candidates: CandidateSet, kind: EntityKind) -> list[dict[str, Any]]:
    bucket = _bucket_for_kind(kind)
    if bucket == "rules_by_doc_ref":
        return [
            rule
            for doc_ref in sorted(candidates.rules_by_doc_ref)
            for rule in candidates.rules_by_doc_ref[doc_ref]
        ]
    value = getattr(candidates, kind)
    if not isinstance(value, list):
        raise UnknownCandidateBucketError(f"missing list bucket for {kind!r}")
    return value


def _find_entity(
    candidates: CandidateSet,
    entity_id: str,
) -> tuple[EntityKind, dict[str, Any], str | None]:
    for kind in _CATALOG_KINDS:
        for entity in _entity_list(candidates, kind):
            if str(entity.get("id")) == entity_id:
                return kind, entity, None
    for doc_ref in sorted(candidates.rules_by_doc_ref):
        for rule in candidates.rules_by_doc_ref[doc_ref]:
            if str(rule.get("id")) == entity_id:
                return "rule", rule, doc_ref
    raise PatchApplicationError(f"entity not found: {entity_id}")


def _sorted_unit_ids(values: Sequence[str]) -> list[str]:
    return sorted(set(values))


def merge_evidence(
    left: Mapping[str, Any] | None,
    right: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Union unit_ids (sorted) and quotes (stable dedupe) for evidence dicts."""
    merged_unit_ids: list[str] = []
    merged_quotes: list[str] = []
    seen_quotes: set[str] = set()
    for evidence in (left, right):
        if not isinstance(evidence, Mapping):
            continue
        for unit_id in evidence.get("unit_ids", []):
            if isinstance(unit_id, str) and unit_id not in merged_unit_ids:
                merged_unit_ids.append(unit_id)
        for quote in evidence.get("quotes", []):
            if isinstance(quote, str) and quote not in seen_quotes:
                seen_quotes.add(quote)
                merged_quotes.append(quote)
    return {"unit_ids": _sorted_unit_ids(merged_unit_ids), "quotes": merged_quotes}


def _deep_merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in overlay.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(value, dict)
            and key.endswith("_evidence")
        ):
            out[key] = merge_evidence(out[key], value)
        elif key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge_dict(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _is_evidence_key(key: str) -> bool:
    return key == "evidence" or key.endswith("_evidence")


def _normalized_guard(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key).strip().casefold(): _normalized_guard(inner)
            for key, inner in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        normalized = [_normalized_guard(item) for item in value]
        return sorted(normalized, key=stable_hash)
    if isinstance(value, str):
        return " ".join(value.split()).casefold()
    return value


def _guard_key(variant: Mapping[str, Any]) -> str:
    return stable_hash(_normalized_guard(variant.get("when")))


def _merge_evidence_tree(base: Any, other: Any) -> Any:
    """Keep entity structure while recursively unioning matching evidence objects."""
    if isinstance(base, dict) and isinstance(other, dict):
        out = copy.deepcopy(base)
        for key, other_value in other.items():
            if _is_evidence_key(key) and isinstance(other_value, Mapping):
                current = out.get(key)
                out[key] = merge_evidence(
                    current if isinstance(current, Mapping) else None,
                    other_value,
                )
            elif key in out and isinstance(out[key], (dict, list)):
                out[key] = _merge_evidence_tree(out[key], other_value)
        return out
    if isinstance(base, list) and isinstance(other, list):
        list_out = copy.deepcopy(base)
        is_variant_list = all(
            isinstance(item, dict) and "when" in item
            for item in [*list_out, *other]
        )
        if not is_variant_list:
            for index, other_item in enumerate(other):
                if index < len(list_out):
                    list_out[index] = _merge_evidence_tree(
                        list_out[index],
                        other_item,
                    )
            return list_out
        variant_indexes = {
            _guard_key(item): index
            for index, item in enumerate(list_out)
            if isinstance(item, dict) and "when" in item
        }
        for other_item in other:
            if not isinstance(other_item, dict):
                continue
            guard_key = _guard_key(other_item)
            target_index = variant_indexes.get(guard_key)
            if target_index is not None:
                list_out[target_index] = _merge_evidence_tree(
                    list_out[target_index],
                    other_item,
                )
            else:
                variant_indexes[guard_key] = len(list_out)
                list_out.append(copy.deepcopy(other_item))
        return sorted(
            list_out,
            key=lambda item: (
                _guard_key(item) if isinstance(item, Mapping) else stable_hash(item),
                stable_hash(item),
            ),
        )
    return copy.deepcopy(base)


def _merge_entity_records(keep: dict[str, Any], others: Sequence[dict[str, Any]]) -> dict[str, Any]:
    merged = copy.deepcopy(keep)
    for other in others:
        merged = _merge_evidence_tree(merged, other)
    return merged


def _entity_index(
    candidates: CandidateSet,
) -> dict[str, tuple[EntityKind, dict[str, Any], str | None]]:
    index: dict[str, tuple[EntityKind, dict[str, Any], str | None]] = {}
    for kind in _CATALOG_KINDS:
        for entity in _entity_list(candidates, kind):
            entity_id = entity.get("id")
            if not isinstance(entity_id, str) or not entity_id:
                raise PatchApplicationError(f"{kind} entity missing non-empty string id")
            if entity_id in index:
                raise PatchApplicationError(f"duplicate candidate entity id: {entity_id}")
            index[entity_id] = (kind, entity, None)
    for group_id in sorted(candidates.rules_by_doc_ref):
        for entity in candidates.rules_by_doc_ref[group_id]:
            entity_id = entity.get("id")
            if not isinstance(entity_id, str) or not entity_id:
                raise PatchApplicationError(
                    f"rule entity in {group_id!r} missing non-empty string id"
                )
            if entity_id in index:
                raise PatchApplicationError(f"duplicate candidate entity id: {entity_id}")
            index[entity_id] = ("rule", entity, group_id)
    return index


def _target_records(
    candidates: CandidateSet,
    patch: Patch,
    *,
    exactly_one: bool = False,
) -> list[tuple[str, EntityKind, dict[str, Any], str | None]]:
    target_ids = patch.target_entity_ids
    if not target_ids:
        raise PatchApplicationError(f"{patch.op} patch requires target_entity_ids")
    if len(set(target_ids)) != len(target_ids):
        raise PatchApplicationError(f"{patch.op} patch target ids must be unique")
    if exactly_one and len(target_ids) != 1:
        raise PatchApplicationError(
            f"{patch.op} patch requires exactly one target_entity_id"
        )
    index = _entity_index(candidates)
    records: list[tuple[str, EntityKind, dict[str, Any], str | None]] = []
    for entity_id in target_ids:
        record = index.get(entity_id)
        if record is None:
            raise PatchApplicationError(f"entity not found: {entity_id}")
        kind, entity, doc_ref = record
        if kind != patch.entity_kind:
            raise PatchApplicationError(
                f"{patch.op} patch kind {patch.entity_kind!r} does not match "
                f"entity {entity_id!r} kind {kind!r}"
            )
        records.append((entity_id, kind, entity, doc_ref))
    return records


def _required_entity_id(entity: Mapping[str, Any], *, context: str) -> str:
    entity_id = entity.get("id")
    if not isinstance(entity_id, str) or not entity_id:
        raise PatchApplicationError(f"{context} requires a non-empty string id")
    return entity_id


def apply_patch_to_candidates(candidates: CandidateSet, patch: Patch) -> CandidateSet:
    """Pure candidate-dict patch ops (add/update/delete/split/merge)."""
    updated = candidates.model_copy(deep=True)
    op = patch.op
    kind = patch.entity_kind
    current_index = _entity_index(updated)

    if op == "add":
        entity = copy.deepcopy(patch.payload)
        entity_id = _required_entity_id(entity, context="add patch payload")
        if entity_id in current_index:
            raise PatchApplicationError(f"add patch id already exists: {entity_id}")
        if kind == "rule":
            doc_ref = entity.pop("doc_ref", None)
            if not isinstance(doc_ref, str) or not doc_ref:
                raise PatchApplicationError(
                    f"add rule patch requires doc_ref in payload for {entity_id}"
                )
            requested_group = entity.pop("group_id", None)
            matching_groups = sorted(
                group_id
                for group_id, mapped_doc_ref in updated.rule_group_doc_refs.items()
                if mapped_doc_ref == doc_ref
            )
            if requested_group is not None:
                if not isinstance(requested_group, str) or not requested_group:
                    raise PatchApplicationError(
                        f"add rule patch group_id must be a non-empty string for {entity_id}"
                    )
                if updated.rule_group_doc_refs.get(requested_group) != doc_ref:
                    raise PatchApplicationError(
                        f"add rule patch group_id {requested_group!r} is not mapped "
                        f"to doc_ref {doc_ref!r}"
                    )
                group_id = requested_group
            elif len(matching_groups) == 1:
                group_id = matching_groups[0]
            else:
                raise PatchApplicationError(
                    f"add rule patch needs one mapped group_id for doc_ref {doc_ref!r}"
                )
            updated.rules_by_doc_ref.setdefault(group_id, []).append(entity)
            updated.rules_by_doc_ref[group_id] = sorted(
                updated.rules_by_doc_ref[group_id],
                key=lambda item: str(item.get("id", "")),
            )
        else:
            bucket = getattr(updated, kind)
            bucket.append(entity)
            setattr(
                updated,
                kind,
                sorted(bucket, key=lambda item: str(item.get("id", ""))),
            )
        _entity_index(updated)
        return updated

    if op == "delete":
        targets = _target_records(updated, patch)
        for entity_id, kind_found, _, target_group_id in targets:
            if kind_found == "rule" and target_group_id is not None:
                updated.rules_by_doc_ref[target_group_id] = [
                    rule
                    for rule in updated.rules_by_doc_ref[target_group_id]
                    if str(rule.get("id")) != entity_id
                ]
            else:
                bucket = getattr(updated, kind_found)
                setattr(
                    updated,
                    kind_found,
                    [entity for entity in bucket if str(entity.get("id")) != entity_id],
                )
        _entity_index(updated)
        return updated

    if op == "update":
        entity_id, kind_found, entity, target_group_id = _target_records(
            updated,
            patch,
            exactly_one=True,
        )[0]
        merged = _deep_merge_dict(entity, patch.payload)
        _required_entity_id(merged, context="updated entity")
        if kind_found == "rule" and target_group_id is not None:
            updated.rules_by_doc_ref[target_group_id] = [
                merged if str(rule.get("id")) == entity_id else rule
                for rule in updated.rules_by_doc_ref[target_group_id]
            ]
        else:
            bucket = getattr(updated, kind_found)
            setattr(
                updated,
                kind_found,
                [merged if str(item.get("id")) == entity_id else item for item in bucket],
            )
        _entity_index(updated)
        return updated

    if op == "split":
        entity_id, kind_found, _, target_group_id = _target_records(
            updated,
            patch,
            exactly_one=True,
        )[0]
        raw_entities = patch.payload.get("entities")
        if not isinstance(raw_entities, list) or not raw_entities:
            raise PatchApplicationError("split patch payload must include entities list")
        if not all(isinstance(item, dict) for item in raw_entities):
            raise PatchApplicationError("split patch entities must all be dicts")
        replacements = [copy.deepcopy(item) for item in raw_entities]
        replacement_ids = [
            _required_entity_id(item, context="split replacement")
            for item in replacements
        ]
        if len(set(replacement_ids)) != len(replacement_ids):
            raise PatchApplicationError("split replacement ids must be unique")
        collisions = sorted((set(replacement_ids) - {entity_id}) & set(current_index))
        if collisions:
            raise PatchApplicationError(
                f"split replacement id collides with candidate: {collisions[0]}"
            )
        if kind_found == "rule" and target_group_id is not None:
            for replacement in replacements:
                replacement.pop("doc_ref", None)
                replacement.pop("group_id", None)
            without = [rule for rule in updated.rules_by_doc_ref[target_group_id] if str(rule.get("id")) != entity_id]
            updated.rules_by_doc_ref[target_group_id] = sorted(
                without + replacements,
                key=lambda item: str(item.get("id", "")),
            )
        else:
            bucket = getattr(updated, kind_found)
            without = [item for item in bucket if str(item.get("id")) != entity_id]
            setattr(
                updated,
                kind_found,
                sorted(without + replacements, key=lambda item: str(item.get("id", ""))),
            )
        _entity_index(updated)
        return updated

    if op == "merge":
        targets = _target_records(updated, patch)
        if len(targets) < 2:
            raise PatchApplicationError("merge patch requires at least two targets")
        keep_id = patch.payload.get("keep")
        if not isinstance(keep_id, str):
            raise PatchApplicationError("merge patch payload must include keep id")
        if keep_id not in patch.target_entity_ids:
            raise PatchApplicationError("merge keep id must be among target_entity_ids")
        rule_group_ids = {
            group_id
            for _, _, _, group_id in targets
            if group_id is not None
        }
        rule_doc_refs = {
            updated.rule_group_doc_refs.get(group_id)
            for group_id in rule_group_ids
        }
        if kind == "rule" and None in rule_doc_refs:
            missing_group = next(
                group_id
                for group_id in sorted(rule_group_ids)
                if group_id not in updated.rule_group_doc_refs
            )
            raise PatchApplicationError(
                f"rule group {missing_group!r} has no doc_ref mapping"
            )
        if kind == "rule" and len(rule_doc_refs) != 1:
            raise PatchApplicationError("merge rule targets must share one doc_ref")
        entities = [entity for _, _, entity, _ in targets]
        keep_entity = current_index[keep_id][1]
        others = [entity for entity in entities if str(entity.get("id")) != keep_id]
        merged = _merge_entity_records(keep_entity, others)
        remove_ids = {str(entity.get("id")) for entity in entities if str(entity.get("id")) != keep_id}
        if kind == "rule":
            keep_group = current_index[keep_id][2]
            if keep_group is None:
                raise PatchApplicationError(
                    f"merge keep rule {keep_id!r} has no group id"
                )
            for group_id in sorted(rule_group_ids):
                rules = [
                    rule
                    for rule in updated.rules_by_doc_ref[group_id]
                    if str(rule.get("id")) not in remove_ids
                    and str(rule.get("id")) != keep_id
                ]
                if group_id == keep_group:
                    rules.append(merged)
                updated.rules_by_doc_ref[group_id] = sorted(
                    rules,
                    key=lambda item: str(item.get("id", "")),
                )
        else:
            bucket = getattr(updated, kind)
            setattr(
                updated,
                kind,
                sorted(
                    [
                        merged if str(item.get("id")) == keep_id else item
                        for item in bucket
                        if str(item.get("id")) not in remove_ids
                    ],
                    key=lambda item: str(item.get("id", "")),
                ),
            )
        _entity_index(updated)
        return updated

    raise PatchApplicationError(f"unsupported patch op: {op!r}")


def _entity_is_value_verified(entity_id: str, result: ProvenanceResult) -> bool:
    for record in result.records_by_entity.get(entity_id, []):
        if record.verification == "value_verified":
            return True
    return False


def mechanical_screen_finding(
    finding: Finding,
    candidates: CandidateSet,
    units: Sequence[SourceUnit],
) -> bool:
    """Return True when fabrication/distortion targets a value_verified entity."""
    if finding.finding_type not in _MECHANICAL_TYPES:
        return False
    if not finding.target_entity_id:
        return False
    try:
        kind_found, entity, _ = _find_entity(candidates, finding.target_entity_id)
    except PatchApplicationError:
        return False
    scoped: EntitiesByKind = {kind_found: [entity]}
    verify = verify_entities(scoped, units)
    return _entity_is_value_verified(finding.target_entity_id, verify)


def _resulting_entity_ids(patch: Patch) -> list[str]:
    if patch.op == "add":
        entity_id = patch.payload.get("id")
        return [str(entity_id)] if isinstance(entity_id, str) else []
    if patch.op == "update":
        entity_id = patch.payload.get("id", patch.target_entity_ids[0])
        return [str(entity_id)] if isinstance(entity_id, str) else []
    if patch.op == "split":
        entities = patch.payload.get("entities")
        if not isinstance(entities, list):
            return []
        return [
            str(entity["id"])
            for entity in entities
            if isinstance(entity, dict) and isinstance(entity.get("id"), str)
        ]
    if patch.op == "merge":
        keep_id = patch.payload.get("keep")
        return [str(keep_id)] if isinstance(keep_id, str) else list(patch.target_entity_ids)
    return []


_PATH_PART_RE = re.compile(r"([^.[]+)|\[(\d+)\]")


def _field_value(entity: dict[str, Any], field: str) -> tuple[bool, Any]:
    if not field:
        return True, entity
    current: Any = entity
    for name, index_text in _PATH_PART_RE.findall(field):
        if name:
            if not isinstance(current, dict) or name not in current:
                return False, None
            current = current[name]
        else:
            index = int(index_text)
            if not isinstance(current, list) or index >= len(current):
                return False, None
            current = current[index]
    return True, current


def _patch_product_failed(
    candidates: CandidateSet,
    entity_ids: Sequence[str],
    result: ProvenanceResult,
) -> bool:
    index = _entity_index(candidates)
    for entity_id in entity_ids:
        indexed = index.get(entity_id)
        if indexed is None:
            return True
        entity = indexed[1]
        records = result.records_by_entity.get(entity_id, [])
        if not records:
            return True
        for record in records:
            present, value = _field_value(entity, record.field)
            if not present or value is None:
                continue
            if isinstance(value, dict) and "$ref" in value:
                continue
            if (
                record.verification == "unverified"
                or record.value_check.status == "fail"
            ):
                return True
    return False


def _before_hash(candidates: CandidateSet, patch: Patch) -> str:
    if patch.op == "add":
        return stable_hash({"op": "add", "kind": patch.entity_kind, "payload": patch.payload})
    ids = sorted(patch.target_entity_ids)
    snapshots = []
    for entity_id in ids:
        _, entity, _ = _find_entity(candidates, entity_id)
        snapshots.append(entity)
    return stable_hash({"ids": ids, "entities": snapshots})


def _audit_before_hash(candidates: CandidateSet, patch: Patch) -> str:
    try:
        return _before_hash(candidates, patch)
    except PatchApplicationError:
        return stable_hash({"candidates": candidates, "patch": patch})


def _rejected_attempt_hash(
    candidates: CandidateSet,
    patch: Patch,
    error: PatchApplicationError | ProvenanceError,
) -> str:
    return stable_hash(
        {
            "candidates": candidates,
            "patch": patch,
            "error": str(error),
        }
    )


def _after_hash(
    candidates: CandidateSet,
    patch: Patch,
    resulting_ids: Sequence[str],
) -> str:
    if patch.op == "delete":
        return stable_hash(
            {
                "deleted_ids": sorted(patch.target_entity_ids),
                "remaining_candidates": candidates,
            }
        )
    index = _entity_index(candidates)
    products = [
        index[entity_id][1]
        for entity_id in sorted(resulting_ids)
        if entity_id in index
    ]
    return stable_hash({"ids": sorted(resulting_ids), "entities": products})


def triage_findings(
    findings: Sequence[Finding],
    candidates: CandidateSet,
    units: Sequence[SourceUnit],
    *,
    round_num: int,
) -> tuple[CandidateSet, list[Finding], list[PatchAuditRecord]]:
    """Mechanical screen, patch apply, and S3 re-verification for one round."""
    current = candidates.model_copy(deep=True)
    resolved: list[Finding] = []
    audit: list[PatchAuditRecord] = []

    for finding in sorted(findings, key=lambda item: item.finding_id):
        item = finding.model_copy(deep=True)
        item.round = round_num
        if item.proposed_patch is None:
            item.resolution = "open"
            resolved.append(item)
            continue

        patch = item.proposed_patch
        if mechanical_screen_finding(item, current, units):
            before = _audit_before_hash(current, patch)
            item.resolution = "rejected_mechanical"
            audit.append(
                PatchAuditRecord(
                    finding_id=item.finding_id,
                    round=round_num,
                    op=patch.op,
                    target_entity_ids=list(patch.target_entity_ids),
                    before_hash=before,
                    after_hash=None,
                    status="rejected_mechanical",
                )
            )
            resolved.append(item)
            continue

        before = _audit_before_hash(current, patch)
        try:
            trial = apply_patch_to_candidates(current, patch)
            verify = verify_entities(trial.to_entities_by_kind(), units)
            resulting_ids = _resulting_entity_ids(patch)
            attempted_after = _after_hash(trial, patch, resulting_ids)
            if patch.op == "delete":
                remaining_ids = set(_entity_index(trial))
                if remaining_ids.intersection(patch.target_entity_ids):
                    raise PatchApplicationError(
                        f"delete patch failed to remove {patch.target_entity_ids!r}"
                    )
                failed = False
            else:
                failed = _patch_product_failed(
                    trial,
                    resulting_ids,
                    verify,
                )
        except (PatchApplicationError, ProvenanceError) as exc:
            item.resolution = "rejected_verification"
            audit.append(
                PatchAuditRecord(
                    finding_id=item.finding_id,
                    round=round_num,
                    op=patch.op,
                    target_entity_ids=list(patch.target_entity_ids),
                    before_hash=before,
                    after_hash=_rejected_attempt_hash(current, patch, exc),
                    status="rejected_verification",
                    detail=str(exc),
                )
            )
            resolved.append(item)
            continue
        if failed:
            item.resolution = "rejected_verification"
            audit.append(
                PatchAuditRecord(
                    finding_id=item.finding_id,
                    round=round_num,
                    op=patch.op,
                    target_entity_ids=list(patch.target_entity_ids),
                    before_hash=before,
                    after_hash=attempted_after,
                    status="rejected_verification",
                )
            )
            resolved.append(item)
            continue

        current = trial
        item.resolution = "applied"
        audit.append(
            PatchAuditRecord(
                finding_id=item.finding_id,
                round=round_num,
                op=patch.op,
                target_entity_ids=list(patch.target_entity_ids),
                before_hash=before,
                after_hash=attempted_after,
                status="applied",
            )
        )
        resolved.append(item)

    return current, resolved, audit


def _defer_open_findings(findings: Sequence[Finding]) -> list[Finding]:
    out: list[Finding] = []
    for finding in findings:
        item = finding.model_copy(deep=True)
        if item.resolution == "open" and item.severity in {"major", "critical"}:
            item.resolution = "deferred_human"
        out.append(item)
    return out


def parse_finding(raw: Mapping[str, Any], *, round_num: int) -> Finding:
    unknown = sorted(set(raw) - set(Finding.model_fields))
    if unknown:
        raise CriticResponseError(
            f"finding has unknown field: {unknown[0]}",
            round_num=round_num,
        )
    raw_patch = raw.get("proposed_patch")
    if isinstance(raw_patch, Mapping):
        unknown_patch = sorted(set(raw_patch) - set(Patch.model_fields))
        if unknown_patch:
            raise CriticResponseError(
                f"patch has unknown field: {unknown_patch[0]}",
                round_num=round_num,
            )
    payload = dict(raw)
    finding_type = payload.get("finding_type")
    # ponytail: critic_rules.md lists prose bullets the LLM copies as finding_type;
    # coerce unknowns to other and keep the original label in description.
    if isinstance(finding_type, str) and finding_type not in _FINDING_TYPES:
        description = str(payload.get("description") or "").strip()
        label = f"[{finding_type}]"
        payload["description"] = f"{label} {description}".strip() if description else label
        payload["finding_type"] = "other"
    try:
        finding = Finding.model_validate(
            {
                **payload,
                "round": round_num,
                "resolution": payload.get("resolution", "open"),
            }
        )
    except ValidationError as exc:
        raise CriticResponseError(
            f"invalid finding: {exc}",
            round_num=round_num,
        ) from exc
    return finding


def parse_findings_response(
    raw: Any,
    *,
    round_num: int,
) -> list[Finding]:
    if not isinstance(raw, dict):
        raise CriticResponseError("critic response must be a JSON object", round_num=round_num)
    unknown = sorted(set(raw) - {"findings"})
    if unknown:
        raise CriticResponseError(
            f"critic response has unknown field: {unknown[0]}",
            round_num=round_num,
        )
    rows = raw.get("findings")
    if rows is None:
        raise CriticResponseError("critic response missing findings", round_num=round_num)
    if not isinstance(rows, list):
        raise CriticResponseError("critic findings must be a list", round_num=round_num)
    findings: list[Finding] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise CriticResponseError(
                f"critic finding row {index} must be an object",
                round_num=round_num,
            )
        finding = parse_finding(row, round_num=round_num)
        if finding.finding_id in seen_ids:
            raise CriticResponseError(
                f"duplicate finding_id in response: {finding.finding_id}",
                round_num=round_num,
            )
        seen_ids.add(finding.finding_id)
        findings.append(finding)
    return findings


def _normalize_finding_ids(
    brand: str,
    findings: Sequence[Finding],
    *,
    start_seq: int,
) -> tuple[list[Finding], int]:
    normalized: list[Finding] = []
    next_seq = start_seq
    brand_slug = slugify(brand)
    for finding in findings:
        item = finding.model_copy(deep=True)
        item.finding_id = f"f_{brand_slug}_{next_seq:04d}"
        normalized.append(item)
        next_seq += 1
    return normalized, next_seq


def _token_lines(tokens: Sequence[dict[str, Any]]) -> str:
    lines: list[str] = []
    for token in sorted(tokens, key=lambda item: str(item.get("id", ""))):
        value = token.get("value") or {}
        default = value.get("default") if isinstance(value, dict) else value
        lines.append(
            f"  {token.get('id')}  key={token.get('key')}  default={json.dumps(default, default=str)}"
        )
    return "\n".join(lines)


def _entity_lines(kind: str, entities: Sequence[dict[str, Any]]) -> str:
    lines = [f"{kind} ({len(entities)}):"]
    for entity in sorted(entities, key=lambda item: str(item.get("id", ""))):
        lines.append(f"  {entity.get('id')}  name={entity.get('name', entity.get('key', ''))}")
    return "\n".join(lines)


def render_catalog_summary(candidates: CandidateSet) -> str:
    sections = [
        "primitive tokens:",
        _token_lines(candidates.token_primitive),
        "semantic tokens:",
        _token_lines(candidates.token_semantic),
        _entity_lines("assets", candidates.asset),
        _entity_lines("subtypes", candidates.subtype),
        _entity_lines("templates", candidates.template),
    ]
    return "\n".join(sections)


def _chunk_catalog_sections(candidates: CandidateSet) -> list[str]:
    full = render_catalog_summary(candidates)
    if len(full) <= _MAX_CATALOG_CHARS:
        return [full]
    by_type: dict[str, list[dict[str, Any]]] = {}
    for token in sorted(
        candidates.token_primitive,
        key=lambda item: str(item.get("id", "")),
    ):
        token_type = str(token.get("token_type", "unknown"))
        by_type.setdefault(token_type, []).append(token)
    chunks: list[str] = []
    for token_type in sorted(by_type):
        partial = CandidateSet(
            token_primitive=by_type[token_type],
            token_semantic=[],
            asset=[],
            subtype=[],
            template=[],
            rules_by_doc_ref={},
        )
        chunks.append(render_catalog_summary(partial))
    if not chunks:
        return [full]
    tail = CandidateSet(
        token_primitive=[],
        token_semantic=list(candidates.token_semantic),
        asset=list(candidates.asset),
        subtype=list(candidates.subtype),
        template=list(candidates.template),
        rules_by_doc_ref={},
    )
    chunks.append(render_catalog_summary(tail))
    return chunks


def _rules_lines(rules: Sequence[dict[str, Any]]) -> str:
    lines: list[str] = []
    for rule in sorted(rules, key=lambda item: str(item.get("id", ""))):
        lines.append(
            f"  {rule.get('id')}  class={rule.get('rule_class')}  "
            f"hardness={rule.get('hardness')}  polarity={rule.get('polarity')}"
        )
    return "\n".join(lines)


def _units_by_doc_ref(units: Sequence[SourceUnit]) -> dict[str, list[SourceUnit]]:
    grouped: dict[str, list[SourceUnit]] = {}
    for unit in units:
        grouped.setdefault(unit.doc_ref, []).append(unit)
    return {
        doc_ref: sorted(items, key=lambda item: (item.ordinal, item.unit_id))
        for doc_ref, items in sorted(grouped.items())
    }


def _rules_for_doc_ref(
    candidates: CandidateSet,
    doc_ref: str,
) -> list[dict[str, Any]]:
    return sorted(
        [
            rule
            for group_id, mapped_doc_ref in sorted(
                candidates.rule_group_doc_refs.items()
            )
            if mapped_doc_ref == doc_ref
            for rule in candidates.rules_by_doc_ref.get(group_id, [])
        ],
        key=lambda item: str(item.get("id", "")),
    )


def _validate_rule_group_mapping(candidates: CandidateSet) -> None:
    missing = sorted(
        set(candidates.rules_by_doc_ref) - set(candidates.rule_group_doc_refs)
    )
    if missing:
        raise CandidateAdapterError(
            f"missing doc_ref mapping for rule group {missing[0]!r}"
        )


def _rule_artifact_filename(group_id: str) -> str:
    if (
        not group_id
        or Path(group_id).name != group_id
        or group_id in {".", ".."}
    ):
        raise CandidateAdapterError(f"unsafe rule group id: {group_id!r}")
    return f"{group_id}.json"


def write_critic_artifacts(
    work_dir: Path,
    *,
    findings: Sequence[Finding],
    audit: Sequence[PatchAuditRecord],
    candidates: CandidateSet,
) -> None:
    write_jsonl(
        work_dir / "findings.jsonl",
        sorted(findings, key=lambda item: (item.round, item.finding_id)),
    )
    audit_dir = work_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        audit_dir / "patches.jsonl",
        sorted(audit, key=lambda item: (item.round, item.finding_id)),
    )
    candidates_dir = work_dir / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    tokens = sorted(
        [
            *[
                {**entity, "kind": "primitive"}
                for entity in candidates.token_primitive
            ],
            *[
                {**entity, "kind": "semantic"}
                for entity in candidates.token_semantic
            ],
        ],
        key=lambda entity: (
            str(entity.get("kind", "")),
            str(entity.get("id", "")),
        ),
    )
    atomic_write_json(candidates_dir / "tokens.json", tokens)
    atomic_write_json(
        candidates_dir / "assets.json",
        sorted(candidates.asset, key=lambda entity: str(entity.get("id", ""))),
    )
    atomic_write_json(
        candidates_dir / "subtypes.json",
        sorted(candidates.subtype, key=lambda entity: str(entity.get("id", ""))),
    )
    atomic_write_json(
        candidates_dir / "templates.json",
        sorted(candidates.template, key=lambda entity: str(entity.get("id", ""))),
    )
    rules_dir = candidates_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    expected_rule_files = {
        _rule_artifact_filename(group_id)
        for group_id in candidates.rules_by_doc_ref
    }
    for path in sorted(rules_dir.glob("*.json")):
        if path.name not in expected_rule_files:
            path.unlink()
    for group_id in sorted(candidates.rules_by_doc_ref):
        atomic_write_json(
            rules_dir / _rule_artifact_filename(group_id),
            sorted(
                candidates.rules_by_doc_ref[group_id],
                key=lambda entity: str(entity.get("id", "")),
            ),
        )


async def _critique_round(
    *,
    brand: str,
    units: Sequence[SourceUnit],
    candidates: CandidateSet,
    client: LLMClient,
    usage: Usage,
    round_num: int,
    variant: RunVariant,
    prompts_dir: Path | None,
    cache_root: Path,
    semaphore: asyncio.Semaphore,
) -> list[Finding]:
    ordered_units = sorted(
        units,
        key=lambda unit: (unit.doc_ref, unit.ordinal, unit.unit_id),
    )
    all_units_text = render_units(ordered_units)
    tpl_catalog = load_prompt(PROMPT_CRITIC_CATALOG, prompts_dir)
    tpl_rules = load_prompt(PROMPT_CRITIC_RULES, prompts_dir)
    findings: list[Finding] = []

    for catalog_chunk in _chunk_catalog_sections(candidates):
        async with semaphore:
            rendered = tpl_catalog.render(
                brand=brand,
                units=all_units_text,
                catalog=catalog_chunk,
            )
            ctx = CacheContext(
                brand=brand,
                variant=variant,
                prompt_name=PROMPT_CRITIC_CATALOG,
                template=tpl_catalog,
                content_hash="",
                cache_root=cache_root,
            )
            raw = await complete_json_cached(
                client,
                ctx,
                rendered.system,
                rendered.user,
                usage,
                extra={"critic_round": round_num, "catalog_chunk": stable_hash(catalog_chunk)},
            )
            findings.extend(parse_findings_response(raw, round_num=round_num))

    grouped = _units_by_doc_ref(ordered_units)
    for doc_ref in sorted(grouped):
        async with semaphore:
            blob_units = grouped[doc_ref]
            rules = _rules_for_doc_ref(candidates, doc_ref)
            group_ids = sorted(
                group_id
                for group_id, mapped_doc_ref in candidates.rule_group_doc_refs.items()
                if mapped_doc_ref == doc_ref
            )
            rendered = tpl_rules.render(
                brand=brand,
                doc_ref=doc_ref,
                group_ids=", ".join(group_ids) or "(none)",
                units=render_units(blob_units),
                rules=_rules_lines(rules),
            )
            ctx = CacheContext(
                brand=brand,
                variant=variant,
                prompt_name=PROMPT_CRITIC_RULES,
                template=tpl_rules,
                content_hash="",
                cache_root=cache_root,
            )
            raw = await complete_json_cached(
                client,
                ctx,
                rendered.system,
                rendered.user,
                usage,
                extra={"critic_round": round_num, "doc_ref": doc_ref},
            )
            findings.extend(parse_findings_response(raw, round_num=round_num))

    return findings


async def run_critic(
    brand: str,
    units: list[SourceUnit],
    candidates: CandidateSet,
    usage: Usage,
    client: LLMClient,
    *,
    work_dir: Path | None = None,
    prompts_dir: Path | None = None,
    cache_root: Path | None = None,
    champion_run_id: str | None = None,
    max_rounds: int | None = None,
    concurrency: int | None = None,
) -> CriticResult:
    """Run ≤ ``MAX_CRITIC_ROUNDS`` adversarial critique with patch triage."""
    rounds = settings.MAX_CRITIC_ROUNDS if max_rounds is None else max_rounds
    if rounds <= 0:
        raise ValueError(f"max_rounds must be positive, got {rounds}")

    sem_limit = concurrency if concurrency is not None else settings.CONCURRENCY
    if sem_limit <= 0:
        raise ValueError(f"concurrency must be greater than zero, got {sem_limit}")
    _validate_rule_group_mapping(candidates)
    semaphore = asyncio.Semaphore(sem_limit)
    variant = _critic_variant(champion_run_id or candidates.champion_run_id)
    resolved_cache_root = cache_root or DEFAULT_CACHE_ROOT

    current = candidates.model_copy(deep=True)
    all_findings: list[Finding] = []
    all_audit: list[PatchAuditRecord] = []
    next_finding_seq = 1

    for round_num in range(1, rounds + 1):
        raw_findings = await _critique_round(
            brand=brand,
            units=units,
            candidates=current,
            client=client,
            usage=usage,
            round_num=round_num,
            variant=variant,
            prompts_dir=prompts_dir,
            cache_root=resolved_cache_root,
            semaphore=semaphore,
        )
        normalized_findings, next_finding_seq = _normalize_finding_ids(
            brand,
            raw_findings,
            start_seq=next_finding_seq,
        )
        current, round_findings, round_audit = triage_findings(
            normalized_findings,
            current,
            units,
            round_num=round_num,
        )
        all_findings.extend(round_findings)
        all_audit.extend(round_audit)

    final_findings = _defer_open_findings(all_findings)
    result = CriticResult(
        candidates=current,
        findings=final_findings,
        audit=all_audit,
        rounds_completed=rounds,
    )
    if work_dir is not None:
        write_critic_artifacts(
            work_dir,
            findings=final_findings,
            audit=all_audit,
            candidates=current,
        )
    return result
