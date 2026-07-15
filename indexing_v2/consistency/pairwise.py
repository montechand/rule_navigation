"""Pairwise KB consistency analysis (S9 layer 1).

Usage: ``from indexing_v2.consistency.pairwise import analyze_pairwise``
"""

from __future__ import annotations

import json
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from indexing_v2.cascade.contexts import enumerate_contexts
from indexing_v2.cascade.guards import (
    conjunction,
    is_satisfiable,
    normalize_guard,
    satisfiable,
    witness,
)
from indexing_v2.cascade.resolve import collect_bindings
from indexing_v2.contracts import SCHEMA_VERSION, Binding, Conflict, Guard, KBSnapshot
from shared.schemas import SECTION_TYPES, BrandRule

STAGE_VERSION = "1.0.0"


class DeadEntry(BaseModel):
    schema_version: str = SCHEMA_VERSION
    entry_id: str
    source_kind: Literal["rule_binding", "token_variant", "token_default", "rule"]
    reason: Literal["unsatisfiable_guard", "empty_selector_sections"]
    detail: str


class PrecedenceProposal(BaseModel):
    schema_version: str = SCHEMA_VERSION
    rule_id: str
    precedence: int
    detail: str


class PairwiseAnalysisResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    conflicts: list[Conflict] = Field(default_factory=list)
    dead_entries: list[DeadEntry] = Field(default_factory=list)
    precedence_proposals: list[PrecedenceProposal] = Field(default_factory=list)


def analyze_pairwise(
    snapshot: KBSnapshot,
    bindings: Optional[list[Binding]] = None,
    *,
    domains: Optional[dict[str, list[str]]] = None,
) -> PairwiseAnalysisResult:
    """Run layer-1 consistency checks over bindings collected from the snapshot."""
    effective_domains = _effective_domains(snapshot, domains)
    resolved_bindings = bindings if bindings is not None else collect_bindings(snapshot)
    conflicts: list[Conflict] = []
    dead_entries = _dead_entries(snapshot, resolved_bindings, effective_domains)
    conflicts.extend(_value_conflicts(resolved_bindings, effective_domains))
    conflicts.extend(_intra_token_conflicts(resolved_bindings, effective_domains))
    conflicts.extend(_verbatim_clashes(snapshot.rules, effective_domains))
    proposals = _precedence_proposals(conflicts, snapshot.rules)
    return PairwiseAnalysisResult(
        conflicts=_dedupe_conflicts(conflicts),
        dead_entries=sorted(dead_entries, key=lambda item: item.entry_id),
        precedence_proposals=sorted(proposals, key=lambda item: (item.rule_id, item.precedence)),
    )


def _effective_domains(
    snapshot: KBSnapshot,
    domains: Optional[dict[str, list[str]]],
) -> dict[str, list[str]]:
    base = {axis: sorted(values) for axis, values in snapshot.predicate_domains.items()}
    contexts = enumerate_contexts(snapshot)
    for axis in ("audience", "surface", "campaign", "theme"):
        base[axis] = sorted({str(getattr(context, axis)) for context in contexts})
    observed_tags = {
        tag
        for context in contexts
        for tag in context.content_tags
    }
    for tag in sorted(observed_tags):
        base[f"tag:{tag}"] = ["absent", "present"]
    sections = set(SECTION_TYPES)
    for rule in snapshot.rules.values():
        sections.update(rule.selector.section_types or [])
    base["section"] = sorted(sections)
    if domains is not None:
        base.update({axis: sorted(values) for axis, values in domains.items()})
    return base


def _dead_entries(
    snapshot: KBSnapshot,
    bindings: list[Binding],
    domains: dict[str, list[str]],
) -> list[DeadEntry]:
    dead: list[DeadEntry] = []
    seen: set[str] = set()
    for rule in snapshot.rules.values():
        if rule.selector.section_types == []:
            key = f"rule:{rule.id}:empty_selector"
            if key not in seen:
                seen.add(key)
                dead.append(
                    DeadEntry(
                        entry_id=rule.id,
                        source_kind="rule",
                        reason="empty_selector_sections",
                        detail=f"rule {rule.id} selector.section_types is empty",
                    )
                )
    for binding in bindings:
        if not is_satisfiable(binding.guard, domains):
            key = f"{binding.source_kind}:{binding.source_id}:{binding.element_path}"
            if key in seen:
                continue
            seen.add(key)
            dead.append(
                DeadEntry(
                    entry_id=binding.source_id,
                    source_kind=binding.source_kind,
                    reason="unsatisfiable_guard",
                    detail=(
                        f"{binding.source_kind} {binding.source_id} guard "
                        f"{_guard_summary(binding.guard)} is unsatisfiable against domains"
                    ),
                )
            )
    return dead


