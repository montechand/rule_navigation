"""WP-01 contract and settings tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from indexing.build_kb import slugify as build_kb_slugify
from indexing_v2 import contracts, settings
from indexing_v2.contracts import (
    SCHEMA_VERSION,
    ContextKey,
    Evidence,
    Finding,
    KBSnapshot,
    LedgerRow,
    ProvenanceRecord,
    RunVariant,
    SourceUnit,
    TriageItem,
    UnitLabel,
    atomic_write_json,
    read_jsonl,
    stable_hash,
    write_jsonl,
)
from shared import config

RULE_NAV_ROOT = Path(__file__).resolve().parent.parent


def test_stable_hash_dict_order_insensitive() -> None:
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})


def test_stable_hash_list_order_sensitive() -> None:
    assert stable_hash([1, 2, 3]) != stable_hash([3, 2, 1])


def test_stable_hash_nested_structure() -> None:
    payload = {"items": [{"z": 1, "a": 2}], "meta": {"k": "v"}}
    assert stable_hash(payload) == stable_hash(
        {"meta": {"k": "v"}, "items": [{"a": 2, "z": 1}]}
    )


def test_atomic_write_json_is_sorted_and_atomic(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "out.json"
    atomic_write_json(target, {"b": 2, "a": {"d": 4, "c": 3}})
    text = target.read_text(encoding="utf-8")
    assert text == json.dumps({"a": {"c": 3, "d": 4}, "b": 2}, indent=2, sort_keys=True) + "\n"
    assert not (tmp_path / "nested" / "out.json.tmp").exists()


def test_jsonl_roundtrip_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    units = [
        SourceUnit(
            unit_id="u_blob_0001",
            brand_id="minibible",
            doc_ref="colors[0]",
            ordinal=1,
            start=0,
            end=4,
            kind="sentence",
            text="test",
        ),
        SourceUnit(
            unit_id="u_blob_0002",
            brand_id="minibible",
            doc_ref="colors[0]",
            ordinal=2,
            start=5,
            end=9,
            kind="sentence",
            text="more",
        ),
    ]
    write_jsonl(path, units)
    loaded = read_jsonl(path, SourceUnit)
    assert loaded == units
    assert path.read_text(encoding="utf-8") == (
        json.dumps(units[0].model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        + "\n"
        + json.dumps(units[1].model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def test_schema_version_and_defaults_on_stage_artifacts() -> None:
    source = SourceUnit(
        unit_id="u_x_0000",
        brand_id="lisraya",
        doc_ref="cta[0]",
        ordinal=0,
        start=0,
        end=1,
        kind="heading",
        text="#",
    )
    assert source.schema_version == SCHEMA_VERSION == "2.0"
    assert source.heading_path == []

    label = UnitLabel(
        unit_id="u_x_0000",
        labels=["value"],
        expected_yield=["token_primitive"],
        required=True,
        heuristic_locked=["value"],
        confidence=0.9,
    )
    assert label.schema_version == "2.0"

    evidence = Evidence(unit_ids=["u_x_0000"])
    assert evidence.quotes == []

    finding = Finding(
        finding_id="f_lisraya_0001",
        round=1,
        finding_type="omission",
        severity="minor",
        description="missing token",
    )
    assert finding.resolution == "open"
    assert finding.unit_ids == []

    triage = TriageItem(
        queue="unclaimed_unit",
        key="abc123",
        subject_id="u_x_0000",
        context="normative sentence unclaimed",
    )
    assert triage.disposition.status == "open"
    assert triage.disposition.note == ""


def test_model_literals_reject_invalid_values() -> None:
    with pytest.raises(ValidationError):
        SourceUnit(
            unit_id="u_x_0000",
            brand_id="lisraya",
            doc_ref="cta[0]",
            ordinal=0,
            start=0,
            end=1,
            kind="not_a_kind",
            text="#",
        )

    with pytest.raises(ValidationError):
        LedgerRow(
            unit_id="u_x_0000",
            required=True,
            expected_yield=["token_primitive"],
            claimed_by=[],
            status="missing_status",
        )


def test_context_key_canonical_empty_tags() -> None:
    key = ContextKey()
    assert key.canonical() == (
        "audience=dtp_patient;campaign=none;surface=email;tags=none;theme=none"
    )


def test_context_key_canonical_nonempty_tags() -> None:
    key = ContextKey(content_tags=["lpga", "secondary_cta"])
    assert key.canonical() == (
        "audience=dtp_patient;campaign=none;surface=email;"
        "tags=lpga+secondary_cta;theme=none"
    )


def test_slugify_matches_build_kb() -> None:
    samples = [
      "CTA Buttons",
      "YOU DESERVE MORE",
      "  mixed-case_123  ",
      "___",
  ]
    for sample in samples:
        assert contracts.slugify(sample) == build_kb_slugify(sample)


def test_kbsnapshot_load_lisraya_fixture() -> None:
    if not config.kb_dir("lisraya").exists():
        pytest.skip("lisraya KB not present in this snapshot")

    snap = KBSnapshot.load("lisraya")
    assert snap.brand == "lisraya"
    assert snap.rules
    assert snap.tokens
    assert "campaign" in snap.predicate_domains
    assert "lisraya_you_deserve_more" in snap.predicate_domains["campaign"]
    assert "content_tag" in snap.predicate_domains
    assert snap.rules[next(iter(snap.rules))].brand_id == "lisraya"


def test_kbsnapshot_tolerates_missing_optional_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    brand_dir = tmp_path / "tinybrand"
    rules_dir = brand_dir / "rules"
    rules_dir.mkdir(parents=True)
    rule = {
        "id": "rule_tinybrand_sample",
        "brand_id": "tinybrand",
        "rule_class": "typography",
        "rule_text": "Body text must be readable.",
        "status": "active",
        "version": 1,
    }
    (rules_dir / "rule_tinybrand_sample.json").write_text(
        json.dumps(rule, indent=2) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(config, "KB_ROOT", tmp_path)
    snap = KBSnapshot.load("tinybrand")
    assert snap.rules["rule_tinybrand_sample"].rule_text.startswith("Body text")
    assert snap.tokens == {}
    assert snap.assets == {}
    assert snap.subtypes == {}
    assert snap.templates == {}


def test_kbsnapshot_rejects_corrupt_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    brand_dir = tmp_path / "badbrand" / "rules"
    brand_dir.mkdir(parents=True)
    (brand_dir / "rule_bad.json").write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(config, "KB_ROOT", tmp_path)
    with pytest.raises(json.JSONDecodeError):
        KBSnapshot.load("badbrand")


def test_settings_defaults_and_override_order(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("RULE_NAV_"):
            monkeypatch.delenv(key, raising=False)

    settings.reload_settings()

    # Compare against the resolution chain (config attr, else module default),
    # not hardcoded model names: deployed models rotate and this test asserts
    # override *order*, not a specific vendor.
    assert settings.CLASSIFY_MODEL == getattr(
        config, "CLASSIFY_MODEL", settings._DEFAULT_CLASSIFY_MODEL
    )
    assert settings.EXTRACT_MODEL == config.EXTRACT_MODEL
    assert settings.CRITIC_MODEL == getattr(
        config, "CRITIC_MODEL", settings._DEFAULT_CRITIC_MODEL
    )
    assert settings.SECONDARY_MODEL == settings.CRITIC_MODEL
    assert settings.MAX_CRITIC_ROUNDS == 2
    assert settings.MAX_GAP_ROUNDS == 3
    assert settings.TRIAGE_FILE == "review/triage.jsonl"
    assert settings.FUZZY_MATCH_MIN_RATIO == pytest.approx(0.92)
    assert settings.DTCG_NAMESPACE == "com.solstice.kb"
    assert settings.CONCURRENCY == 4
    assert settings.TWO_PHASE is False
    assert settings.REF_RETRIES == 2
    assert settings.LINKER_MODEL == settings.CRITIC_MODEL
    assert settings.LINKER_MAX_ADJUDICATIONS == 64
    assert settings.LINKER_GAP_FEEDBACK is True
    assert settings.TABLE_COMPILER is True
    assert [run.model_dump() for run in settings.ENSEMBLE_RUNS] == [
        {"run_id": "r0", "model": settings.EXTRACT_MODEL, "temperature": 0.0, "replicate": 0},
        {"run_id": "r1", "model": settings.EXTRACT_MODEL, "temperature": 0.4, "replicate": 1},
        {"run_id": "r2", "model": settings.CRITIC_MODEL, "temperature": 0.2, "replicate": 0},
    ]

    monkeypatch.setenv("RULE_NAV_EXTRACT_MODEL", "env-extract")
    settings.reload_settings()
    assert settings.EXTRACT_MODEL == "env-extract"

    monkeypatch.delenv("RULE_NAV_EXTRACT_MODEL", raising=False)
    monkeypatch.setattr(config, "EXTRACT_MODEL", "config-extract", raising=False)
    settings.reload_settings()
    assert settings.EXTRACT_MODEL == "config-extract"


def test_settings_reload_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RULE_NAV_CONCURRENCY", "7")
    settings.reload_settings()
    first = settings.CONCURRENCY
    settings.reload_settings()
    assert settings.CONCURRENCY == first == 7


def test_evidence_paths_cover_entity_kinds() -> None:
    assert set(contracts.EVIDENCE_PATHS) == {
        "token_primitive",
        "token_semantic",
        "rule",
        "asset",
        "subtype",
        "template",
        "token_table",
    }


def test_provenance_and_run_variant_defaults() -> None:
    record = ProvenanceRecord(
        entity_id="tok_x",
        field="value.default",
        spans=[],
        value_check={"status": "n/a"},
        verification="unverified",
    )
    assert record.schema_version == "2.0"

    variant = RunVariant(run_id="r0", model="m")
    assert variant.temperature == 0.0
    assert variant.replicate == 0


def test_disposition_factory_not_shared() -> None:
    a = TriageItem(queue="conflict", key="k1", subject_id="s1", context="ctx")
    b = TriageItem(queue="conflict", key="k2", subject_id="s2", context="ctx")
    b.disposition.status = "waived"
    assert a.disposition.status == "open"
