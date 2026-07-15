"""Tests for §5.4.3 provenance store (S3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from indexing_v2.contracts import EVIDENCE_PATHS, EntityKind, SourceUnit, read_jsonl
from indexing_v2.extraction.provenance import (
    STAGE_VERSION,
    ProvenanceError,
    ProvenanceResult,
    QuarantineEntry,
    UnknownEntityKindError,
    active_entities,
    verify_entities,
    write_provenance,
)

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "minibible"


@pytest.fixture
def units() -> list[SourceUnit]:
    return read_jsonl(FIXTURE_ROOT / "expected" / "units.jsonl", SourceUnit)


@pytest.fixture
def units_by_id(units: list[SourceUnit]) -> dict[str, SourceUnit]:
    return {unit.unit_id: unit for unit in units}


def _load_json(name: str) -> dict[str, Any]:
    raw = json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"fixture {name} must contain an object")
    return raw


def test_stage_version_present() -> None:
    assert STAGE_VERSION


def test_unknown_entity_kind_raises() -> None:
    with pytest.raises(UnknownEntityKindError):
        verify_entities({"bogus": [{"id": "x"}]}, [])


def test_duplicate_entity_id_across_buckets_raises() -> None:
    entities = {
        "asset": [{"id": "duplicate_id"}],
        "subtype": [{"id": "duplicate_id"}],
    }
    with pytest.raises(ProvenanceError, match="duplicate entity id: duplicate_id"):
        verify_entities(entities, [])


def test_exact_value_default_verification(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "tok_minibible_color_primary_green_01",
        "token_type": "color",
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
        "value": {
            "default": "#01A47E",
            "default_evidence": {
                "quotes": ["Primary Green #01A47E"],
                "unit_ids": ["u_brand_foundation_0_0004"],
            },
            "variants": None,
        },
    }
    result = verify_entities({"token_primitive": [entity]}, units)
    record = next(r for r in result.records_by_entity[entity["id"]] if r.field == "value.default")
    assert record.verification == "value_verified"
    assert record.value_check.status == "pass"
    assert record.spans[0].match == "exact"


def test_normalized_entity_level_span(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "rule_minibible_sentence_case_headlines",
        "effect": {"value": "sentence_case"},
        "evidence": {
            "quotes": ["sentence case"],
            "unit_ids": ["u_brand_foundation_0_0022"],
        },
    }
    result = verify_entities({"rule": [entity]}, units)
    record = next(r for r in result.records_by_entity[entity["id"]] if r.field == "")
    assert record.verification == "span_verified"
    assert record.spans[0].match == "exact"


def test_fuzzy_entity_level_span(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "rule_minibible_footer_nav_order",
        "effect": {"sequence": ["home", "about", "contact"]},
        "evidence": {
            "quotes": ["brand navigation ordre"],
            "unit_ids": ["u_layout_constraints_0_0018"],
        },
    }
    result = verify_entities({"rule": [entity]}, units, fuzzy_min_ratio=0.85)
    record = next(r for r in result.records_by_entity[entity["id"]] if r.field == "")
    assert record.verification == "span_verified"
    assert record.spans[0].match == "fuzzy"


def test_corrupt_quote_quarantines(units: list[SourceUnit]) -> None:
    payload = _load_json("llm/corrupt_bad_quote/001.json")
    entity = payload["tokens"][0]
    result = verify_entities({"token_primitive": [entity]}, units)
    assert len(result.quarantine) == 1
    assert result.quarantine[0].entity_id == entity["id"]
    default = next(r for r in result.records_by_entity[entity["id"]] if r.field == "value.default")
    assert default.verification == "unverified"
    assert default.value_check.status == "fail"


def test_one_passing_concrete_path_avoids_quarantine(units: list[SourceUnit]) -> None:
    entity = {
        "id": "tok_mixed",
        "token_type": "color",
        "value": {
            "default": "#01A47E",
            "default_evidence": {
                "quotes": ["Primary Green #01A47E"],
                "unit_ids": ["u_brand_foundation_0_0004"],
            },
            "variants": [
                {
                    "value": "#FFFFFF",
                    "evidence": {
                        "quotes": ["not in source at all"],
                        "unit_ids": ["u_brand_foundation_0_0010"],
                    },
                    "when": {"background_group": "dark"},
                }
            ],
        },
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    result = verify_entities({"token_semantic": [entity]}, units)
    assert result.quarantine == []
    active_ids = {
        item["id"] for item in active_entities(result, {"token_semantic": [entity]})["token_semantic"]
    }
    assert entity["id"] in active_ids


def test_ref_value_not_quarantined(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "tok_ref_color",
        "token_type": "color",
        "value": {
            "default": {"$ref": "tok_other"},
            "default_evidence": {
                "quotes": ["Primary Green #01A47E"],
                "unit_ids": ["u_brand_foundation_0_0004"],
            },
            "variants": None,
        },
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    result = verify_entities({"token_primitive": [entity]}, units)
    record = next(r for r in result.records_by_entity[entity["id"]] if r.field == "value.default")
    assert record.value_check.status == "n/a"
    assert record.verification == "unverified"
    assert record.spans[0].match == "exact"
    assert result.quarantine == []


def test_ref_default_without_evidence_is_not_quarantined(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "tok_ref_default_no_evidence",
        "token_type": "color",
        "value": {
            "default": {"$ref": "tok_other"},
            "variants": None,
        },
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    result = verify_entities({"token_primitive": [entity]}, units)
    record = next(
        item
        for item in result.records_by_entity[entity["id"]]
        if item.field == "value.default"
    )
    assert record.value_check.status == "n/a"
    assert record.value_check.detail == "structural $ref"
    assert record.verification == "unverified"
    assert record.spans == []
    assert result.quarantine == []


def test_ref_variant_without_evidence_is_not_quarantined(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "tok_ref_variant_no_evidence",
        "token_type": "color",
        "value": {
            "default": None,
            "variants": [
                {
                    "value": {"$ref": "tok_other"},
                    "when": {"theme": "dark"},
                }
            ],
        },
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    result = verify_entities({"token_semantic": [entity]}, units)
    variant = next(
        item
        for item in result.records_by_entity[entity["id"]]
        if item.field == "value.variants[0].value"
    )
    assert variant.value_check.status == "n/a"
    assert variant.value_check.detail == "structural $ref"
    assert variant.verification == "unverified"
    assert variant.spans == []
    assert result.quarantine == []


def test_ref_with_malformed_evidence_still_raises(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "tok_ref_malformed_evidence",
        "token_type": "color",
        "value": {
            "default": {"$ref": "tok_other"},
            "default_evidence": {
                "quotes": [123],
                "unit_ids": ["u_brand_foundation_0_0004"],
            },
            "variants": None,
        },
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    with pytest.raises(
        ProvenanceError,
        match=r"tok_ref_malformed_evidence/value\.default",
    ):
        verify_entities({"token_primitive": [entity]}, units)


def test_null_optional_evidence_key_is_treated_as_missing(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "rule_null_snippets_evidence",
        "snippets": None,
        "snippets_evidence": None,
        "effect": None,
        "effect_evidence": None,
        "governance": {"preferred_form": None, "preferred_form_evidence": None},
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    result = verify_entities({"rule": [entity]}, units)
    by_field = {record.field: record for record in result.records_by_entity[entity["id"]]}
    assert by_field["snippets"].verification == "unverified"
    assert "missing evidence" in (by_field["snippets"].value_check.detail or "")
    assert by_field["effect"].verification == "unverified"
    assert result.quarantine == []


def test_preferred_form_requires_exact(units: list[SourceUnit]) -> None:
    preferred = "Ask your doctor about treatment options appropriate for you."
    entity: dict[str, Any] = {
        "id": "rule_minibible_disclosure_verbatim",
        "governance": {
            "preferred_form": preferred,
            "preferred_form_evidence": {
                "quotes": [preferred],
                "unit_ids": ["u_brand_foundation_0_0042"],
            },
        },
        "evidence": {
            "quotes": [preferred],
            "unit_ids": ["u_brand_foundation_0_0042"],
        },
    }
    result = verify_entities({"rule": [entity]}, units)
    record = next(
        r for r in result.records_by_entity[entity["id"]] if r.field == "governance.preferred_form"
    )
    assert record.verification == "value_verified"
    assert record.spans[0].match == "exact"


def test_template_body_exact_is_value_verified(units: list[SourceUnit]) -> None:
    body = "Quality  you can trust"
    entity: dict[str, Any] = {
        "id": "tpl_exact_body",
        "body": body,
        "body_evidence": {
            "quotes": [body],
            "unit_ids": ["u_layout_constraints_0_0026"],
        },
        "evidence": {
            "quotes": [body],
            "unit_ids": ["u_layout_constraints_0_0026"],
        },
    }
    result = verify_entities({"template": [entity]}, units)
    record = next(r for r in result.records_by_entity[entity["id"]] if r.field == "body")
    assert record.verification == "value_verified"
    assert record.value_check.status == "pass"
    assert record.spans[0].match == "exact"
    assert result.quarantine == []


@pytest.mark.parametrize(
    "entity",
    [
        {
            "id": "tpl_body_absent",
            "evidence": {
                "quotes": ["Quality  you can trust"],
                "unit_ids": ["u_layout_constraints_0_0026"],
            },
        },
        {
            "id": "tpl_body_null",
            "body": None,
            "evidence": {
                "quotes": ["Quality  you can trust"],
                "unit_ids": ["u_layout_constraints_0_0026"],
            },
        },
    ],
)
def test_template_absent_or_null_body_is_not_quarantined(
    units: list[SourceUnit],
    entity: dict[str, Any],
) -> None:
    result = verify_entities({"template": [entity]}, units)
    body_record = next(
        record for record in result.records_by_entity[entity["id"]] if record.field == "body"
    )
    assert body_record.value_check.status == "n/a"
    assert body_record.verification == "unverified"
    assert result.quarantine == []


@pytest.mark.parametrize(
    "entity",
    [
        {
            "id": "rule_governance_absent",
            "evidence": {
                "quotes": ["sentence case"],
                "unit_ids": ["u_brand_foundation_0_0022"],
            },
        },
        {
            "id": "rule_preferred_form_null",
            "governance": {"preferred_form": None},
            "evidence": {
                "quotes": ["sentence case"],
                "unit_ids": ["u_brand_foundation_0_0022"],
            },
        },
    ],
)
def test_rule_absent_or_null_preferred_form_is_not_quarantined(
    units: list[SourceUnit],
    entity: dict[str, Any],
) -> None:
    result = verify_entities({"rule": [entity]}, units)
    preferred_record = next(
        record
        for record in result.records_by_entity[entity["id"]]
        if record.field == "governance.preferred_form"
    )
    assert preferred_record.value_check.status == "n/a"
    assert preferred_record.verification == "unverified"
    assert result.quarantine == []


@pytest.mark.parametrize(
    ("kind", "entity", "field"),
    [
        (
            "template",
            {
                "id": "tpl_body_without_evidence",
                "body": "Quality  you can trust",
                "evidence": {
                    "quotes": ["Quality  you can trust"],
                    "unit_ids": ["u_layout_constraints_0_0026"],
                },
            },
            "body",
        ),
        (
            "rule",
            {
                "id": "rule_preferred_form_without_evidence",
                "governance": {
                    "preferred_form": (
                        "Ask your doctor about treatment options appropriate for you."
                    )
                },
                "evidence": {
                    "quotes": ["sentence case"],
                    "unit_ids": ["u_brand_foundation_0_0022"],
                },
            },
            "governance.preferred_form",
        ),
    ],
)
def test_present_optional_literal_without_evidence_is_quarantined(
    units: list[SourceUnit],
    kind: EntityKind,
    entity: dict[str, Any],
    field: str,
) -> None:
    result = verify_entities({kind: [entity]}, units)
    record = next(
        item for item in result.records_by_entity[entity["id"]] if item.field == field
    )
    assert record.value_check.status == "fail"
    assert record.verification == "unverified"
    assert [entry.entity_id for entry in result.quarantine] == [entity["id"]]


def test_null_token_values_are_not_quarantined(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "tok_null_values",
        "token_type": "color",
        "value": {
            "default": None,
            "variants": [{"value": None, "when": {"theme": "dark"}}],
        },
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    result = verify_entities({"token_semantic": [entity]}, units)
    concrete_records = [
        record
        for record in result.records_by_entity[entity["id"]]
        if record.field != ""
    ]
    assert {record.field for record in concrete_records} == {
        "value.default",
        "value.variants[0].value",
    }
    assert all(record.value_check.status == "n/a" for record in concrete_records)
    assert result.quarantine == []


@pytest.mark.parametrize(
    ("body", "quote", "match"),
    [
        ("Quality  you can trust", "Quality you can trust", "normalized"),
        ("Quality you can trust", "Quality you can trusst", "fuzzy"),
    ],
)
def test_template_body_nonexact_never_passes_and_quarantines(
    units: list[SourceUnit],
    body: str,
    quote: str,
    match: str,
) -> None:
    entity: dict[str, Any] = {
        "id": f"tpl_{match}_body",
        "body": body,
        "body_evidence": {
            "quotes": [quote],
            "unit_ids": ["u_layout_constraints_0_0026"],
        },
        "evidence": {
            "quotes": ["Quality  you can trust"],
            "unit_ids": ["u_layout_constraints_0_0026"],
        },
    }
    result = verify_entities({"template": [entity]}, units, fuzzy_min_ratio=0.85)
    record = next(r for r in result.records_by_entity[entity["id"]] if r.field == "body")
    assert record.spans[0].match == match
    assert record.verification == "unverified"
    assert record.value_check.status == "fail"
    assert [entry.entity_id for entry in result.quarantine] == [entity["id"]]


def test_variant_value_evidence_sibling(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "tok_minibible_sem_cta_button_fill",
        "token_type": "color",
        "value": {
            "default": "#01A47E",
            "default_evidence": {
                "quotes": ["#01A47E"],
                "unit_ids": ["u_brand_foundation_0_0004"],
            },
            "variants": [
                {
                    "value": "#FFFFFF",
                    "evidence": {
                        "quotes": ["white (#FFFFFF)"],
                        "unit_ids": ["u_brand_foundation_0_0010"],
                    },
                    "when": {"background_group": "dark"},
                }
            ],
        },
        "evidence": {
            "quotes": ["white (#FFFFFF)"],
            "unit_ids": ["u_brand_foundation_0_0010"],
        },
    }
    result = verify_entities({"token_semantic": [entity]}, units)
    variant = next(
        r for r in result.records_by_entity[entity["id"]] if r.field == "value.variants[0].value"
    )
    assert variant.verification == "value_verified"
    assert variant.spans[0].match in {"exact", "normalized"}


def test_missing_field_evidence_is_explicit_unverified(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "tok_entity_only_evidence",
        "token_type": "color",
        "value": {"default": "#01A47E", "variants": None},
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    result = verify_entities({"token_primitive": [entity]}, units)
    root = next(r for r in result.records_by_entity[entity["id"]] if r.field == "")
    default = next(r for r in result.records_by_entity[entity["id"]] if r.field == "value.default")
    assert root.verification == "span_verified"
    assert default.verification == "unverified"
    assert "missing evidence" in (default.value_check.detail or "")


@pytest.mark.parametrize(
    ("kind", "entity"),
    [
        (
            "rule",
            {
                "id": "rule_effect_snippets",
                "effect": {"value": "title_case"},
                "effect_evidence": {
                    "quotes": ["title case"],
                    "unit_ids": ["u_layout_constraints_0_0030"],
                },
                "snippets": ["Quality you can trust"],
                "snippets_evidence": {
                    "quotes": ['"Quality you can trust"'],
                    "unit_ids": ["u_layout_constraints_0_0026"],
                },
                "evidence": {
                    "quotes": ["title case"],
                    "unit_ids": ["u_layout_constraints_0_0030"],
                },
            },
        ),
        (
            "template",
            {
                "id": "tpl_hero",
                "body": "Hero headline copy",
                "body_evidence": {
                    "quotes": ["Hero headline copy: We're here for you"],
                    "unit_ids": ["u_layout_constraints_0_0028"],
                },
                "evidence": {
                    "quotes": ["Hero headline copy"],
                    "unit_ids": ["u_layout_constraints_0_0028"],
                },
            },
        ),
        (
            "asset",
            {
                "id": "asset_logo",
                "name": "Primary logo",
                "evidence": {
                    "quotes": ["Primary logo"],
                    "unit_ids": ["u_brand_foundation_0_0004"],
                },
            },
        ),
        (
            "subtype",
            {
                "id": "subtype_cta",
                "name": "CTA block",
                "evidence": {
                    "quotes": ["at most one primary CTA"],
                    "unit_ids": ["u_layout_constraints_0_0004"],
                },
            },
        ),
    ],
)
def test_evidence_paths_for_kind(
    units: list[SourceUnit],
    kind: EntityKind,
    entity: dict[str, Any],
) -> None:
    result = verify_entities({kind: [entity]}, units, fuzzy_min_ratio=0.85)
    fields = {record.field for record in result.records_by_entity[entity["id"]]}
    assert fields == set(EVIDENCE_PATHS[kind]) or (
        kind in {"token_primitive", "token_semantic"}
        and fields >= {"", "value.default"}
    )


def test_reverse_index_lists_verified_citations(units: list[SourceUnit]) -> None:
    payload = _load_json("llm/tokens_primitive/r0_001.json")
    result = verify_entities({"token_primitive": payload["tokens"]}, units)
    for entity_id, records in result.records_by_entity.items():
        for record in records:
            if record.verification not in {"span_verified", "value_verified"}:
                continue
            for span in record.spans:
                if span.match == "failed":
                    continue
                for unit_id in span.unit_ids:
                    assert entity_id in result.by_unit[unit_id]


def test_reverse_index_excludes_failed_quote_hull(units: list[SourceUnit]) -> None:
    entity: dict[str, Any] = {
        "id": "asset_mixed_quotes",
        "evidence": {
            "quotes": [
                "Primary Green #01A47E",
                "this quote is absent from every cited unit",
            ],
            "unit_ids": [
                "u_brand_foundation_0_0004",
                "u_brand_foundation_0_0005",
            ],
        },
    }
    result = verify_entities({"asset": [entity]}, units)
    record = result.records_by_entity[entity["id"]][0]
    assert record.verification == "span_verified"
    assert {span.match for span in record.spans} == {"exact", "failed"}
    assert result.by_unit["u_brand_foundation_0_0004"] == [entity["id"]]
    assert "u_brand_foundation_0_0005" not in result.by_unit


@pytest.mark.parametrize(
    ("key", "malformed"),
    [
        ("quotes", [123]),
        ("unit_ids", [123]),
        ("quotes", "not-a-list"),
        ("unit_ids", "not-a-list"),
    ],
)
def test_malformed_evidence_raises_typed_error_with_entity_and_path(
    units: list[SourceUnit],
    key: str,
    malformed: object,
) -> None:
    evidence: dict[str, object] = {
        "quotes": ["Primary Green #01A47E"],
        "unit_ids": ["u_brand_foundation_0_0004"],
    }
    evidence[key] = malformed
    entity = {
        "id": "tok_malformed",
        "token_type": "color",
        "value": {
            "default": "#01A47E",
            "default_evidence": evidence,
            "variants": None,
        },
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    with pytest.raises(ProvenanceError, match=r"tok_malformed/value\.default"):
        verify_entities({"token_primitive": [entity]}, units)


def test_active_entities_excludes_quarantined(units: list[SourceUnit]) -> None:
    good = {
        "id": "tok_good",
        "token_type": "color",
        "value": {
            "default": "#01A47E",
            "default_evidence": {
                "quotes": ["Primary Green #01A47E"],
                "unit_ids": ["u_brand_foundation_0_0004"],
            },
            "variants": None,
        },
        "evidence": {
            "quotes": ["Primary Green #01A47E"],
            "unit_ids": ["u_brand_foundation_0_0004"],
        },
    }
    bad = _load_json("llm/corrupt_bad_quote/001.json")["tokens"][0]
    entities = {"token_primitive": [good, bad]}
    result = verify_entities(entities, units)
    active = active_entities(result, entities)
    assert len(active["token_primitive"]) == 1
    assert active["token_primitive"][0]["id"] == good["id"]
    assert len(result.records_by_entity[bad["id"]]) > 0


def test_write_provenance_is_deterministic(tmp_path: Path, units: list[SourceUnit]) -> None:
    payload = _load_json("llm/tokens_primitive/r0_001.json")
    result = verify_entities({"token_primitive": payload["tokens"][:2]}, units)
    write_provenance(result, tmp_path)
    first = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    write_provenance(result, tmp_path)
    second = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert first == second
    assert (tmp_path / "provenance" / "_by_unit.json").exists()
    assert (tmp_path / "quarantine.json").exists()


def test_write_provenance_removes_stale_entity_sidecars(
    tmp_path: Path,
    units: list[SourceUnit],
) -> None:
    payload = _load_json("llm/tokens_primitive/r0_001.json")
    first = verify_entities({"token_primitive": payload["tokens"][:2]}, units)
    write_provenance(first, tmp_path)
    stale_id = payload["tokens"][1]["id"]
    stale_path = tmp_path / "provenance" / f"{stale_id}.json"
    assert stale_path.exists()

    second = verify_entities({"token_primitive": payload["tokens"][:1]}, units)
    write_provenance(second, tmp_path)

    assert not stale_path.exists()
    assert (tmp_path / "provenance" / "_by_unit.json").exists()
    assert {
        path.name
        for path in (tmp_path / "provenance").glob("*.json")
        if path.name != "_by_unit.json"
    } == {f"{payload['tokens'][0]['id']}.json"}


def test_quarantine_entry_and_result_types(units: list[SourceUnit]) -> None:
    payload = _load_json("llm/corrupt_bad_quote/001.json")
    result = verify_entities({"token_primitive": payload["tokens"]}, units)
    assert isinstance(result, ProvenanceResult)
    assert isinstance(result.quarantine[0], QuarantineEntry)
    assert issubclass(ProvenanceResult, BaseModel)
    assert issubclass(QuarantineEntry, BaseModel)
    assert result.schema_version == "2.0"
    assert result.quarantine[0].schema_version == "2.0"


def test_provenance_result_collection_defaults_are_not_shared() -> None:
    first = ProvenanceResult()
    second = ProvenanceResult()
    first.by_unit["u1"] = ["entity"]
    first.records_by_entity["entity"] = []
    first.quarantine.append(
        QuarantineEntry(
            entity_id="entity",
            entity_kind="asset",
            reason="test",
        )
    )
    assert second.by_unit == {}
    assert second.records_by_entity == {}
    assert second.quarantine == []
