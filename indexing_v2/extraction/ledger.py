"""§5.7 S6 coverage ledger, triage queues, and gap loop (WP-11).

Hand-off surfaces for sibling workers:
- WP-10: ``EntityPatcher`` protocol — production patch merge + S3 re-verify (critic path)
- WP-16/17: ``build_ledger``, ``LedgerDocument``, ``write_ledger``, ``rebuild_triage``,
  ``append_triage_items``, ``run_gap_loop``, ``CandidatesBundle``
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from shared.llm import Usage

from .. import settings
from ..contracts import (
    SCHEMA_VERSION,
    Conflict,
    CoverageReport,
    EntityKind,
    Finding,
    LedgerRow,
    Patch,
    ProvenanceRecord,
    RunVariant,
    SourceUnit,
    TriageItem,
    UnitLabel,
    atomic_write_json,
    read_jsonl,
    stable_hash,
    write_jsonl,
)
from .critic import CandidateSet, PatchApplicationError, triage_findings
from .ensemble import build_token_catalog, semantic_match_key
from .prompts import load_prompt
from .provenance import ProvenanceResult, verify_entities
from .runner import (
    CacheContext,
    LLMClient,
    RuleGroupOutput,
    RunOutput,
    _group_id,
    complete_json_cached,
    normalize_rule_groups,
    render_units,
)

if TYPE_CHECKING:
    from ..consistency.pairwise import PairwiseAnalysisResult
    from ..consistency.smt import SmtAnalysisResult

STAGE_VERSION = "ledger-v2.0.0"
PROMPT_GAP_PATCH = "gap_patch"
PROMPT_RULES_CLUSTER = "rules_cluster"
_GAP_CONTEXT_RADIUS = 1
_VERIFIED_LEVELS = frozenset({"span_verified", "value_verified"})
_CLASS_A_CONFLICT_KINDS = frozenset(
    {"hard_hard", "equal_specificity", "verbatim_clash"}
)

LedgerStatus = Literal["covered", "unclaimed", "over_claimed", "excluded"]
GapStopReason = Literal["empty_queue", "zero_progress", "max_rounds"]


class GapLoopInputError(ValueError):
    """The gap-loop caller supplied inconsistent stage inputs."""


class GapPayloadError(ValueError):
    """The LLM gap response failed strict boundary validation."""


class CandidatesBundleAdapterError(ValueError):
    """An ensemble result cannot be adapted without losing group identity."""


@runtime_checkable
class EnsembleCandidates(Protocol):
    champion_run: str
    tokens_primitive: list[dict[str, Any]]
    tokens_semantic: list[dict[str, Any]]
    assets: list[dict[str, Any]]
    subtypes: list[dict[str, Any]]
    templates: list[dict[str, Any]]
    rule_groups: dict[str, list[dict[str, Any]]]
    rule_group_doc_refs: dict[str, str]
    relations_by_group: dict[str, list[dict[str, Any]]]
    conflicts: list[Conflict]


class SoftMismatch(BaseModel):
    """Local ledger extension — not part of shared ``CoverageReport`` contract."""

    schema_version: str = SCHEMA_VERSION
    unit_id: str
    entity_id: str
    entity_kind: EntityKind
    expected_yield: list[EntityKind]


class LedgerDocument(BaseModel):
    """On-disk ``work/ledger.json`` shape (coverage + local soft mismatches)."""

    schema_version: str = SCHEMA_VERSION
    soft_mismatches: list[SoftMismatch] = Field(default_factory=list)
    coverage: CoverageReport


class CandidatesBundle(BaseModel):
    """Merged candidate set post-S4 (and post-critic when available)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: str = SCHEMA_VERSION
    brand: str
    tokens_primitive: list[dict[str, Any]] = Field(default_factory=list)
    tokens_semantic: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    subtypes: list[dict[str, Any]] = Field(default_factory=list)
    templates: list[dict[str, Any]] = Field(default_factory=list)
    rules_by_group: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    rule_group_doc_refs: dict[str, str] = Field(default_factory=dict)
    relations_by_group: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    conflicts: list[Conflict] = Field(default_factory=list)
    units_by_id: dict[str, SourceUnit] = Field(default_factory=dict)
    champion_variant: RunVariant | None = None

    @classmethod
    def from_ensemble(
        cls,
        result: EnsembleCandidates,
        *,
        brand: str,
        units: Sequence[SourceUnit],
        champion_variant: RunVariant,
    ) -> CandidatesBundle:
        if champion_variant.run_id != result.champion_run:
            raise CandidatesBundleAdapterError(
                "champion_variant.run_id does not match ensemble champion_run: "
                f"{champion_variant.run_id!r} != {result.champion_run!r}"
            )
        units_by_id = {
            unit.unit_id: unit
            for unit in sorted(units, key=lambda item: item.unit_id)
        }
        if len(units_by_id) != len(units):
            raise CandidatesBundleAdapterError(
                "ensemble adapter units contain duplicate unit_ids"
            )
        rule_groups = {
            group_id: _sorted_entities(rules)
            for group_id, rules in sorted(result.rule_groups.items())
        }
        relations_by_group = {
            group_id: sorted(
                (dict(relation) for relation in relations),
                key=stable_hash,
            )
            for group_id, relations in sorted(
                result.relations_by_group.items()
            )
        }
        active_groups = set(rule_groups) | set(relations_by_group)
        mappings = dict(sorted(result.rule_group_doc_refs.items()))
        missing = sorted(active_groups - set(mappings))
        unknown = sorted(set(mappings) - active_groups)
        if missing:
            raise CandidatesBundleAdapterError(
                f"missing doc_ref mapping for ensemble group {missing[0]!r}"
            )
        if unknown:
            raise CandidatesBundleAdapterError(
                f"doc_ref mapping references unknown ensemble group {unknown[0]!r}"
            )
        known_doc_refs = {unit.doc_ref for unit in units}
        invalid_doc_refs = sorted(
            {
                doc_ref
                for doc_ref in mappings.values()
                if doc_ref not in known_doc_refs
            }
        )
        if invalid_doc_refs:
            raise CandidatesBundleAdapterError(
                f"group mapping references unknown doc_ref {invalid_doc_refs[0]!r}"
            )
        return cls(
            brand=brand,
            tokens_primitive=_sorted_entities(
                result.tokens_primitive
            ),
            tokens_semantic=_sorted_entities(result.tokens_semantic),
            assets=_sorted_entities(result.assets),
            subtypes=_sorted_entities(result.subtypes),
            templates=_sorted_entities(result.templates),
            rules_by_group=rule_groups,
            rule_group_doc_refs=mappings,
            relations_by_group=relations_by_group,
            conflicts=sorted(
                result.conflicts,
                key=lambda item: (
                    item.kind,
                    item.element_path,
                    item.a_id,
                    item.b_id,
                ),
            ),
            units_by_id=units_by_id,
            champion_variant=champion_variant,
        )

    def with_critic_candidates(
        self,
        patched: CandidateSet,
    ) -> CandidatesBundle:
        """Return a ledger bundle with verified WP-10 candidates applied."""
        patched_groups = set(patched.rules_by_doc_ref)
        mapped_groups = set(patched.rule_group_doc_refs)
        missing = sorted(patched_groups - mapped_groups)
        unknown = sorted(mapped_groups - patched_groups)
        if missing:
            raise CandidatesBundleAdapterError(
                f"missing doc_ref mapping for patched group {missing[0]!r}"
            )
        if unknown:
            raise CandidatesBundleAdapterError(
                f"doc_ref mapping references unknown patched group "
                f"{unknown[0]!r}"
            )
        if (
            self.champion_variant is not None
            and patched.champion_run_id
            != self.champion_variant.run_id
        ):
            raise CandidatesBundleAdapterError(
                "patched champion_run_id does not match source bundle: "
                f"{patched.champion_run_id!r} != "
                f"{self.champion_variant.run_id!r}"
            )

        known_doc_refs = {
            unit.doc_ref for unit in self.units_by_id.values()
        }
        original_rule_group: dict[str, str] = {}
        for group_id, rules in self.rules_by_group.items():
            for rule in rules:
                entity_id = str(rule.get("id", ""))
                if not entity_id:
                    continue
                previous = original_rule_group.setdefault(
                    entity_id,
                    group_id,
                )
                if previous != group_id:
                    raise CandidatesBundleAdapterError(
                        f"source rule {entity_id!r} appears in ambiguous "
                        f"groups {previous!r} and {group_id!r}"
                    )

        rules_by_group: dict[str, list[dict[str, Any]]] = {
            group_id: [] for group_id in sorted(patched_groups)
        }
        seen_rule_groups: dict[str, str] = {}
        result_mappings = {
            group_id: self.rule_group_doc_refs[group_id]
            for group_id in sorted(self.relations_by_group)
            if group_id in self.rule_group_doc_refs
        }
        for group_id in sorted(patched_groups):
            doc_ref = patched.rule_group_doc_refs[group_id]
            if known_doc_refs and doc_ref not in known_doc_refs:
                raise CandidatesBundleAdapterError(
                    f"patched group {group_id!r} references unknown "
                    f"doc_ref {doc_ref!r}"
                )
            source_doc_ref = self.rule_group_doc_refs.get(group_id)
            if (
                source_doc_ref is not None
                and source_doc_ref != doc_ref
            ):
                raise CandidatesBundleAdapterError(
                    f"patched group {group_id!r} maps ambiguously to "
                    f"{source_doc_ref!r} and {doc_ref!r}"
                )
            if (
                group_id not in self.rule_group_doc_refs
                and group_id != _group_id(self.brand, doc_ref)
            ):
                raise CandidatesBundleAdapterError(
                    f"unknown patched group {group_id!r} for "
                    f"doc_ref {doc_ref!r}"
                )
            result_mappings[group_id] = doc_ref
            for rule in _sorted_entities(
                patched.rules_by_doc_ref[group_id]
            ):
                entity_id = str(rule.get("id", ""))
                if entity_id:
                    previous_group = seen_rule_groups.setdefault(
                        entity_id,
                        group_id,
                    )
                    if previous_group != group_id:
                        raise CandidatesBundleAdapterError(
                            f"patched rule {entity_id!r} appears in "
                            f"ambiguous groups {previous_group!r} and "
                            f"{group_id!r}"
                        )
                    original_group = original_rule_group.get(entity_id)
                    if (
                        original_group is not None
                        and original_group != group_id
                    ):
                        raise CandidatesBundleAdapterError(
                            f"patched rule {entity_id!r} moved from "
                            f"group {original_group!r} to {group_id!r}"
                        )
                rules_by_group[group_id].append(dict(rule))

        return CandidatesBundle(
            brand=self.brand,
            tokens_primitive=_sorted_entities(
                patched.token_primitive
            ),
            tokens_semantic=_sorted_entities(patched.token_semantic),
            assets=_sorted_entities(patched.asset),
            subtypes=_sorted_entities(patched.subtype),
            templates=_sorted_entities(patched.template),
            rules_by_group=rules_by_group,
            rule_group_doc_refs=result_mappings,
            relations_by_group={
                group_id: sorted(relations, key=stable_hash)
                for group_id, relations in sorted(
                    self.relations_by_group.items()
                )
            },
            conflicts=sorted(
                self.conflicts,
                key=lambda item: (
                    item.kind,
                    item.element_path,
                    item.a_id,
                    item.b_id,
                ),
            ),
            units_by_id={
                unit_id: self.units_by_id[unit_id]
                for unit_id in sorted(self.units_by_id)
            },
            champion_variant=self.champion_variant,
        )

    @model_validator(mode="after")
    def sort_group_state(self) -> CandidatesBundle:
        self.rules_by_group = {
            group_id: _sorted_entities(rules)
            for group_id, rules in sorted(self.rules_by_group.items())
        }
        self.rule_group_doc_refs = dict(
            sorted(self.rule_group_doc_refs.items())
        )
        self.relations_by_group = {
            group_id: sorted(
                (dict(relation) for relation in relations),
                key=stable_hash,
            )
            for group_id, relations in sorted(
                self.relations_by_group.items()
            )
        }
        return self

    def entities_by_kind(self) -> dict[str, list[dict[str, Any]]]:
        rules = sorted(
            [
                rule
                for group_id in sorted(self.rules_by_group)
                for rule in self.rules_by_group[group_id]
                if isinstance(rule, dict)
            ],
            key=lambda item: (str(item.get("id", "")), stable_hash(item)),
        )
        return {
            "token_primitive": _sorted_entities(self.tokens_primitive),
            "token_semantic": _sorted_entities(self.tokens_semantic),
            "asset": _sorted_entities(self.assets),
            "subtype": _sorted_entities(self.subtypes),
            "template": _sorted_entities(self.templates),
            "rule": rules,
        }


