"""WP-14 binding resolution tests."""

from __future__ import annotations

import pytest

from indexing_v2.cascade.guards import normalize_guard
from indexing_v2.cascade.resolve import (
    STAGE_VERSION,
    TokenResolutionError,
    collect_bindings,
    partial_eval_guard,
    resolve_element,
    resolve_ref_value,
    specificity,
    specificity_without_id,
)
from indexing_v2.contracts import Binding, ContextKey, KBSnapshot
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
            "campaign": ["none"],
            "content_tag": ["lpga"],
        },
    )


def _binding(**kwargs: object) -> Binding:
    defaults = {
        "element_path": "cta.button.fill",
        "value": "#01A47E",
        "guard": {},
        "source_kind": "rule_binding",
        "source_id": "rule_a",
        "hardness": "hard_constraint",
        "scope": "brand",
        "selector_rank": 3,
        "precedence": 0,
    }
    defaults.update(kwargs)
    guard = defaults.pop("guard")
    return Binding(guard=normalize_guard(guard), **defaults)  # type: ignore[arg-type]


def test_stage_version() -> None:
    assert STAGE_VERSION == "1.0.0"


def test_specificity_order_and_source_id_tiebreak() -> None:
    hard = _binding(source_id="rule_hard", hardness="hard_constraint", precedence=0)
    soft = _binding(source_id="rule_soft", hardness="soft_guidance", precedence=99)
    assert specificity(hard) > specificity(soft)
    left = _binding(source_id="aaa", precedence=0)
    right = _binding(source_id="bbb", precedence=0)
    assert specificity(left) < specificity(right)
    assert specificity_without_id(left) == specificity_without_id(right)


def test_collect_bindings_rule_assignments_shape() -> None:
    rules = {
        "rule_colors": BrandRule(
            id="rule_colors",
            brand_id="minibible",
            rule_class="color_application",
            constraint_type="binding",
            selector=Selector(section_types=["cta"], element_path="cta.button.fill"),
            applies_when=[{"kind": "background_group", "value": {"group": "light"}}],
            effect={
                "assignments": [
                    {"element_path": "cta.button.fill", "value": "#01A47E"},
                    {"element_path": "cta.button.label", "token_id": "tok_label"},
                ]
            },
            hardness="hard_constraint",
            rule_text="colors",
        )
    }
    tokens = {
        "tok_label": BrandToken(
            id="tok_label",
            brand_id="minibible",
            token_type="case",
            kind="primitive",
            key="cta.button.label",
            value={"default": "sentence_case"},
        )
    }
    bindings = collect_bindings(_snapshot(rules=rules, tokens=tokens))
    paths = sorted(binding.element_path for binding in bindings)
    assert paths == ["cta.button.fill", "cta.button.label"]
    fill = next(binding for binding in bindings if binding.element_path == "cta.button.fill")
    assert fill.selector_rank == 3
    assert fill.guard["background_group"].values == ["light"]
    assert fill.guard["section"].values == ["cta"]


