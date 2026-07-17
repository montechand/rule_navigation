"""Contract tests for §5.5 S4 ensemble reconciliation (WP-09)."""

from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path
from typing import Any

import pytest

from indexing_v2.cascade.guards import normalize_guard
from indexing_v2.contracts import (
    ProvenanceRecord,
    RunVariant,
    SourceUnit,
    UnitLabel,
    ValueCheck,
    read_jsonl,
    stable_hash,
)
from indexing_v2.extraction.ensemble import (
    STAGE_VERSION,
    RuleGroupMappingError,
    SemanticResolutionError,
    VerifiedRunInput,
    _rule_signature,
    build_token_catalog,
    build_verified_run,
    reconcile_ensemble,
    semantic_match_key,
    write_candidates,
)
from indexing_v2.extraction.critic import CandidateSet
from indexing_v2.extraction.provenance import ProvenanceResult, QuarantineEntry
from indexing_v2.extraction.runner import RunOutput, RuleGroupOutput

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "minibible"


@pytest.fixture
def units() -> list[SourceUnit]:
    return read_jsonl(FIXTURE_ROOT / "expected" / "units.jsonl", SourceUnit)


@pytest.fixture
def labels() -> list[UnitLabel]:
    return read_jsonl(FIXTURE_ROOT / "expected" / "labels.jsonl", UnitLabel)


def _unit(units: list[SourceUnit], unit_id: str) -> SourceUnit:
    return next(unit for unit in units if unit.unit_id == unit_id)


def _label(unit_id: str, kind: str = "token_primitive") -> UnitLabel:
    return UnitLabel(
        unit_id=unit_id,
        labels=["value"],
        expected_yield=[kind],  # type: ignore[list-item]
        required=True,
        heuristic_locked=["value"],
        confidence=1.0,
    )


