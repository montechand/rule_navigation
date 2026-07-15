"""Tests for §5.6 adversarial critic (S5)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from indexing_v2 import settings
from indexing_v2.contracts import Finding, Patch, read_jsonl, stable_hash
from indexing_v2.extraction.critic import (
    STAGE_VERSION,
    CandidateAdapterError,
    CandidateSet,
    CriticResponseError,
    PatchApplicationError,
    apply_patch_to_candidates,
    mechanical_screen_finding,
    merge_evidence,
    parse_finding,
    parse_findings_response,
    render_catalog_summary,
    run_critic,
    triage_findings,
    write_critic_artifacts,
)
from indexing_v2.extraction.provenance import verify_entities
from indexing_v2.extraction.runner import clear_brand_cache
from shared.llm import Usage
from tests.fakes import FIXTURE_ROOT, FakeLLM, MINIBIBLE_BRAND

FIXTURE_LLM = FIXTURE_ROOT / "llm"
BRAND_GROUP_ID = "grp_minibible_brand_foundation_00"
LAYOUT_GROUP_ID = "grp_minibible_layout_constraints_00"


class CriticFakeLLM(FakeLLM):
    """Reuse the single rules fixture for every per-blob critic_rules call."""

    def _resolve_path(self, prompt_name: str, cache_key: str | None, seq: int) -> Path:
        if prompt_name == "critic_rules":
            rules_fixture = self.fixture_root / "critic_rules" / "001.json"
            if rules_fixture.is_file():
                return rules_fixture
        return super()._resolve_path(prompt_name, cache_key, seq)


@pytest.fixture
def units():
    from indexing_v2.contracts import SourceUnit

    return read_jsonl(FIXTURE_ROOT / "expected" / "units.jsonl", SourceUnit)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture_candidates(*, include_subhead: bool = False) -> CandidateSet:
    primitive = _load_json(FIXTURE_LLM / "tokens_primitive" / "r0_001.json")["tokens"]
    if not include_subhead:
        primitive = [
            token
            for token in primitive
            if token["id"] != "tok_minibible_type_subhead_size"
        ]
    semantic = _load_json(FIXTURE_LLM / "tokens_semantic" / "r0_001.json")["tokens"]
    catalog = _load_json(FIXTURE_LLM / "catalog_rest" / "001.json")
    rule_groups = {
        BRAND_GROUP_ID: _load_json(
            FIXTURE_LLM / "rules_cluster" / "brand_foundation_001.json"
        )["rules"],
        LAYOUT_GROUP_ID: _load_json(
            FIXTURE_LLM / "rules_cluster" / "layout_constraints_001.json"
        )["rules"],
    }
    return CandidateSet(
        token_primitive=primitive,
        token_semantic=semantic,
        asset=catalog.get("assets", []),
        subtype=catalog.get("subtypes", []),
        template=catalog.get("templates", []),
        rules_by_doc_ref=rule_groups,
        rule_group_doc_refs={
            BRAND_GROUP_ID: "brand_foundation[0]",
            LAYOUT_GROUP_ID: "layout_constraints[0]",
        },
    )


def _finding(
    *,
    finding_id: str,
    finding_type: str,
    severity: str = "minor",
    patch: Patch | None = None,
    target_entity_id: str | None = None,
) -> Finding:
    return Finding(
        finding_id=finding_id,
        round=1,
        finding_type=finding_type,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        target_entity_id=target_entity_id,
        description="test",
        proposed_patch=patch,
    )


def _subhead_token() -> dict[str, Any]:
    return copy.deepcopy(
        _load_json(FIXTURE_LLM / "critic_catalog" / "001.json")["findings"][0][
            "proposed_patch"
        ]["payload"]
    )


def test_stage_version_present() -> None:
    assert STAGE_VERSION


def test_candidate_set_adapts_ensemble_without_guessing_doc_refs() -> None:
    from indexing_v2.extraction.ensemble import EnsembleResult

    ensemble = EnsembleResult(
        champion_run="r1",
        tokens_primitive=[_subhead_token()],
        rule_groups={
            BRAND_GROUP_ID: [
                {
                    "id": "rule_b",
                    "evidence": {"unit_ids": ["u_b"], "quotes": ["b"]},
                },
                {
                    "id": "rule_a",
                    "evidence": {"unit_ids": ["u_a"], "quotes": ["a"]},
                },
            ]
        },
    )
    with pytest.raises(CandidateAdapterError, match="missing doc_ref mapping"):
        CandidateSet.from_ensemble(ensemble)

    candidates = CandidateSet.from_ensemble(
        ensemble,
        rule_group_doc_refs={BRAND_GROUP_ID: "brand_foundation[0]"},
    )
    round_tripped = CandidateSet.model_validate(candidates.model_dump(mode="json"))
    assert round_tripped.champion_run_id == "r1"
    assert round_tripped.rule_group_doc_refs == {
        BRAND_GROUP_ID: "brand_foundation[0]"
    }
    assert [rule["id"] for rule in round_tripped.rules_by_doc_ref[BRAND_GROUP_ID]] == [
        "rule_a",
        "rule_b",
    ]


def test_merge_evidence_unions_ids_and_quotes() -> None:
    left = {"unit_ids": ["u_b", "u_a"], "quotes": ["14px", "18px"]}
    right = {"unit_ids": ["u_a", "u_c"], "quotes": ["18px", "16px"]}
    merged = merge_evidence(left, right)
    assert merged["unit_ids"] == ["u_a", "u_b", "u_c"]
    assert merged["quotes"] == ["14px", "18px", "16px"]


def test_apply_patch_add_update_delete_split_merge(units) -> None:
    base = _fixture_candidates()
    add_patch = Patch.model_validate(
        _load_json(FIXTURE_LLM / "critic_catalog" / "001.json")["findings"][0]["proposed_patch"]
    )
    added = apply_patch_to_candidates(base, add_patch)
    assert any(
        token["id"] == "tok_minibible_type_subhead_size"
        for token in added.token_primitive
    )

    update_patch = Patch(
        op="update",
        entity_kind="token_primitive",
        target_entity_ids=["tok_minibible_type_subhead_size"],
        payload={"notes": "updated"},
    )
    updated = apply_patch_to_candidates(added, update_patch)
    token = next(
        item for item in updated.token_primitive if item["id"] == "tok_minibible_type_subhead_size"
    )
    assert token["notes"] == "updated"

    split_patch = Patch(
        op="split",
        entity_kind="token_primitive",
        target_entity_ids=["tok_minibible_type_subhead_size"],
        payload={
            "entities": [
                {
                    "id": "tok_minibible_type_subhead_size_a",
                    "key": "type.subhead.size.a",
                    "token_type": "dimension",
                    "value": {"default": "14px"},
                },
                {
                    "id": "tok_minibible_type_subhead_size_b",
                    "key": "type.subhead.size.b",
                    "token_type": "dimension",
                    "value": {"default": "14px"},
                },
            ]
        },
    )
    split = apply_patch_to_candidates(updated, split_patch)
    split_ids = {token["id"] for token in split.token_primitive}
    assert "tok_minibible_type_subhead_size_a" in split_ids
    assert "tok_minibible_type_subhead_size_b" in split_ids
    assert "tok_minibible_type_subhead_size" not in split_ids

    merge_patch = Patch(
        op="merge",
        entity_kind="token_primitive",
        target_entity_ids=[
            "tok_minibible_type_subhead_size_a",
            "tok_minibible_type_subhead_size_b",
        ],
        payload={"keep": "tok_minibible_type_subhead_size_a"},
    )
    merged = apply_patch_to_candidates(split, merge_patch)
    kept = next(
        item
        for item in merged.token_primitive
        if item["id"] == "tok_minibible_type_subhead_size_a"
    )
    assert "tok_minibible_type_subhead_size_b" not in {
        token["id"] for token in merged.token_primitive
    }
    assert kept["key"] == "type.subhead.size.a"

    delete_patch = Patch(
        op="delete",
        entity_kind="token_primitive",
        target_entity_ids=["tok_minibible_type_subhead_size_a"],
    )
    deleted = apply_patch_to_candidates(merged, delete_patch)
    assert "tok_minibible_type_subhead_size_a" not in {
        token["id"] for token in deleted.token_primitive
    }
    del units


def test_merge_patch_unions_evidence(units) -> None:
    base = CandidateSet(
        token_primitive=[
            {
                "id": "tok_a",
                "key": "a",
                "token_type": "color",
                "evidence": {"unit_ids": ["u_a"], "quotes": ["#111111"]},
                "value": {
                    "default": "#111111",
                    "default_evidence": {"unit_ids": ["u_a"], "quotes": ["#111111"]},
                },
            },
            {
                "id": "tok_b",
                "key": "b",
                "token_type": "color",
                "evidence": {"unit_ids": ["u_b"], "quotes": ["#222222"]},
                "value": {
                    "default": "#222222",
                    "default_evidence": {"unit_ids": ["u_b"], "quotes": ["#222222"]},
                },
            },
        ]
    )
    patch = Patch(
        op="merge",
        entity_kind="token_primitive",
        target_entity_ids=["tok_a", "tok_b"],
        payload={"keep": "tok_a"},
    )
    merged = apply_patch_to_candidates(base, patch)
    kept = merged.token_primitive[0]
    assert kept["evidence"]["unit_ids"] == ["u_a", "u_b"]
    assert kept["value"]["default_evidence"]["unit_ids"] == ["u_a", "u_b"]
    del units


def test_merge_patch_recursively_unions_variant_and_rule_evidence() -> None:
    left_token = {
        "id": "tok_variant_left",
        "key": "color.example",
        "token_type": "color",
        "evidence": {"unit_ids": ["u_root"], "quotes": ["root"]},
        "value": {
            "default": "#000000",
            "variants": [
                {
                    "when": {
                        "theme": " Dark ",
                        "content_tag": ["Beta", "alpha"],
                    },
                    "value": "#111111",
                    "evidence": {
                        "unit_ids": ["u_b"],
                        "quotes": ["left quote"],
                    },
                }
            ],
        },
    }
    right_token = copy.deepcopy(left_token)
    right_token["id"] = "tok_variant_right"
    right_token["value"]["default"] = "#FFFFFF"
    right_token["value"]["variants"] = [
        {
            "when": {
                "content_tag": ["ALPHA", "beta"],
                "theme": "dark",
            },
            "value": "#999999",
            "evidence": {
                "unit_ids": ["u_a"],
                "quotes": ["right quote"],
            },
        },
        {
            "when": {"theme": "light"},
            "value": "#222222",
            "evidence": {
                "unit_ids": ["u_c"],
                "quotes": ["light quote"],
            },
        },
    ]
    token_candidates = CandidateSet(token_semantic=[left_token, right_token])
    merged_tokens = apply_patch_to_candidates(
        token_candidates,
        Patch(
            op="merge",
            entity_kind="token_semantic",
            target_entity_ids=["tok_variant_left", "tok_variant_right"],
            payload={"keep": "tok_variant_left"},
        ),
    )
    merged_value = merged_tokens.token_semantic[0]["value"]
    assert merged_value["default"] == "#000000"
    assert len(merged_value["variants"]) == 2
    equivalent = next(
        variant
        for variant in merged_value["variants"]
        if variant["value"] == "#111111"
    )
    variant_evidence = equivalent["evidence"]
    assert variant_evidence["unit_ids"] == ["u_a", "u_b"]
    assert variant_evidence["quotes"] == ["left quote", "right quote"]
    assert {variant["value"] for variant in merged_value["variants"]} == {
        "#111111",
        "#222222",
    }

    left_rule = {
        "id": "rule_left",
        "evidence": {"unit_ids": ["u_b"], "quotes": ["root left"]},
        "snippets": ["approved"],
        "snippets_evidence": {"unit_ids": ["u_b"], "quotes": ["snippet left"]},
        "governance": {
            "preferred_form": "approved",
            "preferred_form_evidence": {
                "unit_ids": ["u_b"],
                "quotes": ["preferred left"],
            },
        },
    }
    right_rule = copy.deepcopy(left_rule)
    right_rule["id"] = "rule_right"
    right_rule["evidence"] = {"unit_ids": ["u_a"], "quotes": ["root right"]}
    right_rule["snippets_evidence"] = {
        "unit_ids": ["u_a"],
        "quotes": ["snippet right"],
    }
    right_rule["governance"]["preferred_form_evidence"] = {
        "unit_ids": ["u_a"],
        "quotes": ["preferred right"],
    }
    rule_candidates = CandidateSet(
        rules_by_doc_ref={"grp_blob_00": [left_rule, right_rule]},
        rule_group_doc_refs={"grp_blob_00": "blob[0]"},
    )
    merged_rules = apply_patch_to_candidates(
        rule_candidates,
        Patch(
            op="merge",
            entity_kind="rule",
            target_entity_ids=["rule_left", "rule_right"],
            payload={"keep": "rule_left"},
        ),
    )
    kept = merged_rules.rules_by_doc_ref["grp_blob_00"][0]
    assert kept["evidence"]["unit_ids"] == ["u_a", "u_b"]
    assert kept["snippets_evidence"]["quotes"] == [
        "snippet left",
        "snippet right",
    ]
    assert kept["governance"]["preferred_form_evidence"]["unit_ids"] == [
        "u_a",
        "u_b",
    ]


def test_patch_shape_and_kind_invariants_raise_typed_errors() -> None:
    candidates = _fixture_candidates(include_subhead=True)
    cross_blob_rules = [
        candidates.rules_by_doc_ref[BRAND_GROUP_ID][0]["id"],
        candidates.rules_by_doc_ref[LAYOUT_GROUP_ID][0]["id"],
    ]
    invalid = [
        (
            Patch(
                op="add",
                entity_kind="token_primitive",
                payload=_subhead_token(),
            ),
            "already exists",
        ),
        (
            Patch(
                op="delete",
                entity_kind="asset",
                target_entity_ids=["tok_minibible_type_subhead_size"],
            ),
            "does not match",
        ),
        (
            Patch(
                op="update",
                entity_kind="token_primitive",
                target_entity_ids=[
                    "tok_minibible_type_subhead_size",
                    "tok_minibible_color_primary_green_01",
                ],
            ),
            "exactly one",
        ),
        (
            Patch(
                op="split",
                entity_kind="token_primitive",
                target_entity_ids=["tok_minibible_type_subhead_size"],
                payload={"entities": [{"key": "missing.id"}]},
            ),
            "non-empty string id",
        ),
        (
            Patch(
                op="split",
                entity_kind="token_primitive",
                target_entity_ids=["tok_minibible_type_subhead_size"],
                payload={
                    "entities": [
                        {
                            **_subhead_token(),
                            "id": "tok_minibible_color_primary_green_01",
                        }
                    ]
                },
            ),
            "collides",
        ),
        (
            Patch(
                op="merge",
                entity_kind="token_primitive",
                target_entity_ids=[
                    "tok_minibible_type_subhead_size",
                    "tok_minibible_color_primary_green_01",
                ],
                payload={"keep": "missing"},
            ),
            "among target",
        ),
        (
            Patch(
                op="merge",
                entity_kind="rule",
                target_entity_ids=cross_blob_rules,
                payload={"keep": cross_blob_rules[0]},
            ),
            "share one doc_ref",
        ),
    ]
    for patch, message in invalid:
        with pytest.raises(PatchApplicationError, match=message):
            apply_patch_to_candidates(candidates, patch)


def test_mechanical_screen_rejects_verified_fabrication(units) -> None:
    candidates = _fixture_candidates()
    bogus = _load_json(FIXTURE_LLM / "critic_catalog" / "002.json")["findings"][0]
    finding = Finding.model_validate(bogus)
    assert mechanical_screen_finding(finding, candidates, units) is True


def test_mechanical_screen_precedes_malformed_patch_application(units) -> None:
    candidates = _fixture_candidates()
    target_id = "tok_minibible_color_primary_green_01"
    malformed_patch = Patch(
        op="delete",
        entity_kind="asset",
        target_entity_ids=[target_id],
    )
    finding = _finding(
        finding_id="f_mechanical_first",
        finding_type="fabrication",
        severity="major",
        patch=malformed_patch,
        target_entity_id=target_id,
    )
    after, resolved, audit = triage_findings(
        [finding],
        candidates,
        units,
        round_num=1,
    )
    assert resolved[0].resolution == "rejected_mechanical"
    assert audit[0].status == "rejected_mechanical"
    assert after.model_dump() == candidates.model_dump()


def test_malformed_finding_does_not_block_later_valid_patch(units) -> None:
    candidates = _fixture_candidates(include_subhead=False)
    malformed = _finding(
        finding_id="f_a_invalid",
        finding_type="omission",
        patch=Patch(
            op="delete",
            entity_kind="token_primitive",
            target_entity_ids=["tok_missing"],
        ),
    )
    valid = _finding(
        finding_id="f_b_valid",
        finding_type="omission",
        patch=Patch(
            op="add",
            entity_kind="token_primitive",
            payload=_subhead_token(),
        ),
    )
    after, resolved, audit = triage_findings(
        [malformed, valid],
        candidates,
        units,
        round_num=1,
    )
    assert [finding.resolution for finding in resolved] == [
        "rejected_verification",
        "applied",
    ]
    assert [record.status for record in audit] == [
        "rejected_verification",
        "applied",
    ]
    assert audit[0].detail == "entity not found: tok_missing"
    assert audit[0].after_hash is not None
    assert "tok_minibible_type_subhead_size" in {
        token["id"] for token in after.token_primitive
    }


def test_malformed_evidence_does_not_block_later_valid_patch(units) -> None:
    candidates = _fixture_candidates(include_subhead=False)
    malformed_token = _subhead_token()
    malformed_token["evidence"]["unit_ids"] = "not-a-list"
    malformed = _finding(
        finding_id="f_a_bad_evidence",
        finding_type="omission",
        patch=Patch(
            op="add",
            entity_kind="token_primitive",
            payload=malformed_token,
        ),
    )
    valid = _finding(
        finding_id="f_b_valid",
        finding_type="omission",
        patch=Patch(
            op="add",
            entity_kind="token_primitive",
            payload=_subhead_token(),
        ),
    )
    after, resolved, audit = triage_findings(
        [malformed, valid],
        candidates,
        units,
        round_num=1,
    )
    assert [finding.resolution for finding in resolved] == [
        "rejected_verification",
        "applied",
    ]
    assert "unit_ids must be a list of strings" in (audit[0].detail or "")
    assert audit[0].after_hash is not None
    assert "tok_minibible_type_subhead_size" in {
        token["id"] for token in after.token_primitive
    }


def test_triage_rejects_verification_without_mutation(units) -> None:
    candidates = _fixture_candidates()
    corrupt = _load_json(FIXTURE_LLM / "corrupt_bad_quote" / "001.json")["tokens"][0]
    patch = Patch(
        op="add",
        entity_kind="token_primitive",
        payload=corrupt,
    )
    finding = _finding(
        finding_id="f_test_bad",
        finding_type="omission",
        patch=patch,
    )
    after, resolved, audit = triage_findings([finding], candidates, units, round_num=1)
    assert resolved[0].resolution == "rejected_verification"
    assert audit[0].status == "rejected_verification"
    assert audit[0].after_hash is not None
    assert "tok_minibible_spacing_phantom_99" not in {
        token["id"] for token in after.token_primitive
    }
    assert candidates.model_dump() == after.model_dump()


def test_triage_verifies_only_patch_products(units, monkeypatch) -> None:
    candidates = _fixture_candidates(include_subhead=False)
    patch = Patch(
        op="add",
        entity_kind="token_primitive",
        payload=_subhead_token(),
    )
    finding = _finding(
        finding_id="f_scoped_verification",
        finding_type="omission",
        patch=patch,
    )
    verified_entity_ids: list[set[str]] = []

    def recording_verify(entities_by_kind, source_units):
        verified_entity_ids.append(
            {
                entity["id"]
                for bucket in entities_by_kind.values()
                for entity in bucket
            }
        )
        return verify_entities(entities_by_kind, source_units)

    monkeypatch.setattr(
        "indexing_v2.extraction.critic.verify_entities",
        recording_verify,
    )

    _, resolved, _ = triage_findings(
        [finding],
        candidates,
        units,
        round_num=1,
    )

    assert resolved[0].resolution == "applied"
    assert verified_entity_ids == [{"tok_minibible_type_subhead_size"}]


def test_triage_accepts_all_five_patch_ops(units) -> None:
    add_patch = Patch(
        op="add",
        entity_kind="token_primitive",
        payload=_subhead_token(),
    )
    update_patch = Patch(
        op="update",
        entity_kind="token_primitive",
        target_entity_ids=["tok_minibible_type_subhead_size"],
        payload={"notes": "critic-confirmed"},
    )
    delete_patch = Patch(
        op="delete",
        entity_kind="token_primitive",
        target_entity_ids=["tok_minibible_type_subhead_size"],
    )

    split_a = _subhead_token()
    split_a.update(id="tok_minibible_type_subhead_size_a", key="type.subhead.size.a")
    split_b = _subhead_token()
    split_b.update(id="tok_minibible_type_subhead_size_b", key="type.subhead.size.b")
    split_patch = Patch(
        op="split",
        entity_kind="token_primitive",
        target_entity_ids=["tok_minibible_type_subhead_size"],
        payload={"entities": [split_a, split_b]},
    )

    merge_base = _fixture_candidates(include_subhead=True)
    duplicate = _subhead_token()
    duplicate.update(id="tok_minibible_type_subhead_size_duplicate")
    merge_base.token_primitive.append(duplicate)
    merge_patch = Patch(
        op="merge",
        entity_kind="token_primitive",
        target_entity_ids=[
            "tok_minibible_type_subhead_size",
            "tok_minibible_type_subhead_size_duplicate",
        ],
        payload={"keep": "tok_minibible_type_subhead_size"},
    )

    cases = [
        (_fixture_candidates(include_subhead=False), add_patch, {"tok_minibible_type_subhead_size"}),
        (_fixture_candidates(include_subhead=True), update_patch, {"tok_minibible_type_subhead_size"}),
        (_fixture_candidates(include_subhead=True), delete_patch, set()),
        (
            _fixture_candidates(include_subhead=True),
            split_patch,
            {
                "tok_minibible_type_subhead_size_a",
                "tok_minibible_type_subhead_size_b",
            },
        ),
        (merge_base, merge_patch, {"tok_minibible_type_subhead_size"}),
    ]
    for index, (candidates, patch, expected_ids) in enumerate(cases, start=1):
        finding = _finding(
            finding_id=f"f_triage_{index}",
            finding_type="omission",
            patch=patch,
        )
        after, resolved, audit = triage_findings(
            [finding],
            candidates,
            units,
            round_num=1,
        )
        assert resolved[0].resolution == "applied", patch.op
        assert audit[0].status == "applied", patch.op
        assert audit[0].after_hash is not None, patch.op
        if patch.op in {"delete", "split"}:
            assert audit[0].after_hash != audit[0].before_hash
        result_ids = {
            token["id"]
            for token in after.token_primitive
            if token["id"].startswith("tok_minibible_type_subhead_size")
        }
        assert result_ids == expected_ids, patch.op


def test_triage_rejects_bad_variant_even_with_valid_default(units) -> None:
    candidates = _fixture_candidates()
    target_id = "tok_minibible_color_primary_green_01"
    patch = Patch(
        op="update",
        entity_kind="token_primitive",
        target_entity_ids=[target_id],
        payload={
            "value": {
                "variants": [
                    {
                        "when": {"theme": "dark"},
                        "value": "#BADBAD",
                        "evidence": {
                            "unit_ids": ["u_brand_foundation_0_0004"],
                            "quotes": ["not quoted anywhere"],
                        },
                    }
                ]
            }
        },
    )
    finding = _finding(
        finding_id="f_bad_variant",
        finding_type="wrong_condition",
        patch=patch,
    )
    after, resolved, audit = triage_findings(
        [finding],
        candidates,
        units,
        round_num=1,
    )
    assert resolved[0].resolution == "rejected_verification"
    assert audit[0].after_hash is not None
    assert after.model_dump() == candidates.model_dump()


def test_triage_rejects_missing_root_and_effect_evidence(units) -> None:
    token = _subhead_token()
    token.pop("evidence")
    missing_root = Patch(
        op="add",
        entity_kind="token_primitive",
        payload=token,
    )

    rule = copy.deepcopy(
        _fixture_candidates().rules_by_doc_ref[BRAND_GROUP_ID][0]
    )
    rule["id"] = "rule_minibible_missing_effect_evidence"
    rule["doc_ref"] = "brand_foundation[0]"
    rule.pop("effect_evidence")
    missing_effect = Patch(op="add", entity_kind="rule", payload=rule)

    for finding_id, patch in (
        ("f_missing_root", missing_root),
        ("f_missing_effect", missing_effect),
    ):
        candidates = _fixture_candidates(include_subhead=False)
        _, resolved, audit = triage_findings(
            [
                _finding(
                    finding_id=finding_id,
                    finding_type="omission",
                    patch=patch,
                )
            ],
            candidates,
            units,
            round_num=1,
        )
        assert resolved[0].resolution == "rejected_verification"
        assert audit[0].after_hash is not None


def test_parse_findings_response_rejects_malformed() -> None:
    with pytest.raises(CriticResponseError, match="must be a JSON object"):
        parse_findings_response([], round_num=1)
    with pytest.raises(CriticResponseError, match="missing findings"):
        parse_findings_response({}, round_num=1)
    with pytest.raises(CriticResponseError, match="row 0 must be an object"):
        parse_findings_response({"findings": ["not-an-object"]}, round_num=1)
    duplicate = {
        "finding_id": "f_duplicate",
        "finding_type": "omission",
        "severity": "minor",
        "description": "duplicate",
    }
    with pytest.raises(CriticResponseError, match="duplicate finding_id"):
        parse_findings_response(
            {"findings": [duplicate, duplicate]},
            round_num=1,
        )
    with pytest.raises(CriticResponseError, match="finding has unknown field"):
        parse_findings_response(
            {"findings": [{**duplicate, "unexpected": True}]},
            round_num=1,
        )
    with pytest.raises(CriticResponseError, match="patch has unknown field"):
        parse_findings_response(
            {
                "findings": [
                    {
                        **duplicate,
                        "proposed_patch": {
                            "op": "delete",
                            "entity_kind": "token_primitive",
                            "target_entity_ids": ["tok_x"],
                            "unexpected": True,
                        },
                    }
                ]
            },
            round_num=1,
        )
    parsed = parse_findings_response(
        {
            "findings": [
                {
                    **duplicate,
                    "proposed_patch": {
                        "op": "delete",
                        "entity_kind": "token_primitive",
                    },
                }
            ]
        },
        round_num=1,
    )
    assert parsed[0].proposed_patch is not None
    assert parsed[0].proposed_patch.target_entity_ids == []


def test_parse_finding_coerces_unknown_finding_type_to_other() -> None:
    finding = parse_finding(
        {
            "finding_id": "f_lisraya_1",
            "finding_type": "wrong hardness, polarity, or scope vs source",
            "severity": "major",
            "description": "scope should be org_baseline",
            "unit_ids": ["u_other_rules_2_0001"],
        },
        round_num=1,
    )
    assert finding.finding_type == "other"
    assert finding.description.startswith(
        "[wrong hardness, polarity, or scope vs source]"
    )
    missed = parse_finding(
        {
            "finding_id": "f_lisraya_2",
            "finding_type": "missed relation",
            "severity": "minor",
            "description": "should refines sibling",
        },
        round_num=1,
    )
    assert missed.finding_type == "other"
    assert "[missed relation]" in missed.description


def test_defer_open_major_findings_after_round_cap(units) -> None:
    candidates = _fixture_candidates()
    finding = _finding(
        finding_id="f_major_open",
        finding_type="governance_miss",
        severity="major",
        patch=None,
    )
    _, resolved, _ = triage_findings([finding], candidates, units, round_num=1)
    assert resolved[0].resolution == "open"
    from indexing_v2.extraction.critic import _defer_open_findings

    deferred = _defer_open_findings(resolved)
    assert deferred[0].resolution == "deferred_human"
    del units


@pytest.mark.asyncio
async def test_run_critic_applies_valid_patch_and_rejects_bogus(units, tmp_path: Path) -> None:
    settings.reload_settings()
    clear_brand_cache(MINIBIBLE_BRAND)
    llm = CriticFakeLLM()
    usage = Usage()
    work_dir = tmp_path / "work"
    candidates = _fixture_candidates(include_subhead=False)

    result = await run_critic(
        MINIBIBLE_BRAND,
        units,
        candidates,
        usage,
        llm,
        work_dir=work_dir,
        cache_root=tmp_path / "cache",
        champion_run_id="r0",
    )

    assert result.rounds_completed == settings.MAX_CRITIC_ROUNDS
    assert any(
        token["id"] == "tok_minibible_type_subhead_size"
        for token in result.candidates.token_primitive
    )
    by_id = {finding.finding_id: finding for finding in result.findings}
    assert by_id["f_minibible_0001"].resolution == "applied"
    assert by_id["f_minibible_0002"].resolution == "rejected_mechanical"

    verify = verify_entities(result.candidates.to_entities_by_kind(), units)
    default = next(
        record
        for record in verify.records_by_entity["tok_minibible_type_subhead_size"]
        if record.field == "value.default"
    )
    assert default.verification == "value_verified"

    assert (work_dir / "findings.jsonl").is_file()
    assert (work_dir / "audit" / "patches.jsonl").is_file()
    assert usage.llm_calls >= 3


@pytest.mark.asyncio
async def test_run_critic_calls_rules_per_blob(units, tmp_path: Path) -> None:
    settings.reload_settings()
    clear_brand_cache(MINIBIBLE_BRAND, tmp_path / "cache")
    llm = CriticFakeLLM()
    usage = Usage()
    candidates = _fixture_candidates()

    await run_critic(
        MINIBIBLE_BRAND,
        units,
        candidates,
        usage,
        llm,
        cache_root=tmp_path / "cache",
        champion_run_id="r0",
        max_rounds=1,
    )

    rules_calls = [call for call in llm.calls() if call.prompt_name == "critic_rules"]
    assert len(rules_calls) == 2
    doc_refs = set()
    for call in rules_calls:
        assert "Blob doc_ref:" in call.user
        assert "Candidate rule group ids:" in call.user
        line = next(line for line in call.user.splitlines() if line.startswith("Blob doc_ref:"))
        doc_refs.add(line.split(":", 1)[1].strip())
    assert doc_refs == {"brand_foundation[0]", "layout_constraints[0]"}
    rendered_group_ids = "\n".join(call.user for call in rules_calls)
    assert BRAND_GROUP_ID in rendered_group_ids
    assert LAYOUT_GROUP_ID in rendered_group_ids


@pytest.mark.asyncio
async def test_driver_normalizes_colliding_finding_ids_in_call_order(
    units,
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "llm"
    finding_payload = {
        "findings": [
            {
                "finding_id": "f_collision",
                "finding_type": "omission",
                "severity": "minor",
                "description": "same model id from every call",
            }
        ]
    }
    for prompt_name in ("critic_catalog", "critic_rules"):
        directory = fixture_root / prompt_name
        directory.mkdir(parents=True)
        (directory / "001.json").write_text(
            json.dumps(finding_payload),
            encoding="utf-8",
        )
    llm = CriticFakeLLM(fixture_root=fixture_root)
    result = await run_critic(
        "Mini Bible!",
        units,
        CandidateSet(),
        Usage(),
        llm,
        cache_root=tmp_path / "cache",
        max_rounds=1,
    )
    assert [finding.finding_id for finding in result.findings] == [
        "f_mini_bible_0001",
        "f_mini_bible_0002",
        "f_mini_bible_0003",
    ]


@pytest.mark.asyncio
async def test_driver_preserves_invalid_and_applies_later_valid_finding(
    units,
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "llm"
    catalog_dir = fixture_root / "critic_catalog"
    rules_dir = fixture_root / "critic_rules"
    catalog_dir.mkdir(parents=True)
    rules_dir.mkdir(parents=True)
    malformed_token = _subhead_token()
    malformed_token["value"]["default_evidence"]["quotes"] = "not-a-list"
    payload = {
        "findings": [
            {
                "finding_id": "f_bad",
                "finding_type": "omission",
                "severity": "minor",
                "description": "malformed evidence",
                "proposed_patch": {
                    "op": "add",
                    "entity_kind": "token_primitive",
                    "payload": malformed_token,
                },
            },
            {
                "finding_id": "f_good",
                "finding_type": "omission",
                "severity": "minor",
                "description": "valid add",
                "proposed_patch": {
                    "op": "add",
                    "entity_kind": "token_primitive",
                    "payload": _subhead_token(),
                },
            },
        ]
    }
    (catalog_dir / "001.json").write_text(json.dumps(payload), encoding="utf-8")
    (rules_dir / "001.json").write_text(
        json.dumps({"findings": []}),
        encoding="utf-8",
    )
    result = await run_critic(
        MINIBIBLE_BRAND,
        units,
        _fixture_candidates(include_subhead=False),
        Usage(),
        CriticFakeLLM(fixture_root=fixture_root),
        cache_root=tmp_path / "cache",
        max_rounds=1,
    )
    assert [finding.resolution for finding in result.findings] == [
        "rejected_verification",
        "applied",
    ]
    assert "quotes must be a list of strings" in (result.audit[0].detail or "")
    assert "tok_minibible_type_subhead_size" in {
        token["id"] for token in result.candidates.token_primitive
    }


@pytest.mark.asyncio
async def test_run_critic_rejects_nonpositive_concurrency(units) -> None:
    with pytest.raises(ValueError, match="concurrency must be greater than zero"):
        await run_critic(
            MINIBIBLE_BRAND,
            units,
            CandidateSet(),
            Usage(),
            CriticFakeLLM(),
            max_rounds=1,
            concurrency=0,
        )


@pytest.mark.asyncio
async def test_audit_hashes_are_deterministic(units, tmp_path: Path) -> None:
    settings.reload_settings()
    cache_root = tmp_path / "cache"
    outputs: list[bytes] = []
    for _ in range(2):
        clear_brand_cache(MINIBIBLE_BRAND, cache_root)
        llm = CriticFakeLLM()
        usage = Usage()
        work_dir = tmp_path / f"run_{len(outputs)}"
        await run_critic(
            MINIBIBLE_BRAND,
            units,
            _fixture_candidates(include_subhead=False),
            usage,
            llm,
            work_dir=work_dir,
            cache_root=cache_root,
            champion_run_id="r0",
        )
        outputs.append((work_dir / "audit" / "patches.jsonl").read_bytes())
    assert outputs[0] == outputs[1]
    rows = json.loads(f"[{outputs[0].decode().replace('}\n{', '},{')}]")
    applied = next(row for row in rows if row["status"] == "applied")
    assert len(applied["before_hash"]) == 16
    assert len(applied["after_hash"]) == 16
    assert applied["before_hash"] != applied["after_hash"]


def test_write_critic_artifacts_round_trip(tmp_path: Path, units) -> None:
    candidates = _fixture_candidates()
    findings = [
        _finding(finding_id="f_x", finding_type="omission", severity="info", patch=None),
    ]
    audit = []
    write_critic_artifacts(
        tmp_path,
        findings=findings,
        audit=audit,
        candidates=candidates,
    )
    assert (tmp_path / "findings.jsonl").is_file()
    tokens_path = tmp_path / "candidates" / "tokens.json"
    assert tokens_path.is_file()
    written_tokens = _load_json(tokens_path)
    assert {token["kind"] for token in written_tokens} == {
        "primitive",
        "semantic",
    }
    assert [
        (token["kind"], token["id"])
        for token in written_tokens
    ] == sorted((token["kind"], token["id"]) for token in written_tokens)
    reversed_candidates = candidates.model_copy(deep=True)
    reversed_candidates.token_primitive.reverse()
    reversed_candidates.token_semantic.reverse()
    reversed_candidates.asset.reverse()
    assert render_catalog_summary(candidates) == render_catalog_summary(
        reversed_candidates
    )
    rules_dir = tmp_path / "candidates" / "rules"
    original_files = sorted(path.name for path in rules_dir.glob("*.json"))
    assert original_files == [
        f"{BRAND_GROUP_ID}.json",
        f"{LAYOUT_GROUP_ID}.json",
    ]
    (rules_dir / "stale.json").write_text("{}\n", encoding="utf-8")
    write_critic_artifacts(
        tmp_path,
        findings=findings,
        audit=audit,
        candidates=CandidateSet(),
    )
    assert list(rules_dir.glob("*.json")) == []
    del units


def test_apply_patch_missing_entity_raises() -> None:
    with pytest.raises(PatchApplicationError, match="entity not found"):
        apply_patch_to_candidates(
            CandidateSet(),
            Patch(
                op="delete",
                entity_kind="token_primitive",
                target_entity_ids=["missing"],
            ),
        )


def test_stable_hash_used_for_audit_before_state(units) -> None:
    candidates = _fixture_candidates()
    patch = Patch.model_validate(
        _load_json(FIXTURE_LLM / "critic_catalog" / "001.json")["findings"][0]["proposed_patch"]
    )
    from indexing_v2.extraction.critic import _before_hash

    assert _before_hash(candidates, patch) == stable_hash(
        {"op": "add", "kind": "token_primitive", "payload": patch.payload}
    )
    del units
