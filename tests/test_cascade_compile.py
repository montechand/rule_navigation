"""WP-14 cascade compile tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from indexing_v2.cascade.compile import (
    STAGE_VERSION,
    CascadeSheet,
    analyze_shadowed_bindings,
    compile_cascade,
    get_sheet,
)
from indexing_v2.cascade.guards import normalize_guard
from indexing_v2.cascade.resolve import collect_bindings
from indexing_v2.contracts import Binding, KBSnapshot, stable_hash
from shared.schemas import BrandRule, BrandToken, Selector


def _snapshot() -> KBSnapshot:
    return KBSnapshot(
        brand="minibible",
        rules={
            "rule_headline": BrandRule(
                id="rule_headline",
                brand_id="minibible",
                rule_class="typography",
                constraint_type="binding",
                selector=Selector(element_path="headline"),
                effect={"value": "sentence_case"},
                hardness="hard_constraint",
                rule_text="sentence case",
            ),
            "rule_cta_max": BrandRule(
                id="rule_cta_max",
                brand_id="minibible",
                rule_class="layout",
                constraint_type="cardinality",
                selector=Selector(element_path="cta.button.primary"),
                effect={"max": 1, "per": "email", "target": "cta.button.primary"},
                hardness="hard_constraint",
                evaluation_scope="email",
                rule_text="max one",
            ),
        },
        tokens={
            "tok_sem": BrandToken(
                id="tok_sem",
                brand_id="minibible",
                token_type="color",
                kind="semantic",
                key="cta.button.fill",
                value={"default": "#01A47E"},
                element_paths=["cta.button.fill"],
            )
        },
        assets={},
        subtypes={},
        templates={},
        predicate_domains={
            "campaign": ["none"],
            "theme": ["none"],
            "background_group": ["dark", "light"],
            "content_tag": [],
        },
    )


def test_stage_version() -> None:
    assert STAGE_VERSION == "1.0.0"


def test_campaign_free_contexts_dedupe_to_one_sheet(tmp_path: Path) -> None:
    snapshot = _snapshot()
    kb_hash = "fixture_kb_hash"
    index = compile_cascade(snapshot, tmp_path, kb_hash)
    hashes = {entry.sheet_hash for entry in index.contexts.values()}
    assert len(hashes) == 1
    assert len(list((tmp_path / "sheets").glob("*.json"))) == 1


def test_sheet_sample_shape_matches_spec(tmp_path: Path) -> None:
    snapshot = _snapshot()
    kb_hash = "fixture_kb_hash"
    compile_cascade(snapshot, tmp_path, kb_hash)
    sheet_path = next((tmp_path / "sheets").glob("*.json"))
    payload = json.loads(sheet_path.read_text(encoding="utf-8"))
    sheet = CascadeSheet.model_validate(payload)
    assert sheet.schema_version == "2.0"
    assert sheet.kb_hash == kb_hash
    assert sheet.email.structure.cardinality
    assert sheet.sections["*"].elements["cta.button.fill"].candidates


def test_hash_excludes_only_context(tmp_path: Path) -> None:
    snapshot = _snapshot()
    compile_cascade(snapshot, tmp_path, "hash_a")
    payload = json.loads(next((tmp_path / "sheets").glob("*.json")).read_text(encoding="utf-8"))
    without_context = {key: value for key, value in payload.items() if key != "context"}
    assert stable_hash(without_context) == next((tmp_path / "sheets").glob("*.json")).stem
    assert "kb_hash" in without_context


def test_get_sheet_defaults_and_unknown_axis(tmp_path: Path) -> None:
    snapshot = _snapshot()
    kb_root = tmp_path / "minibible"
    cascade_root = kb_root / "cascade"
    compile_cascade(snapshot, cascade_root, "kb_hash")
    sheet = get_sheet(cascade_root)
    assert sheet.context.audience == "dtp_patient"
    assert sheet.context.surface == "email"
    assert sheet.context.campaign == "none"
    assert sheet.context.theme == "none"
    assert sheet.context.tags == []
    assert get_sheet(kb_root).kb_hash == "kb_hash"
    with pytest.raises(KeyError, match="unknown axis"):
        get_sheet(cascade_root, audience="dtp_patient", surface="email", bogus="x")
    with pytest.raises(ValueError, match="unknown value.*campaign"):
        get_sheet(cascade_root, campaign="missing_campaign")
    with pytest.raises(ValueError, match="duplicate aliases"):
        get_sheet(cascade_root, tags=[], content_tags=[])


def test_stale_sheet_cleanup(tmp_path: Path) -> None:
    snapshot = _snapshot()
    compile_cascade(snapshot, tmp_path, "kb_hash")
    stale = tmp_path / "sheets" / "deadbeefdeadbeef.json"
    stale.write_text("{}", encoding="utf-8")
    compile_cascade(snapshot, tmp_path, "kb_hash")
    assert not stale.exists()


def test_compile_determinism_twice(tmp_path: Path) -> None:
    snapshot = _snapshot()
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    compile_cascade(snapshot, out_a, "kb_hash")
    compile_cascade(snapshot, out_b, "kb_hash")
    index_a = (out_a / "contexts.json").read_text(encoding="utf-8")
    index_b = (out_b / "contexts.json").read_text(encoding="utf-8")
    assert index_a == index_b
    sheet_a = next((out_a / "sheets").glob("*.json")).read_text(encoding="utf-8")
    sheet_b = next((out_b / "sheets").glob("*.json")).read_text(encoding="utf-8")
    assert sheet_a == sheet_b


def test_shadowed_binding_never_wins() -> None:
    snapshot = KBSnapshot(
        brand="minibible",
        rules={
            "rule_soft": BrandRule(
                id="rule_soft",
                brand_id="minibible",
                rule_class="color_application",
                constraint_type="binding",
                selector=Selector(element_path="cta.button.fill"),
                effect={"value": "#EEEEEE"},
                hardness="soft_guidance",
                rule_text="soft",
            ),
            "rule_hard": BrandRule(
                id="rule_hard",
                brand_id="minibible",
                rule_class="color_application",
                constraint_type="binding",
                selector=Selector(element_path="cta.button.fill"),
                effect={"value": "#01A47E"},
                hardness="hard_constraint",
                rule_text="hard",
            ),
        },
        tokens={},
        assets={},
        subtypes={},
        templates={},
        predicate_domains={
            "campaign": ["none"],
            "theme": ["none"],
            "background_group": ["dark", "light"],
            "content_tag": [],
        },
    )
    bindings = collect_bindings(snapshot)
    soft = next(binding for binding in bindings if binding.source_id == "rule_soft")
    shadowed = analyze_shadowed_bindings(snapshot, bindings)
    entry = next((item for item in shadowed if item.source_id == soft.source_id), None)
    assert entry is not None
    assert entry.reason == "shadowed"
    assert "rule_hard" in entry.shadowed_by


def test_email_scoping_buckets_and_governance_are_complete(tmp_path: Path) -> None:
    snapshot = KBSnapshot(
        brand="minibible",
        rules={
            "rule_hcp_binding": BrandRule(
                id="rule_hcp_binding",
                brand_id="minibible",
                rule_class="typography",
                audience="hcp",
                content_types=["web"],
                constraint_type="binding",
                selector=Selector(element_path="headline.case"),
                effect={"value": "title_case"},
                rule_text="hcp web",
            ),
            "rule_hcp_forbidden": BrandRule(
                id="rule_hcp_forbidden",
                brand_id="minibible",
                rule_class="copy_editorial",
                audience="hcp",
                content_types=["web"],
                evaluation_scope="email",
                constraint_type="verbatim_content",
                hardness="hard_constraint",
                governance={"gov_type": "regulatory", "verdict": "forbidden"},
                rule_text="forbidden claim",
            ),
            "rule_hcp_default": BrandRule(
                id="rule_hcp_default",
                brand_id="minibible",
                rule_class="layout",
                audience="hcp",
                content_types=["web"],
                evaluation_scope="email",
                hardness="strong_default",
                rule_text="default",
            ),
            "rule_hcp_guidance": BrandRule(
                id="rule_hcp_guidance",
                brand_id="minibible",
                rule_class="layout",
                audience="hcp",
                content_types=["web"],
                evaluation_scope="email",
                hardness="soft_guidance",
                rule_text="guidance",
            ),
            "rule_dtp_cta": BrandRule(
                id="rule_dtp_cta",
                brand_id="minibible",
                rule_class="layout",
                audience="dtp_patient",
                content_types=["email"],
                selector=Selector(section_types=["cta"]),
                hardness="strong_default",
                rule_text="dtp cta",
            ),
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
        assets={},
        subtypes={},
        templates={},
        predicate_domains={},
    )
    compile_cascade(snapshot, tmp_path, "kb_hash")
    hcp_web = get_sheet(tmp_path, audience="hcp", surface="web")
    assert hcp_web.sections["*"].elements["headline.case"].resolved == "title_case"
    assert hcp_web.sections["*"].elements["hero.color"].resolved == "#000000"
    assert hcp_web.email.hard_constraints == ["rule_hcp_forbidden"]
    assert hcp_web.email.strong_defaults == ["rule_hcp_default"]
    assert hcp_web.email.soft_guidance == ["rule_hcp_guidance"]
    assert hcp_web.email.governance[0].rule_id == "rule_hcp_forbidden"
    assert hcp_web.email.governance[0].verdict == "forbidden"
    assert hcp_web.email.governance[0].preferred_form is None

    dtp_email = get_sheet(tmp_path)
    assert "headline.case" not in dtp_email.sections["*"].elements
    assert "hero.color" not in dtp_email.sections["*"].elements
    assert dtp_email.email.hard_constraints == []
    assert dtp_email.email.governance == []
    assert dtp_email.sections["cta"].rules.default == ["rule_dtp_cta"]


def test_named_section_strips_selector_guard_and_resolves(tmp_path: Path) -> None:
    snapshot = KBSnapshot(
        brand="minibible",
        rules={
            "rule_cta_fill": BrandRule(
                id="rule_cta_fill",
                brand_id="minibible",
                rule_class="color_application",
                constraint_type="binding",
                selector=Selector(section_types=["cta"], element_path="cta.button.fill"),
                effect={"value": "#01A47E"},
                rule_text="cta fill",
            )
        },
        tokens={},
        assets={},
        subtypes={},
        templates={},
        predicate_domains={},
    )
    compile_cascade(snapshot, tmp_path, "kb_hash")
    sheet = get_sheet(tmp_path)
    prop = sheet.sections["cta"].elements["cta.button.fill"]
    assert prop.resolved == "#01A47E"
    assert prop.candidates[0].residual_guard == {}
    assert "cta.button.fill" not in sheet.sections["*"].elements


def test_compiled_semantic_rule_assignment_keeps_variant_trace(tmp_path: Path) -> None:
    snapshot = KBSnapshot(
        brand="minibible",
        rules={
            "rule_cta_semantic": BrandRule(
                id="rule_cta_semantic",
                brand_id="minibible",
                rule_class="color_application",
                constraint_type="binding",
                selector=Selector(section_types=["cta"], element_path="cta.button.fill"),
                effect={
                    "assignments": [
                        {
                            "element_path": "cta.button.fill",
                            "token_id": "tok_cta_fill",
                        }
                    ]
                },
                hardness="hard_constraint",
                rule_text="assign semantic CTA fill",
            )
        },
        tokens={
            "tok_cta_fill": BrandToken(
                id="tok_cta_fill",
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
        },
        assets={},
        subtypes={},
        templates={},
        predicate_domains={"background_group": ["dark", "light"]},
    )
    compile_cascade(snapshot, tmp_path, "kb_hash")
    prop = get_sheet(tmp_path).sections["cta"].elements["cta.button.fill"]
    assert prop.candidates[0].source_id == "rule_cta_semantic:variant:0"
    assert prop.candidates[0].value == "#FFFFFF"
    assert prop.candidates[0].residual_guard["background_group"].values == ["dark"]
    assert prop.candidates[1].source_id == "rule_cta_semantic:default"
    assert prop.candidates[1].value == "#01A47E"


def test_section_conflicts_require_overlapping_residual_guards(tmp_path: Path) -> None:
    def snapshot(second_guard: object) -> KBSnapshot:
        return KBSnapshot(
            brand="minibible",
            rules={
                "rule_mobile": BrandRule(
                    id="rule_mobile",
                    brand_id="minibible",
                    rule_class="color_application",
                    constraint_type="binding",
                    selector=Selector(section_types=["cta"], element_path="cta.button.fill"),
                    applies_when=[{"kind": "breakpoint", "value": "mobile"}],
                    effect={"value": "red"},
                    rule_text="mobile red",
                ),
                "rule_other": BrandRule(
                    id="rule_other",
                    brand_id="minibible",
                    rule_class="color_application",
                    constraint_type="binding",
                    selector=Selector(section_types=["cta"], element_path="cta.button.fill"),
                    applies_when=[{"kind": "breakpoint", "value": second_guard}],
                    effect={"value": "blue"},
                    rule_text="other blue",
                ),
            },
            tokens={},
            assets={},
            subtypes={},
            templates={},
            predicate_domains={},
        )

    disjoint_root = tmp_path / "disjoint"
    compile_cascade(snapshot("desktop"), disjoint_root, "kb_hash")
    disjoint = get_sheet(disjoint_root).sections["cta"].elements["cta.button.fill"]
    assert disjoint.conflict is False
    assert all("section" not in candidate.residual_guard for candidate in disjoint.candidates)

    overlap_root = tmp_path / "overlap"
    compile_cascade(snapshot(["desktop", "mobile"]), overlap_root, "kb_hash")
    overlap = get_sheet(overlap_root).sections["cta"].elements["cta.button.fill"]
    assert overlap.conflict is True
    assert overlap.tied_source_ids == ["rule_mobile", "rule_other"]


def test_shadow_analysis_evaluates_disjoint_and_multivalue_cells() -> None:
    snapshot = KBSnapshot(
        brand="minibible",
        rules={},
        tokens={},
        assets={},
        subtypes={},
        templates={},
        predicate_domains={},
    )
    disjoint = [
        Binding(
            element_path="hero.color",
            value="desktop",
            guard=normalize_guard({"breakpoint": "desktop"}),
            source_kind="rule_binding",
            source_id="rule_desktop_hard",
            hardness="hard_constraint",
            scope="brand",
            selector_rank=3,
            precedence=0,
        ),
        Binding(
            element_path="hero.color",
            value="mobile",
            guard=normalize_guard({"breakpoint": "mobile"}),
            source_kind="rule_binding",
            source_id="rule_mobile_soft",
            hardness="soft_guidance",
            scope="brand",
            selector_rank=3,
            precedence=0,
        ),
    ]
    assert analyze_shadowed_bindings(snapshot, disjoint) == []

    multivalue = [
        Binding(
            element_path="hero.layout",
            value="dense",
            guard=normalize_guard({"device_density": "dense"}),
            source_kind="rule_binding",
            source_id="rule_dense_hard",
            hardness="hard_constraint",
            scope="brand",
            selector_rank=3,
            precedence=0,
        ),
        Binding(
            element_path="hero.layout",
            value="adaptive",
            guard=normalize_guard({"device_density": ["dense", "sparse"]}),
            source_kind="rule_binding",
            source_id="rule_adaptive_soft",
            hardness="soft_guidance",
            scope="brand",
            selector_rank=3,
            precedence=0,
        ),
    ]
    assert analyze_shadowed_bindings(snapshot, multivalue) == []