def test_semantic_rule_assignment_expands_default_variants_and_combines_guards() -> None:
    tokens = {
        "tok_sem": BrandToken(
            id="tok_sem",
            brand_id="minibible",
            token_type="color",
            kind="semantic",
            key="cta.button.fill",
            value={
                "default": {"$ref": "tok_green"},
                "variants": [
                    {
                        "when": {"background_group": "dark"},
                        "value": {"$ref": "tok_white"},
                    }
                ],
            },
            element_paths=["cta.button.fill"],
            audience="hcp",
            scope="campaign:flip",
            gated={"is_gated": True, "gate": {"kind": "content_tag", "value": "lpga"}},
        ),
        "tok_green": BrandToken(
            id="tok_green",
            brand_id="minibible",
            token_type="color",
            kind="primitive",
            key="color.green",
            value={"default": "#01A47E"},
        ),
        "tok_white": BrandToken(
            id="tok_white",
            brand_id="minibible",
            token_type="color",
            kind="primitive",
            key="color.white",
            value={"default": "#FFFFFF"},
        ),
    }
    rules = {
        "rule_assign": BrandRule(
            id="rule_assign",
            brand_id="minibible",
            rule_class="color_application",
            audience="hcp",
            content_types=["web"],
            constraint_type="binding",
            selector=Selector(section_types=["cta"], element_path="cta.button.fill"),
            applies_when=[{"kind": "theme", "value": "launch"}],
            effect={
                "assignments": [
                    {"element_path": "cta.button.fill", "token_id": "tok_sem"}
                ]
            },
            hardness="hard_constraint",
            precedence=7,
            rule_text="assign semantic fill",
        )
    }
    bindings = collect_bindings(_snapshot(rules=rules, tokens=tokens))
    rule_bindings = [
        binding for binding in bindings if binding.source_kind == "rule_binding"
    ]
    assert [binding.source_id for binding in rule_bindings] == [
        "rule_assign:default",
        "rule_assign:variant:0",
    ]
    assert [binding.value for binding in rule_bindings] == ["#01A47E", "#FFFFFF"]
    default, variant = rule_bindings
    assert default.scope == variant.scope == "campaign"
    assert default.precedence == variant.precedence == 7
    assert default.guard["audience"].values == ["hcp"]
    assert default.guard["surface"].values == ["web"]
    assert default.guard["campaign"].values == ["flip"]
    assert default.guard["theme"].values == ["launch"]
    assert default.guard["tag:lpga"].values == ["present"]
    assert default.guard["section"].values == ["cta"]
    assert variant.guard["background_group"].values == ["dark"]

    context = ContextKey(
        audience="hcp",
        surface="web",
        campaign="flip",
        theme="launch",
        content_tags=["lpga"],
    )
    resolved = resolve_element("cta.button.fill", bindings, context)
    assert resolved.candidates[0].source_id == "rule_assign:variant:0"
    assert resolved.candidates[0].value == "#FFFFFF"
    assert resolved.candidates[0].residual_guard["background_group"].values == ["dark"]


def test_explicit_rule_assignment_value_does_not_expand_semantic_variants() -> None:
    token = BrandToken(
        id="tok_sem",
        brand_id="minibible",
        token_type="color",
        kind="semantic",
        key="cta.button.fill",
        value={
            "default": "#01A47E",
            "variants": [{"when": {"background_group": "dark"}, "value": "#FFFFFF"}],
        },
    )
    rule = BrandRule(
        id="rule_explicit",
        brand_id="minibible",
        rule_class="color_application",
        constraint_type="binding",
        selector=Selector(element_path="cta.button.fill"),
        effect={
            "assignments": [
                {
                    "element_path": "cta.button.fill",
                    "token_id": "tok_sem",
                    "value": "#000000",
                }
            ]
        },
        rule_text="explicit black",
    )
    bindings = collect_bindings(_snapshot(rules={rule.id: rule}, tokens={token.id: token}))
    rule_bindings = [
        binding for binding in bindings if binding.source_kind == "rule_binding"
    ]
    assert [(binding.source_id, binding.value) for binding in rule_bindings] == [
        ("rule_explicit", "#000000")
    ]


