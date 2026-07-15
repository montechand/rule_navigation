"""Binding collection, specificity ordering, and per-property resolution (§5.10.2).

Usage: ``from indexing_v2.cascade.resolve import collect_bindings, resolve_element, specificity``
"""

from __future__ import annotations

import json
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from indexing_v2.cascade.guards import normalize_guard, satisfiable
from indexing_v2.contracts import SCHEMA_VERSION, Binding, ContextKey, Guard, GuardTerm, KBSnapshot
from shared.schemas import BrandRule, BrandToken

STAGE_VERSION = "1.0.0"

# §5.10.1 residual axes (verbatim) plus ``section`` from §9.6 selector folding.
RESIDUAL_AXES: tuple[str, ...] = (
    "section_type",
    "background_group",
    "breakpoint",
    "position_in_email",
    "adjacent_section_state",
    "first_mention",
    "background_token",
    "section",
)

EMAIL_LEVEL_AXES: frozenset[str] = frozenset({"audience", "surface", "campaign", "theme"})


class TokenResolutionError(Exception):
    """Raised when a ``$ref`` chain is cyclic or references a missing token."""

    def __init__(self, message: str, *, chain: list[str]) -> None:
        super().__init__(message)
        self.chain = chain


class ResolvedCandidate(BaseModel):
    schema_version: str = SCHEMA_VERSION
    value: Any
    token_id: Optional[str] = None
    residual_guard: Guard
    source_id: str
    source_kind: Literal["rule_binding", "token_variant", "token_default"]
    hardness: Literal["hard_constraint", "strong_default", "soft_guidance"]
    spec: list[Any] = Field(default_factory=list)


class ResolvedProperty(BaseModel):
    schema_version: str = SCHEMA_VERSION
    element_path: str
    candidates: list[ResolvedCandidate] = Field(default_factory=list)
    resolved: Any = None
    conflict: bool = False
    tied_source_ids: list[str] = Field(default_factory=list)


def specificity(binding: Binding) -> tuple[Any, ...]:
    """Total order per ``SPECIFICITY_DOC`` including ``source_id`` as final tiebreak."""
    return specificity_without_id(binding) + (binding.source_id,)


def specificity_without_id(binding: Binding) -> tuple[int, int, int, int, int, int]:
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


def collect_bindings(snapshot: KBSnapshot) -> list[Binding]:
    """Collect all bindings from semantic tokens and binding rules in the snapshot."""
    bindings: list[Binding] = []
    for token in snapshot.tokens.values():
        if token.kind != "semantic":
            continue
        bindings.extend(_bindings_for_token(token, snapshot.tokens))
    for rule in snapshot.rules.values():
        bindings.extend(_bindings_for_rule(rule, snapshot.tokens))
    return sorted(bindings, key=lambda item: (item.element_path, item.source_id, item.source_kind))


def resolve_ref_value(
    value: Any,
    tokens: dict[str, BrandToken],
    *,
    seen: Optional[set[str]] = None,
    chain: Optional[list[str]] = None,
) -> Any:
    """Resolve ``$ref`` chains to concrete primitive defaults."""
    visited = seen or set()
    ref_chain = chain or []
    if isinstance(value, dict) and "$ref" in value:
        token_id = str(value["$ref"])
        next_chain = ref_chain + [token_id]
        if token_id in visited:
            raise TokenResolutionError(
                f"cyclic $ref chain: {' -> '.join(next_chain)}",
                chain=next_chain,
            )
        token = tokens.get(token_id)
        if token is None:
            raise TokenResolutionError(
                f"missing token in $ref chain: {' -> '.join(next_chain)}",
                chain=next_chain,
            )
        inner = token.value if isinstance(token.value, dict) else {"default": token.value}
        return resolve_ref_value(
            inner.get("default", inner),
            tokens,
            seen=visited | {token_id},
            chain=next_chain,
        )
    return value


def partial_eval_guard(guard: Guard, context: ContextKey, observed_tags: set[str]) -> Guard | None:
    """Partial-evaluate email-level axes; ``None`` when the context contradicts the guard."""
    residual: Guard = {}
    for axis in sorted(guard):
        term = guard[axis]
        if axis.startswith("tag:"):
            tag = axis[4:]
            required = "present" if tag in context.content_tags else "absent"
            if required not in term.values:
                return None
            continue
        if axis in EMAIL_LEVEL_AXES:
            ctx_value = _context_axis_value(axis, context)
            if ctx_value not in term.values:
                return None
            continue
        residual[axis] = term
    # Tags required present by guard but absent from context tags are already handled above.
    for tag in observed_tags:
        axis = f"tag:{tag}"
        if axis in guard:
            continue
        if tag in context.content_tags:
            continue
        # Guard may require absent via explicit term only; no implicit absent constraints.
    return normalize_guard(residual)


