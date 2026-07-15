"""Email-level context enumeration for cascade compilation (§5.10.1).

Usage: ``from indexing_v2.cascade.contexts import enumerate_contexts, observed_content_tag_combos``
"""

from __future__ import annotations

from typing import Any

from indexing_v2.cascade.guards import normalize_guard
from indexing_v2.contracts import ContextKey, KBSnapshot

STAGE_VERSION = "1.0.0"


def observed_content_tag_combos(snapshot: KBSnapshot) -> list[list[str]]:
    """Tag sets from template/asset ``requires_content_tags`` plus singles and empty."""
    combos: set[tuple[str, ...]] = {()}
    observed = set(snapshot.predicate_domains.get("content_tag", []))
    for guard in _observed_guards(snapshot):
        observed.update(axis[4:] for axis in guard if axis.startswith("tag:"))
    for tags in _required_tag_lists(snapshot):
        observed.update(tags)
        if len(tags) > 1:
            combos.add(tags)
    observed.update(_forbidden_tags(snapshot))
    for tag in sorted(observed):
        combos.add((tag,))
    return [list(combo) for combo in sorted(combos, key=lambda item: (len(item), item))]


def enumerate_contexts(snapshot: KBSnapshot) -> list[ContextKey]:
    """Deterministically enumerate email-level audience×surface×campaign×theme×tags."""
    audiences = _audience_domain(snapshot)
    surfaces = _surface_domain(snapshot)
    campaigns = _named_domain(snapshot, "campaign")
    themes = _named_domain(snapshot, "theme")
    tag_combos = observed_content_tag_combos(snapshot)

    contexts: list[ContextKey] = []
    for audience in audiences:
        for surface in surfaces:
            for campaign in campaigns:
                for theme in themes:
                    for tags in tag_combos:
                        contexts.append(
                            ContextKey(
                                audience=audience,
                                surface=surface,
                                campaign=campaign,
                                theme=theme,
                                content_tags=sorted(tags),
                            )
                        )
    return contexts


def _audience_domain(snapshot: KBSnapshot) -> list[str]:
    values = {"dtp_patient"}
    values.update(snapshot.predicate_domains.get("audience", []))
    for rule in snapshot.rules.values():
        if rule.audience:
            values.add(rule.audience)
    for token in snapshot.tokens.values():
        if token.audience:
            values.add(token.audience)
    for template in snapshot.templates.values():
        if template.audience:
            values.add(template.audience)
    values.update(_guard_axis_values(snapshot, "audience"))
    values.update(_usage_axis_values(snapshot, "audience"))
    return sorted(values)


def _surface_domain(snapshot: KBSnapshot) -> list[str]:
    values = {"email"}
    values.update(snapshot.predicate_domains.get("surface", []))
    for rule in snapshot.rules.values():
        for item in rule.content_types or []:
            values.add(item)
    values.update(_guard_axis_values(snapshot, "surface"))
    values.update(_usage_axis_values(snapshot, "surface"))
    return sorted(values)


def _named_domain(snapshot: KBSnapshot, axis: str) -> list[str]:
    values = set(snapshot.predicate_domains.get(axis, []))
    values.update(_guard_axis_values(snapshot, axis))
    values.update(_usage_axis_values(snapshot, axis))
    if axis == "campaign":
        for token in snapshot.tokens.values():
            if token.scope.startswith("campaign:"):
                values.add(token.scope.split(":", 1)[1])
    values.add("none")
    return sorted(values)


def _observed_guards(snapshot: KBSnapshot) -> list[dict[str, Any]]:
    guards: list[dict[str, Any]] = []
    for rule in snapshot.rules.values():
        guards.append(normalize_guard(rule.applies_when))
    for token in snapshot.tokens.values():
        if token.gated and isinstance(token.gated, dict) and token.gated.get("gate") is not None:
            guards.append(normalize_guard(token.gated["gate"]))
        value = token.value if isinstance(token.value, dict) else {}
        for variant in value.get("variants") or []:
            if isinstance(variant, dict):
                guards.append(normalize_guard(variant.get("when")))
    return guards


def _guard_axis_values(snapshot: KBSnapshot, axis: str) -> set[str]:
    values: set[str] = set()
    for guard in _observed_guards(snapshot):
        if axis in guard:
            values.update(guard[axis].values)
    return values


def _usage_conditions(snapshot: KBSnapshot) -> list[dict[str, Any]]:
    usage: list[dict[str, Any]] = []
    for template in snapshot.templates.values():
        if isinstance(template.usage_conditions, dict):
            usage.append(template.usage_conditions)
    for asset in snapshot.assets.values():
        if isinstance(asset.usage_conditions, dict):
            usage.append(asset.usage_conditions)
    return usage


def _usage_axis_values(snapshot: KBSnapshot, axis: str) -> set[str]:
    values: set[str] = set()
    for usage in _usage_conditions(snapshot):
        raw = usage.get(axis)
        if raw is None:
            continue
        if isinstance(raw, list):
            values.update(str(item) for item in raw)
        else:
            values.add(str(raw))
    return values


def _required_tag_lists(snapshot: KBSnapshot) -> list[tuple[str, ...]]:
    out: set[tuple[str, ...]] = set()
    for usage in _usage_conditions(snapshot):
        raw = usage.get("requires_content_tags")
        if not isinstance(raw, list):
            continue
        tags = tuple(sorted({str(tag) for tag in raw if tag is not None}))
        if tags:
            out.add(tags)
    return sorted(out)


def _forbidden_tags(snapshot: KBSnapshot) -> set[str]:
    tags: set[str] = set()
    for usage in _usage_conditions(snapshot):
        raw = usage.get("forbidden_content_tags")
        if isinstance(raw, list):
            tags.update(str(tag) for tag in raw if tag is not None)
    return tags