class GapLoopResult(BaseModel):
    """S6 handoff to orchestration/reporting with final patched state."""

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: str = SCHEMA_VERSION
    coverage: CoverageReport
    soft_mismatches: list[SoftMismatch] = Field(default_factory=list)
    triage: list[TriageItem] = Field(default_factory=list)
    rounds_run: int
    stopped_reason: GapStopReason
    candidates: CandidatesBundle
    provenance: ProvenanceResult


class GapPatchPayload(BaseModel):
    """Validated JSON-only response from gap and full Pass-B prompts."""

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: str = SCHEMA_VERSION
    tokens: list[dict[str, Any]] = Field(default_factory=list)
    rules: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    subtypes: list[dict[str, Any]] = Field(default_factory=list)
    templates: list[dict[str, Any]] = Field(default_factory=list)
    relations: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_entity_ids(self) -> GapPatchPayload:
        seen: set[str] = set()
        for bucket_name in ("tokens", "rules", "assets", "subtypes", "templates"):
            for index, entity in enumerate(getattr(self, bucket_name)):
                entity_id = entity.get("id")
                if not isinstance(entity_id, str) or not entity_id:
                    raise ValueError(
                        f"{bucket_name}[{index}] requires a non-empty string id"
                    )
                if entity_id in seen:
                    raise ValueError(f"duplicate gap entity id: {entity_id}")
                seen.add(entity_id)
        for index, token in enumerate(self.tokens):
            marker = token.get("entity_kind")
            if marker is not None and marker not in {
                "token_primitive",
                "token_semantic",
            }:
                raise ValueError(
                    f"tokens[{index}].entity_kind must be "
                    "token_primitive or token_semantic"
                )
        return self


@runtime_checkable
class EntityPatcher(Protocol):
    """Injected patch boundary; production delegates to WP-10 semantics."""

    def apply_gap_payload(
        self,
        payload: GapPatchPayload,
        candidates: CandidatesBundle,
        *,
        units: Sequence[SourceUnit],
        doc_ref: str,
        gap_round: int,
        target_expected_yield: set[EntityKind],
        replace_rules: bool = False,
    ) -> tuple[CandidatesBundle, ProvenanceResult]: ...