def resolve_element(
    element_path: str,
    bindings: list[Binding],
    email_ctx: ContextKey,
    *,
    observed_tags: Optional[set[str]] = None,
) -> ResolvedProperty:
    """Resolve one element path under an email-level context."""
    tags = observed_tags if observed_tags is not None else set(email_ctx.content_tags)
    survivors: list[tuple[Binding, Guard]] = []
    for binding in bindings:
        if binding.element_path != element_path:
            continue
        residual = partial_eval_guard(binding.guard, email_ctx, tags)
        if residual is None:
            continue
        survivors.append((binding, residual))

    ranked = sorted(
        survivors,
        key=lambda item: (specificity(item[0]), item[0].source_id),
        reverse=True,
    )

    candidates: list[ResolvedCandidate] = []
    for binding, residual in ranked:
        candidates.append(
            ResolvedCandidate(
                value=binding.value,
                token_id=binding.token_id,
                residual_guard=residual,
                source_id=binding.source_id,
                source_kind=binding.source_kind,
                hardness=binding.hardness,
                spec=list(specificity(binding)),
            )
        )

    return _resolved_property(element_path, candidates)


def _resolved_property(
    element_path: str,
    candidates: list[ResolvedCandidate],
) -> ResolvedProperty:
    ranked = sorted(candidates, key=lambda candidate: tuple(candidate.spec), reverse=True)
    conflict_ids: set[str] = set()
    if ranked:
        top_rank = tuple(ranked[0].spec[:6])
        tied = [candidate for candidate in ranked if tuple(candidate.spec[:6]) == top_rank]
        for index, left in enumerate(tied):
            for right in tied[index + 1 :]:
                if _value_key(left.value) == _value_key(right.value):
                    continue
                if satisfiable(left.residual_guard, right.residual_guard):
                    conflict_ids.update((left.source_id, right.source_id))
    resolved: Any = None
    if ranked and not conflict_ids and not ranked[0].residual_guard:
        resolved = ranked[0].value
    return ResolvedProperty(
        element_path=element_path,
        candidates=ranked,
        resolved=resolved,
        conflict=bool(conflict_ids),
        tied_source_ids=sorted(conflict_ids),
    )


def _bindings_for_token(token: BrandToken, tokens: dict[str, BrandToken]) -> list[Binding]:
    bindings: list[Binding] = []
    paths = token.element_paths or [token.key]
    hardness: Literal["hard_constraint", "strong_default", "soft_guidance"] = "strong_default"
    scope, token_guard = _token_constraints(token)
    value = token.value if isinstance(token.value, dict) else {"default": token.value}
    default_raw = value.get("default")
    if default_raw is not None:
        resolved = resolve_ref_value(default_raw, tokens)
        for path in paths:
            bindings.append(
                Binding(
                    element_path=path,
                    token_id=token.id,
                    value=resolved,
                    guard=token_guard,
                    source_kind="token_default",
                    source_id=token.id,
                    hardness=hardness,
                    scope=scope,
                    selector_rank=3,
                    precedence=0,
                )
            )
    for variant in value.get("variants") or []:
        if not isinstance(variant, dict):
            continue
        variant_guard = normalize_guard(variant.get("when"))
        variant_guard = _merge_guards(variant_guard, token_guard)
        raw_value = variant.get("value")
        if raw_value is None:
            continue
        resolved = resolve_ref_value(raw_value, tokens)
        for path in paths:
            bindings.append(
                Binding(
                    element_path=path,
                    token_id=token.id,
                    value=resolved,
                    guard=variant_guard,
                    source_kind="token_variant",
                    source_id=token.id,
                    hardness=hardness,
                    scope=scope,
                    selector_rank=3,
                    precedence=0,
                )
            )
    return bindings


