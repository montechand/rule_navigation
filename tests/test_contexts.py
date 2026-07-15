"""WP-14 context enumeration tests."""

from __future__ import annotations

from indexing_v2.cascade.contexts import STAGE_VERSION, enumerate_contexts, observed_content_tag_combos
from indexing_v2.contracts import KBSnapshot
from shared.schemas import BrandRule, BrandToken, DesignAsset, DesignTemplate


def _snapshot(
    *,
    rules: dict[str, BrandRule] | None = None,
    tokens: dict[str, BrandToken] | None = None,
    templates: dict[str, DesignTemplate] | None = None,
    assets: dict[str, DesignAsset] | None = None,
    domains: dict[str, list[str]] | None = None,
) -> KBSnapshot:
    return KBSnapshot(
        brand="minibible",
        rules=rules or {},
        tokens=tokens or {},
        assets=assets or {},
        subtypes={},
        templates=templates or {},
        predicate_domains=(
            domains
            if domains is not None
            else {
                "campaign": ["none"],
                "theme": ["none"],
                "content_tag": ["lpga", "secondary_cta"],
            }
        ),
    )


def test_stage_version() -> None:
    assert STAGE_VERSION == "1.0.0"


def test_observed_tag_combos_no_powerset() -> None:
    snapshot = _snapshot(
        templates={
            "tpl_a": DesignTemplate(
                id="tpl_a",
                brand_id="minibible",
                name="A",
                usage_conditions={"requires_content_tags": ["lpga", "secondary_cta"]},
            )
        }
    )
    combos = observed_content_tag_combos(snapshot)
    assert [] in combos
    assert ["lpga"] in combos
    assert ["secondary_cta"] in combos
    assert ["lpga", "secondary_cta"] in combos
    assert ["lpga", "secondary_cta", "extra"] not in combos


def test_enumerate_includes_none_campaign_and_theme() -> None:
    snapshot = _snapshot(domains={"campaign": ["none", "flip"], "theme": ["none", "dark"]})
    contexts = enumerate_contexts(snapshot)
    keys = {ctx.canonical() for ctx in contexts}
    assert "audience=dtp_patient;campaign=flip;surface=email;tags=none;theme=dark" in keys
    assert {ctx.audience for ctx in contexts} == {"dtp_patient"}
    assert {ctx.surface for ctx in contexts} == {"email"}


def test_content_tags_sorted_in_context() -> None:
    snapshot = _snapshot(
        templates={
            "tpl_a": DesignTemplate(
                id="tpl_a",
                brand_id="minibible",
                name="A",
                usage_conditions={"requires_content_tags": ["secondary_cta", "lpga"]},
            )
        }
    )
    contexts = enumerate_contexts(snapshot)
    combo_ctx = next(ctx for ctx in contexts if ctx.content_tags == ["lpga", "secondary_cta"])
    assert combo_ctx.canonical().endswith("tags=lpga+secondary_cta;theme=none")


def test_context_enumeration_is_deterministic() -> None:
    snapshot = _snapshot()
    first = [ctx.canonical() for ctx in enumerate_contexts(snapshot)]
    second = [ctx.canonical() for ctx in enumerate_contexts(snapshot)]
    assert first == second


def test_domains_are_observed_from_snapshot_with_empty_predicate_domains() -> None:
    snapshot = _snapshot(
        rules={
            "rule_hcp_web": BrandRule(
                id="rule_hcp_web",
                brand_id="minibible",
                rule_class="layout",
                audience="hcp",
                content_types=["web"],
                applies_when=[
                    {"kind": "content_tag", "value": "rule_tag"},
                    {"kind": "campaign", "value": "launch"},
                ],
                rule_text="hcp web",
            )
        },
        tokens={
            "tok_gate": BrandToken(
                id="tok_gate",
                brand_id="minibible",
                token_type="color",
                kind="semantic",
                key="hero.color",
                value={"default": "#000000"},
                audience="caregiver",
                scope="campaign:partner",
                gated={"is_gated": True, "gate": {"kind": "content_tag", "value": "token_tag"}},
            )
        },
        templates={
            "tpl_tags": DesignTemplate(
                id="tpl_tags",
                brand_id="minibible",
                name="Tags",
                audience="hcp",
                usage_conditions={
                    "requires_content_tags": ["usage_b", "usage_a"],
                    "forbidden_content_tags": ["forbid_b", "forbid_a"],
                },
            )
        },
        assets={
            "ast_single": DesignAsset(
                id="ast_single",
                brand_id="minibible",
                asset_type="photo",
                usage_conditions={
                    "requires_content_tags": ["asset_tag"],
                    "forbidden_content_tags": ["asset_forbidden"],
                },
            )
        },
        domains={},
    )
    contexts = enumerate_contexts(snapshot)
    assert {ctx.audience for ctx in contexts} == {"caregiver", "dtp_patient", "hcp"}
    assert {ctx.surface for ctx in contexts} == {"email", "web"}
    assert {ctx.campaign for ctx in contexts} == {"launch", "none", "partner"}
    combos = observed_content_tag_combos(snapshot)
    assert combos == [
        [],
        ["asset_forbidden"],
        ["asset_tag"],
        ["forbid_a"],
        ["forbid_b"],
        ["rule_tag"],
        ["token_tag"],
        ["usage_a"],
        ["usage_b"],
        ["usage_a", "usage_b"],
    ]
    assert ["forbid_a", "forbid_b"] not in combos
