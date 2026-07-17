"""S6b linker matcher, patching, and deterministic artifact tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from indexing.build_kb import (
    Warnings,
    build_graph,
    validate_catalog,
    validate_rule,
)
from indexing_v2.contracts import LinkAssignment, LinkSignals
from indexing_v2.extraction.ledger import CandidatesBundle
from indexing_v2.linker import (
    _append_assignment,
    match_pair,
    run_linker_stage,
)
from shared.llm import Usage

FIXTURE = Path(__file__).parent / "fixtures" / "linker" / "bundle.json"


def _bundle() -> CandidatesBundle:
    return CandidatesBundle.model_validate(
        json.loads(FIXTURE.read_text(encoding="utf-8"))
    )


def _by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in rows}


def test_matcher_golden_pairs_and_demotions() -> None:
    bundle = _bundle()
    tokens = _by_id([*bundle.tokens_primitive, *bundle.tokens_semantic])
    rules = _by_id(bundle.rules_by_group["grp_fixture"])
    golden = {
        "tok_lisraya_padding_section_vertical": "rule_lisraya_modular_section_block_structure",
        "tok_lisraya_size_email_body_width": "rule_lisraya_modular_section_block_structure",
        "tok_lisraya_opacity_dropshadow_navy_18": "rule_lisraya_icon_callout_badge_dropshadow_mandatory",
        "tok_lisraya_text_style_patient_quote": "rule_lisraya_patient_quote_attribution_style",
        "tok_lisraya_icon_style_rounded_bars": "rule_lisraya_chart_rounded_bar_shapes",
    }
    for token_id, rule_id in golden.items():
        assert match_pair(tokens[token_id], rules[rule_id]).tier == "AUTO"

    assert (
        match_pair(
            tokens["tok_lisraya_cta_button_fill"],
            rules["rule_lisraya_cta_one_primary_per_section"],
        ).tier
        == "ADJUDICATE"
    )
    assert (
        match_pair(
            tokens["tok_lisraya_size_icon_badge_inner_icon"],
            rules["rule_lisraya_forms_labels_and_tap_targets"],
        ).tier
        == "ADJUDICATE"
    )


@pytest.mark.asyncio
async def test_run_linker_auto_needs_rule_idempotent_and_deterministic(
    tmp_path: Path,
) -> None:
    first, patched = await run_linker_stage(
        bundle=_bundle(),
        provenance=None,
        units=[],
        client=None,
        usage=Usage(),
        work_dir=tmp_path / "first",
        cache_root=tmp_path / "cache",
    )
    pairs = {
        (assignment.token_id, patch.rule_id)
        for patch in first.patches
        for assignment in patch.assignments
    }
    assert {
        (
            "tok_lisraya_padding_section_vertical",
            "rule_lisraya_modular_section_block_structure",
        ),
        (
            "tok_lisraya_size_email_body_width",
            "rule_lisraya_modular_section_block_structure",
        ),
        (
            "tok_lisraya_opacity_dropshadow_navy_18",
            "rule_lisraya_icon_callout_badge_dropshadow_mandatory",
        ),
        (
            "tok_lisraya_text_style_patient_quote",
            "rule_lisraya_patient_quote_attribution_style",
        ),
        (
            "tok_lisraya_icon_style_rounded_bars",
            "rule_lisraya_chart_rounded_bar_shapes",
        ),
    } <= pairs
    needs = {row["token_id"] for row in first.needs_rule_tokens}
    assert {
        "tok_lisraya_weight_agenda_bold",
        "tok_lisraya_size_body_secondary",
    } <= needs

    second, _ = await run_linker_stage(
        bundle=patched,
        provenance=None,
        units=[],
        client=None,
        usage=Usage(),
        work_dir=tmp_path / "second",
        cache_root=tmp_path / "cache",
    )
    assert second.patches == []

    again, _ = await run_linker_stage(
        bundle=_bundle(),
        provenance=None,
        units=[],
        client=None,
        usage=Usage(),
        work_dir=tmp_path / "again",
        cache_root=tmp_path / "cache",
    )
    assert again == first
    assert (
        tmp_path / "first" / "linker" / "linker_result.json"
    ).read_bytes() == (
        tmp_path / "again" / "linker" / "linker_result.json"
    ).read_bytes()


class _BindAllClient:
    """Fake LLM client that binds every adjudicated pair."""

    async def complete_json(self, model: str, system: str, user: str, **kwargs: Any) -> Any:
        import re

        token_ids = sorted(set(re.findall(r'"token_id":\s*"([^"]+)"', user)))
        return {
            "decisions": [
                {
                    "token_id": token_id,
                    "decision": "bind",
                    "element_path": "fixture.path",
                    "reason": "test",
                }
                for token_id in token_ids
            ]
        }

    async def chat(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("linker adjudication must use complete_json")


@pytest.mark.asyncio
async def test_default_budget_adjudicates_instead_of_exhausting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from indexing_v2 import settings

    monkeypatch.delenv("RULE_NAV_LINKER_MAX_ADJUDICATIONS", raising=False)
    settings.reload_settings()
    assert settings.LINKER_MAX_ADJUDICATIONS > 0
    result, _ = await run_linker_stage(
        bundle=_bundle(),
        provenance=None,
        units=[],
        client=_BindAllClient(),
        usage=Usage(),
        work_dir=tmp_path,
        cache_root=tmp_path / "cache",
    )
    assert result.metrics["adjudicated_binds"] > 0
    assert not [
        row
        for row in result.adjudication_open
        if row["decision"] == "budget_exhausted"
    ]


@pytest.mark.asyncio
async def test_zero_budget_warns_instead_of_silently_skipping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from indexing_v2 import settings

    monkeypatch.setenv("RULE_NAV_LINKER_MAX_ADJUDICATIONS", "0")
    settings.reload_settings()
    printed: list[str] = []

    class _Console:
        def print(self, *args: Any, **kwargs: Any) -> None:
            printed.append(" ".join(str(a) for a in args))

    try:
        result, _ = await run_linker_stage(
            bundle=_bundle(),
            provenance=None,
            units=[],
            client=_BindAllClient(),
            usage=Usage(),
            work_dir=tmp_path,
            cache_root=tmp_path / "cache",
            console=_Console(),
        )
    finally:
        monkeypatch.delenv("RULE_NAV_LINKER_MAX_ADJUDICATIONS", raising=False)
        settings.reload_settings()
    assert result.metrics["adjudicated_binds"] == 0
    assert any("LINKER_MAX_ADJUDICATIONS=0" in line for line in printed)
    assert all(
        row["decision"] == "budget_exhausted" for row in result.adjudication_open
    )


def test_preflight_flags_degenerate_env_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from indexing_v2 import settings
    from indexing_v2.preflight import check_degenerate_env

    monkeypatch.setenv("RULE_NAV_LINKER_MAX_ADJUDICATIONS", "0")
    settings.reload_settings()
    try:
        warnings = check_degenerate_env(echo=lambda _msg: None)
    finally:
        monkeypatch.delenv("RULE_NAV_LINKER_MAX_ADJUDICATIONS", raising=False)
        settings.reload_settings()
    assert any("LINKER_MAX_ADJUDICATIONS" in warning for warning in warnings)
    settings.reload_settings()
    assert check_degenerate_env(echo=lambda _msg: None) == []


def test_gap_minted_rule_id_never_double_prefixes() -> None:
    # F2 regression: gap rules arriving with a pre-set id and empty rule_text
    # used to yield rule_{brand}_rule_{brand}_* after Pass C + v1 validation.
    from indexing_v2.build_kb import _prepare_rule_for_pass_c

    raw = {
        "id": "rule_x_foo",
        "rule_text": "",
        "constraint_type": "binding",
        "effect": None,
    }
    prepared = _prepare_rule_for_pass_c(raw, "x")
    assert prepared["rule_text"] == "foo"
    assert prepared["slug"] == "foo"
    warns = Warnings()
    rule = validate_rule(prepared, "x", "grp_x", "doc[0]", set(), set(), warns, [])
    assert rule is not None
    assert rule.id == "rule_x_foo"


def test_validate_rule_strips_leaked_brand_prefix_from_slug() -> None:
    warns = Warnings()
    rule = validate_rule(
        {"slug": "rule_x_bar", "rule_text": "Bar must hold."},
        "x",
        "grp_x",
        "doc[0]",
        set(),
        set(),
        warns,
        [],
    )
    assert rule is not None
    assert rule.id == "rule_x_bar"


@pytest.mark.parametrize("effect", [None, [], {"assignments": []}])
def test_patch_application_normalizes_effect_and_deduplicates(effect: Any) -> None:
    rule = {"id": "rule_x", "effect": effect, "token_ids": []}
    assignment = LinkAssignment(
        token_id="tok_x",
        element_path="body.size",
        signals=LinkSignals(),
    )
    assert _append_assignment(rule, assignment, "linker-v1:auto", "size.body")
    assert rule["effect"]["assignments"] == [
        {
            "element_path": "body.size",
            "token_id": "tok_x",
            "linked_by": "linker-v1:auto",
        }
    ]
    assert not _append_assignment(
        rule,
        assignment,
        "linker-v1:auto",
        "size.body",
    )


@pytest.mark.asyncio
async def test_no_linker_is_valid_pass_through(tmp_path: Path) -> None:
    bundle = _bundle()
    before = bundle.model_dump(mode="json")
    result, after = await run_linker_stage(
        bundle=bundle,
        provenance=None,
        units=[],
        client=None,
        usage=Usage(),
        work_dir=tmp_path,
        cache_root=tmp_path / "cache",
        no_linker=True,
    )
    assert result.patches == []
    assert after.model_dump(mode="json") == before
    artifact = json.loads(
        (tmp_path / "linker" / "linker_result.json").read_text(encoding="utf-8")
    )
    assert artifact["schema_version"] == "2.0"


@pytest.mark.asyncio
async def test_link_patch_materializes_token_ids_and_graph_edges(
    tmp_path: Path,
) -> None:
    result, patched = await run_linker_stage(
        bundle=_bundle(),
        provenance=None,
        units=[],
        client=None,
        usage=Usage(),
        work_dir=tmp_path,
        cache_root=tmp_path / "cache",
    )
    assert result.patches
    raw = next(
        rule
        for rule in patched.rules_by_group["grp_fixture"]
        if rule["id"] == "rule_lisraya_modular_section_block_structure"
    )
    raw["slug"] = "modular_section_block_structure"
    raw["intent"] = "Preserve modular section dimensions."
    warnings = Warnings()
    token_ids = {
        "tok_lisraya_padding_section_vertical",
        "tok_lisraya_size_email_body_width",
    }
    catalog = validate_catalog(
        {
            "tokens": [
                token
                for token in patched.tokens_primitive
                if token["id"] in token_ids
            ],
            "assets": [],
            "subtypes": [],
            "templates": [],
            "template_groups": [],
            "asset_groups": [],
        },
        "lisraya",
        warnings,
    )
    rule = validate_rule(
        raw,
        "lisraya",
        "grp_fixture",
        "fixture[0]",
        set(),
        set(catalog["tokens"]),
        warnings,
        [],
    )
    assert rule is not None
    assert token_ids <= set(rule.token_ids)
    graph = build_graph(
        {rule.id: rule},
        catalog,
        [],
        [],
    )
    edges = {
        (edge["src"], edge["dst"], edge["type"])
        for edge in graph["edges"]
    }
    assert {
        (rule.id, token_id, "references_token")
        for token_id in token_ids
    } <= edges