def _value_conflicts(bindings: list[Binding], domains: dict[str, list[str]]) -> list[Conflict]:
    conflicts: list[Conflict] = []
    by_path: dict[str, list[Binding]] = {}
    for binding in bindings:
        by_path.setdefault(binding.element_path, []).append(binding)
    for path, group in sorted(by_path.items()):
        for idx, left in enumerate(group):
            for right in group[idx + 1 :]:
                if left.token_id is not None and left.token_id == right.token_id:
                    continue
                if _same_value(left.value, right.value):
                    continue
                if not satisfiable(left.guard, right.guard):
                    continue
                overlap = conjunction(left.guard, right.guard)
                if overlap is None or not is_satisfiable(overlap, domains):
                    continue
                witness_ctx = witness(overlap, domains)
                detail = (
                    f"value conflict at {path}: {left.source_id}={_value_label(left.value)} "
                    f"vs {right.source_id}={_value_label(right.value)}; "
                    f"witness={json.dumps(witness_ctx, sort_keys=True)}"
                )
                if left.hardness == "hard_constraint" and right.hardness == "hard_constraint":
                    conflicts.append(
                        Conflict(
                            kind="hard_hard",
                            element_path=path,
                            a_id=left.source_id,
                            b_id=right.source_id,
                            overlap_guard=overlap,
                            detail=detail,
                        )
                    )
                    continue
                if _equal_through_precedence(left, right):
                    conflicts.append(
                        Conflict(
                            kind="equal_specificity",
                            element_path=path,
                            a_id=left.source_id,
                            b_id=right.source_id,
                            overlap_guard=overlap,
                            detail=detail,
                        )
                    )
    return conflicts


def _intra_token_conflicts(bindings: list[Binding], domains: dict[str, list[str]]) -> list[Conflict]:
    conflicts: list[Conflict] = []
    by_token: dict[str, list[Binding]] = {}
    for binding in bindings:
        if binding.token_id is None or binding.source_kind != "token_variant":
            continue
        by_token.setdefault(binding.token_id, []).append(binding)
    for token_id, group in sorted(by_token.items()):
        for idx, left in enumerate(group):
            for right in group[idx + 1 :]:
                if _same_value(left.value, right.value):
                    continue
                if not satisfiable(left.guard, right.guard):
                    continue
                overlap = conjunction(left.guard, right.guard)
                if overlap is None or not is_satisfiable(overlap, domains):
                    continue
                witness_ctx = witness(overlap, domains)
                conflicts.append(
                    Conflict(
                        kind="intra_token",
                        element_path=left.element_path,
                        a_id=left.source_id,
                        b_id=right.source_id,
                        overlap_guard=overlap,
                        detail=(
                            f"intra_token {token_id}: {_value_label(left.value)} vs "
                            f"{_value_label(right.value)}; witness="
                            f"{json.dumps(witness_ctx, sort_keys=True)}"
                        ),
                    )
                )
    return conflicts


def _verbatim_clashes(rules: dict[str, BrandRule], domains: dict[str, list[str]]) -> list[Conflict]:
    verbatim_rules: list[BrandRule] = []
    for rule in rules.values():
        preferred = _preferred_form(rule)
        if preferred is None:
            continue
        if rule.constraint_type == "verbatim_content" or preferred is not None:
            verbatim_rules.append(rule)
    conflicts: list[Conflict] = []
    for idx, left in enumerate(verbatim_rules):
        left_form = _preferred_form(left)
        left_guard = _rule_scope_guard(left)
        left_path = left.selector.element_path
        for right in verbatim_rules[idx + 1 :]:
            right_form = _preferred_form(right)
            if right_form is None or left_form == right_form:
                continue
            if left.selector.element_path != right.selector.element_path:
                continue
            if _constraint_trigger(left) != _constraint_trigger(right):
                continue
            right_guard = _rule_scope_guard(right)
            if not satisfiable(left_guard, right_guard):
                continue
            overlap = conjunction(left_guard, right_guard)
            if overlap is None or not is_satisfiable(overlap, domains):
                continue
            witness_ctx = witness(overlap, domains)
            a_id, b_id = sorted([left.id, right.id])
            conflicts.append(
                Conflict(
                    kind="verbatim_clash",
                    element_path=left_path,
                    a_id=a_id,
                    b_id=b_id,
                    overlap_guard=overlap,
                    detail=(
                        f"verbatim clash at {left_path}: {left.id} vs {right.id}; "
                        f"witness={json.dumps(witness_ctx, sort_keys=True)}"
                    ),
                )
            )
    return conflicts


