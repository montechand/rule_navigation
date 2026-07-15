"""Finite-domain guard algebra for cascade and consistency analysis.

Usage: ``from indexing_v2.cascade.guards import normalize_guard, satisfiable, witness``
"""

from __future__ import annotations

from typing import Any

from indexing_v2.contracts import Guard, GuardTerm
from shared.schemas import PREDICATE_REGISTRY, Predicate

STAGE_VERSION = "1.0.0"

_TAG_DOMAIN = ("absent", "present")
_PREDICATE_VALUE_FIELDS: dict[str, str] = {
    "background_group": "group",
    "background_token": "token_id",
    "theme": "theme",
    "content_tag": "tag",
    "campaign": "name",
    "breakpoint": "breakpoint",
    "adjacent_section_state": "state",
    "position_in_email": "position",
    "first_mention": "term",
}


def normalize_guard(source: Any) -> Guard:
    """Normalize predicates or ``when`` mappings to a canonical conjunctive ``Guard``."""
    if source is None:
        return {}
    if isinstance(source, Predicate):
        return _merge_guards({}, _guard_from_predicate(source))
    if isinstance(source, list):
        out: Guard = {}
        for item in source:
            out = _merge_guards(out, normalize_guard(item))
        return _canonicalize(out)
    if isinstance(source, dict):
        if "kind" in source:
            return _canonicalize(_guard_from_predicate(Predicate.model_validate(source)))
        out = {}
        for axis, raw in source.items():
            out = _merge_guards(out, _guard_from_axis_term(str(axis), raw))
        return _canonicalize(out)
    if hasattr(source, "model_dump"):
        return normalize_guard(source.model_dump(mode="json"))
    raise TypeError(f"unsupported guard source: {type(source)!r}")


def satisfiable(a: Guard, b: Guard) -> bool:
    """True when shared axes have intersecting value sets."""
    if any(not term.values for term in a.values()) or any(not term.values for term in b.values()):
        return False
    for axis in sorted(set(a) & set(b)):
        if _intersect_terms(a[axis], b[axis]) is None:
            return False
    return True


def conjunction(a: Guard, b: Guard) -> Guard | None:
    """Merge two guards; ``None`` when unsatisfiable."""
    if any(not term.values for term in a.values()) or any(not term.values for term in b.values()):
        return None
    merged: Guard = {}
    for axis in sorted(set(a) | set(b)):
        if axis in a and axis in b:
            term = _intersect_terms(a[axis], b[axis])
            if term is None:
                return None
            merged[axis] = term
        elif axis in a:
            merged[axis] = a[axis]
        else:
            merged[axis] = b[axis]
    return _canonicalize(merged)


def witness(g: Guard, domains: dict[str, list[str]]) -> dict[str, str]:
    """Deterministic satisfying assignment using sorted domain values."""
    assignment: dict[str, str] = {}
    for axis in sorted(g):
        allowed = _allowed_values(axis, g[axis], domains)
        if not allowed:
            raise ValueError(f"no satisfying value for axis {axis!r}")
        assignment[axis] = allowed[0]
    return assignment


def is_satisfiable(g: Guard, domains: dict[str, list[str]]) -> bool:
    """False when any bound axis has an empty feasible domain."""
    if not g:
        return True
    for axis in sorted(g):
        if not _allowed_values(axis, g[axis], domains):
            return False
    return True


def _canonicalize(guard: Guard) -> Guard:
    out: Guard = {}
    for axis in sorted(guard):
        term = guard[axis]
        values = sorted(set(term.values))
        if not values:
            out[axis] = GuardTerm(op=term.op, values=[])
            continue
        op: str = "eq" if len(values) == 1 else "in"
        out[axis] = GuardTerm(op=op, values=values)  # type: ignore[arg-type]
    return out


def _merge_guards(left: Guard, right: Guard) -> Guard:
    merged: Guard = {}
    for axis in sorted(set(left) | set(right)):
        if axis in left and axis in right:
            term = _intersect_terms(left[axis], right[axis])
            merged[axis] = term if term is not None else GuardTerm(op="eq", values=[])
        elif axis in left:
            merged[axis] = left[axis]
        else:
            merged[axis] = right[axis]
    return merged


def _guard_from_predicate(predicate: Predicate) -> Guard:
    if predicate.kind == "content_tag":
        tags = _predicate_value_strings(predicate.kind, predicate.value)
        out: Guard = {}
        for tag in tags:
            out[f"tag:{tag}"] = GuardTerm(op="eq", values=["present"])
        return out
    values = _predicate_value_strings(predicate.kind, predicate.value)
    if not values:
        return {}
    if len(values) == 1:
        return {predicate.kind: GuardTerm(op="eq", values=[values[0]])}
    return {predicate.kind: GuardTerm(op="in", values=sorted(values))}