def _token(
    token_id: str,
    key: str,
    default: Any,
    unit: SourceUnit,
    *,
    token_type: str = "color",
    scope: str = "global",
    quote: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    cited = quote or str(default)
    return {
        "id": token_id,
        "key": key,
        "token_type": token_type,
        "scope": scope,
        "value": {
            "default": default,
            "default_evidence": {
                "quotes": [cited],
                "unit_ids": [unit.unit_id],
            },
            "variants": None,
        },
        "evidence": {
            "quotes": [cited],
            "unit_ids": [unit.unit_id],
        },
        **extra,
    }


def _semantic(
    token_id: str,
    key: str,
    default: Any,
    unit: SourceUnit,
    *,
    token_type: str = "dimension",
    quote: str,
    variants: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": token_id,
        "key": key,
        "token_type": token_type,
        "value": {
            "default": default,
            "default_evidence": {
                "quotes": [quote],
                "unit_ids": [unit.unit_id],
            },
            "variants": variants,
        },
        "evidence": {
            "quotes": [quote],
            "unit_ids": [unit.unit_id],
        },
    }


def _output(
    run_id: str,
    *,
    primitive: list[dict[str, Any]] | None = None,
    semantic: list[dict[str, Any]] | None = None,
    assets: list[dict[str, Any]] | None = None,
    rules: list[dict[str, Any]] | None = None,
    relations: list[dict[str, Any]] | None = None,
    group_id: str = "grp_test",
    doc_ref: str = "test[0]",
) -> RunOutput:
    group = RuleGroupOutput(
        group_id=group_id,
        doc_ref=doc_ref,
        original_text="",
        rules=rules or [],
        relations=relations or [],
    )
    return RunOutput(
        variant=RunVariant(run_id=run_id, model=f"fake-{run_id}"),
        primitive_tokens=primitive or [],
        semantic_tokens=semantic or [],
        catalog_rest={"assets": assets or [], "subtypes": [], "templates": []},
        rule_groups=[group] if rules or relations else [],
        rules_by_doc_ref={doc_ref: rules or []} if rules else {},
    )


def _verified(
    run_id: str,
    units: list[SourceUnit],
    **kwargs: Any,
) -> VerifiedRunInput:
    return build_verified_run(_output(run_id, **kwargs), units)


def _load_run_output(run_id: str) -> RunOutput:
    primitive = json.loads(
        (FIXTURE_ROOT / "llm/tokens_primitive" / f"{run_id}_001.json").read_text()
    )["tokens"]
    semantic = json.loads(
        (FIXTURE_ROOT / "llm/tokens_semantic" / f"{run_id}_001.json").read_text()
    )["tokens"]
    catalog = json.loads((FIXTURE_ROOT / "llm/catalog_rest" / "001.json").read_text())
    groups: list[RuleGroupOutput] = []
    for path in sorted((FIXTURE_ROOT / "llm/rules_cluster").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        doc_ref = (
            "brand_foundation[0]"
            if path.name.startswith("brand_foundation")
            else "layout_constraints[0]"
        )
        groups.append(
            RuleGroupOutput(
                group_id=f"grp_minibible_{doc_ref.split('[')[0]}_00",
                doc_ref=doc_ref,
                original_text="",
                rules=payload["rules"],
                relations=payload.get("relations", []),
            )
        )
    return RunOutput(
        variant=RunVariant(run_id=run_id, model=f"fake-{run_id}"),
        primitive_tokens=primitive,
        semantic_tokens=semantic,
        catalog_rest=catalog,
        rule_groups=groups,
        rules_by_doc_ref={group.doc_ref: group.rules for group in groups},
    )


def _fixture_runs(units: list[SourceUnit]) -> list[VerifiedRunInput]:
    return [
        build_verified_run(_load_run_output(run_id), units)
        for run_id in ("r0", "r1", "r2")
    ]


def _manual_run(
    output: RunOutput,
    *,
    records: dict[str, list[ProvenanceRecord]] | None = None,
    by_unit: dict[str, list[str]] | None = None,
    quarantine: list[QuarantineEntry] | None = None,
) -> VerifiedRunInput:
    return VerifiedRunInput(
        output=output,
        provenance=ProvenanceResult(
            records_by_entity=records or {},
            by_unit=by_unit or {},
            quarantine=quarantine or [],
        ),
    )


def _record(
    entity_id: str,
    field: str,
    verification: str,
) -> ProvenanceRecord:
    return ProvenanceRecord(
        entity_id=entity_id,
        field=field,
        spans=[],
        value_check=ValueCheck(status="pass"),
        verification=verification,  # type: ignore[arg-type]
    )


def test_stage_version_present() -> None:
    assert STAGE_VERSION == "1.3.0"


def test_minibible_three_run_reconcile(
    units: list[SourceUnit],
    labels: list[UnitLabel],
) -> None:
    result = reconcile_ensemble(_fixture_runs(units), units, labels)
    assert result.champion_run == "r1"
    primitive_ids = {entity["id"] for entity in result.tokens_primitive}
    assert "tok_minibible_spacing_subhead_margin" in primitive_ids
    assert "tok_minibible_spacing_phantom_99" not in primitive_ids
    assert any(
        finding.target_entity_id == "tok_minibible_spacing_phantom_99"
        for finding in result.findings
    )
    same_value = next(
        entity
        for entity in result.tokens_primitive
        if entity["value"]["default"] == "16px"
        and entity["token_type"] == "spacing"
    )
    assert "spacing.step.md" in same_value["aliases"]
    assert same_value["extraction_meta"]["support"] == 3
    expected_units = {
        unit_id
        for token in _load_run_output("r0").primitive_tokens
        if token.get("token_type") == "spacing"
        and token.get("value", {}).get("default") == "16px"
        for unit_id in token["evidence"]["unit_ids"]
    }
    assert expected_units <= set(same_value["evidence"]["unit_ids"])


def test_primitive_key_is_exact_and_preserves_different_keys_as_aliases(
    units: list[SourceUnit],
) -> None:
    source = _unit(units, "u_brand_foundation_0_0004")
    left = _token("tok_a", "color.primary", "#01A47E", source)
    right = _token("tok_b", "color.brand_teal", "#01a47e", source)
    result = reconcile_ensemble(
        [
            _verified("r0", units, primitive=[left]),
            _verified("r1", units, primitive=[right]),
        ],
        units,
        [_label(source.unit_id)],
    )
    assert len(result.tokens_primitive) == 1
    merged = result.tokens_primitive[0]
    assert merged["id"] == "tok_a"
    assert merged["key"] == "color.primary"
    assert "color.brand_teal" in merged["aliases"]
    assert merged["extraction_meta"]["field_agreement"]["key"] == 0.5


def test_span_verified_singleton_is_rejected(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0004")
    asset = {
        "id": "asset_single",
        "asset_type": "logo",
        "uri": "https://example.test/logo.svg",
        "evidence": {
            "quotes": ["Primary Green"],
            "unit_ids": [source.unit_id],
        },
    }
    result = reconcile_ensemble(
        [
            _verified("r0", units, assets=[asset]),
            _verified("r1", units),
        ],
        units,
        [_label(source.unit_id, "asset")],
    )
    assert result.assets == []
    assert any(finding.target_entity_id == "asset_single" for finding in result.findings)


def test_value_verified_redundant_singleton_is_rejected(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0010")
    global_tokens = [
        _token(f"tok_white_{run}", "color.white", "#FFFFFF", source)
        for run in ("r0", "r1", "r2")
    ]
    redundant = _token(
        "tok_white_brand",
        "color.white.brand",
        "#FFFFFF",
        source,
        scope="brand",
    )
    result = reconcile_ensemble(
        [
            _verified("r0", units, primitive=[global_tokens[0]]),
            _verified("r1", units, primitive=[global_tokens[1]]),
            _verified("r2", units, primitive=[global_tokens[2], redundant]),
        ],
        units,
        [_label(source.unit_id)],
    )
    assert {entity["id"] for entity in result.tokens_primitive} == {"tok_white_r0"}
    assert any(finding.target_entity_id == "tok_white_brand" for finding in result.findings)


def test_k1_applies_singleton_policy_deliberately(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0004")
    token = _token("tok_green", "color.green", "#01A47E", source)
    asset = {
        "id": "asset_span_only",
        "asset_type": "logo",
        "evidence": {"quotes": ["Primary Green"], "unit_ids": [source.unit_id]},
    }
    result = reconcile_ensemble(
        [_verified("r0", units, primitive=[token], assets=[asset])],
        units,
        [_label(source.unit_id)],
    )
    assert [entity["id"] for entity in result.tokens_primitive] == ["tok_green"]
    assert result.assets == []
    assert result.tokens_primitive[0]["extraction_meta"]["confidence"] == "high"


def test_duplicate_emission_is_one_vote(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0004")
    r0 = [
        _token("tok_a0", "color.green.a", "#01A47E", source, notes="A"),
        _token("tok_b0", "color.green.b", "#01A47E", source, notes="A"),
    ]
    r1 = [_token("tok_r1", "color.green.r1", "#01A47E", source, notes="B")]
    r2 = [_token("tok_r2", "color.green.r2", "#01A47E", source, notes="B")]
    result = reconcile_ensemble(
        [
            _verified("r0", units, primitive=r0),
            _verified("r1", units, primitive=r1),
            _verified("r2", units, primitive=r2),
        ],
        units,
        [_label(source.unit_id)],
    )
    merged = result.tokens_primitive[0]
    assert merged["notes"] == "B"
    assert merged["extraction_meta"]["support"] == 3
    assert merged["extraction_meta"]["field_agreement"]["notes"] == pytest.approx(2 / 3)
    assert "color.green.b" in merged["aliases"]


def test_nested_ref_semantic_key_matches_direct_default(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0020")
    primitive = _token(
        "tok_primitive",
        "size.base",
        "16px",
        source,
        token_type="dimension",
    )
    alias = _semantic(
        "tok_alias",
        "size.alias",
        {"$ref": "tok_primitive"},
        source,
        quote="16px",
    )
    nested = _semantic(
        "tok_body_ref",
        "body.text.size",
        {"$ref": "tok_alias"},
        source,
        quote="16px",
    )
    direct = _semantic(
        "tok_body_direct",
        "body.text.size",
        "16px",
        source,
        quote="16px",
    )
    ref_output = _output("r0", primitive=[primitive], semantic=[alias, nested])
    direct_output = _output("r1", semantic=[direct])
    assert semantic_match_key(nested, build_token_catalog(ref_output)) == semantic_match_key(
        direct,
        build_token_catalog(direct_output),
    )
    result = reconcile_ensemble(
        [
            build_verified_run(ref_output, units),
            build_verified_run(direct_output, units),
        ],
        units,
        [_label(source.unit_id, "token_semantic")],
    )
    body = [entity for entity in result.tokens_semantic if entity["key"] == "body.text.size"]
    assert len(body) == 1
    assert body[0]["extraction_meta"]["support"] == 2


def test_ref_resolution_errors_are_typed_and_deterministic() -> None:
    missing = {"id": "sem", "key": "x", "token_type": "dimension", "value": {"default": {"$ref": "nope"}}}
    with pytest.raises(SemanticResolutionError, match=r"sem: missing \$ref default: nope"):
        semantic_match_key(missing, {})

    cycle_a = {"id": "a", "key": "a", "token_type": "dimension", "value": {"default": {"$ref": "b"}}}
    cycle_b = {"id": "b", "key": "b", "token_type": "dimension", "value": {"default": {"$ref": "a"}}}
    with pytest.raises(SemanticResolutionError, match=r"cyclic \$ref default: b -> a -> b"):
        semantic_match_key(cycle_a, {"a": cycle_a, "b": cycle_b})


def test_match_key_degrades_on_type_shape_mismatch() -> None:
    # LLM declared color but the $ref resolves to a gradient mapping (real
    # lisraya crash): must yield a deterministic key-order-independent canon,
    # not a TypeError.
    gradient = {
        "id": "tok_g",
        "key": "g",
        "token_type": "gradient",
        "value": {"default": {"type": "linear", "stops": ["#FFDF55", "#FAA21B"]}},
    }
    mislabeled = {
        "id": "tok_c",
        "key": "c",
        "token_type": "color",
        "value": {"default": {"$ref": "tok_g"}},
    }
    _, canon = semantic_match_key(mislabeled, {"tok_g": gradient})
    assert canon == '{"stops":["#FFDF55","#FAA21B"],"type":"linear"}'
    # Same mapping with different key order groups identically.
    reordered = dict(gradient, value={"default": {"stops": ["#FFDF55", "#FAA21B"], "type": "linear"}})
    _, canon2 = semantic_match_key(mislabeled, {"tok_g": reordered})
    assert canon2 == canon
    # Properly-typed gradients keep the richer gradient canon.
    _, gcanon = semantic_match_key(
        dict(gradient, id="tok_g2", value={"default": {"$ref": "tok_g"}}),
        {"tok_g": gradient, "tok_g2": gradient},
    )
    assert gcanon == '{"angle":0,"stops":["#ffdf55","#faa21b"]}'


def test_duplicate_ids_across_merge_groups_collapse_instead_of_crashing() -> None:
    # Real lisraya crash: two merge groups (whitespace-variant shadow values)
    # both kept id tok_..._shadow_icon_badge; final verify raised
    # ProvenanceError("duplicate entity id"). Collapse must keep the higher-
    # support entity and emit a finding.
    from indexing_v2.extraction.ensemble import _collapse_duplicate_ids

    low = {"id": "tok_x_shadow", "value": "a", "extraction_meta": {"support": 1}}
    high = {"id": "tok_x_shadow", "value": "b", "extraction_meta": {"support": 2}}
    other = {"id": "tok_x_other", "extraction_meta": {"support": 1}}
    findings: list[Any] = []
    out = _collapse_duplicate_ids([low, high, other], findings)
    assert out == [high, other]
    assert len(findings) == 1
    assert "duplicate id across merge groups collapsed" in findings[0].description
    # Ties keep the first (sorted/materialization order) deterministically.
    assert _collapse_duplicate_ids([low, dict(low, value="c")], None) == [low]


def test_equivalent_guards_union_once(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0020")
    simple = {
        "value": "16px",
        "when": {"breakpoint": "mobile"},
        "evidence": {"quotes": ["16px"], "unit_ids": [source.unit_id]},
    }
    normalized = {
        "value": "16px",
        "when": {"breakpoint": {"op": "eq", "values": ["mobile"]}},
        "evidence": {"quotes": ["16px"], "unit_ids": [source.unit_id]},
    }
    left = _semantic("sem_a", "body.size", "18px", source, quote="18px", variants=[simple])
    right = _semantic("sem_b", "body.size", "18px", source, quote="18px", variants=[normalized])
    result = reconcile_ensemble(
        [
            _verified("r0", units, semantic=[left]),
            _verified("r1", units, semantic=[right]),
        ],
        units,
        [_label(source.unit_id, "token_semantic")],
    )
    merged = result.tokens_semantic[0]
    assert len(merged["value"]["variants"]) == 1
    guard_hash = stable_hash(normalize_guard(simple["when"]))
    assert merged["extraction_meta"]["field_agreement"][f"value.variants[{guard_hash}]"] == 1.0


def test_scalar_union_counts_missing_and_adds_dissent_only_field(
    units: list[SourceUnit],
) -> None:
    source = _unit(units, "u_brand_foundation_0_0004")
    r0 = _token("tok_r0", "green", "#01A47E", source)
    r1 = _token("tok_r1", "green", "#01A47E", source, dissent_note="present")
    r2 = _token("tok_r2", "green", "#01A47E", source, dissent_note="present")
    result = reconcile_ensemble(
        [
            _verified("r0", units, primitive=[r0]),
            _verified("r1", units, primitive=[r1]),
            _verified("r2", units, primitive=[r2]),
        ],
        units,
        [_label(source.unit_id)],
    )
    merged = result.tokens_primitive[0]
    assert merged["dissent_note"] == "present"
    assert merged["extraction_meta"]["field_agreement"]["dissent_note"] == pytest.approx(2 / 3)


def test_rule_prose_is_champion_verbatim(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0022")

    def rule(run_id: str, text: str) -> dict[str, Any]:
        return {
            "id": f"rule_{run_id}",
            "slug": "headline_style",
            "rule_class": "typography",
            "selector": {"element_path": "headline"},
            "rule_text": text,
            "intent": f"intent {text}",
            "evidence": {
                "quotes": ["sentence case"],
                "unit_ids": [source.unit_id],
            },
        }

    result = reconcile_ensemble(
        [
            _verified("r0", units, rules=[rule("r0", "champion prose")]),
            _verified("r1", units, rules=[rule("r1", "dissent prose")]),
            _verified("r2", units, rules=[rule("r2", "dissent prose")]),
        ],
        units,
        [],
    )
    merged = result.rule_groups["grp_test"][0]
    assert merged["rule_text"] == "champion prose"
    assert merged["intent"] == "intent champion prose"


def test_rules_merge_by_effect_signature_across_different_slugs(
    units: list[SourceUnit],
) -> None:
    source = _unit(units, "u_layout_constraints_0_0008")
    quote = source.text.strip()

    def rule(run_id: str, slug: str) -> dict[str, Any]:
        return {
            "id": f"rule_{run_id}",
            "slug": slug,
            "rule_class": "spacing",
            "constraint_type": "binding",
            "effect": [
                {
                    "element_path": "section.padding",
                    "token_id": "tok_spacing",
                }
            ],
            "rule_text": "Use section padding.",
            "effect_evidence": {
                "unit_ids": [source.unit_id],
                "quotes": [quote],
            },
            "evidence": {
                "unit_ids": [source.unit_id],
                "quotes": [quote],
            },
        }

    result = reconcile_ensemble(
        [
            _manual_run(_output("r0", rules=[rule("r0", "section_spacing_rhythm")])),
            _manual_run(
                _output("r1", rules=[rule("r1", "section_padding_vertical_rhythm")])
            ),
        ],
        units,
        [],
    )
    assert len(result.rule_groups["grp_test"]) == 1
    assert any(
        finding.severity == "info"
        and "merged_by_signature" in finding.description
        for finding in result.findings
    )
    assert _rule_signature({"slug": "alpha"}) != _rule_signature({"slug": "beta"})


def test_rule_group_handoff_preserves_doc_ref_and_consensus_relations(
    units: list[SourceUnit],
) -> None:
    shared = {"kind": "depends_on", "from": "rule_a", "to": "rule_b"}
    shared_reordered = {"to": "rule_b", "from": "rule_a", "kind": "depends_on"}
    champion_only = {"kind": "champion_only", "from": "rule_a", "to": "rule_c"}
    consensus = {"kind": "paired_with", "from": "rule_b", "to": "rule_c"}
    dissent = {"kind": "dissent_only", "from": "rule_c", "to": "rule_d"}
    runs = [
        _manual_run(
            _output(
                "r0",
                relations=[shared, champion_only, shared],
                group_id="grp_rel",
                doc_ref="blob[0]",
            )
        ),
        _manual_run(
            _output(
                "r1",
                relations=[shared_reordered, consensus, dissent],
                group_id="grp_rel",
                doc_ref="blob[0]",
            )
        ),
        _manual_run(
            _output(
                "r2",
                relations=[shared, consensus],
                group_id="grp_rel",
                doc_ref="blob[0]",
            )
        ),
    ]
    result = reconcile_ensemble(runs, units, [])
    assert result.champion_run == "r0"
    assert result.rule_group_doc_refs == {"grp_rel": "blob[0]"}
    relation_keys = [
        json.dumps(relation, sort_keys=True, separators=(",", ":"))
        for relation in result.relations_by_group["grp_rel"]
    ]
    assert relation_keys == sorted(
        [
            json.dumps(shared, sort_keys=True, separators=(",", ":")),
            json.dumps(champion_only, sort_keys=True, separators=(",", ":")),
            json.dumps(consensus, sort_keys=True, separators=(",", ":")),
        ]
    )
    assert all("support" not in relation for relation in result.relations_by_group["grp_rel"])

    baseline = result.model_dump(mode="json")
    for ordering in itertools.permutations(runs):
        assert reconcile_ensemble(ordering, units, []).model_dump(mode="json") == baseline


def test_rule_group_doc_ref_conflict_is_typed(units: list[SourceUnit]) -> None:
    relation = {"kind": "depends_on", "from": "a", "to": "b"}
    left = _manual_run(
        _output(
            "r0",
            relations=[relation],
            group_id="grp_conflict",
            doc_ref="left[0]",
        )
    )
    right = _manual_run(
        _output(
            "r1",
            relations=[relation],
            group_id="grp_conflict",
            doc_ref="right[0]",
        )
    )
    with pytest.raises(
        RuleGroupMappingError,
        match=r"grp_conflict.*left\[0\].*right\[0\]",
    ):
        reconcile_ensemble([left, right], units, [])


def test_candidate_set_from_ensemble_uses_result_doc_refs(
    units: list[SourceUnit],
    labels: list[UnitLabel],
) -> None:
    result = reconcile_ensemble(_fixture_runs(units), units, labels)
    candidates = CandidateSet.from_ensemble(result)
    assert candidates.rule_group_doc_refs == {
        group_id: result.rule_group_doc_refs[group_id]
        for group_id in sorted(result.rule_groups)
    }
    assert candidates.rules_by_doc_ref == result.rule_groups


def test_champion_coverage_excludes_quarantined_claims(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0004")
    bad = _token("bad", "green", "#01A47E", source)
    good = _token("good", "green", "#01A47E", source)
    r0 = _manual_run(
        _output("r0", primitive=[bad]),
        by_unit={source.unit_id: ["bad"]},
        quarantine=[
            QuarantineEntry(entity_id="bad", entity_kind="token_primitive", reason="bad")
        ],
    )
    r1 = _manual_run(
        _output("r1", primitive=[good]),
        by_unit={source.unit_id: ["good"]},
    )
    result = reconcile_ensemble([r0, r1], units, [_label(source.unit_id)])
    assert result.champion_run == "r1"


def test_champion_value_rate_includes_rules(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0042")

    def rule(entity_id: str) -> dict[str, Any]:
        text = "Ask your doctor about treatment options appropriate for you."
        return {
            "id": entity_id,
            "rule_class": "governance",
            "selector": {"element_path": "disclosure"},
            "governance": {
                "preferred_form": text,
                "preferred_form_evidence": {
                    "quotes": [text],
                    "unit_ids": [source.unit_id],
                },
            },
            "evidence": {"quotes": [text], "unit_ids": [source.unit_id]},
        }

    r0_rule = rule("rule_r0")
    r1_rule = rule("rule_r1")
    r0 = _manual_run(
        _output("r0", rules=[r0_rule]),
        records={"rule_r0": [_record("rule_r0", "governance.preferred_form", "unverified")]},
    )
    r1 = _manual_run(
        _output("r1", rules=[r1_rule]),
        records={"rule_r1": [_record("rule_r1", "governance.preferred_form", "value_verified")]},
    )
    result = reconcile_ensemble([r0, r1], units, [])
    assert result.champion_run == "r1"
    assert result.rule_groups["grp_test"][0]["id"] == "rule_r1"


def test_semantic_conflict_keeps_exactly_champion_default_group(
    units: list[SourceUnit],
) -> None:
    source = _unit(units, "u_brand_foundation_0_0020")
    r0 = [
        _semantic("sem_a", "body.size", "18px", source, quote="18px"),
        _semantic("sem_b", "body.size", "16px", source, quote="16px"),
    ]
    r1 = [_semantic("sem_r1", "body.size", "18px", source, quote="18px")]
    r2 = [_semantic("sem_r2", "body.size", "16px", source, quote="16px")]
    result = reconcile_ensemble(
        [
            _verified("r0", units, semantic=r0),
            _verified("r1", units, semantic=r1),
            _verified("r2", units, semantic=r2),
        ],
        units,
        [_label(source.unit_id, "token_semantic")],
    )
    assert len(result.tokens_semantic) == 1
    assert result.tokens_semantic[0]["id"] == "sem_a"
    assert result.tokens_semantic[0]["value"]["default"] == "18px"
    assert result.tokens_semantic[0]["extraction_meta"]["support"] == 2
    assert any(conflict.kind == "intra_token" for conflict in result.conflicts)


def test_run_ids_must_be_unique_and_nonempty(units: list[SourceUnit]) -> None:
    empty = _manual_run(_output(""))
    with pytest.raises(ValueError, match="non-empty run_ids"):
        reconcile_ensemble([empty], units, [])
    duplicate = _manual_run(_output("r0"))
    with pytest.raises(ValueError, match="duplicate run_ids: r0"):
        reconcile_ensemble([duplicate, copy.deepcopy(duplicate)], units, [])


def test_reconcile_does_not_mutate_inputs(
    units: list[SourceUnit],
    labels: list[UnitLabel],
) -> None:
    runs = _fixture_runs(units)
    before = [run.model_dump(mode="json") for run in runs]
    reconcile_ensemble(runs, units, labels)
    assert [run.model_dump(mode="json") for run in runs] == before


def test_run_order_permutation_invariant(
    units: list[SourceUnit],
    labels: list[UnitLabel],
) -> None:
    runs = _fixture_runs(units)
    baseline = reconcile_ensemble(runs, units, labels).model_dump(mode="json")
    for ordering in itertools.permutations(runs):
        assert reconcile_ensemble(ordering, units, labels).model_dump(mode="json") == baseline


def test_final_s3_quarantine_is_not_an_active_candidate(units: list[SourceUnit]) -> None:
    source = _unit(units, "u_brand_foundation_0_0004")
    bad0 = {
        "id": "bad0",
        "key": "color.bad",
        "token_type": "color",
        "value": {"default": "#01A47E", "variants": None},
    }
    bad1 = {**bad0, "id": "bad1"}
    r0 = _manual_run(
        _output("r0", primitive=[bad0]),
        records={"bad0": [_record("bad0", "value.default", "value_verified")]},
    )
    r1 = _manual_run(
        _output("r1", primitive=[bad1]),
        records={"bad1": [_record("bad1", "value.default", "value_verified")]},
    )
    result = reconcile_ensemble([r0, r1], units, [_label(source.unit_id)])
    assert result.tokens_primitive == []
    assert [entry.entity_id for entry in result.provenance.quarantine] == ["bad0"]


def test_write_candidates_deterministic_and_stale_safe(
    units: list[SourceUnit],
    labels: list[UnitLabel],
    tmp_path: Path,
) -> None:
    result = reconcile_ensemble(_fixture_runs(units), units, labels)
    work_dir = tmp_path / "work"
    write_candidates(result, work_dir)
    first = (work_dir / "candidates" / "tokens.json").read_bytes()
    stale = work_dir / "candidates" / "stale.json"
    stale.write_text("{}", encoding="utf-8")
    stale_rule = work_dir / "candidates" / "rules" / "stale.json"
    stale_rule.parent.mkdir(parents=True, exist_ok=True)
    stale_rule.write_text("[]", encoding="utf-8")
    write_candidates(result, work_dir)
    assert (work_dir / "candidates" / "tokens.json").read_bytes() == first
    assert not stale.exists()
    assert not stale_rule.exists()