def _sorted_entities(
    entities: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(
        entities,
        key=lambda item: (
            str(item.get("id", "")),
            str(item.get("key", item.get("name", ""))),
            stable_hash(item),
        ),
    )


def _labels_by_id(labels: Sequence[UnitLabel]) -> dict[str, UnitLabel]:
    return {label.unit_id: label for label in labels}


def _entity_kind_index(candidates: CandidatesBundle) -> dict[str, EntityKind]:
    index: dict[str, EntityKind] = {}
    for kind, entities in candidates.entities_by_kind().items():
        for entity in entities:
            entity_id = entity.get("id")
            if isinstance(entity_id, str) and entity_id:
                index[entity_id] = kind  # type: ignore[assignment]
    return index


def _quarantined_ids(provenance: ProvenanceResult) -> set[str]:
    return {entry.entity_id for entry in provenance.quarantine}


def _record_cites_unit(record: ProvenanceRecord, unit_id: str) -> bool:
    if record.verification not in _VERIFIED_LEVELS:
        return False
    for span in record.spans:
        if span.match == "failed":
            continue
        if unit_id in span.unit_ids:
            return True
    return False


def _claims_by_unit(
    provenance: ProvenanceResult,
    candidates: CandidatesBundle,
) -> dict[str, list[tuple[str, EntityKind]]]:
    quarantined = _quarantined_ids(provenance)
    kind_index = _entity_kind_index(candidates)
    claims: dict[str, list[tuple[str, EntityKind]]] = {}
    for entity_id in sorted(provenance.records_by_entity):
        if entity_id in quarantined:
            continue
        entity_kind = kind_index.get(entity_id)
        if entity_kind is None:
            continue
        for record in provenance.records_by_entity[entity_id]:
            for span in record.spans:
                if span.match == "failed" or record.verification not in _VERIFIED_LEVELS:
                    continue
                for unit_id in span.unit_ids:
                    bucket = claims.setdefault(unit_id, [])
                    if not any(existing_id == entity_id for existing_id, _ in bucket):
                        bucket.append((entity_id, entity_kind))
    for unit_id in claims:
        claims[unit_id].sort(key=lambda item: item[0])
    return claims


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _unit_doc_ref(unit_id: str, candidates: CandidatesBundle) -> str:
    unit = candidates.units_by_id.get(unit_id)
    if unit is not None:
        return unit.doc_ref
    return ""


def _ledger_status(
    label: UnitLabel,
    claims: list[tuple[str, EntityKind]],
) -> LedgerStatus:
    if not label.required:
        return "excluded"
    if not claims:
        return "unclaimed"
    if "normative" in label.labels:
        rule_claims = [entity_id for entity_id, kind in claims if kind == "rule"]
        if len(rule_claims) > 1:
            return "over_claimed"
    return "covered"


def _soft_mismatches_for_unit(
    label: UnitLabel,
    claims: list[tuple[str, EntityKind]],
) -> list[SoftMismatch]:
    if not label.expected_yield:
        return []
    expected = set(label.expected_yield)
    out: list[SoftMismatch] = []
    for entity_id, entity_kind in claims:
        if entity_kind not in expected:
            out.append(
                SoftMismatch(
                    unit_id=label.unit_id,
                    entity_id=entity_id,
                    entity_kind=entity_kind,
                    expected_yield=list(label.expected_yield),
                )
            )
    return out


def _orphan_entity_ids(
    provenance: ProvenanceResult,
    candidates: CandidatesBundle,
) -> list[str]:
    from ..contracts import EVIDENCE_PATHS

    orphans: list[str] = []
    for kind, entities in candidates.entities_by_kind().items():
        if kind not in EVIDENCE_PATHS:
            continue
        paths = EVIDENCE_PATHS[kind]
        if not paths:
            continue
        for entity in entities:
            entity_id = str(entity.get("id", ""))
            if not entity_id:
                continue
            records = provenance.records_by_entity.get(entity_id, [])
            verified = any(
                record.verification in _VERIFIED_LEVELS
                and record.spans
                and any(span.match != "failed" for span in record.spans)
                for record in records
            )
            if not verified:
                orphans.append(entity_id)
    return sorted(orphans)


def build_ledger(
    labels: Sequence[UnitLabel],
    provenance_index: ProvenanceResult,
    candidates: CandidatesBundle,
    *,
    rounds: int = 0,
) -> tuple[CoverageReport, list[SoftMismatch]]:
    """Pure coverage ledger from labels, provenance, and candidates."""
    labels_sorted = sorted(labels, key=lambda item: item.unit_id)
    claims_by_unit = _claims_by_unit(provenance_index, candidates)
    soft_mismatches: list[SoftMismatch] = []
    rows: list[LedgerRow] = []
    unclaimed_ids: list[str] = []
    over_claimed_ids: list[str] = []

    per_blob_counts: dict[str, dict[str, int]] = {}

    def _blob_bucket(doc_ref: str) -> dict[str, int]:
        return per_blob_counts.setdefault(
            doc_ref,
            {
                "value_required": 0,
                "value_covered": 0,
                "normative_required": 0,
                "normative_covered": 0,
                "verbatim_required": 0,
                "verbatim_covered": 0,
                "n_required": 0,
            },
        )

    for label in labels_sorted:
        claims = claims_by_unit.get(label.unit_id, [])
        status = _ledger_status(label, claims)
        soft_mismatches.extend(_soft_mismatches_for_unit(label, claims))
        rows.append(
            LedgerRow(
                unit_id=label.unit_id,
                required=label.required,
                expected_yield=list(label.expected_yield),
                claimed_by=[entity_id for entity_id, _ in claims],
                status=status,
            )
        )
        if status == "unclaimed" and label.required:
            unclaimed_ids.append(label.unit_id)
        if status == "over_claimed":
            over_claimed_ids.append(label.unit_id)

        if not label.required:
            continue
        doc_ref = _unit_doc_ref(label.unit_id, candidates)
        bucket = _blob_bucket(doc_ref)
        bucket["n_required"] += 1
        covered = status == "covered"
        if "value" in label.labels:
            bucket["value_required"] += 1
            if covered:
                bucket["value_covered"] += 1
        if "normative" in label.labels:
            bucket["normative_required"] += 1
            if covered:
                bucket["normative_covered"] += 1
        if "verbatim" in label.labels:
            bucket["verbatim_required"] += 1
            if covered:
                bucket["verbatim_covered"] += 1

    value_required = sum(1 for label in labels_sorted if label.required and "value" in label.labels)
    value_covered = sum(
        1
        for row, label in zip(rows, labels_sorted, strict=True)
        if label.required and "value" in label.labels and row.status == "covered"
    )
    normative_required = sum(
        1 for label in labels_sorted if label.required and "normative" in label.labels
    )
    normative_covered = sum(
        1
        for row, label in zip(rows, labels_sorted, strict=True)
        if label.required and "normative" in label.labels and row.status == "covered"
    )
    verbatim_required = sum(
        1 for label in labels_sorted if label.required and "verbatim" in label.labels
    )
    verbatim_covered = sum(
        1
        for row, label in zip(rows, labels_sorted, strict=True)
        if label.required and "verbatim" in label.labels and row.status == "covered"
    )

    per_blob: dict[str, dict[str, float]] = {}
    for doc_ref in sorted(per_blob_counts):
        bucket = per_blob_counts[doc_ref]
        per_blob[doc_ref] = {
            "value": _ratio(bucket["value_covered"], bucket["value_required"]),
            "normative": _ratio(bucket["normative_covered"], bucket["normative_required"]),
            "verbatim": _ratio(bucket["verbatim_covered"], bucket["verbatim_required"]),
            "n_required": float(bucket["n_required"]),
        }

    soft_mismatches.sort(key=lambda item: (item.unit_id, item.entity_id))

    report = CoverageReport(
        brand=candidates.brand,
        rounds=rounds,
        value_coverage=_ratio(value_covered, value_required),
        normative_coverage=_ratio(normative_covered, normative_required),
        verbatim_coverage=_ratio(verbatim_covered, verbatim_required),
        per_blob=per_blob,
        unclaimed_unit_ids=sorted(unclaimed_ids),
        over_claimed_unit_ids=sorted(over_claimed_ids),
        orphan_entity_ids=_orphan_entity_ids(provenance_index, candidates),
        rows=rows,
    )
    return report, soft_mismatches


def triage_key_unclaimed(doc_ref: str, unit_text: str) -> str:
    return stable_hash((doc_ref, unit_text))


def triage_key_over_claimed(doc_ref: str, unit_text: str) -> str:
    return stable_hash((doc_ref, unit_text))


def triage_key_conflict(conflict: Conflict) -> str:
    ids = sorted([conflict.a_id, conflict.b_id])
    return stable_hash((conflict.kind, conflict.element_path, ids))


def triage_key_global_unsat(
    context_key: str,
    core: Sequence[str],
) -> str:
    return stable_hash(
        ("global_unsat", context_key, tuple(sorted(core)))
    )


def triage_key_unverified_value(semantic_match_key: Any) -> str:
    return stable_hash(semantic_match_key)


def _candidate_token_catalog(
    candidates: CandidatesBundle,
) -> dict[str, dict[str, Any]]:
    variant = candidates.champion_variant or RunVariant(
        run_id="r0",
        model=settings.EXTRACT_MODEL,
    )
    return build_token_catalog(
        RunOutput(
            variant=variant,
            primitive_tokens=_sorted_entities(
                candidates.tokens_primitive
            ),
            semantic_tokens=_sorted_entities(
                candidates.tokens_semantic
            ),
        )
    )


def _unverified_semantic_entities(
    provenance: ProvenanceResult,
    candidates: CandidatesBundle,
) -> list[tuple[str, dict[str, Any]]]:
    from .align import is_concrete_value_field

    out: list[tuple[str, dict[str, Any]]] = []
    for entity in candidates.tokens_semantic:
        entity_id = str(entity.get("id", ""))
        if not entity_id:
            continue
        records = provenance.records_by_entity.get(entity_id, [])
        concrete = [record for record in records if is_concrete_value_field(record.field)]
        if not concrete:
            continue
        if all(record.verification == "value_verified" for record in concrete):
            continue
        out.append((entity_id, entity))
    out.sort(key=lambda item: item[0])
    return out


def compute_triage_items(
    report: CoverageReport,
    *,
    labels_by_id: Mapping[str, UnitLabel],
    candidates: CandidatesBundle,
    provenance: ProvenanceResult,
) -> list[TriageItem]:
    items: list[TriageItem] = []
    token_catalog = _candidate_token_catalog(candidates)
    del labels_by_id
    for unit_id in report.unclaimed_unit_ids:
        unit = candidates.units_by_id.get(unit_id)
        doc_ref = unit.doc_ref if unit is not None else _unit_doc_ref(unit_id, candidates)
        unit_text = unit.text if unit is not None else ""
        items.append(
            TriageItem(
                queue="unclaimed_unit",
                key=triage_key_unclaimed(doc_ref, unit_text),
                subject_id=unit_id,
                context=f"required unit unclaimed in {doc_ref}",
            )
        )
    for unit_id in report.over_claimed_unit_ids:
        unit = candidates.units_by_id.get(unit_id)
        doc_ref = unit.doc_ref if unit is not None else _unit_doc_ref(unit_id, candidates)
        unit_text = unit.text if unit is not None else ""
        items.append(
            TriageItem(
                queue="over_claimed",
                key=triage_key_over_claimed(doc_ref, unit_text),
                subject_id=unit_id,
                context=f"normative unit claimed by >1 rule in {doc_ref}",
            )
        )
    for entity_id, entity in _unverified_semantic_entities(provenance, candidates):
        match_key = semantic_match_key(entity, token_catalog)
        items.append(
            TriageItem(
                queue="unverified_value",
                key=triage_key_unverified_value(match_key),
                subject_id=entity_id,
                context=f"semantic token unverified: {match_key[0]}",
            )
        )
    for conflict in sorted(candidates.conflicts, key=lambda item: (item.kind, item.a_id, item.b_id)):
        items.append(
            TriageItem(
                queue="conflict",
                key=triage_key_conflict(conflict),
                subject_id=conflict.a_id,
                context=conflict.detail,
            )
        )
    items.sort(key=lambda item: (item.queue, item.key, item.subject_id))
    return items


def compute_s9_triage_items(
    pairwise: PairwiseAnalysisResult | None,
    smt: SmtAnalysisResult | None,
) -> list[TriageItem]:
    """Build the deterministic current S9 conflict snapshot."""
    items = [
        TriageItem(
            queue="conflict",
            key=triage_key_conflict(conflict),
            subject_id=conflict.a_id,
            context=conflict.detail,
        )
        for conflict in (pairwise.conflicts if pairwise is not None else [])
    ]
    if smt is not None and smt.status == "completed":
        items.extend(
            TriageItem(
                queue="conflict",
                key=triage_key_global_unsat(row.context_key, row.core),
                subject_id=row.context_key,
                context=row.detail,
            )
            for row in smt.global_unsat
        )
    return sorted(
        items,
        key=lambda item: (
            item.queue,
            item.key,
            item.subject_id,
            item.context,
        ),
    )


def current_class_a_conflict_keys(
    triage: Sequence[TriageItem],
    *,
    pairwise: PairwiseAnalysisResult | None,
    smt: SmtAnalysisResult | None,
) -> list[str]:
    """Return open current keys for acceptance-blocking S9 conflicts."""
    class_a_keys = {
        triage_key_conflict(conflict)
        for conflict in (pairwise.conflicts if pairwise is not None else [])
        if conflict.kind in _CLASS_A_CONFLICT_KINDS
    }
    if smt is not None and smt.status == "completed":
        class_a_keys.update(
            triage_key_global_unsat(row.context_key, row.core)
            for row in smt.global_unsat
        )
    return sorted(
        {
            item.key
            for item in triage
            if item.queue == "conflict"
            and item.disposition.status == "open"
            and item.key in class_a_keys
        }
    )


def load_triage_history(path: Path) -> list[TriageItem]:
    if not path.is_file():
        return []
    return read_jsonl(path, TriageItem)


def _latest_disposition_by_key(history: Sequence[TriageItem]) -> dict[tuple[str, str], TriageItem]:
    latest: dict[tuple[str, str], TriageItem] = {}
    for item in history:
        latest[(item.queue, item.key)] = item
    return latest


def rebuild_triage(
    computed: Sequence[TriageItem],
    history: Sequence[TriageItem],
) -> tuple[list[TriageItem], list[TriageItem]]:
    """Merge computed items with append-only history; latest disposition per key wins."""
    prior = _latest_disposition_by_key(history)
    merged: list[TriageItem] = []
    to_append: list[TriageItem] = []
    seen: set[tuple[str, str]] = set()
    for item in sorted(
        computed,
        key=lambda row: (
            row.queue,
            row.key,
            row.subject_id,
            row.context,
        ),
    ):
        identity = (item.queue, item.key)
        if identity in seen:
            continue
        seen.add(identity)
        previous = prior.get(identity)
        if previous is not None:
            merged_item = item.model_copy(update={"disposition": previous.disposition})
        else:
            merged_item = item
        merged.append(merged_item)
        if merged_item.disposition.status == "open" and (
            previous is None or previous.disposition.status != "open"
        ):
            to_append.append(merged_item)
    merged.sort(key=lambda row: (row.queue, row.key, row.subject_id))
    return merged, to_append


def append_triage_items(path: Path, items: Sequence[TriageItem]) -> None:
    """Append-only writer; pipeline never authors waived/deferred dispositions."""
    open_items = [item for item in items if item.disposition.status == "open"]
    if not open_items:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(item.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        for item in open_items
    ]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def write_ledger(work_dir: Path, document: LedgerDocument) -> None:
    atomic_write_json(work_dir / "ledger.json", document.model_dump(mode="json"))


def write_triage_snapshot(path: Path, items: Sequence[TriageItem]) -> None:
    """Deterministic full snapshot (used by tests; production stays append-only)."""
    write_jsonl(path, sorted(items, key=lambda row: (row.queue, row.key, row.subject_id)))


def catalog_summary_text(candidates: CandidatesBundle) -> str:
    """Compact candidate catalog for gap prompts (mirrors runner layout)."""
    lines: list[str] = []

    def _token_lines(tokens: Sequence[dict[str, Any]]) -> list[str]:
        out: list[str] = []
        for token in _sorted_entities(tokens):
            value = token.get("value") or {}
            default = value.get("default") if isinstance(value, dict) else value
            out.append(
                f"  {token.get('id')}  key={token.get('key')}  "
                f"default={json.dumps(default, sort_keys=True, separators=(',', ':'), default=str)}"
            )
        return out

    lines.append(f"primitive tokens ({len(candidates.tokens_primitive)}):")
    lines.extend(_token_lines(candidates.tokens_primitive))
    lines.append(f"semantic tokens ({len(candidates.tokens_semantic)}):")
    lines.extend(_token_lines(candidates.tokens_semantic))
    for heading, entities in (
        ("assets", candidates.assets),
        ("subtypes", candidates.subtypes),
        ("templates", candidates.templates),
    ):
        lines.append(f"{heading} ({len(entities)}):")
        for entity in _sorted_entities(entities):
            lines.append(
                f"  {entity.get('id')}  "
                f"name={entity.get('name', entity.get('key', ''))}"
            )
    lines.append(f"rules ({sum(len(v) for v in candidates.rules_by_group.values())}):")
    for group_id in sorted(candidates.rules_by_group):
        for rule in _sorted_entities(candidates.rules_by_group[group_id]):
            lines.append(
                f"  {rule.get('id')}  group={group_id}  class={rule.get('rule_class')}"
            )
    return "\n".join(lines)


def _units_by_doc_ref(units: Sequence[SourceUnit]) -> dict[str, list[SourceUnit]]:
    grouped: dict[str, list[SourceUnit]] = {}
    for unit in units:
        grouped.setdefault(unit.doc_ref, []).append(unit)
    for doc_ref in grouped:
        grouped[doc_ref] = sorted(
            grouped[doc_ref],
            key=lambda item: (item.ordinal, item.unit_id),
        )
    return grouped


def _gap_context_units(
    target_ids: set[str],
    units_by_doc: dict[str, list[SourceUnit]],
    units_by_id: Mapping[str, SourceUnit],
) -> list[SourceUnit]:
    seen: set[str] = set()
    context: list[SourceUnit] = []
    for unit_id in sorted(target_ids):
        target = units_by_id[unit_id]
        doc_units = units_by_doc[target.doc_ref]
        index = next(idx for idx, row in enumerate(doc_units) if row.unit_id == unit_id)
        start = max(0, index - _GAP_CONTEXT_RADIUS)
        end = min(len(doc_units), index + _GAP_CONTEXT_RADIUS + 1)
        for unit in doc_units[start:end]:
            if unit.unit_id in seen:
                continue
            seen.add(unit.unit_id)
            context.append(unit)
    return sorted(
        context,
        key=lambda item: (item.doc_ref, item.ordinal, item.unit_id),
    )


def _legacy_group_doc_ref(
    group_id: str,
    rules: Sequence[Mapping[str, Any]],
    *,
    units_by_id: Mapping[str, SourceUnit],
) -> str:
    doc_refs: set[str] = set()
    for rule in rules:
        explicit = rule.get("doc_ref")
        if isinstance(explicit, str) and explicit:
            doc_refs.add(explicit)
        evidence = rule.get("evidence")
        if not isinstance(evidence, Mapping):
            continue
        raw_unit_ids = evidence.get("unit_ids")
        if not isinstance(raw_unit_ids, list):
            continue
        for unit_id in raw_unit_ids:
            unit = units_by_id.get(str(unit_id))
            if unit is not None:
                doc_refs.add(unit.doc_ref)
    if len(doc_refs) != 1:
        detail = (
            "no source doc_ref"
            if not doc_refs
            else f"ambiguous source doc_refs {sorted(doc_refs)!r}"
        )
        raise CandidatesBundleAdapterError(
            f"legacy rule group {group_id!r} has {detail}"
        )
    return next(iter(doc_refs))


def _to_critic_candidates(candidates: CandidatesBundle) -> CandidateSet:
    # Preserve empty groups so rule_group_doc_refs stays aligned with
    # rules_by_doc_ref. Dropping empty buckets left orphan mappings that
    # with_critic_candidates rejected after S5 emptied a group.
    rules_by_group: dict[str, list[dict[str, Any]]] = {
        group_id: [] for group_id in sorted(candidates.rules_by_group)
    }
    if candidates.rule_group_doc_refs:
        missing = sorted(
            set(candidates.rules_by_group)
            - set(candidates.rule_group_doc_refs)
        )
        if missing:
            raise CandidatesBundleAdapterError(
                f"missing doc_ref mapping for rule group {missing[0]!r}"
            )
        rule_group_doc_refs = {
            group_id: candidates.rule_group_doc_refs[group_id]
            for group_id in sorted(candidates.rules_by_group)
        }
    else:
        rule_group_doc_refs = {
            group_id: _legacy_group_doc_ref(
                group_id,
                candidates.rules_by_group[group_id],
                units_by_id=candidates.units_by_id,
            )
            for group_id in sorted(candidates.rules_by_group)
        }
    for group_id in sorted(candidates.rules_by_group):
        for rule in _sorted_entities(candidates.rules_by_group[group_id]):
            clean = dict(rule)
            clean.pop("doc_ref", None)
            rules_by_group[group_id].append(clean)
    return CandidateSet(
        token_primitive=_sorted_entities(candidates.tokens_primitive),
        token_semantic=_sorted_entities(candidates.tokens_semantic),
        asset=_sorted_entities(candidates.assets),
        subtype=_sorted_entities(candidates.subtypes),
        template=_sorted_entities(candidates.templates),
        rules_by_doc_ref={
            group_id: _sorted_entities(rules)
            for group_id, rules in sorted(rules_by_group.items())
        },
        rule_group_doc_refs=dict(sorted(rule_group_doc_refs.items())),
        champion_run_id=(
            candidates.champion_variant.run_id
            if candidates.champion_variant is not None
            else "r0"
        ),
    )


def _from_critic_candidates(
    patched: CandidateSet,
    source: CandidatesBundle,
) -> CandidatesBundle:
    """Compatibility alias; Wave-4 should call ``source.with_critic_candidates``."""
    return source.with_critic_candidates(patched)


def _critic_kind_by_id(candidates: CandidateSet) -> dict[str, EntityKind]:
    index: dict[str, EntityKind] = {}
    for raw_kind, entities in candidates.to_entities_by_kind().items():
        if raw_kind not in {
            "token_primitive",
            "token_semantic",
            "asset",
            "subtype",
            "template",
            "rule",
        }:
            continue
        kind = cast(EntityKind, raw_kind)
        for entity in entities:
            entity_id = entity.get("id")
            if isinstance(entity_id, str) and entity_id:
                index[entity_id] = kind
    return index


def _token_gap_kind(
    entity: Mapping[str, Any],
    existing_kind: EntityKind | None,
    target_expected_yield: set[EntityKind],
) -> EntityKind:
    marker = entity.get("entity_kind")
    if marker is not None and marker not in {
        "token_primitive",
        "token_semantic",
    }:
        raise GapPayloadError(
            f"gap token {entity.get('id')!r} has invalid entity_kind {marker!r}"
        )
    if existing_kind in {"token_primitive", "token_semantic"}:
        if marker is not None and marker != existing_kind:
            raise GapPayloadError(
                f"gap token {entity.get('id')!r} conflicts with existing kind "
                f"{existing_kind!r}"
            )
        return existing_kind
    if marker in {"token_primitive", "token_semantic"}:
        return cast(EntityKind, marker)
    if (
        "token_primitive" in target_expected_yield
        and "token_semantic" not in target_expected_yield
    ):
        # ponytail: legacy r0 fixtures predate entity_kind; only an
        # unambiguously primitive target may use this CP-3 compatibility path.
        return "token_primitive"
    raise GapPayloadError(
        f"new gap token {entity.get('id')!r} requires explicit entity_kind"
    )


def _gap_entity_specs(
    payload: GapPatchPayload,
    candidates: CandidateSet,
    *,
    target_expected_yield: set[EntityKind],
) -> list[tuple[EntityKind, dict[str, Any]]]:
    existing = _critic_kind_by_id(candidates)
    specs: list[tuple[EntityKind, dict[str, Any]]] = []
    for raw in payload.tokens:
        entity = dict(raw)
        entity_id = str(entity["id"])
        kind = _token_gap_kind(
            entity,
            existing.get(entity_id),
            target_expected_yield,
        )
        entity.pop("entity_kind", None)
        if existing.get(entity_id) not in {None, kind}:
            raise GapPayloadError(
                f"gap token {entity_id!r} conflicts with existing kind "
                f"{existing[entity_id]!r}"
            )
        specs.append((kind, entity))
    for kind, rows in (
        ("rule", payload.rules),
        ("asset", payload.assets),
        ("subtype", payload.subtypes),
        ("template", payload.templates),
    ):
        for raw in rows:
            entity = dict(raw)
            entity_id = str(entity["id"])
            if existing.get(entity_id) not in {None, kind}:
                raise GapPayloadError(
                    f"gap entity {entity_id!r} conflicts with existing kind "
                    f"{existing[entity_id]!r}"
                )
            specs.append((kind, entity))
    return sorted(
        specs,
        key=lambda item: (item[0], str(item[1]["id"]), stable_hash(item[1])),
    )


def _gap_finding(patch: Patch, *, gap_round: int, index: int) -> Finding:
    return Finding(
        finding_id=f"f_gap_{gap_round:02d}_{index:04d}_{stable_hash(patch)}",
        round=gap_round,
        finding_type="omission",
        severity="minor",
        target_entity_id=(
            patch.target_entity_ids[0] if patch.target_entity_ids else None
        ),
        description="S6 gap extraction candidate",
        proposed_patch=patch,
    )


def _apply_critic_patch(
    current: CandidateSet,
    patch: Patch,
    *,
    units: Sequence[SourceUnit],
    gap_round: int,
    index: int,
) -> tuple[CandidateSet, bool]:
    try:
        updated, findings, _audit = triage_findings(
            [_gap_finding(patch, gap_round=gap_round, index=index)],
            current,
            units,
            round_num=gap_round,
        )
    except PatchApplicationError as exc:
        raise GapPayloadError(f"invalid gap patch: {exc}") from exc
    return updated, findings[0].resolution == "applied"


class CriticEntityPatcher:
    """Thin S6 adapter over WP-10 patch application and S3 verification."""

    def apply_gap_payload(
        self,
        payload: GapPatchPayload,
        candidates: CandidatesBundle,
        *,
        units: Sequence[SourceUnit],
        doc_ref: str,
        gap_round: int,
        target_expected_yield: set[EntityKind],
        replace_rules: bool = False,
    ) -> tuple[CandidatesBundle, ProvenanceResult]:
        initial = _to_critic_candidates(candidates)
        target_group_id = _group_id(candidates.brand, doc_ref)
        existing_ids = set(_critic_kind_by_id(initial))
        if any(
            str(rule["id"]) not in existing_ids
            for rule in payload.rules
        ):
            initial.rules_by_doc_ref.setdefault(target_group_id, [])
            initial.rule_group_doc_refs[target_group_id] = doc_ref
        current = initial
        initial_rule_ids = {
            str(rule.get("id", ""))
            for group_id, rules in initial.rules_by_doc_ref.items()
            if initial.rule_group_doc_refs.get(group_id) == doc_ref
            for rule in rules
            if rule.get("id")
        }
        incoming_rule_ids = {str(rule["id"]) for rule in payload.rules}
        all_incoming_applied = True

        for index, (kind, entity) in enumerate(
            _gap_entity_specs(
                payload,
                current,
                target_expected_yield=target_expected_yield,
            ),
            start=1,
        ):
            entity_id = str(entity["id"])
            existing_kind = _critic_kind_by_id(current).get(entity_id)
            patch_payload = dict(entity)
            patch_payload.pop("doc_ref", None)
            if existing_kind is None:
                if kind == "rule":
                    patch_payload["doc_ref"] = doc_ref
                    patch_payload["group_id"] = target_group_id
                patch = Patch(
                    op="add",
                    entity_kind=kind,
                    payload=patch_payload,
                )
            else:
                patch = Patch(
                    op="update",
                    entity_kind=kind,
                    target_entity_ids=[entity_id],
                    payload=patch_payload,
                )
            current, applied = _apply_critic_patch(
                current,
                patch,
                units=units,
                gap_round=gap_round,
                index=index,
            )
            all_incoming_applied = all_incoming_applied and applied

        if replace_rules and all_incoming_applied:
            for offset, entity_id in enumerate(
                sorted(initial_rule_ids - incoming_rule_ids),
                start=1,
            ):
                current, _ = _apply_critic_patch(
                    current,
                    Patch(
                        op="delete",
                        entity_kind="rule",
                        target_entity_ids=[entity_id],
                    ),
                    units=units,
                    gap_round=gap_round,
                    index=len(payload.rules) + offset,
                )

        if current.model_dump(mode="json") == initial.model_dump(mode="json"):
            result = candidates.model_copy(deep=True)
        else:
            result = candidates.with_critic_candidates(current)
        if payload.relations and all_incoming_applied:
            group_id = _group_id(candidates.brand, doc_ref)
            relations_by_group = {
                key: [dict(relation) for relation in rows]
                for key, rows in result.relations_by_group.items()
            }
            if replace_rules:
                relations_by_group[group_id] = [
                    dict(relation)
                    for relation in sorted(payload.relations, key=stable_hash)
                ]
            else:
                merged = {
                    stable_hash(relation): dict(relation)
                    for relation in relations_by_group.get(group_id, [])
                }
                merged.update(
                    {
                        stable_hash(relation): dict(relation)
                        for relation in payload.relations
                    }
                )
                relations_by_group[group_id] = [
                    merged[key] for key in sorted(merged)
                ]
            result = result.model_copy(
                update={
                    "relations_by_group": relations_by_group,
                    "rule_group_doc_refs": {
                        **result.rule_group_doc_refs,
                        group_id: doc_ref,
                    },
                },
                deep=True,
            )
        elif replace_rules and all_incoming_applied:
            group_id = _group_id(candidates.brand, doc_ref)
            relations_by_group = {
                key: [dict(relation) for relation in rows]
                for key, rows in result.relations_by_group.items()
            }
            relations_by_group[group_id] = []
            result = result.model_copy(
                update={
                    "relations_by_group": relations_by_group,
                    "rule_group_doc_refs": {
                        **result.rule_group_doc_refs,
                        group_id: doc_ref,
                    },
                },
                deep=True,
            )
        provenance = verify_entities(result.entities_by_kind(), units)
        return result, provenance


async def _gap_patch_blob(
    *,
    brand: str,
    doc_ref: str,
    target_unit_ids: set[str],
    target_expected_yield: set[EntityKind],
    units_by_doc: dict[str, list[SourceUnit]],
    units_by_id: Mapping[str, SourceUnit],
    candidates: CandidatesBundle,
    client: LLMClient,
    variant: RunVariant,
    usage: Usage,
    cache_root: Path,
    gap_round: int,
    prompts_dir: Path | None,
) -> GapPatchPayload:
    context_units = _gap_context_units(target_unit_ids, units_by_doc, units_by_id)
    template = load_prompt(PROMPT_GAP_PATCH, prompts_dir)
    rendered = template.render(
        brand=brand,
        doc_ref=doc_ref,
        target_unit_ids=json.dumps(sorted(target_unit_ids), separators=(",", ":")),
        target_expected_yield=json.dumps(
            sorted(target_expected_yield),
            separators=(",", ":"),
        ),
        units=render_units(context_units),
        catalog=catalog_summary_text(candidates),
    )
    ctx = CacheContext(
        brand=brand,
        variant=variant,
        prompt_name=PROMPT_GAP_PATCH,
        template=template,
        content_hash="",
        cache_root=cache_root,
    )
    result = await complete_json_cached(
        client,
        ctx,
        rendered.system,
        rendered.user,
        usage,
        gap_round=gap_round,
    )
    return _parse_gap_payload(result)


async def _full_blob_reextract(
    *,
    brand: str,
    doc_ref: str,
    blob_units: list[SourceUnit],
    candidates: CandidatesBundle,
    client: LLMClient,
    variant: RunVariant,
    usage: Usage,
    cache_root: Path,
    gap_round: int,
    prompts_dir: Path | None,
) -> GapPatchPayload:
    from .runner import PROMPT_RULES_CLUSTER

    template = load_prompt(PROMPT_RULES_CLUSTER, prompts_dir)
    group_id = _group_id(brand, doc_ref)
    rendered = template.render(
        brand=brand,
        doc_ref=doc_ref,
        group_id=group_id,
        units=render_units(blob_units),
        catalog=catalog_summary_text(candidates),
    )
    ctx = CacheContext(
        brand=brand,
        variant=variant,
        prompt_name=PROMPT_RULES_CLUSTER,
        template=template,
        content_hash="",
        cache_root=cache_root,
    )
    result = await complete_json_cached(
        client,
        ctx,
        rendered.system,
        rendered.user,
        usage,
        gap_round=gap_round,
        extra={"doc_ref": doc_ref, "group_id": group_id, "gap_escalation": True},
    )
    return _parse_gap_payload(
        _normalize_full_blob_payload(
            result,
            brand=brand,
            doc_ref=doc_ref,
            group_id=group_id,
            blob_units=blob_units,
            candidates=candidates,
        )
    )


def _normalize_full_blob_payload(
    raw: Any,
    *,
    brand: str,
    doc_ref: str,
    group_id: str,
    blob_units: Sequence[SourceUnit],
    candidates: CandidatesBundle,
) -> Any:
    """Adapt slug-only rules_cluster output to the strict S6 gap contract."""
    if not isinstance(raw, Mapping):
        return raw
    rules = raw.get("rules")
    relations = raw.get("relations", [])
    if not isinstance(rules, list) or not isinstance(relations, list):
        return raw
    if not all(isinstance(rule, Mapping) for rule in rules) or not all(
        isinstance(relation, Mapping) for relation in relations
    ):
        return raw

    # IDs belonging to the group being replaced may be reused. IDs in every
    # other group are reserved so escalation cannot create cross-group collisions.
    reserved_ids = {
        str(rule["id"])
        for existing_group_id, existing_rules in candidates.rules_by_group.items()
        if existing_group_id != group_id
        for rule in existing_rules
        if isinstance(rule.get("id"), str) and rule["id"]
    }
    group = RuleGroupOutput(
        group_id=group_id,
        doc_ref=doc_ref,
        original_text="".join(unit.text for unit in blob_units),
        rules=[dict(rule) for rule in rules],
        relations=[dict(relation) for relation in relations],
    )
    normalized = normalize_rule_groups(
        brand,
        [group],
        used_ids=reserved_ids,
    )[0]
    return {
        **raw,
        "rules": normalized.rules,
        "relations": normalized.relations,
    }


def _parse_gap_payload(raw: Any) -> GapPatchPayload:
    try:
        return GapPatchPayload.model_validate(raw)
    except ValidationError as exc:
        raise GapPayloadError(f"invalid gap response: {exc}") from exc


async def run_gap_loop(
    labels: Sequence[UnitLabel],
    candidates: CandidatesBundle,
    provenance: ProvenanceResult,
    *,
    units: Sequence[SourceUnit],
    client: LLMClient,
    usage: Usage,
    patcher: EntityPatcher | None = None,
    work_dir: Path | None = None,
    triage_path: Path | None = None,
    cache_root: Path | None = None,
    prompts_dir: Path | None = None,
    max_rounds: int | None = None,
    console: Any | None = None,
) -> GapLoopResult:
    """Async gap driver (≤ ``MAX_GAP_ROUNDS``) with blob escalation on no-shrink."""
    from .runner import DEFAULT_CACHE_ROOT

    cap = settings.MAX_GAP_ROUNDS if max_rounds is None else max_rounds
    if cap <= 0:
        raise GapLoopInputError(f"max_rounds must be positive, got {cap}")

    units_by_id = {unit.unit_id: unit for unit in units}
    if len(units_by_id) != len(units):
        raise GapLoopInputError("units contain duplicate unit_ids")
    missing_required = sorted(
        label.unit_id
        for label in labels
        if label.required and label.unit_id not in units_by_id
    )
    if missing_required:
        raise GapLoopInputError(
            f"required unit_ids missing from units: {missing_required}"
        )

    def _log(message: str) -> None:
        if console is not None:
            console.print(f"[cyan][{candidates.brand}][/cyan] {message}")

    resolved_patcher = patcher or CriticEntityPatcher()
    variant = candidates.champion_variant or RunVariant(run_id="r0", model=settings.EXTRACT_MODEL)
    units_by_doc = _units_by_doc_ref(units)
    labels_by_id = _labels_by_id(labels)

    current_candidates = candidates.model_copy(
        update={"units_by_id": units_by_id},
        deep=True,
    )
    entity_total = sum(
        len(bucket) for bucket in current_candidates.entities_by_kind().values()
    )
    # Authoritative source units invalidate stale pre-S6 quote verification.
    _log(f"s6 initial full-KB verify: entities={entity_total} units={len(units)}")
    verify_started = time.perf_counter()
    current_provenance = verify_entities(
        current_candidates.entities_by_kind(),
        units,
    )
    _log(
        f"s6 initial verify done in {time.perf_counter() - verify_started:.1f}s "
        f"quarantine={len(current_provenance.quarantine)}"
    )
    del provenance
    rounds_run = 0
    stopped_reason: GapStopReason = "empty_queue"
    prev_unclaimed: set[str] = set()
    escalate_next: set[str] = set()
    escalated_doc_refs: set[str] = set()
    resolved_cache = cache_root or DEFAULT_CACHE_ROOT

    while rounds_run < cap:
        report, soft = build_ledger(labels, current_provenance, current_candidates, rounds=rounds_run)
        unclaimed = set(report.unclaimed_unit_ids)
        if not unclaimed:
            stopped_reason = "empty_queue"
            _log(f"s6 round {rounds_run}: empty unclaimed queue — stopping")
            break

        if rounds_run > 0 and unclaimed == prev_unclaimed and not escalate_next:
            stopped_reason = "zero_progress"
            _log(
                f"s6 round {rounds_run}: zero progress "
                f"(unclaimed={len(unclaimed)}) — stopping"
            )
            break

        by_blob: dict[str, set[str]] = {}
        for unit_id in unclaimed:
            unit = units_by_id[unit_id]
            by_blob.setdefault(unit.doc_ref, set()).add(unit_id)

        _log(
            f"s6 round {rounds_run + 1}/{cap}: unclaimed_units={len(unclaimed)} "
            f"blobs={len(by_blob)} escalate={sorted(escalate_next) or '[]'}"
        )

        blob_unclaimed_before: dict[str, set[str]] = {}
        escalated_docs_this_round: set[str] = set()
        for blob_index, (doc_ref, blob_targets) in enumerate(
            sorted(by_blob.items()),
            start=1,
        ):
            blob_unclaimed_before[doc_ref] = set(blob_targets)
            mode = "escalate" if doc_ref in escalate_next else "gap_patch"
            _log(
                f"s6 round {rounds_run + 1} blob {blob_index}/{len(by_blob)}: "
                f"{doc_ref} targets={len(blob_targets)} mode={mode}"
            )
            blob_started = time.perf_counter()
            if doc_ref in escalate_next:
                escalated_docs_this_round.add(doc_ref)
                escalated_doc_refs.add(doc_ref)
                blob_units = units_by_doc[doc_ref]
                _log(f"s6 {doc_ref}: full blob re-extract LLM")
                payload = await _full_blob_reextract(
                    brand=current_candidates.brand,
                    doc_ref=doc_ref,
                    blob_units=blob_units,
                    candidates=current_candidates,
                    client=client,
                    variant=variant,
                    usage=usage,
                    cache_root=resolved_cache,
                    gap_round=rounds_run + 1,
                    prompts_dir=prompts_dir,
                )
                _log(
                    f"s6 {doc_ref}: applying escalate payload "
                    f"tokens={len(payload.tokens)} rules={len(payload.rules)} "
                    f"assets={len(payload.assets)}"
                )
                current_candidates, current_provenance = (
                    resolved_patcher.apply_gap_payload(
                        payload,
                        current_candidates,
                        units=units,
                        doc_ref=doc_ref,
                        gap_round=rounds_run + 1,
                        target_expected_yield={
                            kind
                            for unit_id in blob_targets
                            for kind in labels_by_id[unit_id].expected_yield
                        },
                        replace_rules=True,
                    )
                )
            else:
                _log(f"s6 {doc_ref}: gap_patch LLM")
                payload = await _gap_patch_blob(
                    brand=current_candidates.brand,
                    doc_ref=doc_ref,
                    target_unit_ids=blob_targets,
                    target_expected_yield={
                        kind
                        for unit_id in blob_targets
                        for kind in labels_by_id[unit_id].expected_yield
                    },
                    units_by_doc=units_by_doc,
                    units_by_id=units_by_id,
                    candidates=current_candidates,
                    client=client,
                    variant=variant,
                    usage=usage,
                    cache_root=resolved_cache,
                    gap_round=rounds_run + 1,
                    prompts_dir=prompts_dir,
                )
                _log(
                    f"s6 {doc_ref}: applying gap payload "
                    f"tokens={len(payload.tokens)} rules={len(payload.rules)} "
                    f"assets={len(payload.assets)} "
                    f"(includes full-KB re-verify)"
                )
                current_candidates, current_provenance = (
                    resolved_patcher.apply_gap_payload(
                        payload,
                        current_candidates,
                        units=units,
                        doc_ref=doc_ref,
                        gap_round=rounds_run + 1,
                        target_expected_yield={
                            kind
                            for unit_id in blob_targets
                            for kind in labels_by_id[unit_id].expected_yield
                        },
                    )
                )
            _log(
                f"s6 {doc_ref}: blob done in {time.perf_counter() - blob_started:.1f}s"
            )

        rounds_run += 1
        post_report, soft = build_ledger(
            labels,
            current_provenance,
            current_candidates,
            rounds=rounds_run,
        )
        if not post_report.unclaimed_unit_ids:
            stopped_reason = "empty_queue"
            report, soft = post_report, soft
            _log(f"s6 after round {rounds_run}: queue drained")
            break
        post_unclaimed = set(post_report.unclaimed_unit_ids)
        next_escalate: set[str] = set()
        for doc_ref, before_ids in blob_unclaimed_before.items():
            after_ids = {uid for uid in post_unclaimed if units_by_id[uid].doc_ref == doc_ref}
            if (
                before_ids
                and len(after_ids) >= len(before_ids)
                and doc_ref not in escalated_doc_refs
            ):
                next_escalate.add(doc_ref)

        pending_escalations = next_escalate - escalated_docs_this_round
        _log(
            f"s6 after round {rounds_run}: unclaimed={len(post_unclaimed)} "
            f"(was {len(unclaimed)}) escalate_next={sorted(pending_escalations) or '[]'}"
        )
        if post_unclaimed == unclaimed:
            if pending_escalations and rounds_run < cap:
                escalate_next = pending_escalations
                prev_unclaimed = unclaimed
                report, soft = post_report, soft
                continue
            stopped_reason = "zero_progress"
            report, soft = post_report, soft
            break

        escalate_next = pending_escalations
        prev_unclaimed = unclaimed
        report, soft = post_report, soft

    else:
        stopped_reason = "max_rounds"

    final_report, final_soft = build_ledger(
        labels,
        current_provenance,
        current_candidates,
        rounds=rounds_run,
    )
    computed = compute_triage_items(
        final_report,
        labels_by_id=labels_by_id,
        candidates=current_candidates,
        provenance=current_provenance,
    )
    history = load_triage_history(triage_path) if triage_path is not None else []
    merged, to_append = rebuild_triage(computed, history)
    if triage_path is not None:
        append_triage_items(triage_path, to_append)
    if work_dir is not None:
        write_ledger(
            work_dir,
            LedgerDocument(coverage=final_report, soft_mismatches=final_soft),
        )

    _log(
        f"s6 gap loop finished: rounds={rounds_run} stop={stopped_reason} "
        f"unclaimed={len(final_report.unclaimed_unit_ids)}"
    )
    return GapLoopResult(
        coverage=final_report,
        soft_mismatches=final_soft,
        triage=merged,
        rounds_run=rounds_run,
        stopped_reason=stopped_reason,
        candidates=current_candidates,
        provenance=current_provenance,
    )