def _precedence_proposals(
    conflicts: list[Conflict],
    rules: dict[str, BrandRule],
) -> list[PrecedenceProposal]:
    proposals: list[PrecedenceProposal] = []
    seen: set[tuple[str, str]] = set()
    for conflict in conflicts:
        if conflict.kind != "equal_specificity":
            continue
        left_rule = _owning_rule(conflict.a_id, rules)
        right_rule = _owning_rule(conflict.b_id, rules)
        if left_rule is None or right_rule is None or left_rule.id == right_rule.id:
            continue
        a_id, b_id = sorted((left_rule.id, right_rule.id))
        pair = (a_id, b_id)
        if pair in seen:
            continue
        seen.add(pair)
        later = _later_rule(left_rule, right_rule)
        earlier = right_rule if later.id == left_rule.id else left_rule
        proposed = max(later.precedence, earlier.precedence) + 1
        proposals.append(
            PrecedenceProposal(
                rule_id=later.id,
                precedence=proposed,
                detail=(
                    f"propose precedence {proposed} for {later.id} over {earlier.id} "
                    f"based on doc_ref order ({later.doc_ref} after {earlier.doc_ref})"
                ),
            )
        )
    return proposals


def _owning_rule(source_id: str, rules: dict[str, BrandRule]) -> BrandRule | None:
    candidates = [
        rule
        for rule_id, rule in rules.items()
        if source_id == rule_id
        or (
            source_id.startswith(rule_id)
            and len(source_id) > len(rule_id)
            and source_id[len(rule_id)] in "#:"
        )
    ]
    return max(candidates, key=lambda rule: len(rule.id), default=None)


def _later_rule(left: BrandRule, right: BrandRule) -> BrandRule:
    left_key = _doc_ref_sort_key(left.doc_ref)
    right_key = _doc_ref_sort_key(right.doc_ref)
    if left_key == right_key:
        return right if right.id > left.id else left
    return right if right_key > left_key else left


def _doc_ref_sort_key(doc_ref: Optional[str]) -> tuple[str, int]:
    if not doc_ref:
        return ("", -1)
    if "[" in doc_ref and doc_ref.endswith("]"):
        category, index_text = doc_ref[:-1].split("[", 1)
        try:
            return (category, int(index_text))
        except ValueError:
            return (doc_ref, 0)
    return (doc_ref, 0)


def _specificity_rank(binding: Binding) -> tuple[int, int, int, int, int, int]:
    hardness_rank = {"hard_constraint": 3, "strong_default": 2, "soft_guidance": 1}[binding.hardness]
    scope_rank = {"campaign": 3, "brand": 2, "org_baseline": 1}[binding.scope]
    source_kind_rank = {
        "rule_binding": 2,
        "token_variant": 1,
        "token_default": 0,
    }[binding.source_kind]
    return (
        hardness_rank,
        scope_rank,
        binding.selector_rank,
        len(binding.guard),
        source_kind_rank,
        binding.precedence,
    )


def _equal_through_precedence(left: Binding, right: Binding) -> bool:
    return _specificity_rank(left) == _specificity_rank(right)


def _dedupe_conflicts(conflicts: list[Conflict]) -> list[Conflict]:
    seen: set[tuple[str, Optional[str], str, str]] = set()
    out: list[Conflict] = []
    for conflict in sorted(
        conflicts,
        key=lambda item: (item.kind, item.element_path or "", item.a_id, item.b_id),
    ):
        a_id, b_id = sorted((conflict.a_id, conflict.b_id))
        key = (conflict.kind, conflict.element_path, a_id, b_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            Conflict(
                kind=conflict.kind,
                element_path=conflict.element_path,
                a_id=a_id,
                b_id=b_id,
                overlap_guard=conflict.overlap_guard,
                detail=conflict.detail,
            )
        )
    return out


def _preferred_form(rule: BrandRule) -> Optional[str]:
    governance = rule.governance if isinstance(rule.governance, dict) else None
    if governance is None:
        return None
    preferred = governance.get("preferred_form")
    return str(preferred) if preferred is not None else None


def _constraint_trigger(rule: BrandRule) -> str:
    effect = rule.effect if isinstance(rule.effect, dict) else {}
    trigger = effect.get("trigger")
    if isinstance(trigger, BaseModel):
        trigger = trigger.model_dump(mode="json")
    return json.dumps(trigger, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _rule_scope_guard(rule: BrandRule) -> Guard:
    guards = [normalize_guard(rule.applies_when)]
    if rule.audience:
        guards.append(normalize_guard({"audience": rule.audience}))
    if rule.content_types is not None:
        guards.append(normalize_guard({"surface": rule.content_types}))
    if rule.selector.section_types is not None:
        guards.append(normalize_guard({"section": rule.selector.section_types}))
    return normalize_guard(guards)


def _same_value(left: Any, right: Any) -> bool:
    return json.dumps(left, sort_keys=True, ensure_ascii=False) == json.dumps(
        right, sort_keys=True, ensure_ascii=False
    )


def _value_label(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _guard_summary(guard: Guard) -> str:
    return json.dumps(
        {axis: term.model_dump(mode="json") for axis, term in sorted(guard.items())},
        sort_keys=True,
        ensure_ascii=False,
    )