def test_semantic_rule_assignment_missing_and_cyclic_refs_raise() -> None:
    rule = BrandRule(
        id="rule_assign",
        brand_id="minibible",
        rule_class="color_application",
        constraint_type="binding",
        selector=Selector(element_path="cta.button.fill"),
        effect={"assignments": [{"token_id": "tok_sem"}]},
        rule_text="assign semantic",
    )
    missing = BrandToken(
        id="tok_sem",
        brand_id="minibible",
        token_type="color",
        kind="semantic",
        key="cta.button.fill",
        value={"default": {"$ref": "tok_missing"}},
    )
    with pytest.raises(TokenResolutionError, match=r"tok_missing"):
        collect_bindings(_snapshot(rules={rule.id: rule}, tokens={missing.id: missing}))

    cyclic = {
        "tok_sem": BrandToken(
            id="tok_sem",
            brand_id="minibible",
            token_type="color",
            kind="semantic",
            key="cta.button.fill",
            value={"default": {"$ref": "tok_a"}},
        ),
        "tok_a": BrandToken(
            id="tok_a",
            brand_id="minibible",
            token_type="color",
            kind="primitive",
            key="color.a",
            value={"default": {"$ref": "tok_sem"}},
        ),
    }
    with pytest.raises(TokenResolutionError, match=r"tok_a -> tok_sem -> tok_a"):
        collect_bindings(_snapshot(rules={rule.id: rule}, tokens=cyclic))


def test_collect_bindings_semantic_default_and_variant() -> None:
    tokens = {
        "tok_sem": BrandToken(
            id="tok_sem",
            brand_id="minibible",
            token_type="color",
            kind="semantic",
            key="cta.button.fill",
            value={
                "default": {"$ref": "tok_prim"},
                "variants": [{"when": {"background_group": "dark"}, "value": "#FFFFFF"}],
            },
            element_paths=["cta.button.fill"],
            scope="campaign:flip",
        ),
        "tok_prim": BrandToken(
            id="tok_prim",
            brand_id="minibible",
            token_type="color",
            kind="primitive",
            key="color.primary",
            value={"default": "#01A47E"},
        ),
    }
    bindings = collect_bindings(_snapshot(tokens=tokens))
    kinds = {(binding.source_kind, binding.value) for binding in bindings}
    assert ("token_default", "#01A47E") in kinds
    assert ("token_variant", "#FFFFFF") in kinds
    default = next(binding for binding in bindings if binding.source_kind == "token_default")
    assert default.guard["campaign"].values == ["flip"]
    assert default.scope == "campaign"


def test_rule_and_token_email_scope_remove_inactive_candidates() -> None:
    snapshot = _snapshot(
        rules={
            "rule_hcp_web": BrandRule(
                id="rule_hcp_web",
                brand_id="minibible",
                rule_class="typography",
                audience="hcp",
                content_types=["web"],
                constraint_type="binding",
                selector=Selector(element_path="headline.case"),
                effect={"value": "title_case"},
                rule_text="hcp web title case",
            )
        },
        tokens={
            "tok_hcp": BrandToken(
                id="tok_hcp",
                brand_id="minibible",
                token_type="color",
                kind="semantic",
                key="hero.color",
                value={"default": "#000000"},
                element_paths=["hero.color"],
                audience="hcp",
            )
        },
    )
    bindings = collect_bindings(snapshot)
    rule_binding = next(binding for binding in bindings if binding.source_id == "rule_hcp_web")
    token_binding = next(binding for binding in bindings if binding.source_id == "tok_hcp")
    assert rule_binding.guard["audience"].values == ["hcp"]
    assert rule_binding.guard["surface"].values == ["web"]
    assert token_binding.guard["audience"].values == ["hcp"]

    dtp_email = ContextKey()
    hcp_web = ContextKey(audience="hcp", surface="web")
    assert resolve_element("headline.case", bindings, dtp_email).candidates == []
    assert resolve_element("hero.color", bindings, dtp_email).candidates == []
    assert resolve_element("headline.case", bindings, hcp_web).resolved == "title_case"
    assert resolve_element("hero.color", bindings, hcp_web).resolved == "#000000"


