"""WP-13 pairwise consistency tests."""

from __future__ import annotations

import json

import pytest

from indexing_v2.consistency.pairwise import STAGE_VERSION, analyze_pairwise
from indexing_v2.contracts import Binding, KBSnapshot
from shared.schemas import BrandRule, BrandToken, Selector


def _snapshot(
    *,
    rules: dict[str, BrandRule] | None = None,
    tokens: dict[str, BrandToken] | None = None,
    domains: dict[str, list[str]] | None = None,
) -> KBSnapshot:
    return KBSnapshot(
        brand="minibible",
        rules=rules or {},
        tokens=tokens or {},
        assets={},
        subtypes={},
        templates={},
        predicate_domains=domains
        or {
            "background_group": ["dark", "light"],
            "breakpoint": ["desktop", "mobile"],
            "campaign": ["none"],
            "content_tag": ["lpga"],
        },
    )


def _binding(
    *,
    source_id: str,
    element_path: str,
    value: object,
    guard: dict[str, object] | None = None,
    hardness: str = "hard_constraint",
    precedence: int = 0,
    source_kind: str = "rule_binding",
    token_id: str | None = None,
    scope: str = "brand",
    selector_rank: int = 3,
) -> Binding:
    from indexing_v2.cascade.guards import normalize_guard

    return Binding(
        element_path=element_path,
        token_id=token_id,
        value=value,
        guard=normalize_guard(guard or {}),
        source_kind=source_kind,  # type: ignore[arg-type]
        source_id=source_id,
        hardness=hardness,  # type: ignore[arg-type]
        scope=scope,  # type: ignore[arg-type]
        selector_rank=selector_rank,
        precedence=precedence,
    )


def _verbatim_rule(
    rule_id: str,
    preferred_form: str,
    *,
    audience: str | None = None,
    content_types: list[str] | None = None,
    sections: list[str] | None = None,
) -> BrandRule:
    return BrandRule(
        id=rule_id,
        brand_id="minibible",
        rule_class="governance",
        audience=audience,
        content_types=content_types,
        constraint_type="verbatim_content",
        selector=Selector(section_types=sections, element_path="disclosure"),
        effect={"trigger": {"kind": "content_tag", "value": "safety"}},
        governance={"preferred_form": preferred_form},
        rule_text=preferred_form,
    )


def test_stage_version() -> None:
    assert STAGE_VERSION == "1.0.0"
    assert analyze_pairwise(_snapshot(), []).schema_version == "2.0"


def test_hard_hard_conflict_with_witness() -> None:
    bindings = [
        _binding(
            source_id="rule_minibible_cta_fill_green",
            element_path="cta.button.fill",
            value="#01A47E",
            guard={"background_group": "light"},
        ),
        _binding(
            source_id="rule_minibible_cta_fill_orange",
            element_path="cta.button.fill",
            value="#FF5733",
            guard={"background_group": "light"},
        ),
    ]
    result = analyze_pairwise(_snapshot(), bindings)
    hard = [item for item in result.conflicts if item.kind == "hard_hard"]
    assert len(hard) == 1
    assert hard[0].a_id == "rule_minibible_cta_fill_green"
    assert hard[0].b_id == "rule_minibible_cta_fill_orange"
    assert "witness=" in hard[0].detail
    assert hard[0].overlap_guard["background_group"].values == ["light"]


def test_production_collector_scoped_assignment_bindings_are_live() -> None:
    def rule(rule_id: str, value: str) -> BrandRule:
        return BrandRule(
            id=rule_id,
            brand_id="minibible",
            rule_class="color_application",
            audience="hcp",
            content_types=["web"],
            scope="campaign",
            selector=Selector(section_types=["cta"], element_path="cta.button.fill"),
            applies_when=[
                {"kind": "campaign", "value": "launch"},
                {"kind": "content_tag", "value": "lpga"},
            ],
            constraint_type="binding",
            effect={
                "assignments": [
                    {"element_path": "cta.button.fill", "value": value},
                ]
            },
            hardness="hard_constraint",
            rule_text=rule_id,
        )

    rules = {
        "rule_scoped_green": rule("rule_scoped_green", "#01A47E"),
        "rule_scoped_orange": rule("rule_scoped_orange", "#FF5733"),
    }
    result = analyze_pairwise(_snapshot(rules=rules))

    assert result.dead_entries == []
    conflict = next(item for item in result.conflicts if item.kind == "hard_hard")
    assert {conflict.a_id, conflict.b_id} == set(rules)
    assert conflict.overlap_guard["audience"].values == ["hcp"]
    assert conflict.overlap_guard["surface"].values == ["web"]
    assert conflict.overlap_guard["campaign"].values == ["launch"]
    assert conflict.overlap_guard["tag:lpga"].values == ["present"]
    assert conflict.overlap_guard["section"].values == ["cta"]