def _bindings_for_rule(rule: BrandRule, tokens: dict[str, BrandToken]) -> list[Binding]:
    if rule.constraint_type != "binding":
        return []
    effect = rule.effect if isinstance(rule.effect, dict) else None
    if effect is None:
        return []

    selector = rule.selector
    selector_rank = 1
    if selector.element_path:
        selector_rank = 3
    elif selector.section_types:
        selector_rank = 2

    base_guard = _merge_guards(
        normalize_guard(rule.applies_when),
        _axis_guard("audience", [rule.audience] if rule.audience else None),
        _axis_guard("surface", rule.content_types),
    )
    section_guard = _selector_section_guard(selector.section_types)
    rule_guard = _merge_guards(base_guard, section_guard)

    assignments: list[dict[str, Any]] = []
    raw_assignments = effect.get("assignments")
    if isinstance(raw_assignments, list):
        assignments = [item for item in raw_assignments if isinstance(item, dict)]
    elif "value" in effect:
        assignments = [
            {
                "element_path": selector.element_path or "*",
                "value": effect["value"],
                "token_id": rule.token_ids[0] if rule.token_ids else None,
            }
        ]

    bindings: list[Binding] = []
    for index, assignment in enumerate(assignments):
        element_path = str(assignment.get("element_path") or selector.element_path or "*")
        token_id = assignment.get("token_id")
        token_id_str = str(token_id) if token_id is not None else None
        assignment_id = rule.id if len(assignments) == 1 else f"{rule.id}#{index}"
        raw_value = assignment.get("value")
        if raw_value is not None:
            bindings.append(
                _rule_binding(
                    rule,
                    element_path=element_path,
                    token_id=token_id_str,
                    value=resolve_ref_value(raw_value, tokens),
                    guard=rule_guard,
                    source_id=assignment_id,
                    scope=rule.scope,  # type: ignore[arg-type]
                    selector_rank=selector_rank,
                )
            )
            continue
        if token_id_str is None:
            continue
        token = tokens.get(token_id_str)
        if token is None:
            raise TokenResolutionError(
                f"missing token {token_id_str} for rule {rule.id}",
                chain=[token_id_str],
            )
        token_scope, token_guard = _token_constraints(token)
        effective_guard = _merge_guards(rule_guard, token_guard)
        effective_scope = _higher_scope(rule.scope, token_scope)
        token_value = token.value if isinstance(token.value, dict) else {"default": token.value}
        default_raw = token_value.get("default")
        if default_raw is not None:
            default_id = f"{assignment_id}:default" if token.kind == "semantic" else assignment_id
            bindings.append(
                _rule_binding(
                    rule,
                    element_path=element_path,
                    token_id=token_id_str,
                    value=resolve_ref_value(default_raw, tokens),
                    guard=effective_guard,
                    source_id=default_id,
                    scope=effective_scope,
                    selector_rank=selector_rank,
                )
            )
        if token.kind != "semantic":
            continue
        for variant_index, variant in enumerate(token_value.get("variants") or []):
            if not isinstance(variant, dict) or variant.get("value") is None:
                continue
            bindings.append(
                _rule_binding(
                    rule,
                    element_path=element_path,
                    token_id=token_id_str,
                    value=resolve_ref_value(variant["value"], tokens),
                    guard=_merge_guards(effective_guard, normalize_guard(variant.get("when"))),
                    source_id=f"{assignment_id}:variant:{variant_index}",
                    scope=effective_scope,
                    selector_rank=selector_rank,
                )
            )
    return bindings


def _rule_binding(
    rule: BrandRule,
    *,
    element_path: str,
    token_id: Optional[str],
    value: Any,
    guard: Guard,
    source_id: str,
    scope: Literal["org_baseline", "brand", "campaign"],
    selector_rank: int,
) -> Binding:
    return Binding(
        element_path=element_path,
        token_id=token_id,
        value=value,
        guard=guard,
        source_kind="rule_binding",
        source_id=source_id,
        hardness=rule.hardness,  # type: ignore[arg-type]
        scope=scope,
        selector_rank=selector_rank,
        precedence=rule.precedence,
    )


def _selector_section_guard(section_types: Optional[list[str]]) -> Guard:
    if section_types is None:
        return {}
    if not section_types:
        return {"section": GuardTerm(op="in", values=[])}
    return {"section": GuardTerm(op="in", values=sorted(section_types))}


def _axis_guard(axis: str, values: Optional[list[str]]) -> Guard:
    if values is None:
        return {}
    return normalize_guard({axis: values})


def _token_scope(token: BrandToken) -> tuple[Literal["org_baseline", "brand", "campaign"], Guard]:
    scope_text = token.scope or "global"
    if scope_text.startswith("campaign:"):
        campaign = scope_text.split(":", 1)[1]
        return "campaign", normalize_guard({"campaign": campaign})
    if scope_text.startswith("partnership:"):
        return "brand", {}
    return "org_baseline", {}


def _token_constraints(
    token: BrandToken,
) -> tuple[Literal["org_baseline", "brand", "campaign"], Guard]:
    scope, scope_guard = _token_scope(token)
    gate_guard: Guard = {}
    if token.gated and isinstance(token.gated, dict) and token.gated.get("gate") is not None:
        gate_guard = normalize_guard(token.gated["gate"])
    return (
        scope,
        _merge_guards(
            scope_guard,
            _axis_guard("audience", [token.audience] if token.audience else None),
            gate_guard,
        ),
    )


def _higher_scope(
    rule_scope: str,
    token_scope: Literal["org_baseline", "brand", "campaign"],
) -> Literal["org_baseline", "brand", "campaign"]:
    scopes: dict[str, Literal["org_baseline", "brand", "campaign"]] = {
        "org_baseline": "org_baseline",
        "brand": "brand",
        "campaign": "campaign",
    }
    normalized_rule = scopes.get(rule_scope, "brand")
    ranks = {"org_baseline": 1, "brand": 2, "campaign": 3}
    return token_scope if ranks[token_scope] > ranks[normalized_rule] else normalized_rule


def _merge_guards(*guards: Guard) -> Guard:
    parts = [guard for guard in guards if guard]
    if not parts:
        return {}
    return normalize_guard(parts)


def _context_axis_value(axis: str, context: ContextKey) -> str:
    if axis == "audience":
        return context.audience
    if axis == "surface":
        return context.surface
    if axis == "campaign":
        return context.campaign
    if axis == "theme":
        return context.theme
    raise KeyError(axis)


def _value_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)