def _guard_from_axis_term(axis: str, raw: Any) -> Guard:
    if axis.startswith("tag:"):
        return _guard_from_tag_axis(axis, raw)
    if axis == "content_tag":
        return _guard_from_content_tag_raw(raw)
    if isinstance(raw, GuardTerm):
        return {axis: raw}
    if isinstance(raw, dict) and "op" in raw and "values" in raw:
        term = GuardTerm.model_validate(raw)
        if term.op == "has_tag":
            out: Guard = {}
            for tag in term.values:
                out[f"tag:{tag}"] = GuardTerm(op="eq", values=["present"])
            return out
        return {axis: term}
    if isinstance(raw, str):
        return {axis: GuardTerm(op="eq", values=[raw])}
    if isinstance(raw, list):
        return {axis: GuardTerm(op="in", values=sorted(str(v) for v in raw))}
    if isinstance(raw, dict):
        if "kind" in raw:
            return _guard_from_predicate(Predicate.model_validate(raw))
        field = _PREDICATE_VALUE_FIELDS.get(axis)
        if field is not None and field in raw:
            return {axis: GuardTerm(op="eq", values=[str(raw[field])])}
        if len(raw) == 1:
            inner_axis, inner = next(iter(raw.items()))
            if inner_axis in PREDICATE_REGISTRY or inner_axis.startswith("tag:"):
                return normalize_guard({inner_axis: inner})
            return _guard_from_axis_term(axis, inner)
        values: list[str] = []
        for inner_axis, inner in raw.items():
            values.extend(_predicate_value_strings(str(inner_axis), inner))
        if not values:
            return {}
        if len(values) == 1:
            return {axis: GuardTerm(op="eq", values=[values[0]])}
        return {axis: GuardTerm(op="in", values=sorted(values))}
    return {axis: GuardTerm(op="eq", values=[str(raw)])}


def _guard_from_content_tag_raw(raw: Any) -> Guard:
    if isinstance(raw, dict) and raw.get("op") == "has_tag":
        term = GuardTerm.model_validate(raw)
        out: Guard = {}
        for tag in term.values:
            out[f"tag:{tag}"] = GuardTerm(op="eq", values=["present"])
        return out
    if isinstance(raw, dict) and "tag" in raw:
        return {f"tag:{raw['tag']}": GuardTerm(op="eq", values=["present"])}
    if isinstance(raw, str):
        return {f"tag:{raw}": GuardTerm(op="eq", values=["present"])}
    return normalize_guard({"kind": "content_tag", "value": raw})


def _guard_from_tag_axis(axis: str, raw: Any) -> Guard:
    if isinstance(raw, dict) and "op" in raw and "values" in raw:
        term = GuardTerm.model_validate(raw)
        values = sorted(set(term.values))
        op: str = "eq" if len(values) == 1 else "in"
        return {axis: GuardTerm(op=op, values=values)}  # type: ignore[arg-type]
    if isinstance(raw, str):
        return {axis: GuardTerm(op="eq", values=[raw])}
    return {axis: GuardTerm(op="eq", values=["present"])}


def _predicate_value_strings(kind: str, value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        field = _PREDICATE_VALUE_FIELDS.get(kind)
        if field is not None and field in value:
            return [str(value[field])]
        if len(value) == 1:
            inner_axis, inner = next(iter(value.items()))
            return _predicate_value_strings(str(inner_axis), inner)
        out: list[str] = []
        for inner_axis, inner in value.items():
            out.extend(_predicate_value_strings(str(inner_axis), inner))
        return out
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _term_values(term: GuardTerm) -> set[str]:
    return set(term.values)


def _intersect_terms(left: GuardTerm, right: GuardTerm) -> GuardTerm | None:
    values = sorted(_term_values(left) & _term_values(right))
    if not values:
        return None
    op: str = "eq" if len(values) == 1 else "in"
    return GuardTerm(op=op, values=values)  # type: ignore[arg-type]


def _allowed_values(axis: str, term: GuardTerm, domains: dict[str, list[str]]) -> list[str]:
    domain = _axis_domain(axis, domains)
    if not domain:
        return []
    feasible = sorted(_term_values(term) & set(domain))
    return feasible


def _axis_domain(axis: str, domains: dict[str, list[str]]) -> list[str]:
    if axis in domains:
        return sorted(domains[axis])
    if axis.startswith("tag:"):
        return list(_TAG_DOMAIN)
    return []