def test_equal_specificity_conflict_and_precedence_proposal() -> None:
    bindings = [
        _binding(
            source_id="rule_a",
            element_path="cta.button.label",
            value="Start now",
            hardness="strong_default",
            precedence=0,
        ),
        _binding(
            source_id="rule_b",
            element_path="cta.button.label",
            value="Begin today",
            hardness="strong_default",
            precedence=0,
        ),
    ]
    rules = {
        "rule_a": BrandRule(
            id="rule_a",
            brand_id="minibible",
            rule_class="copy_editorial",
            rule_text="A",
            doc_ref="brand_foundation[0]",
        ),
        "rule_b": BrandRule(
            id="rule_b",
            brand_id="minibible",
            rule_class="copy_editorial",
            rule_text="B",
            doc_ref="layout_constraints[0]",
        ),
    }
    result = analyze_pairwise(_snapshot(rules=rules), bindings)
    kinds = {item.kind for item in result.conflicts}
    assert "equal_specificity" in kinds
    assert result.precedence_proposals
    assert result.precedence_proposals[0].rule_id == "rule_b"
    assert result.precedence_proposals[0].precedence == 1
    assert result.precedence_proposals[0].schema_version == "2.0"


def test_token_default_and_one_variant_are_not_intra_token_conflict() -> None:
    bindings = [
        _binding(
            source_id="tok_sem_cta",
            token_id="tok_sem_cta",
            source_kind="token_default",
            element_path="cta.button.fill",
            value="#01A47E",
            hardness="strong_default",
        ),
        _binding(
            source_id="tok_sem_cta",
            token_id="tok_sem_cta",
            source_kind="token_variant",
            element_path="cta.button.fill",
            value="#FFFFFF",
            guard={"background_group": "dark"},
            hardness="strong_default",
        ),
    ]
    result = analyze_pairwise(_snapshot(), bindings)
    intra = [item for item in result.conflicts if item.kind == "intra_token"]
    assert intra == []


def test_overlapping_token_variants_are_intra_token_conflict() -> None:
    bindings = [
        _binding(
            source_id="tok_sem_cta",
            token_id="tok_sem_cta",
            source_kind="token_variant",
            element_path="cta.button.fill",
            value="#FFFFFF",
            guard={"background_group": "dark"},
            hardness="strong_default",
        ),
        _binding(
            source_id="tok_sem_cta",
            token_id="tok_sem_cta",
            source_kind="token_variant",
            element_path="cta.button.fill",
            value="#EEEEEE",
            guard={"background_group": "dark", "breakpoint": "mobile"},
            hardness="strong_default",
        ),
    ]
    result = analyze_pairwise(_snapshot(), bindings)
    intra = [item for item in result.conflicts if item.kind == "intra_token"]
    assert len(intra) == 1
    assert intra[0].a_id == intra[0].b_id == "tok_sem_cta"


def test_production_semantic_assignment_default_and_variant_do_not_conflict() -> None:
    tokens = {
        "tok_sem_cta": BrandToken(
            id="tok_sem_cta",
            brand_id="minibible",
            token_type="color",
            kind="semantic",
            key="cta.button.fill",
            element_paths=["cta.button.fill"],
            value={
                "default": "#01A47E",
                "variants": [
                    {
                        "when": {"background_group": "dark"},
                        "value": "#FFFFFF",
                    }
                ],
            },
            scope="campaign:launch",
        )
    }
    rules = {
        "rule_assign_semantic": BrandRule(
            id="rule_assign_semantic",
            brand_id="minibible",
            rule_class="color_application",
            constraint_type="binding",
            selector=Selector(section_types=["cta"], element_path="cta.button.fill"),
            effect={
                "assignments": [
                    {
                        "element_path": "cta.button.fill",
                        "token_id": "tok_sem_cta",
                    }
                ]
            },
            rule_text="Assign semantic CTA fill.",
        )
    }

    result = analyze_pairwise(_snapshot(rules=rules, tokens=tokens))

    assert result.conflicts == []
    assert result.dead_entries == []


