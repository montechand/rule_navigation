"""Integrity checks for the minibible fixture corpus and FakeLLM (WP-02)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tests.fakes import (
    FIXTURE_ROOT,
    FakeLLM,
    MINIBIBLE_BRAND,
    UnexpectedLLMCallError,
)

pytest.importorskip("pydantic")

contracts = pytest.importorskip("indexing_v2.contracts")
SourceUnit = contracts.SourceUnit
UnitLabel = contracts.UnitLabel
KBSnapshot = contracts.KBSnapshot

from shared import config as shared_config  # noqa: E402
from shared.llm import Usage  # noqa: E402
from shared.schemas import BrandRule, BrandToken  # noqa: E402
from indexing_v2.extraction.classify_units import classify_units  # noqa: E402
from indexing_v2.extraction.ledger import GapPatchPayload  # noqa: E402


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _fixture_entities(fixture_root: Path) -> list[tuple[Path, str, dict]]:
    llm_root = fixture_root / "llm"
    entities: list[tuple[Path, str, dict]] = []
    for directory, kind, bucket in (
        ("tokens_primitive", "token_primitive", "tokens"),
        ("tokens_semantic", "token_semantic", "tokens"),
        ("rules_cluster", "rule", "rules"),
    ):
        for path in sorted((llm_root / directory).glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            entities.extend((path, kind, entity) for entity in payload[bucket])

    catalog_path = llm_root / "catalog_rest" / "001.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for bucket, kind in (
        ("assets", "asset"),
        ("subtypes", "subtype"),
        ("templates", "template"),
    ):
        entities.extend((catalog_path, kind, entity) for entity in catalog[bucket])

    for path in sorted((llm_root / "gap_patch").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        GapPatchPayload.model_validate(payload)
        for bucket, kind in (("tokens", "token_primitive"), ("rules", "rule")):
            entities.extend((path, kind, entity) for entity in payload[bucket])

    for relative, kind, bucket in (
        ("corrupt_bad_quote/001.json", "token_primitive", "tokens"),
    ):
        path = llm_root / relative
        payload = json.loads(path.read_text(encoding="utf-8"))
        entities.extend((path, kind, entity) for entity in payload[bucket])

    for directory in ("critic_catalog", "critic_rules"):
        for path in sorted((llm_root / directory).glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for finding in payload["findings"]:
                patch = finding.get("proposed_patch")
                if not patch or patch["op"] not in {"add", "update", "split"}:
                    continue
                entity = patch.get("payload")
                if isinstance(entity, dict) and "id" in entity:
                    entities.append((path, patch["entity_kind"], entity))
    return entities


@pytest.fixture
def fixture_root() -> Path:
    return FIXTURE_ROOT


@pytest.fixture
def units(fixture_root: Path) -> list[SourceUnit]:
    return [SourceUnit.model_validate(r) for r in _read_jsonl(fixture_root / "expected" / "units.jsonl")]


@pytest.fixture
def labels(fixture_root: Path) -> list[UnitLabel]:
    return [UnitLabel.model_validate(r) for r in _read_jsonl(fixture_root / "expected" / "labels.jsonl")]


@pytest.fixture
def blobs(fixture_root: Path) -> dict[str, str]:
    return json.loads((fixture_root / "blobs.json").read_text(encoding="utf-8"))


@pytest.fixture
def plants(fixture_root: Path) -> list[dict]:
    return json.loads((fixture_root / "plant_index.json").read_text(encoding="utf-8"))


@pytest.fixture
def candidates_summary(fixture_root: Path) -> dict:
    return json.loads((fixture_root / "expected" / "candidates_summary.json").read_text(encoding="utf-8"))


def test_all_fourteen_plants_documented(plants: list[dict]) -> None:
    assert len(plants) == 14
    ids = {p["id"] for p in plants}
    assert ids == set(range(1, 15))
    for p in plants:
        assert p["name"]
        assert p["description"]
        assert p["units"]


def test_source_unit_invariants(units: list[SourceUnit], blobs: dict[str, str]) -> None:
    by_blob: dict[str, list[SourceUnit]] = {}
    for u in units:
        by_blob.setdefault(u.doc_ref, []).append(u)
    assert len(by_blob) == 2
    for doc_ref, us in by_blob.items():
        blob = blobs[doc_ref]
        assert "\r" not in blob
        us_sorted = sorted(us, key=lambda x: x.ordinal)
        assert [u.ordinal for u in us_sorted] == list(range(len(us_sorted)))
        pos = 0
        for u in us_sorted:
            assert u.brand_id == MINIBIBLE_BRAND
            assert u.start == pos
            assert blob[u.start : u.end] == u.text
            pos = u.end
        assert pos == len(blob)
        blank_spans = [(u.start, u.end, u.text) for u in us_sorted if u.kind == "blank"]
        expected_blank_spans = [
            (match.start(), match.end(), match.group())
            for match in re.finditer(r"(?m)^(?:[ \t]*\n)+", blob)
        ]
        assert blank_spans == expected_blank_spans


def test_labels_reference_units_and_are_sorted(labels: list[UnitLabel], units: list[SourceUnit]) -> None:
    unit_ids = {u.unit_id for u in units}
    labels_by_unit = {label.unit_id: label for label in labels}
    blank_units = [unit for unit in units if unit.kind == "blank"]
    assert len(labels) == len(units)
    assert blank_units
    for lb in labels:
        assert lb.unit_id in unit_ids
        assert lb.labels == sorted(set(lb.labels))
        assert lb.heuristic_locked == sorted(set(lb.heuristic_locked))
        assert lb.expected_yield == sorted(set(lb.expected_yield))
    for unit in blank_units:
        label = labels_by_unit[unit.unit_id]
        assert label.labels == ["noise"]
        assert label.heuristic_locked == ["noise"]
        assert label.required is False


def test_candidates_summary_ids_coherent(candidates_summary: dict, units: list[SourceUnit]) -> None:
    unit_ids = {u.unit_id for u in units}
    for key in ("tokens_primitive", "tokens_semantic", "rules"):
        ids = candidates_summary[key]
        assert ids == sorted(set(ids)), key
    assert candidates_summary["ensemble"]["r2_fabricated_singleton"] not in candidates_summary["tokens_primitive"]
    for uid in candidates_summary["excluded_unit_ids"]:
        assert uid in unit_ids
    assert candidates_summary["critic"]["valid_patch_finding"].startswith("f_")


def test_classifier_fixtures_partition_expected_labels(
    fixture_root: Path,
    units: list[SourceUnit],
    labels: list[UnitLabel],
) -> None:
    ordered_units = sorted(units, key=lambda unit: (unit.doc_ref, unit.ordinal))
    expected_by_id = {label.unit_id: label for label in labels}
    paths = sorted((fixture_root / "llm" / "unit_classifier").glob("*.json"))
    assert [path.name for path in paths] == ["001.json", "002.json"]

    all_rows: list[dict] = []
    for batch_index, path in enumerate(paths):
        rows = json.loads(path.read_text(encoding="utf-8"))["units"]
        assert len(rows) == 40
        expected_ids = [
            unit.unit_id
            for unit in ordered_units[batch_index * 40 : (batch_index + 1) * 40]
        ]
        assert [row["unit_id"] for row in rows] == expected_ids
        for row in rows:
            assert set(row) == {
                "unit_id",
                "labels",
                "expected_yield",
                "required",
                "confidence",
            }
            expected = expected_by_id[row["unit_id"]]
            assert row == {
                "unit_id": expected.unit_id,
                "labels": expected.labels,
                "expected_yield": expected.expected_yield,
                "required": expected.required,
                "confidence": expected.confidence,
            }
        all_rows.extend(rows)

    all_ids = [row["unit_id"] for row in all_rows]
    assert len(all_ids) == len(set(all_ids)) == len(ordered_units)
    assert set(all_ids) == {unit.unit_id for unit in ordered_units}


@pytest.mark.asyncio
async def test_full_classifier_run_matches_expected_labels(
    tmp_path: Path,
    units: list[SourceUnit],
    labels: list[UnitLabel],
) -> None:
    llm = FakeLLM()
    usage = Usage()
    actual = await classify_units(
        MINIBIBLE_BRAND,
        units,
        client=llm,
        usage=usage,
        batch_size=40,
        cache_root=tmp_path,
    )

    assert actual == sorted(labels, key=lambda label: label.unit_id)
    assert [call.prompt_name for call in llm.calls()] == [
        "unit_classifier",
        "unit_classifier",
    ]
    assert [call.seq for call in llm.calls()] == [1, 2]
    assert usage.llm_calls == 2


def test_canned_llm_unit_references_exist(
    fixture_root: Path,
    units: list[SourceUnit],
) -> None:
    unit_ids = {unit.unit_id for unit in units}
    blank_ids = {unit.unit_id for unit in units if unit.kind == "blank"}

    def collect(value: object) -> set[str]:
        if isinstance(value, dict):
            refs = {
                item
                for key, item in value.items()
                if key == "unit_id" and isinstance(item, str) and item.startswith("u_")
            }
            for key, item in value.items():
                if key == "unit_ids" and isinstance(item, list):
                    refs.update(x for x in item if isinstance(x, str))
                else:
                    refs.update(collect(item))
            return refs
        if isinstance(value, list):
            return set().union(*(collect(item) for item in value)) if value else set()
        return set()

    for path in sorted((fixture_root / "llm").rglob("*.json")):
        refs = collect(json.loads(path.read_text(encoding="utf-8")))
        assert refs <= unit_ids, f"{path.name}: unknown unit ids {sorted(refs - unit_ids)}"
        if path.parent.name != "unit_classifier":
            assert refs.isdisjoint(blank_ids), (
                f"{path.name}: cites blank units {sorted(refs & blank_ids)}"
            )


def test_canned_entities_have_valid_field_evidence(
    fixture_root: Path,
    units: list[SourceUnit],
) -> None:
    units_by_id = {unit.unit_id: unit for unit in units}
    allowed_bad = {
        (
            "llm/corrupt_bad_quote/001.json",
            "tok_minibible_color_corrupt_quote",
            "",
        ),
        (
            "llm/corrupt_bad_quote/001.json",
            "tok_minibible_color_corrupt_quote",
            "value.default",
        ),
        (
            "llm/tokens_primitive/r2_001.json",
            "tok_minibible_spacing_phantom_99",
            "",
        ),
        (
            "llm/tokens_primitive/r2_001.json",
            "tok_minibible_spacing_phantom_99",
            "value.default",
        ),
    }

    for path, kind, entity in _fixture_entities(fixture_root):
        evidence_fields: list[tuple[str, dict, object]] = [
            ("", entity["evidence"], entity)
        ]
        value = entity.get("value")
        if kind in {"token_primitive", "token_semantic"} and isinstance(value, dict):
            if "default" in value:
                evidence_fields.append(
                    ("value.default", value["default_evidence"], value["default"])
                )
            for index, variant in enumerate(value.get("variants") or []):
                evidence_fields.append(
                    (
                        f"value.variants[{index}].value",
                        variant["evidence"],
                        variant["value"],
                    )
                )
        if kind == "rule":
            if entity.get("effect") is not None:
                evidence_fields.append(
                    ("effect", entity["effect_evidence"], entity["effect"])
                )
            if entity.get("snippets") is not None:
                evidence_fields.append(
                    ("snippets", entity["snippets_evidence"], entity["snippets"])
                )
            governance = entity.get("governance")
            if isinstance(governance, dict) and governance.get("preferred_form") is not None:
                evidence_fields.append(
                    (
                        "governance.preferred_form",
                        governance["preferred_form_evidence"],
                        governance["preferred_form"],
                    )
                )
        if kind == "template" and entity.get("body") is not None:
            evidence_fields.append(("body", entity["body_evidence"], entity["body"]))

        relative = path.relative_to(fixture_root).as_posix()
        expected_paths = set(contracts.EVIDENCE_PATHS[kind])
        for field_path, evidence, raw_value in evidence_fields:
            assert (
                field_path == ""
                or field_path in expected_paths
                or (
                    field_path.startswith("value.variants[")
                    and "value.variants[*].value" in expected_paths
                )
            )
            unit_ids = evidence["unit_ids"]
            quotes = evidence["quotes"]
            assert unit_ids and quotes
            assert all(unit_id in units_by_id for unit_id in unit_ids)
            key = (relative, entity["id"], field_path)
            quote_is_real = all(
                any(quote in units_by_id[unit_id].text for unit_id in unit_ids)
                for quote in quotes
            )
            if key in allowed_bad:
                assert not quote_is_real
                continue
            assert quote_is_real, key
            if len(unit_ids) > 1:
                assert len(unit_ids) == len(set(unit_ids)), key
                for unit_id in unit_ids:
                    other_unit_ids = [other for other in unit_ids if other != unit_id]
                    assert any(
                        quote in units_by_id[unit_id].text
                        and all(
                            quote not in units_by_id[other].text
                            for other in other_unit_ids
                        )
                        for quote in quotes
                    ), (key, unit_id)

            is_token_value = (
                field_path == "value.default"
                or field_path.startswith("value.variants[")
            )
            if is_token_value and not (
                isinstance(raw_value, dict) and "$ref" in raw_value
            ):
                assert any(str(raw_value) in quote for quote in quotes), key
            if field_path in {"governance.preferred_form", "body"}:
                assert quotes == [raw_value], key


def test_primitive_runs_dedupe_primary_green_aliases(
    fixture_root: Path,
    units: list[SourceUnit],
) -> None:
    alias_units = {
        "u_brand_foundation_0_0004",
        "u_brand_foundation_0_0005",
    }
    units_by_id = {unit.unit_id: unit for unit in units}
    for path in sorted((fixture_root / "llm" / "tokens_primitive").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        matches = [
            token
            for token in payload["tokens"]
            if (
                token["token_type"],
                token["value"]["default"].lower(),
                token.get("scope", "global"),
            )
            == ("color", "#01a47e", "global")
        ]
        assert len(matches) == 1, path.name
        token = matches[0]
        assert set(token["aliases"]) == {"Primary Green", "Brand Teal"}
        evidence = token["evidence"]
        assert set(evidence["unit_ids"]) == alias_units
        assert len(set(evidence["quotes"])) == 2
        independently_covered = {
            unit_id
            for unit_id in alias_units
            if any(
                quote in units_by_id[unit_id].text
                and all(
                    quote not in units_by_id[other].text
                    for other in alias_units - {unit_id}
                )
                for quote in evidence["quotes"]
            )
        }
        assert independently_covered == alias_units


def test_ensemble_metadata_matches_canned_runs(
    fixture_root: Path,
    candidates_summary: dict,
) -> None:
    run_ids: dict[str, set[str]] = {}
    for run_id in ("r0", "r1", "r2"):
        payload = json.loads(
            (fixture_root / "llm" / "tokens_primitive" / f"{run_id}_001.json").read_text(
                encoding="utf-8"
            )
        )
        run_ids[run_id] = {token["id"] for token in payload["tokens"]}

    ensemble = candidates_summary["ensemble"]
    assert ensemble["r0_only"] == sorted(run_ids["r0"] - run_ids["r1"] - run_ids["r2"])
    assert ensemble["r1_r2_added"] == sorted(
        (run_ids["r1"] & run_ids["r2"]) - run_ids["r0"]
    )
    assert ensemble["r2_fabricated_singleton"] in (
        run_ids["r2"] - run_ids["r0"] - run_ids["r1"]
    )


@pytest.mark.asyncio
async def test_fake_llm_serves_and_logs_calls() -> None:
    llm = FakeLLM()
    usage = Usage()
    out = await llm.complete_json(
        "fake",
        "sys",
        "user",
        usage=usage,
        prompt_name="unit_classifier",
    )
    assert "units" in out
    assert len(llm.calls()) == 1
    rec = llm.calls()[0]
    assert rec.prompt_name == "unit_classifier"
    assert len(rec.rendered_hash) == 16
    assert usage.llm_calls == 1
    assert usage.input_tokens > 0
    assert usage.output_tokens > 0


@pytest.mark.asyncio
async def test_fake_llm_cache_key_and_sequential_lookup() -> None:
    llm = FakeLLM()
    r0 = await llm.complete_json("m", "s", "u", prompt_name="tokens_primitive", cache_key="r0_001")
    r1 = await llm.complete_json("m", "s", "u", prompt_name="tokens_primitive", cache_key="r1_001")
    assert r0 != r1
    assert "tok_minibible_spacing_subhead_margin" in {t["id"] for t in r1["tokens"]}
    assert "tok_minibible_spacing_subhead_margin" not in {t["id"] for t in r0["tokens"]}


@pytest.mark.asyncio
async def test_fake_llm_rejects_unexpected_call() -> None:
    llm = FakeLLM()
    with pytest.raises(UnexpectedLLMCallError):
        await llm.complete_json("m", "s", "u", prompt_name="nonexistent_prompt")


@pytest.mark.asyncio
async def test_fake_llm_rejects_classifier_target_from_wrong_batch() -> None:
    llm = FakeLLM()
    with pytest.raises(
        UnexpectedLLMCallError,
        match="001.json missing TARGET unit 'u_brand_foundation_0_0040'",
    ):
        await llm.complete_json(
            "m",
            "s",
            "[u_brand_foundation_0_0040] (heading) TARGET heading",
            prompt_name="unit_classifier",
        )


def test_corrupt_quote_not_in_source(blobs: dict[str, str]) -> None:
    corrupt = json.loads(
        (FIXTURE_ROOT / "llm" / "corrupt_bad_quote" / "001.json").read_text(encoding="utf-8")
    )
    quote = corrupt["tokens"][0]["evidence"]["quotes"][0]
    blob = blobs["brand_foundation[0]"]
    assert quote not in blob
    assert "DEADBE" in quote


def test_r2_fabricated_quote_not_in_source(blobs: dict[str, str]) -> None:
    r2 = json.loads((FIXTURE_ROOT / "llm" / "tokens_primitive" / "r2_001.json").read_text(encoding="utf-8"))
    phantom = next(t for t in r2["tokens"] if t["id"] == "tok_minibible_spacing_phantom_99")
    assert phantom["evidence"]["quotes"] == ["99px"]
    assert "99px" not in blobs["layout_constraints[0]"]


def test_fakes_module_has_no_network_clients() -> None:
    import tests.fakes as fakes_mod

    src = Path(fakes_mod.__file__).read_text(encoding="utf-8")
    for forbidden in ("openai", "anthropic", "httpx", "aiohttp", "requests"):
        assert forbidden not in src


def test_bible_shape_and_brand(fixture_root: Path) -> None:
    bible = json.loads((fixture_root / "bible.json").read_text(encoding="utf-8"))
    assert "website" in bible
    assert len(bible["website"]) == 2
    total_blobs = sum(len(v) for v in bible["website"].values())
    assert total_blobs == 2


def test_plant_index_markdown_lists_all_plants(fixture_root: Path, plants: list[dict]) -> None:
    md = (fixture_root / "PLANT_INDEX.md").read_text(encoding="utf-8")
    for p in plants:
        assert f"PLANT {p['id']}" in md
        assert p["name"] in md


def test_kb_fixture_loads_typed_snapshot(
    fixture_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shared_config, "KB_ROOT", fixture_root / "kb")
    snapshot = KBSnapshot.load(MINIBIBLE_BRAND)

    rule = snapshot.rules["rule_minibible_sentence_case_headlines"]
    token = snapshot.tokens["tok_minibible_color_primary_green_01"]
    assert isinstance(rule, BrandRule)
    assert isinstance(token, BrandToken)
    assert rule.brand_id == MINIBIBLE_BRAND
    assert rule.rule_text == "Headlines must use sentence case only."
    assert token.brand_id == MINIBIBLE_BRAND
    assert token.aliases == ["Primary Green", "Brand Teal"]


def test_unit_count_near_fifty(units: list[SourceUnit]) -> None:
    # The fixture has ~47 content/structural plants plus 33 explicit blank-run units.
    assert 75 <= len(units) <= 85
