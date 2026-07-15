"""WP-11 S6 coverage ledger, triage, and gap loop tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from indexing_v2.consistency.pairwise import PairwiseAnalysisResult
from indexing_v2.consistency.smt import (
    GlobalUnsatConflict,
    SmtAnalysisResult,
)
from indexing_v2.contracts import (
    Conflict,
    Disposition,
    Finding,
    RunVariant,
    SourceUnit,
    TriageItem,
    UnitLabel,
    read_jsonl,
    stable_hash,
)
from indexing_v2.extraction.critic import (
    CandidateSet,
    CriticResult,
    triage_findings,
)
from indexing_v2.extraction.ensemble import (
    EnsembleResult,
    SemanticResolutionError,
    build_token_catalog,
    build_verified_run,
    reconcile_ensemble,
    semantic_match_key,
)
from indexing_v2.extraction.ledger import (
    CandidatesBundle,
    CandidatesBundleAdapterError,
    CriticEntityPatcher,
    GapLoopInputError,
    GapPatchPayload,
    GapPayloadError,
    LedgerDocument,
    _normalize_full_blob_payload,
    _parse_gap_payload,
    _to_critic_candidates,
    append_triage_items,
    build_ledger,
    catalog_summary_text,
    compute_s9_triage_items,
    compute_triage_items,
    current_class_a_conflict_keys,
    load_triage_history,
    rebuild_triage,
    run_gap_loop,
    triage_key_global_unsat,
    triage_key_unclaimed,
    write_ledger,
    write_triage_snapshot,
)
from indexing_v2.extraction.prompts import load_prompt
from indexing_v2.extraction.provenance import ProvenanceResult, verify_entities
from indexing_v2.extraction.runner import (
    RuleGroupOutput,
    RunOutput,
    _group_id,
)
from shared.llm import Usage
from tests.fakes import FIXTURE_ROOT, FakeLLM, MINIBIBLE_BRAND

FIXTURE_LLM_ROOT = FIXTURE_ROOT / "llm"


@pytest.fixture
def units() -> list[SourceUnit]:
    return read_jsonl(FIXTURE_ROOT / "expected" / "units.jsonl", SourceUnit)


@pytest.fixture
def labels() -> list[UnitLabel]:
    return read_jsonl(FIXTURE_ROOT / "expected" / "labels.jsonl", UnitLabel)


@pytest.fixture
def units_by_id(units: list[SourceUnit]) -> dict[str, SourceUnit]:
    return {unit.unit_id: unit for unit in units}


@pytest.fixture
def labels_by_id(labels: list[UnitLabel]) -> dict[str, UnitLabel]:
    return {label.unit_id: label for label in labels}


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"fixture {path} must contain an object")
    return raw


def _provenance_for(candidates: CandidatesBundle, units: list[SourceUnit]) -> ProvenanceResult:
    return verify_entities(candidates.entities_by_kind(), units)


def _fixture_candidates(
    units_by_id: dict[str, SourceUnit],
    *,
    run_id: str = "r0",
    include_subhead_token: bool = False,
) -> CandidatesBundle:
    primitives = _load_json(FIXTURE_LLM_ROOT / "tokens_primitive" / f"{run_id}_001.json")["tokens"]
    semantics = _load_json(FIXTURE_LLM_ROOT / "tokens_semantic" / f"{run_id}_001.json")["tokens"]
    catalog = _load_json(FIXTURE_LLM_ROOT / "catalog_rest" / "001.json")
    rules_by_group: dict[str, list[dict[str, Any]]] = {}
    rule_group_doc_refs: dict[str, str] = {}
    for path in sorted((FIXTURE_LLM_ROOT / "rules_cluster").glob("*.json")):
        payload = _load_json(path)
        for rule in payload.get("rules") or []:
            unit_id = str(rule["evidence"]["unit_ids"][0])
            doc_ref = units_by_id[unit_id].doc_ref
            group_id = _group_id(MINIBIBLE_BRAND, doc_ref)
            rules_by_group.setdefault(group_id, []).append(rule)
            rule_group_doc_refs[group_id] = doc_ref

    if include_subhead_token:
        gap_patch = _load_json(FIXTURE_LLM_ROOT / "gap_patch" / "001.json")
        primitives = list(primitives) + list(gap_patch.get("tokens") or [])

    return CandidatesBundle(
        brand=MINIBIBLE_BRAND,
        tokens_primitive=list(primitives),
        tokens_semantic=list(semantics),
        assets=list(catalog.get("assets") or []),
        subtypes=list(catalog.get("subtypes") or []),
        templates=list(catalog.get("templates") or []),
        rules_by_group=rules_by_group,
        rule_group_doc_refs=rule_group_doc_refs,
        units_by_id=dict(units_by_id),
        champion_variant=RunVariant(run_id="r1", model="fake-model", temperature=0.4, replicate=1),
    )


def _cp3_fixture_run_output(
    run_id: str,
    relation: dict[str, Any],
) -> RunOutput:
    primitives = _load_json(
        FIXTURE_LLM_ROOT
        / "tokens_primitive"
        / f"{run_id}_001.json"
    )["tokens"]
    primitives = [
        token
        for token in primitives
        if token["id"] != "tok_minibible_type_subhead_size"
    ]
    semantics = _load_json(
        FIXTURE_LLM_ROOT
        / "tokens_semantic"
        / f"{run_id}_001.json"
    )["tokens"]
    catalog = _load_json(
        FIXTURE_LLM_ROOT / "catalog_rest" / "001.json"
    )
    groups: list[RuleGroupOutput] = []
    rules_by_doc_ref: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(
        (FIXTURE_LLM_ROOT / "rules_cluster").glob("*.json")
    ):
        payload = _load_json(path)
        doc_ref = (
            "brand_foundation[0]"
            if path.name.startswith("brand_foundation")
            else "layout_constraints[0]"
        )
        rules = list(payload["rules"])
        groups.append(
            RuleGroupOutput(
                group_id=_group_id(MINIBIBLE_BRAND, doc_ref),
                doc_ref=doc_ref,
                original_text="",
                rules=rules,
                relations=(
                    [relation]
                    if doc_ref == "layout_constraints[0]"
                    else []
                ),
            )
        )
        rules_by_doc_ref[doc_ref] = rules
    return RunOutput(
        variant=RunVariant(
            run_id=run_id,
            model=f"fake-{run_id}",
        ),
        primitive_tokens=primitives,
        semantic_tokens=semantics,
        catalog_rest=catalog,
        rules_by_doc_ref=rules_by_doc_ref,
        rule_groups=groups,
    )


def test_gap_patch_prompt_renders() -> None:
    template = load_prompt("gap_patch")
    rendered = template.render(
        brand="minibible",
        doc_ref="layout_constraints[0]",
        target_unit_ids='["u_x"]',
        target_expected_yield='["rule"]',
        units="[u_x] (sentence) sample",
        catalog="primitive tokens (0):",
    )
    assert rendered.system
    assert "layout_constraints[0]" in rendered.user
    assert 'TARGET UNIT IDS:\n["u_x"]' in rendered.user
    assert 'TARGET EXPECTED YIELD:\n["rule"]' in rendered.user
    assert "evidence context" in rendered.system
    assert "{brand}" not in rendered.user


def test_stage_boundaries_are_versioned_and_strict() -> None:
    bundle = CandidatesBundle(brand=MINIBIBLE_BRAND)
    assert bundle.schema_version == "2.0"
    with pytest.raises(ValidationError):
        CandidatesBundle.model_validate(
            {"brand": MINIBIBLE_BRAND, "unexpected": True}
        )


def test_candidates_bundle_from_ensemble_round_trips_to_critic(
    labels: list[UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    source = _fixture_candidates(units_by_id)
    group_id = sorted(source.rules_by_group)[0]
    relation = {
        "kind": "supports",
        "from_id": source.rules_by_group[group_id][0]["id"],
        "to_id": source.tokens_primitive[0]["id"],
    }
    ensemble = EnsembleResult(
        champion_run="r1",
        tokens_primitive=list(reversed(source.tokens_primitive)),
        tokens_semantic=list(reversed(source.tokens_semantic)),
        assets=list(reversed(source.assets)),
        subtypes=list(reversed(source.subtypes)),
        templates=list(reversed(source.templates)),
        rule_groups={
            key: list(reversed(rules))
            for key, rules in reversed(
                list(source.rules_by_group.items())
            )
        },
        rule_group_doc_refs=dict(
            reversed(list(source.rule_group_doc_refs.items()))
        ),
        relations_by_group={group_id: [relation]},
        conflicts=list(source.conflicts),
    )
    bundle = CandidatesBundle.from_ensemble(
        ensemble,
        brand=MINIBIBLE_BRAND,
        units=units,
        champion_variant=RunVariant(
            run_id="r1",
            model="fake-model",
        ),
    )
    critic = CandidateSet.from_ensemble(ensemble)
    assert critic.champion_run_id == ensemble.champion_run
    assert critic.rule_group_doc_refs == bundle.rule_group_doc_refs
    assert critic.rules_by_doc_ref == bundle.rules_by_group
    assert bundle.relations_by_group[group_id] == [relation]
    report, _ = build_ledger(
        labels,
        verify_entities(bundle.entities_by_kind(), units),
        bundle,
    )
    assert report.brand == MINIBIBLE_BRAND

    with pytest.raises(
        CandidatesBundleAdapterError,
        match="missing doc_ref mapping",
    ):
        CandidatesBundle.from_ensemble(
            ensemble.model_copy(
                update={"rule_group_doc_refs": {}},
                deep=True,
            ),
            brand=MINIBIBLE_BRAND,
            units=units,
            champion_variant=RunVariant(
                run_id="r1",
                model="fake-model",
            ),
        )


@pytest.mark.asyncio
async def test_cp3_stage_chain_uses_public_critic_handoff(
    labels: list[UnitLabel],
    units: list[SourceUnit],
    tmp_path: Path,
) -> None:
    relation = {
        "kind": "depends_on",
        "from": "rule_minibible_cta_fill_green",
        "to": "rule_minibible_cta_max_one",
    }
    outputs = [
        _cp3_fixture_run_output(run_id, relation)
        for run_id in ("r0", "r1", "r2")
    ]
    ensemble = reconcile_ensemble(
        [
            build_verified_run(output, units)
            for output in outputs
        ],
        units,
        labels,
    )
    source = CandidatesBundle.from_ensemble(
        ensemble,
        brand=MINIBIBLE_BRAND,
        units=units,
        champion_variant=RunVariant(
            run_id=ensemble.champion_run,
            model="fake-champion",
        ),
    )
    critic_input = CandidateSet.from_ensemble(ensemble)
    finding = Finding.model_validate(
        _load_json(
            FIXTURE_LLM_ROOT / "critic_catalog" / "001.json"
        )["findings"][0]
    )
    patched, findings, audit = triage_findings(
        [finding],
        critic_input,
        units,
        round_num=1,
    )
    critic_result = CriticResult(
        candidates=patched,
        findings=findings,
        audit=audit,
        rounds_completed=1,
    )
    assert findings[0].resolution == "applied"

    after_critic = source.with_critic_candidates(
        critic_result.candidates
    )
    critic_token_id = "tok_minibible_type_subhead_size"
    assert critic_token_id in {
        token["id"] for token in after_critic.tokens_primitive
    }
    assert (
        after_critic.champion_variant
        == source.champion_variant
    )
    assert (
        after_critic.rule_group_doc_refs
        == ensemble.rule_group_doc_refs
    )
    assert (
        after_critic.relations_by_group
        == ensemble.relations_by_group
    )

    target_label = next(
        label
        for label in labels
        if label.unit_id == "u_brand_foundation_0_0024"
    )
    gap_result = await run_gap_loop(
        [target_label],
        after_critic,
        verify_entities(after_critic.entities_by_kind(), units),
        units=units,
        client=GapFakeLLM(
            fixture_root=FIXTURE_LLM_ROOT,
            brand=MINIBIBLE_BRAND,
        ),
        usage=Usage(),
        cache_root=tmp_path / "cache",
        max_rounds=1,
    )
    row = gap_result.coverage.rows[0]
    assert row.status == "covered"
    assert critic_token_id in row.claimed_by
    assert critic_token_id in gap_result.provenance.records_by_entity
    assert (
        gap_result.candidates.relations_by_group
        == ensemble.relations_by_group
    )

    unknown_mapping = critic_result.candidates.model_copy(
        update={
            "rule_group_doc_refs": {
                **critic_result.candidates.rule_group_doc_refs,
                "grp_unknown": "layout_constraints[0]",
            }
        },
        deep=True,
    )
    with pytest.raises(
        CandidatesBundleAdapterError,
        match="unknown patched group",
    ):
        source.with_critic_candidates(unknown_mapping)


def test_to_critic_candidates_preserves_empty_rule_groups(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    source = _fixture_candidates(units_by_id)
    empty_group = "grp_minibible_emptied_00"
    source.rules_by_group[empty_group] = []
    source.rule_group_doc_refs[empty_group] = "brand_foundation[0]"

    critic = _to_critic_candidates(source)

    assert empty_group in critic.rules_by_doc_ref
    assert critic.rules_by_doc_ref[empty_group] == []
    assert critic.rule_group_doc_refs[empty_group] == "brand_foundation[0]"
    round_tripped = source.with_critic_candidates(critic)
    assert empty_group in round_tripped.rules_by_group
    assert round_tripped.rules_by_group[empty_group] == []
    assert (
        round_tripped.rule_group_doc_refs[empty_group]
        == "brand_foundation[0]"
    )


def _over_claimed_fixture(
    units_by_id: dict[str, SourceUnit],
    unit_id: str,
) -> tuple[CandidatesBundle, ProvenanceResult]:
    unit = units_by_id[unit_id]
    candidates = _fixture_candidates(units_by_id)
    quote = unit.text.strip()[:30]
    rule_a = {
        "id": "rule_test_over_a",
        "rule_class": "layout",
        "selector": {"element_path": "cta"},
        "effect": {"value": "a"},
        "evidence": {"unit_ids": [unit_id], "quotes": [quote]},
    }
    rule_b = {
        "id": "rule_test_over_b",
        "rule_class": "layout",
        "selector": {"element_path": "cta"},
        "effect": {"value": "b"},
        "evidence": {"unit_ids": [unit_id], "quotes": [quote]},
    }
    candidates.rules_by_group["_over_claimed"] = [rule_a, rule_b]
    provenance = verify_entities(candidates.entities_by_kind(), list(units_by_id.values()))
    return candidates, provenance


def _kind_mismatch_fixture(
    units_by_id: dict[str, SourceUnit],
) -> tuple[CandidatesBundle, ProvenanceResult]:
    unit_id = "u_brand_foundation_0_0004"
    quote = "#01A47E"
    candidates = _fixture_candidates(units_by_id)
    candidates.rules_by_group["_kind_mismatch"] = [
        {
            "id": "rule_minibible_kind_mismatch",
            "rule_class": "color",
            "selector": {"element_path": "color.primary"},
            "effect": {"value": quote},
            "evidence": {"unit_ids": [unit_id], "quotes": [quote]},
        }
    ]
    provenance = verify_entities(candidates.entities_by_kind(), list(units_by_id.values()))
    return candidates, provenance


def test_build_ledger_fixture_plants(
    labels: list[UnitLabel],
    labels_by_id: dict[str, UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    candidates = _fixture_candidates(units_by_id, include_subhead_token=False)
    provenance = _provenance_for(candidates, units)
    report, _soft = build_ledger(labels, provenance, candidates)

    excluded = next(row for row in report.rows if row.unit_id == "u_brand_foundation_0_0046")
    assert excluded.status == "excluded"
    assert not excluded.required

    unclaimed = next(row for row in report.rows if row.unit_id == "u_layout_constraints_0_0014")
    assert unclaimed.status == "unclaimed"
    assert "normative" in labels_by_id["u_layout_constraints_0_0014"].labels

    over_candidates, over_prov = _over_claimed_fixture(
        units_by_id,
        "u_layout_constraints_0_0008",
    )
    over_report, _ = build_ledger(labels, over_prov, over_candidates)
    over_row = next(row for row in over_report.rows if row.unit_id == "u_layout_constraints_0_0008")
    assert over_row.status == "over_claimed"

    kind_candidates, kind_prov = _kind_mismatch_fixture(units_by_id)
    kind_report, kind_soft = build_ledger(labels, kind_prov, kind_candidates)
    value_row = next(
        row for row in kind_report.rows if row.unit_id == "u_brand_foundation_0_0004"
    )
    assert value_row.status == "covered"
    assert kind_soft
    assert kind_soft[0].entity_kind == "rule"
    assert "token_primitive" in kind_soft[0].expected_yield

    orphan_candidates = _fixture_candidates(units_by_id)
    orphan_candidates.tokens_primitive.append(
        {
            "id": "tok_minibible_spacing_phantom_99",
            "token_type": "margin",
            "key": "spacing.phantom",
            "value": {"default": "99px", "variants": None},
            "evidence": {"unit_ids": ["u_layout_constraints_0_0014"], "quotes": ["phantom"]},
        }
    )
    orphan_prov = verify_entities(orphan_candidates.entities_by_kind(), units)
    orphan_report, _ = build_ledger(labels, orphan_prov, orphan_candidates)
    assert "tok_minibible_spacing_phantom_99" in orphan_report.orphan_entity_ids


def test_triage_content_hash_invalidation(tmp_path: Path, units_by_id: dict[str, SourceUnit]) -> None:
    labels = read_jsonl(FIXTURE_ROOT / "expected" / "labels.jsonl", UnitLabel)
    unit = units_by_id["u_layout_constraints_0_0014"]
    key = triage_key_unclaimed(unit.doc_ref, unit.text)
    triage_path = tmp_path / "review" / "triage.jsonl"
    triage_path.parent.mkdir(parents=True)
    waived = TriageItem(
        queue="unclaimed_unit",
        key=key,
        subject_id=unit.unit_id,
        context="old",
        disposition=Disposition(
            status="waived",
            reason="accepted_risk",
            note="ok",
        ),
    )
    triage_path.write_text(
        json.dumps(waived.model_dump(mode="json"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert load_triage_history(triage_path)[0].disposition.status == "waived"

    changed_units = dict(units_by_id)
    changed_units[unit.unit_id] = unit.model_copy(update={"text": unit.text + " extra"})
    candidates = _fixture_candidates(changed_units, include_subhead_token=False)
    provenance = _provenance_for(candidates, list(changed_units.values()))
    report, _ = build_ledger(labels, provenance, candidates)
    computed = compute_triage_items(
        report,
        labels_by_id={label.unit_id: label for label in labels},
        candidates=candidates,
        provenance=provenance,
    )
    merged, to_append = rebuild_triage(computed, load_triage_history(triage_path))
    item = next(row for row in merged if row.subject_id == unit.unit_id)
    assert item.key != key
    assert item.disposition.status == "open"
    assert to_append


def test_triage_latest_disposition_wins(tmp_path: Path, units_by_id: dict[str, SourceUnit]) -> None:
    labels = read_jsonl(FIXTURE_ROOT / "expected" / "labels.jsonl", UnitLabel)
    unit = units_by_id["u_layout_constraints_0_0014"]
    key = triage_key_unclaimed(unit.doc_ref, unit.text)
    triage_path = tmp_path / "review" / "triage.jsonl"
    append_triage_items(
        triage_path,
        [
            TriageItem(
                queue="unclaimed_unit",
                key=key,
                subject_id=unit.unit_id,
                context="first",
            )
        ],
    )
    # ponytail: waived/deferred are human-authored; seed directly for history replay test.
    waived = TriageItem(
        queue="unclaimed_unit",
        key=key,
        subject_id=unit.unit_id,
        context="second",
        disposition=Disposition(status="waived", reason="duplicate", note="seen"),
    )
    with triage_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(waived.model_dump(mode="json"), sort_keys=True) + "\n")
    candidates = _fixture_candidates(units_by_id, include_subhead_token=False)
    provenance = _provenance_for(candidates, list(units_by_id.values()))
    report, _ = build_ledger(labels, provenance, candidates)
    computed = compute_triage_items(
        report,
        labels_by_id={label.unit_id: label for label in labels},
        candidates=candidates,
        provenance=provenance,
    )
    merged, _ = rebuild_triage(computed, load_triage_history(triage_path))
    item = next(row for row in merged if row.key == key)
    assert item.disposition.status == "waived"
    assert item.disposition.note == "seen"


def test_quarantined_semantic_still_enters_unverified_queue(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    entity_id = "tok_minibible_sem_unquotable"
    candidates = CandidatesBundle(
        brand=MINIBIBLE_BRAND,
        tokens_semantic=[
            {
                "id": entity_id,
                "key": "cta.button.unquotable",
                "token_type": "color",
                "value": {
                    "default": "#DEAD00",
                    "default_evidence": {
                        "unit_ids": ["u_brand_foundation_0_0004"],
                        "quotes": ["not in source"],
                    },
                    "variants": None,
                },
                "evidence": {
                    "unit_ids": ["u_brand_foundation_0_0004"],
                    "quotes": ["not in source"],
                },
            }
        ],
        units_by_id=units_by_id,
    )
    provenance = verify_entities(candidates.entities_by_kind(), units)
    assert entity_id in {entry.entity_id for entry in provenance.quarantine}
    report, _ = build_ledger([], provenance, candidates)
    items = compute_triage_items(
        report,
        labels_by_id={},
        candidates=candidates,
        provenance=provenance,
    )
    item = next(row for row in items if row.subject_id == entity_id)
    assert item.queue == "unverified_value"


def _ref_token(
    entity_id: str,
    key: str,
    default: Any,
    unit: SourceUnit,
) -> dict[str, Any]:
    return {
        "id": entity_id,
        "key": key,
        "token_type": "dimension",
        "value": {
            "default": default,
            "default_evidence": {
                "unit_ids": [unit.unit_id],
                "quotes": ["16px"],
            },
            "variants": None,
        },
        "evidence": {
            "unit_ids": [unit.unit_id],
            "quotes": ["16px"],
        },
    }


def test_semantic_triage_key_matches_public_helper_for_nested_refs(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    unit = units_by_id["u_brand_foundation_0_0020"]
    primitive = _ref_token(
        "tok_ref_primitive",
        "size.base",
        "16px",
        unit,
    )
    alias = _ref_token(
        "tok_ref_alias",
        "size.alias",
        {"$ref": primitive["id"]},
        unit,
    )
    nested = _ref_token(
        "tok_ref_nested",
        "body.text.size",
        {"$ref": alias["id"]},
        unit,
    )
    candidates = CandidatesBundle(
        brand=MINIBIBLE_BRAND,
        tokens_primitive=[primitive],
        tokens_semantic=[alias, nested],
        units_by_id=units_by_id,
    )
    provenance = verify_entities(
        candidates.entities_by_kind(),
        units,
    )
    report, _ = build_ledger([], provenance, candidates)
    items = compute_triage_items(
        report,
        labels_by_id={},
        candidates=candidates,
        provenance=provenance,
    )
    catalog = build_token_catalog(
        RunOutput(
            variant=RunVariant(run_id="r0", model="fake-model"),
            primitive_tokens=[primitive],
            semantic_tokens=[alias, nested],
        )
    )
    expected_key = stable_hash(semantic_match_key(nested, catalog))
    nested_item = next(
        item for item in items if item.subject_id == nested["id"]
    )
    assert nested_item.key == expected_key


@pytest.mark.parametrize("cyclic", [False, True])
def test_semantic_triage_preserves_typed_ref_errors(
    cyclic: bool,
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    unit = units_by_id["u_brand_foundation_0_0020"]
    first = _ref_token(
        "tok_ref_a",
        "body.text.a",
        {"$ref": "tok_ref_b"},
        unit,
    )
    semantics = [first]
    if cyclic:
        semantics.append(
            _ref_token(
                "tok_ref_b",
                "body.text.b",
                {"$ref": "tok_ref_a"},
                unit,
            )
        )
    candidates = CandidatesBundle(
        brand=MINIBIBLE_BRAND,
        tokens_semantic=semantics,
        units_by_id=units_by_id,
    )
    provenance = verify_entities(
        candidates.entities_by_kind(),
        units,
    )
    report, _ = build_ledger([], provenance, candidates)
    expected = "cyclic" if cyclic else "missing"
    with pytest.raises(SemanticResolutionError, match=expected):
        compute_triage_items(
            report,
            labels_by_id={},
            candidates=candidates,
            provenance=provenance,
        )


def test_unquotable_gap_products_do_not_mutate_candidates(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    candidates = _fixture_candidates(units_by_id, include_subhead_token=False)
    before = candidates.model_dump(mode="json")
    patcher = CriticEntityPatcher()

    corrupt_token = _load_json(
        FIXTURE_LLM_ROOT / "corrupt_bad_quote" / "001.json"
    )["tokens"][0]
    after_token, _ = patcher.apply_gap_payload(
        GapPatchPayload(tokens=[corrupt_token]),
        candidates,
        units=units,
        doc_ref="layout_constraints[0]",
        gap_round=1,
        target_expected_yield={"token_primitive"},
    )
    assert after_token.model_dump(mode="json") == before

    corrupt_rule = {
        "id": "rule_minibible_unquotable_gap",
        "rule_class": "layout",
        "selector": {"element_path": "cta.button"},
        "effect": {"value": "invented"},
        "evidence": {
            "unit_ids": ["u_layout_constraints_0_0014"],
            "quotes": ["not in source"],
        },
    }
    after_rule, _ = patcher.apply_gap_payload(
        GapPatchPayload(rules=[corrupt_rule]),
        candidates,
        units=units,
        doc_ref="layout_constraints[0]",
        gap_round=1,
        target_expected_yield={"rule"},
    )
    assert after_rule.model_dump(mode="json") == before


def test_legacy_rule_group_rejects_ambiguous_doc_refs(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    candidates = CandidatesBundle(
        brand=MINIBIBLE_BRAND,
        rules_by_group={
            "legacy_group": [
                {
                    "id": "rule_legacy_a",
                    "evidence": {
                        "unit_ids": ["u_brand_foundation_0_0004"],
                        "quotes": ["#01A47E"],
                    },
                },
                {
                    "id": "rule_legacy_b",
                    "evidence": {
                        "unit_ids": ["u_layout_constraints_0_0014"],
                        "quotes": ["12px"],
                    },
                },
            ]
        },
        units_by_id=units_by_id,
    )
    with pytest.raises(
        CandidatesBundleAdapterError,
        match="ambiguous source doc_refs",
    ):
        CriticEntityPatcher().apply_gap_payload(
            GapPatchPayload(),
            candidates,
            units=units,
            doc_ref="brand_foundation[0]",
            gap_round=1,
            target_expected_yield={"rule"},
        )


def test_gap_payload_validation_is_strict() -> None:
    with pytest.raises(GapPayloadError, match="invalid gap response"):
        _parse_gap_payload({"tokens": "not-a-list", "rules": []})
    with pytest.raises(GapPayloadError, match="non-empty string id"):
        _parse_gap_payload({"tokens": [{}], "rules": []})
    with pytest.raises(GapPayloadError, match="entity_kind"):
        _parse_gap_payload(
            {
                "tokens": [
                    {
                        "id": "tok_bad_kind",
                        "entity_kind": "semantic",
                    }
                ]
            }
        )


def test_full_blob_payload_assigns_rule_ids_and_maps_relations(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    candidates = _fixture_candidates(units_by_id)
    doc_ref = "layout_constraints[0]"
    group_id = _group_id(MINIBIBLE_BRAND, doc_ref)
    normalized = _normalize_full_blob_payload(
        {
            "rules": [
                {
                    "slug": "content-contrast",
                    "rule_text": "Maintain sufficient content contrast.",
                }
            ],
            "relations": [
                {
                    "src_slug": "content-contrast",
                    "dst_slug": "content-contrast",
                    "relation": "depends_on",
                }
            ],
        },
        brand=MINIBIBLE_BRAND,
        doc_ref=doc_ref,
        group_id=group_id,
        blob_units=[unit for unit in units if unit.doc_ref == doc_ref],
        candidates=candidates,
    )

    payload = _parse_gap_payload(normalized)

    assert payload.rules[0]["id"] == "rule_minibible_content_contrast"
    assert payload.relations[0]["src_rule_id"] == payload.rules[0]["id"]
    assert payload.relations[0]["dst_rule_id"] == payload.rules[0]["id"]


def test_gap_token_kind_is_explicit_for_new_semantics(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    candidates = _fixture_candidates(units_by_id)
    semantic = dict(
        _load_json(FIXTURE_LLM_ROOT / "tokens_semantic" / "r0_001.json")[
            "tokens"
        ][0]
    )
    semantic["id"] = "tok_minibible_binding_cta"
    semantic["entity_kind"] = "token_semantic"
    patched, _ = CriticEntityPatcher().apply_gap_payload(
        GapPatchPayload(tokens=[semantic]),
        candidates,
        units=units,
        doc_ref="layout_constraints[0]",
        gap_round=1,
        target_expected_yield={"token_semantic"},
    )
    assert semantic["id"] in {
        token["id"] for token in patched.tokens_semantic
    }
    assert semantic["id"] not in {
        token["id"] for token in patched.tokens_primitive
    }

    ambiguous = _load_json(
        FIXTURE_LLM_ROOT / "gap_patch" / "001.json"
    )["tokens"][0]
    ambiguous["id"] = "tok_minibible_ambiguous_new"
    ambiguous.pop("entity_kind", None)
    with pytest.raises(GapPayloadError, match="requires explicit entity_kind"):
        CriticEntityPatcher().apply_gap_payload(
            GapPatchPayload(tokens=[ambiguous]),
            candidates,
            units=units,
            doc_ref="layout_constraints[0]",
            gap_round=1,
            target_expected_yield={
                "token_primitive",
                "token_semantic",
            },
        )


def test_full_replacement_empty_rules_deletes_blob_rules(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    doc_ref = "layout_constraints[0]"
    candidates = _fixture_candidates(units_by_id)
    before = {
        rule["id"]
        for rule in candidates.entities_by_kind()["rule"]
        if any(
            units_by_id[unit_id].doc_ref == doc_ref
            for unit_id in rule["evidence"]["unit_ids"]
        )
    }
    assert before
    patched, _ = CriticEntityPatcher().apply_gap_payload(
        GapPatchPayload(),
        candidates,
        units=units,
        doc_ref=doc_ref,
        gap_round=1,
        target_expected_yield={"rule"},
        replace_rules=True,
    )
    assert before.isdisjoint(
        {
            rule["id"]
            for rule in patched.entities_by_kind()["rule"]
        }
    )


def test_new_rules_and_relations_use_runner_group_id(
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    doc_ref = "layout_constraints[0]"
    candidates = _fixture_candidates(units_by_id)
    rule = dict(
        _load_json(
            FIXTURE_LLM_ROOT
            / "rules_cluster"
            / "layout_constraints_001.json"
        )["rules"][0]
    )
    rule["id"] = "rule_minibible_gap_group_mapping"
    rule["selector"] = {"element_path": "gap.group.mapping"}
    relation = {
        "kind": "supports",
        "from_id": rule["id"],
        "to_id": "tok_minibible_color_primary_green_01",
    }
    patched, _ = CriticEntityPatcher().apply_gap_payload(
        GapPatchPayload(rules=[rule], relations=[relation]),
        candidates,
        units=units,
        doc_ref=doc_ref,
        gap_round=1,
        target_expected_yield={"rule"},
    )
    group_id = _group_id(MINIBIBLE_BRAND, doc_ref)
    assert rule["id"] in {
        row["id"] for row in patched.rules_by_group[group_id]
    }
    assert doc_ref not in patched.rules_by_group
    assert patched.relations_by_group[group_id] == [relation]


class GapFakeLLM(FakeLLM):
    """Reuse canned fixtures for multi-blob / multi-round gap loop tests."""

    def _resolve_path(self, prompt_name: str, cache_key, seq: int):  # type: ignore[no-untyped-def]
        if prompt_name == "gap_patch":
            return self.fixture_root / "gap_patch" / "001.json"
        if prompt_name == "rules_cluster":
            ordered = sorted((self.fixture_root / "rules_cluster").glob("*.json"))
            if ordered:
                return ordered[min(max(seq, 1) - 1, len(ordered) - 1)]
        return super()._resolve_path(prompt_name, cache_key, seq)


class StalledPatcher(CriticEntityPatcher):
    def apply_gap_payload(  # type: ignore[no-untyped-def]
        self,
        payload,
        candidates,
        *,
        units,
        doc_ref,
        gap_round,
        target_expected_yield,
        replace_rules=False,
    ):
        del payload, doc_ref, gap_round, target_expected_yield, replace_rules
        return candidates, verify_entities(candidates.entities_by_kind(), units)


@pytest.mark.asyncio
async def test_gap_loop_drains_unclaimed_in_two_rounds(
    labels: list[UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
    tmp_path: Path,
) -> None:
    candidates = _fixture_candidates(units_by_id, include_subhead_token=False)
    provenance = _provenance_for(candidates, units)
    assert "u_layout_constraints_0_0014" in build_ledger(labels, provenance, candidates)[0].unclaimed_unit_ids

    llm = GapFakeLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND)
    result = await run_gap_loop(
        labels,
        candidates,
        provenance,
        units=units,
        client=llm,
        usage=Usage(),
        work_dir=tmp_path / "work",
        triage_path=tmp_path / "review" / "triage.jsonl",
        cache_root=tmp_path / "cache",
        max_rounds=2,
    )
    assert result.rounds_run <= 2
    assert "u_layout_constraints_0_0014" not in result.coverage.unclaimed_unit_ids
    assert any(call.prompt_name == "gap_patch" for call in llm.calls())
    added_id = "tok_minibible_spacing_subhead_margin"
    assert added_id in {
        token["id"] for token in result.candidates.tokens_primitive
    }
    assert (
        result.candidates.rule_group_doc_refs
        == candidates.rule_group_doc_refs
    )
    assert (
        set(result.candidates.rules_by_group)
        == set(candidates.rules_by_group)
    )
    assert any(
        record.verification in {"span_verified", "value_verified"}
        and any(
            "u_layout_constraints_0_0014" in span.unit_ids
            for span in record.spans
        )
        for record in result.provenance.records_by_entity[added_id]
    )


@pytest.mark.asyncio
async def test_gap_loop_preserves_relations_in_handoff(
    labels_by_id: dict[str, UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "llm"
    (fixture_root / "gap_patch").mkdir(parents=True)
    payload = _load_json(FIXTURE_LLM_ROOT / "gap_patch" / "001.json")
    relation = {
        "kind": "supports",
        "from_id": "tok_minibible_spacing_subhead_margin",
        "to_id": "rule_minibible_cta_max_one",
    }
    payload["relations"] = [relation]
    (fixture_root / "gap_patch" / "001.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    candidates = _fixture_candidates(
        units_by_id,
        include_subhead_token=False,
    )
    result = await run_gap_loop(
        [labels_by_id["u_layout_constraints_0_0014"]],
        candidates,
        _provenance_for(candidates, units),
        units=units,
        client=GapFakeLLM(
            fixture_root=fixture_root,
            brand=MINIBIBLE_BRAND,
        ),
        usage=Usage(),
        cache_root=tmp_path / "cache",
        max_rounds=1,
    )
    group_id = _group_id(MINIBIBLE_BRAND, "layout_constraints[0]")
    assert result.candidates.relations_by_group[group_id] == [relation]


@pytest.mark.asyncio
async def test_gap_loop_zero_progress_terminates(
    labels: list[UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
    tmp_path: Path,
) -> None:
    candidates = _fixture_candidates(units_by_id, include_subhead_token=False)
    provenance = _provenance_for(candidates, units)
    llm = GapFakeLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND)
    result = await run_gap_loop(
        labels,
        candidates,
        provenance,
        units=units,
        client=llm,
        usage=Usage(),
        patcher=StalledPatcher(),
        cache_root=tmp_path / "cache",
        max_rounds=3,
    )
    assert result.stopped_reason == "zero_progress"
    assert result.coverage.unclaimed_unit_ids


@pytest.mark.asyncio
async def test_gap_loop_no_shrink_escalates_to_rules_cluster(
    labels: list[UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
    tmp_path: Path,
) -> None:
    candidates = _fixture_candidates(units_by_id, include_subhead_token=False)
    provenance = _provenance_for(candidates, units)
    llm = GapFakeLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND)
    result = await run_gap_loop(
        labels,
        candidates,
        provenance,
        units=units,
        client=llm,
        usage=Usage(),
        patcher=StalledPatcher(),
        cache_root=tmp_path / "cache",
        max_rounds=2,
    )
    prompt_names = [call.prompt_name for call in llm.calls()]
    assert "gap_patch" in prompt_names
    assert "rules_cluster" in prompt_names
    assert result.rounds_run >= 2


class TwoBlobEscalationPatcher(StalledPatcher):
    def __init__(self) -> None:
        self.full_calls: list[str] = []

    def apply_gap_payload(  # type: ignore[no-untyped-def]
        self,
        payload,
        candidates,
        *,
        units,
        doc_ref,
        gap_round,
        target_expected_yield,
        replace_rules=False,
    ):
        del payload, gap_round, target_expected_yield
        if not replace_rules:
            return candidates, verify_entities(
                candidates.entities_by_kind(),
                units,
            )
        self.full_calls.append(doc_ref)
        updated = candidates.model_copy(deep=True)
        if doc_ref == "doc_a[0]":
            updated.rules_by_group = {
                group_id: [
                    rule
                    for rule in rules
                    if rule.get("id") != "rule_blob_b_initial"
                ]
                for group_id, rules in updated.rules_by_group.items()
            }
        return updated, verify_entities(
            updated.entities_by_kind(),
            units,
        )


@pytest.mark.asyncio
async def test_each_stalled_blob_gets_one_full_reextraction(
    tmp_path: Path,
) -> None:
    units = [
        SourceUnit(
            unit_id="u_blob_a",
            brand_id=MINIBIBLE_BRAND,
            doc_ref="doc_a[0]",
            ordinal=0,
            start=0,
            end=10,
            kind="sentence",
            text="A required.",
        ),
        SourceUnit(
            unit_id="u_blob_b",
            brand_id=MINIBIBLE_BRAND,
            doc_ref="doc_b[0]",
            ordinal=0,
            start=0,
            end=10,
            kind="sentence",
            text="B covered.",
        ),
    ]
    labels = [
        UnitLabel(
            unit_id=unit.unit_id,
            labels=["normative"],
            expected_yield=["rule"],
            required=True,
            heuristic_locked=["normative"],
            confidence=1.0,
        )
        for unit in units
    ]
    candidates = CandidatesBundle(
        brand=MINIBIBLE_BRAND,
        rules_by_group={
            _group_id(MINIBIBLE_BRAND, "doc_b[0]"): [
                {
                    "id": "rule_blob_b_initial",
                    "rule_class": "layout",
                    "selector": {"element_path": "blob.b"},
                    "effect": {"value": "covered"},
                    "evidence": {
                        "unit_ids": ["u_blob_b"],
                        "quotes": ["B covered."],
                    },
                }
            ]
        },
    )
    patcher = TwoBlobEscalationPatcher()
    result = await run_gap_loop(
        labels,
        candidates,
        verify_entities(candidates.entities_by_kind(), units),
        units=units,
        client=GapFakeLLM(
            fixture_root=FIXTURE_LLM_ROOT,
            brand=MINIBIBLE_BRAND,
        ),
        usage=Usage(),
        patcher=patcher,
        cache_root=tmp_path / "cache",
        max_rounds=4,
    )
    assert patcher.full_calls == ["doc_a[0]", "doc_b[0]"]
    assert result.stopped_reason == "zero_progress"


@pytest.mark.asyncio
async def test_gap_loop_populates_authoritative_unit_index(
    labels_by_id: dict[str, UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
    tmp_path: Path,
) -> None:
    unit_id = "u_brand_foundation_0_0004"
    candidates = _fixture_candidates(units_by_id)
    provenance = _provenance_for(candidates, units)
    candidates.units_by_id = {}
    result = await run_gap_loop(
        [labels_by_id[unit_id]],
        candidates,
        provenance,
        units=units,
        client=GapFakeLLM(fixture_root=FIXTURE_LLM_ROOT),
        usage=Usage(),
        cache_root=tmp_path / "cache",
        max_rounds=1,
    )
    assert result.candidates.units_by_id[unit_id].doc_ref == "brand_foundation[0]"
    assert set(result.coverage.per_blob) == {"brand_foundation[0]"}


@pytest.mark.asyncio
async def test_gap_loop_invalidates_stale_provenance(
    labels: list[UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
    tmp_path: Path,
) -> None:
    candidates = _fixture_candidates(units_by_id)
    stale_provenance = _provenance_for(candidates, units)
    stale_report, _ = build_ledger(
        labels,
        stale_provenance,
        candidates,
    )
    covered = next(
        row
        for row in stale_report.rows
        if row.required and row.status == "covered"
    )
    label = next(
        row for row in labels if row.unit_id == covered.unit_id
    )
    changed_unit = units_by_id[covered.unit_id].model_copy(
        update={"text": "Authoritative source text replaced completely."}
    )
    changed_units = [
        changed_unit if unit.unit_id == covered.unit_id else unit
        for unit in units
    ]
    result = await run_gap_loop(
        [label],
        candidates,
        stale_provenance,
        units=changed_units,
        client=GapFakeLLM(
            fixture_root=FIXTURE_LLM_ROOT,
            brand=MINIBIBLE_BRAND,
        ),
        usage=Usage(),
        patcher=StalledPatcher(),
        cache_root=tmp_path / "cache",
        max_rounds=1,
    )
    assert covered.unit_id in result.coverage.unclaimed_unit_ids
    item = next(
        row
        for row in result.triage
        if row.subject_id == covered.unit_id
    )
    assert item.disposition.status == "open"
    assert item.key == triage_key_unclaimed(
        changed_unit.doc_ref,
        changed_unit.text,
    )


@pytest.mark.asyncio
async def test_gap_loop_rejects_invalid_inputs(
    labels_by_id: dict[str, UnitLabel],
    units: list[SourceUnit],
    units_by_id: dict[str, SourceUnit],
) -> None:
    candidates = _fixture_candidates(units_by_id)
    provenance = _provenance_for(candidates, units)
    with pytest.raises(GapLoopInputError, match="max_rounds must be positive"):
        await run_gap_loop(
            [],
            candidates,
            provenance,
            units=units,
            client=GapFakeLLM(fixture_root=FIXTURE_LLM_ROOT),
            usage=Usage(),
            max_rounds=0,
        )
    with pytest.raises(GapLoopInputError, match="required unit_ids missing"):
        await run_gap_loop(
            [labels_by_id["u_brand_foundation_0_0004"]],
            candidates,
            provenance,
            units=[],
            client=GapFakeLLM(fixture_root=FIXTURE_LLM_ROOT),
            usage=Usage(),
            max_rounds=1,
        )


def test_write_ledger_deterministic_bytes(tmp_path: Path, units_by_id: dict[str, SourceUnit]) -> None:
    labels = read_jsonl(FIXTURE_ROOT / "expected" / "labels.jsonl", UnitLabel)
    candidates = _fixture_candidates(units_by_id)
    provenance = _provenance_for(candidates, list(units_by_id.values()))
    report, soft = build_ledger(labels, provenance, candidates)
    doc = LedgerDocument(coverage=report, soft_mismatches=soft)
    work_dir = tmp_path / "work"
    write_ledger(work_dir, doc)
    first = (work_dir / "ledger.json").read_bytes()
    write_ledger(work_dir, doc)
    second = (work_dir / "ledger.json").read_bytes()
    assert first == second
    assert b"soft_mismatches" in first


def test_catalog_summary_is_compact(units_by_id: dict[str, SourceUnit]) -> None:
    candidates = _fixture_candidates(units_by_id)
    summary = catalog_summary_text(candidates)
    assert "primitive tokens" in summary
    assert "tok_minibible_color_primary_green_01" in summary


def test_catalog_summary_permutation_bytes_and_hash(
    units_by_id: dict[str, SourceUnit],
) -> None:
    original = _fixture_candidates(units_by_id)
    permuted = original.model_copy(deep=True)
    permuted.tokens_primitive.reverse()
    permuted.tokens_semantic.reverse()
    permuted.assets.reverse()
    permuted.subtypes.reverse()
    permuted.templates.reverse()
    permuted.rules_by_group = {
        group_id: list(reversed(rules))
        for group_id, rules in reversed(list(permuted.rules_by_group.items()))
    }
    first = catalog_summary_text(original).encode()
    second = catalog_summary_text(permuted).encode()
    assert first == second
    assert stable_hash(first.decode()) == stable_hash(second.decode())


def test_conflict_triage_key_stable() -> None:
    conflict = Conflict(
        kind="hard_hard",
        element_path="cta.button.fill",
        a_id="rule_a",
        b_id="rule_b",
        overlap_guard={},
        detail="clash",
    )
    candidates = CandidatesBundle(brand=MINIBIBLE_BRAND, conflicts=[conflict])
    empty_report, _ = build_ledger([], verify_entities({}, []), candidates)
    items = compute_triage_items(
        empty_report,
        labels_by_id={},
        candidates=candidates,
        provenance=verify_entities({}, []),
    )
    assert len(items) == 1
    assert items[0].queue == "conflict"
    assert items[0].key == stable_hash(
        ("hard_hard", "cta.button.fill", sorted(["rule_a", "rule_b"]))
    )


def test_global_unsat_triage_key_is_core_order_independent() -> None:
    expected = stable_hash(
        ("global_unsat", "context-a", ("rule_a", "rule_b"))
    )
    assert (
        triage_key_global_unsat(
            "context-a",
            ["rule_b", "rule_a"],
        )
        == expected
    )
    assert (
        triage_key_global_unsat(
            "context-a",
            ["rule_a", "rule_b"],
        )
        == expected
    )


def test_s9_triage_generation_is_deterministic() -> None:
    conflicts = [
        Conflict(
            kind="intra_token",
            element_path="body.color",
            a_id="token_b",
            b_id="token_a",
            overlap_guard={},
            detail="intra-token conflict",
        ),
        Conflict(
            kind="hard_hard",
            element_path="cta.fill",
            a_id="rule_b",
            b_id="rule_a",
            overlap_guard={},
            detail="hard conflict",
        ),
    ]
    global_unsat = [
        GlobalUnsatConflict(
            context_key="context-b",
            core=["rule_d", "rule_c"],
            detail="global conflict b",
        ),
        GlobalUnsatConflict(
            context_key="context-a",
            core=["rule_b", "rule_a"],
            detail="global conflict a",
        ),
    ]
    first = compute_s9_triage_items(
        PairwiseAnalysisResult(conflicts=conflicts),
        SmtAnalysisResult(
            status="completed",
            global_unsat=global_unsat,
        ),
    )
    second = compute_s9_triage_items(
        PairwiseAnalysisResult(conflicts=list(reversed(conflicts))),
        SmtAnalysisResult(
            status="completed",
            global_unsat=[
                row.model_copy(update={"core": list(reversed(row.core))})
                for row in reversed(global_unsat)
            ],
        ),
    )
    assert [item.model_dump(mode="json") for item in first] == [
        item.model_dump(mode="json") for item in second
    ]
    assert all(item.queue == "conflict" for item in first)


def test_s9_triage_merge_honors_waivers_and_current_keys() -> None:
    hard_conflict = Conflict(
        kind="hard_hard",
        element_path="cta.fill",
        a_id="rule_a",
        b_id="rule_b",
        overlap_guard={},
        detail="hard conflict",
    )
    intra_conflict = Conflict(
        kind="intra_token",
        element_path="body.color",
        a_id="token_a",
        b_id="token_b",
        overlap_guard={},
        detail="intra-token conflict",
    )
    pairwise = PairwiseAnalysisResult(
        conflicts=[hard_conflict, intra_conflict]
    )
    smt = SmtAnalysisResult(
        status="completed",
        global_unsat=[
            GlobalUnsatConflict(
                context_key="context-a",
                core=["rule_c", "rule_d"],
                detail="global conflict",
            )
        ],
    )
    computed = compute_s9_triage_items(pairwise, smt)
    hard_key = next(
        item.key
        for item in computed
        if item.subject_id == hard_conflict.a_id
    )
    global_key = triage_key_global_unsat(
        "context-a",
        ["rule_d", "rule_c"],
    )
    assert current_class_a_conflict_keys(
        computed,
        pairwise=pairwise,
        smt=smt,
    ) == sorted([hard_key, global_key])
    history = [
        TriageItem(
            queue="conflict",
            key=hard_key,
            subject_id=hard_conflict.a_id,
            context="first seen",
        ),
        TriageItem(
            queue="conflict",
            key=hard_key,
            subject_id=hard_conflict.a_id,
            context="waived",
            disposition=Disposition(
                status="waived",
                reason="accepted_risk",
            ),
        ),
        TriageItem(
            queue="conflict",
            key=global_key,
            subject_id="context-a",
            context="deferred",
            disposition=Disposition(
                status="deferred",
                reason="source_ambiguous",
            ),
        ),
        TriageItem(
            queue="conflict",
            key="fixed-conflict",
            subject_id="old-rule",
            context="no longer computed",
        ),
    ]
    merged, to_append = rebuild_triage(
        [*computed, computed[0]],
        history,
    )
    assert len({(item.queue, item.key) for item in merged}) == len(merged)
    assert "fixed-conflict" not in {item.key for item in merged}
    assert next(
        item for item in merged if item.key == hard_key
    ).disposition.status == "waived"
    assert next(
        item for item in merged if item.key == global_key
    ).disposition.status == "deferred"
    assert current_class_a_conflict_keys(
        merged,
        pairwise=pairwise,
        smt=smt,
    ) == []
    assert len(to_append) == 1
    assert to_append[0].subject_id == intra_conflict.a_id


def test_s9_triage_omits_smt_rows_when_skipped() -> None:
    smt = SmtAnalysisResult(
        status="skipped",
        global_unsat=[
            GlobalUnsatConflict(
                context_key="ignored",
                core=["rule_a"],
                detail="must not become triage",
            )
        ],
    )
    assert compute_s9_triage_items(None, smt) == []


def test_write_triage_snapshot_sorted(tmp_path: Path) -> None:
    path = tmp_path / "triage.jsonl"
    items = [
        TriageItem(queue="conflict", key="b", subject_id="s2", context="c2"),
        TriageItem(queue="unclaimed_unit", key="a", subject_id="s1", context="c1"),
    ]
    write_triage_snapshot(path, items)
    text = path.read_text(encoding="utf-8")
    assert text.index("conflict") < text.index("unclaimed_unit")
