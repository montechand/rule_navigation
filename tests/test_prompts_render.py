"""WP-08 extraction prompt template render and port fidelity tests."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

import pytest

from indexing_v2.contracts import EVIDENCE_PATHS, EntityKind, SourceUnit
from indexing_v2.extraction.prompts import PromptRenderError, load_prompt
from indexing_v2.extraction.runner import render_units

RULE_NAV_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = RULE_NAV_ROOT / "tests" / "fixtures" / "minibible"
PROMPTS_DIR = RULE_NAV_ROOT / "indexing_v2" / "extraction" / "prompts"

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

# WP-07 evidence convention markers keyed by entity kind from EVIDENCE_PATHS.
EVIDENCE_CONVENTION_MARKERS: dict[str, list[str]] = {
    "token_primitive": [
        '"evidence"',
        "default_evidence",
        "value.variants",
        "verbatim substring",
    ],
    "token_semantic": [
        '"evidence"',
        "default_evidence",
        '"evidence" next to "value"',
        "value.variants",
    ],
    "asset": ['"evidence"'],
    "subtype": ['"evidence"'],
    "template": ['"evidence"', "body_evidence"],
    "rule": [
        '"evidence"',
        "effect_evidence",
        "snippets_evidence",
        "preferred_form_evidence",
    ],
}

# Behavioral fingerprints ported from v1 build_kb.py constants (sorted, hashed for stability).
V1_BEHAVIOR_MARKERS: dict[str, list[str]] = {
    "tokens_primitive": sorted(
        [
            "EXHAUSTIVE",
            "One value = one token",
            "VALUES ARE CONCRETE",
            "derived_from",
            "other.<snake_case_name>",
            "Do not invent values not in the document",
            "SOURCE UNITS",
            "[unit_id] (kind) text",
        ]
    ),
    "tokens_semantic": sorted(
        [
            "SEMANTIC token",
            "IF/ELSE",
            '"$ref": "tok_..."',
            "element_paths",
            "background_group",
            "Use ONLY primitive ids from the catalog below",
            "default_evidence",
        ]
    ),
    "catalog_rest": sorted(
        [
            "Do NOT extract governance/compliance statements here",
            "STRUCTURAL CLASSES ONLY",
            "body VERBATIM",
            "template_groups",
            "asset_groups",
            "body_evidence",
            "graphic_device",
        ]
    ),
    "rules_cluster": sorted(
        [
            "CLUSTER, don't atomize",
            "VALUES LIVE IN TOKENS",
            "Effect payload shapes by constraint_type",
            "binding:",
            "cardinality:",
            "ordering:",
            "pairing:",
            "exclusivity:",
            "verbatim_content:",
            "GOVERNANCE FACET",
            "preferred_form_evidence",
            "effect_evidence",
            "snippets_evidence",
            "NEVER write raw entity ids",
        ]
    ),
}

V1_BEHAVIOR_HASHES = {
    name: hashlib.sha256("|".join(markers).encode()).hexdigest()[:16]
    for name, markers in V1_BEHAVIOR_MARKERS.items()
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture
def minibible_units() -> list[SourceUnit]:
    rows = _read_jsonl(FIXTURE_ROOT / "expected" / "units.jsonl")
    return [SourceUnit.model_validate(row) for row in rows]


@pytest.fixture
def render_context(minibible_units: list[SourceUnit]) -> dict[str, str]:
    brand = "minibible"
    units_text = render_units(minibible_units)
    primitives = "\n".join(
        [
            "  tok_minibible_color_primary_green_01  key=color.primary.green  default=\"#01A47E\"",
            "  tok_minibible_color_white  key=color.neutral.white  default=\"#FFFFFF\"",
        ]
    )
    tokens = primitives + "\n  tok_minibible_sem_cta_button_fill  key=cta.button.fill  default=\"#01A47E\""
    catalog = (
        f"primitive tokens (2):\n{primitives}\n"
        f"semantic tokens (1):\n  tok_minibible_sem_cta_button_fill  key=cta.button.fill  default=\"#01A47E\""
    )
    return {
        "brand": brand,
        "units": units_text,
        "primitives": primitives,
        "tokens": tokens,
        "catalog": catalog,
        "doc_ref": "brand_foundation[0]",
        "group_id": "grp_minibible_brand_foundation_00",
    }


def _combined_text(template_name: str) -> str:
    template = load_prompt(template_name, PROMPTS_DIR)
    return f"{template.system}\n{template.user}"


def _assert_no_unresolved(text: str) -> None:
    unresolved = _PLACEHOLDER_RE.findall(text)
    assert not unresolved, f"unresolved placeholders: {unresolved}"


def _assert_markers_present(text: str, markers: list[str], *, label: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert not missing, f"{label} missing markers: {missing}"


def _behavior_hash(template_name: str) -> str:
    text = _combined_text(template_name)
    found = [marker for marker in V1_BEHAVIOR_MARKERS[template_name] if marker in text]
    return hashlib.sha256("|".join(found).encode()).hexdigest()[:16]


@pytest.mark.parametrize(
    ("template_name", "render_kwargs"),
    [
        ("tokens_primitive", {"brand", "units"}),
        ("tokens_semantic", {"brand", "units", "primitives"}),
        ("catalog_rest", {"brand", "units", "tokens"}),
        ("rules_cluster", {"brand", "doc_ref", "group_id", "units", "catalog"}),
    ],
)
def test_prompt_placeholders_match_runner(
    template_name: str,
    render_kwargs: set[str],
    render_context: dict[str, str],
) -> None:
    template = load_prompt(template_name, PROMPTS_DIR)
    assert set(template.placeholders()) == render_kwargs
    rendered = template.render(**{key: render_context[key] for key in render_kwargs})
    _assert_no_unresolved(rendered.system)
    _assert_no_unresolved(rendered.user)


def test_all_four_prompts_render_with_fixtures(render_context: dict[str, str]) -> None:
    renders = {
        "tokens_primitive": load_prompt("tokens_primitive", PROMPTS_DIR).render(
            brand=render_context["brand"], units=render_context["units"]
        ),
        "tokens_semantic": load_prompt("tokens_semantic", PROMPTS_DIR).render(
            brand=render_context["brand"],
            units=render_context["units"],
            primitives=render_context["primitives"],
        ),
        "catalog_rest": load_prompt("catalog_rest", PROMPTS_DIR).render(
            brand=render_context["brand"],
            units=render_context["units"],
            tokens=render_context["tokens"],
        ),
        "rules_cluster": load_prompt("rules_cluster", PROMPTS_DIR).render(
            brand=render_context["brand"],
            doc_ref=render_context["doc_ref"],
            group_id=render_context["group_id"],
            units=render_context["units"],
            catalog=render_context["catalog"],
        ),
    }
    for name, rendered in renders.items():
        combined = f"{rendered.system}\n{rendered.user}"
        _assert_no_unresolved(combined)
        assert render_context["brand"] in combined
        assert "[u_" in combined, f"{name} must reference rendered unit ids"
        assert "(kind)" not in combined or "[unit_id] (kind) text" in combined


@pytest.mark.parametrize("entity_kind", sorted(EVIDENCE_PATHS))
def test_evidence_convention_markers_per_entity_kind(entity_kind: str) -> None:
    prompt_by_kind = {
        "token_primitive": "tokens_primitive",
        "token_semantic": "tokens_semantic",
        "asset": "catalog_rest",
        "subtype": "catalog_rest",
        "template": "catalog_rest",
        "rule": "rules_cluster",
    }
    kind = cast(EntityKind, entity_kind)
    template_name = prompt_by_kind[kind]
    text = _combined_text(template_name)
    _assert_markers_present(
        text,
        EVIDENCE_CONVENTION_MARKERS[kind],
        label=f"{kind} in {template_name}",
    )
    for path in EVIDENCE_PATHS[kind]:
        if path == "":
            continue
        if path == "value.default":
            assert "default_evidence" in text
        elif path == "value.variants[*].value":
            assert "variants" in text and "evidence" in text
        elif path == "body":
            assert "body_evidence" in text
        elif path == "governance.preferred_form":
            assert "preferred_form_evidence" in text
        elif path == "effect":
            assert "effect_evidence" in text
        elif path == "snippets":
            assert "snippets_evidence" in text


@pytest.mark.parametrize("template_name", sorted(V1_BEHAVIOR_MARKERS))
def test_v1_behavioral_markers_preserved(template_name: str) -> None:
    text = _combined_text(template_name)
    for marker in V1_BEHAVIOR_MARKERS[template_name]:
        assert marker in text, f"{template_name} missing v1 marker: {marker!r}"
    assert _behavior_hash(template_name) == V1_BEHAVIOR_HASHES[template_name]


def test_catalog_and_rules_system_prompts_differ() -> None:
    catalog = load_prompt("catalog_rest", PROMPTS_DIR)
    rules = load_prompt("rules_cluster", PROMPTS_DIR)
    assert "entity catalog" in catalog.system
    assert "CLUSTER brand_rule" in rules.system
    assert catalog.system != rules.system


def test_render_rejects_unknown_placeholder(render_context: dict[str, str]) -> None:
    template = load_prompt("tokens_primitive", PROMPTS_DIR)
    with pytest.raises(PromptRenderError) as exc:
        template.render(brand=render_context["brand"])
    assert "units" in exc.value.missing


def test_units_placeholder_receives_rendered_format(
    render_context: dict[str, str],
) -> None:
    rendered = load_prompt("tokens_primitive", PROMPTS_DIR).render(
        brand=render_context["brand"],
        units=render_context["units"],
    )
    assert "[u_brand_foundation_0_0000]" in rendered.user
    assert "(heading)" in rendered.user
    assert "DESIGN BIBLE" not in rendered.user
    assert "SOURCE UNITS" in rendered.user