def test_verbatim_clash() -> None:
    rules = {
        "rule_disclosure_a": BrandRule(
            id="rule_disclosure_a",
            brand_id="minibible",
            rule_class="governance",
            constraint_type="verbatim_content",
            selector=Selector(element_path="disclosure"),
            effect={"trigger": {"kind": "content_tag", "value": "safety"}},
            governance={"preferred_form": "Ask your doctor."},
            rule_text="A",
        ),
        "rule_disclosure_b": BrandRule(
            id="rule_disclosure_b",
            brand_id="minibible",
            rule_class="governance",
            constraint_type="verbatim_content",
            selector=Selector(element_path="disclosure"),
            effect={"trigger": {"kind": "content_tag", "value": "safety"}},
            governance={"preferred_form": "Consult your physician."},
            rule_text="B",
        ),
    }
    result = analyze_pairwise(_snapshot(rules=rules), [])
    clashes = [item for item in result.conflicts if item.kind == "verbatim_clash"]
    assert len(clashes) == 1
    assert set((clashes[0].a_id, clashes[0].b_id)) == {
        "rule_disclosure_a",
        "rule_disclosure_b",
    }


def test_verbatim_different_triggers_do_not_clash() -> None:
    rules = {
        "rule_disclosure_a": BrandRule(
            id="rule_disclosure_a",
            brand_id="minibible",
            rule_class="governance",
            constraint_type="verbatim_content",
            selector=Selector(element_path="disclosure"),
            effect={"trigger": {"kind": "content_tag", "value": "safety"}},
            governance={"preferred_form": "Ask your doctor."},
            rule_text="A",
        ),
        "rule_disclosure_b": BrandRule(
            id="rule_disclosure_b",
            brand_id="minibible",
            rule_class="governance",
            constraint_type="verbatim_content",
            selector=Selector(element_path="disclosure"),
            effect={"trigger": {"kind": "content_tag", "value": "eligibility"}},
            governance={"preferred_form": "Consult your physician."},
            rule_text="B",
        ),
    }
    result = analyze_pairwise(_snapshot(rules=rules), [])
    assert [item for item in result.conflicts if item.kind == "verbatim_clash"] == []


def test_verbatim_same_audience_surface_and_overlapping_sections_clash() -> None:
    rules = {
        "rule_disclosure_a": _verbatim_rule(
            "rule_disclosure_a",
            "Ask your doctor.",
            audience="hcp",
            content_types=["web"],
            sections=["footer", "hero"],
        ),
        "rule_disclosure_b": _verbatim_rule(
            "rule_disclosure_b",
            "Consult your physician.",
            audience="hcp",
            content_types=["web"],
            sections=["footer"],
        ),
    }

    result = analyze_pairwise(_snapshot(rules=rules), [])

    clash = next(item for item in result.conflicts if item.kind == "verbatim_clash")
    assert clash.overlap_guard["audience"].values == ["hcp"]
    assert clash.overlap_guard["surface"].values == ["web"]
    assert clash.overlap_guard["section"].values == ["footer"]


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (
            {"audience": "hcp"},
            {"audience": "dtp_patient"},
        ),
        (
            {"content_types": ["web"]},
            {"content_types": ["email"]},
        ),
        (
            {"sections": ["hero"]},
            {"sections": ["footer"]},
        ),
    ],
)
def test_verbatim_disjoint_rule_scopes_do_not_clash(
    left: dict[str, object],
    right: dict[str, object],
) -> None:
    rules = {
        "rule_disclosure_a": _verbatim_rule(
            "rule_disclosure_a",
            "Ask your doctor.",
            **left,  # type: ignore[arg-type]
        ),
        "rule_disclosure_b": _verbatim_rule(
            "rule_disclosure_b",
            "Consult your physician.",
            **right,  # type: ignore[arg-type]
        ),
    }

    result = analyze_pairwise(_snapshot(rules=rules), [])

    assert [item for item in result.conflicts if item.kind == "verbatim_clash"] == []


def test_dead_unsat_retired_campaign_domain_excludes_value() -> None:
    bindings = [
        _binding(
            source_id="rule_minibible_retired_campaign_layout",
            element_path="hero",
            value="legacy_hero_gradient",
            guard={"campaign": "retired_campaign"},
            hardness="strong_default",
        )
    ]
    domains = {"campaign": ["none"], "background_group": ["dark", "light"]}
    result = analyze_pairwise(_snapshot(domains=domains), bindings, domains=domains)
    dead = [item for item in result.dead_entries if item.entry_id == "rule_minibible_retired_campaign_layout"]
    assert len(dead) == 1
    assert dead[0].reason == "unsatisfiable_guard"
    assert dead[0].schema_version == "2.0"