def test_resolve_ref_cycle_and_missing() -> None:
    tokens = {
        "tok_a": BrandToken(
            id="tok_a",
            brand_id="minibible",
            token_type="color",
            kind="primitive",
            key="a",
            value={"default": {"$ref": "tok_b"}},
        ),
        "tok_b": BrandToken(
            id="tok_b",
            brand_id="minibible",
            token_type="color",
            kind="primitive",
            key="b",
            value={"default": {"$ref": "tok_a"}},
        ),
        "tok_missing": BrandToken(
            id="tok_missing",
            brand_id="minibible",
            token_type="color",
            kind="primitive",
            key="m",
            value={"default": {"$ref": "tok_ghost"}},
        ),
    }
    with pytest.raises(TokenResolutionError, match="cyclic"):
        resolve_ref_value({"$ref": "tok_a"}, tokens)
    with pytest.raises(TokenResolutionError, match="missing"):
        resolve_ref_value({"$ref": "tok_missing"}, tokens)


@pytest.mark.parametrize(
    ("guard", "context", "expected_residual"),
    [
        ({"campaign": "none"}, ContextKey(), {}),
        ({"campaign": "flip"}, ContextKey(), None),
        ({"tag:lpga": "present"}, ContextKey(content_tags=["lpga"]), {}),
        ({"tag:lpga": "present"}, ContextKey(content_tags=[]), None),
        ({"background_group": "light"}, ContextKey(), {"background_group": "light"}),
    ],
)
def test_partial_eval_table(
    guard: dict[str, str],
    context: ContextKey,
    expected_residual: dict[str, str] | None,
) -> None:
    result = partial_eval_guard(normalize_guard(guard), context, {"lpga"})
    if expected_residual is None:
        assert result is None
    else:
        assert result is not None
        for axis, value in expected_residual.items():
            assert result[axis].values == [value]


def test_resolved_null_when_top_residual_guard() -> None:
    only_default = resolve_element(
        "cta.button.fill",
        [
            _binding(
                source_id="tok_sem",
                source_kind="token_default",
                hardness="strong_default",
                guard={},
                value="#01A47E",
            )
        ],
        ContextKey(),
    )
    assert only_default.resolved == "#01A47E"
    assert only_default.candidates[0].residual_guard == {}

    residual_top = resolve_element(
        "cta.button.fill",
        [
            _binding(
                source_id="tok_sem",
                source_kind="token_variant",
                hardness="strong_default",
                guard={"background_group": "dark"},
                value="#FFFFFF",
            )
        ],
        ContextKey(),
    )
    assert residual_top.resolved is None


def test_resolved_null_on_equal_specificity_value_conflict() -> None:
    bindings = [
        _binding(source_id="rule_a", value="#01A47E", hardness="strong_default"),
        _binding(source_id="rule_b", value="#FF5733", hardness="strong_default"),
    ]
    resolved = resolve_element("cta.button.fill", bindings, ContextKey())
    assert resolved.resolved is None
    assert resolved.conflict is True
    assert resolved.tied_source_ids == ["rule_a", "rule_b"]


def test_equal_specificity_disjoint_residual_guards_are_not_conflict() -> None:
    bindings = [
        _binding(source_id="rule_mobile", value="red", guard={"breakpoint": "mobile"}),
        _binding(source_id="rule_desktop", value="blue", guard={"breakpoint": "desktop"}),
    ]
    resolved = resolve_element("cta.button.fill", bindings, ContextKey())
    assert resolved.resolved is None
    assert resolved.conflict is False
    assert resolved.tied_source_ids == []


def test_equal_specificity_overlapping_residual_guards_are_conflict() -> None:
    bindings = [
        _binding(
            source_id="rule_all_breakpoints",
            value="red",
            guard={"breakpoint": ["desktop", "mobile"]},
        ),
        _binding(source_id="rule_mobile", value="blue", guard={"breakpoint": "mobile"}),
    ]
    resolved = resolve_element("cta.button.fill", bindings, ContextKey())
    assert resolved.conflict is True
    assert resolved.tied_source_ids == ["rule_all_breakpoints", "rule_mobile"]


def test_resolve_trace_includes_full_specificity_tuple() -> None:
    binding = _binding(source_id="rule_a", hardness="hard_constraint", precedence=2)
    resolved = resolve_element("cta.button.fill", [binding], ContextKey())
    assert resolved.candidates[0].spec == list(specificity(binding))