def test_paired_dead_guards_are_dead_without_conflict_or_witness_crash() -> None:
    bindings = [
        _binding(
            source_id="rule_retired_a",
            element_path="hero.layout",
            value="legacy_a",
            guard={"campaign": "retired_campaign"},
        ),
        _binding(
            source_id="rule_retired_b",
            element_path="hero.layout",
            value="legacy_b",
            guard={"campaign": "retired_campaign"},
        ),
    ]
    domains = {"campaign": ["none"]}
    result = analyze_pairwise(_snapshot(domains=domains), bindings, domains=domains)
    assert result.conflicts == []
    assert {item.entry_id for item in result.dead_entries} == {
        "rule_retired_a",
        "rule_retired_b",
    }


def test_cardinality_rules_not_flagged_as_binding_conflicts() -> None:
    rules = {
        "rule_minibible_cta_max_one": BrandRule(
            id="rule_minibible_cta_max_one",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            effect={"max": 1, "per": "email", "target": "cta.button.primary"},
            hardness="hard_constraint",
            rule_text="max one",
            selector=Selector(element_path="cta.button.primary"),
        ),
        "rule_minibible_cta_min_two_touchpoints": BrandRule(
            id="rule_minibible_cta_min_two_touchpoints",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            effect={"min": 2, "per": "email", "target": "cta"},
            hardness="hard_constraint",
            rule_text="min two",
            selector=Selector(element_path="cta"),
        ),
    }
    result = analyze_pairwise(_snapshot(rules=rules), [])
    assert result.conflicts == []


def test_precedence_proposals_not_applied_to_rules() -> None:
    rules = {
        "rule_a": BrandRule(
            id="rule_a",
            brand_id="minibible",
            rule_class="copy_editorial",
            rule_text="A",
            precedence=0,
            doc_ref="brand_foundation[0]",
        ),
        "rule_b": BrandRule(
            id="rule_b",
            brand_id="minibible",
            rule_class="copy_editorial",
            rule_text="B",
            precedence=0,
            doc_ref="layout_constraints[0]",
        ),
    }
    bindings = [
        _binding(source_id="rule_a", element_path="cta.label", value="A", hardness="strong_default"),
        _binding(source_id="rule_b", element_path="cta.label", value="B", hardness="strong_default"),
    ]
    result = analyze_pairwise(_snapshot(rules=rules), bindings)
    assert rules["rule_a"].precedence == 0
    assert rules["rule_b"].precedence == 0
    assert result.precedence_proposals


def test_precedence_proposal_resolves_synthetic_binding_source_ids() -> None:
    rules = {
        "rule_a": BrandRule(
            id="rule_a",
            brand_id="minibible",
            rule_class="copy_editorial",
            rule_text="A",
            doc_ref="brand_foundation[0]",
        ),
        "rule_b": BrandRule(
            id="rule_b",
            brand_id="minibible",
            rule_class="copy_editorial",
            rule_text="B",
            doc_ref="layout_constraints[0]",
        ),
    }
    bindings = [
        _binding(
            source_id="rule_a#0",
            element_path="cta.label",
            value="A",
            hardness="strong_default",
        ),
        _binding(
            source_id="rule_b:default",
            element_path="cta.label",
            value="B",
            hardness="strong_default",
        ),
    ]

    result = analyze_pairwise(_snapshot(rules=rules), bindings)

    conflict = next(item for item in result.conflicts if item.kind == "equal_specificity")
    assert {conflict.a_id, conflict.b_id} == {"rule_a#0", "rule_b:default"}
    assert [(item.rule_id, item.precedence) for item in result.precedence_proposals] == [
        ("rule_b", 1)
    ]


def test_precedence_not_proposed_between_assignments_of_same_rule() -> None:
    rule = BrandRule(
        id="rule_assign",
        brand_id="minibible",
        rule_class="copy_editorial",
        rule_text="Assignments.",
    )
    bindings = [
        _binding(
            source_id="rule_assign#0",
            element_path="cta.label",
            value="A",
            hardness="strong_default",
        ),
        _binding(
            source_id="rule_assign#1",
            element_path="cta.label",
            value="B",
            hardness="strong_default",
        ),
    ]

    result = analyze_pairwise(_snapshot(rules={rule.id: rule}), bindings)

    assert any(item.kind == "equal_specificity" for item in result.conflicts)
    assert result.precedence_proposals == []


def test_pairwise_determinism_twice() -> None:
    bindings = [
        _binding(
            source_id="rule_minibible_cta_fill_green",
            element_path="cta.button.fill",
            value="#01A47E",
            guard={"background_group": "light"},
        ),
        _binding(
            source_id="rule_minibible_cta_fill_orange",
            element_path="cta.button.fill",
            value="#FF5733",
            guard={"background_group": "light"},
        ),
    ]
    first = analyze_pairwise(_snapshot(), bindings).model_dump(mode="json")
    second = analyze_pairwise(_snapshot(), bindings).model_dump(mode="json")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
