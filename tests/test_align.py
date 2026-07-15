"""Tests for §5.4.2 alignment and §5.4.3 verification."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from indexing_v2.contracts import EvidenceSpan, SourceUnit, read_jsonl
from indexing_v2.extraction.align import (
    STAGE_VERSION,
    AlignmentResult,
    align_quote,
    align_quote_with_detail,
    check_value_in_span,
    verify_value_path,
)

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "minibible"


@pytest.fixture
def units_by_id() -> dict[str, SourceUnit]:
    rows = read_jsonl(FIXTURE_ROOT / "expected" / "units.jsonl", SourceUnit)
    return {u.unit_id: u for u in rows}


def _blob_slice(units_by_id: dict[str, SourceUnit], span: EvidenceSpan) -> str:
    units = sorted(
        (units_by_id[unit_id] for unit_id in span.unit_ids),
        key=lambda unit: unit.ordinal,
    )
    return "".join(
        unit.text[
            max(span.start, unit.start) - unit.start
            : min(span.end, unit.end) - unit.start
        ]
        for unit in units
    )


def test_exact_alignment_on_fixture_color(units_by_id: dict[str, SourceUnit]) -> None:
    quote = "Primary Green #01A47E"
    span = align_quote(
        quote,
        units_by_id,
        ["u_brand_foundation_0_0004"],
    )
    assert span.match == "exact"
    assert _blob_slice(units_by_id, span) == quote


def test_normalized_alignment_double_spaces(units_by_id: dict[str, SourceUnit]) -> None:
    unit = units_by_id["u_layout_constraints_0_0026"]
    quote = '"Quality you can trust"'
    span = align_quote(quote, units_by_id, [unit.unit_id])
    assert span.match == "normalized"
    raw = _blob_slice(units_by_id, span)
    assert raw == '"Quality  you can trust"'
    assert span.start == unit.start + unit.text.index('"Quality')


def test_normalized_alignment_curly_apostrophe(units_by_id: dict[str, SourceUnit]) -> None:
    unit = units_by_id["u_layout_constraints_0_0028"]
    quote = "Hero headline copy: We're here for you"
    span = align_quote(quote, units_by_id, [unit.unit_id])
    assert span.match == "normalized"
    raw = _blob_slice(units_by_id, span)
    assert "We\u2019re" in raw or "We're" in raw
    assert span.start < span.end


def test_normalized_alignment_maps_decomposed_accent_to_raw_slice() -> None:
    raw = "Cafe\u0301"
    unit = SourceUnit(
        unit_id="u_unicode_0000",
        brand_id="minibible",
        doc_ref="unicode[0]",
        ordinal=0,
        start=10,
        end=10 + len(raw),
        kind="sentence",
        text=raw,
    )
    span = align_quote("CAFÉ", {unit.unit_id: unit}, [unit.unit_id])
    assert span.match == "normalized"
    assert _blob_slice({unit.unit_id: unit}, span) == raw
    assert (span.start, span.end) == (10, 10 + len(raw))


def test_normalized_alignment_maps_casefold_expansion_to_raw_slice() -> None:
    raw = "Straße"
    unit = SourceUnit(
        unit_id="u_casefold_0000",
        brand_id="minibible",
        doc_ref="unicode[0]",
        ordinal=0,
        start=20,
        end=20 + len(raw),
        kind="sentence",
        text=raw,
    )
    result = align_quote_with_detail("STRASSE", {unit.unit_id: unit}, [unit.unit_id])
    span = result.span
    assert span.match == "normalized"
    assert _blob_slice({unit.unit_id: unit}, span) == raw
    assert (span.start, span.end) == (20, 20 + len(raw))
    assert result.detail is None


def test_fuzzy_alignment_when_quote_is_close(units_by_id: dict[str, SourceUnit]) -> None:
    unit = units_by_id["u_brand_foundation_0_0004"]
    quote = "Primary Green #01A47E is the main brand colour"
    span = align_quote(quote, units_by_id, [unit.unit_id], fuzzy_min_ratio=0.85)
    assert span.match in {"fuzzy", "normalized", "exact"}


def test_widen_to_neighbor_unit(units_by_id: dict[str, SourceUnit]) -> None:
    # Quote lives in neighbor u_0004 but model cites u_0005.
    quote = "Primary Green #01A47E"
    span = align_quote(quote, units_by_id, ["u_brand_foundation_0_0005"])
    assert span.match == "fuzzy"
    assert span.unit_ids == ["u_brand_foundation_0_0004"]


def test_failed_alignment_hull(units_by_id: dict[str, SourceUnit]) -> None:
    quote = "this quote does not exist anywhere in the cited units"
    cited = ["u_brand_foundation_0_0004"]
    span = align_quote(quote, units_by_id, cited)
    assert span.match == "failed"
    unit = units_by_id[cited[0]]
    assert span.start == unit.start
    assert span.end == unit.end


def test_ambiguity_prefers_cited_unit(units_by_id: dict[str, SourceUnit]) -> None:
    quote = "#01A47E"
    result = align_quote_with_detail(
        quote,
        units_by_id,
        ["u_brand_foundation_0_0005"],
    )
    assert result.span.match in {"exact", "normalized", "fuzzy"}
    assert result.span.unit_ids[0] == "u_brand_foundation_0_0005"


def test_repeated_equal_quality_quote_reports_ambiguity_and_earliest() -> None:
    text = "Echo now. Echo now."
    unit = SourceUnit(
        unit_id="u_repeat_0000",
        brand_id="minibible",
        doc_ref="repeat[0]",
        ordinal=0,
        start=30,
        end=30 + len(text),
        kind="sentence",
        text=text,
    )
    result = align_quote_with_detail("Echo now", {unit.unit_id: unit}, [unit.unit_id])
    assert result.span.match == "exact"
    assert result.span.start == unit.start
    assert result.detail == "ambiguous(n=2)"


def test_random_true_substrings_are_exact(units_by_id: dict[str, SourceUnit]) -> None:
    rng = random.Random(0)
    for unit in units_by_id.values():
        if len(unit.text) < 8:
            continue
        for _ in range(3):
            start = rng.randint(0, len(unit.text) - 4)
            end = rng.randint(start + 3, min(len(unit.text), start + 40))
            quote = unit.text[start:end]
            span = align_quote(quote, units_by_id, [unit.unit_id])
            assert span.match == "exact"
            assert _blob_slice(units_by_id, span) == quote


def test_check_value_in_span_color(units_by_id: dict[str, SourceUnit]) -> None:
    quote = "Primary Green #01A47E"
    span = align_quote(quote, units_by_id, ["u_brand_foundation_0_0004"])
    check = check_value_in_span("color", "#01A47E", span, units_by_id)
    assert check.status == "pass"


def test_verify_concrete_value_path(units_by_id: dict[str, SourceUnit]) -> None:
    quote = "Primary Green #01A47E"
    result = verify_value_path(
        field_path="value.default",
        token_type="color",
        raw_value="#01A47E",
        quote=quote,
        units_by_id=units_by_id,
        cited_unit_ids=["u_brand_foundation_0_0004"],
    )
    assert result.verification == "value_verified"
    assert result.value_check.status == "pass"


def test_verify_preferred_form_requires_exact(units_by_id: dict[str, SourceUnit]) -> None:
    preferred = "Ask your doctor about treatment options appropriate for you."
    result = verify_value_path(
        field_path="governance.preferred_form",
        token_type="preferred_form",
        raw_value=preferred,
        quote=preferred,
        units_by_id=units_by_id,
        cited_unit_ids=["u_brand_foundation_0_0042"],
    )
    assert result.verification == "value_verified"
    assert result.span.match == "exact"


def test_preferred_form_fuzzy_only_fails(units_by_id: dict[str, SourceUnit]) -> None:
    preferred = "Ask your doctor about treatment options appropriate for you."
    noisy = preferred.replace("doctor", "doctr")
    result = verify_value_path(
        field_path="governance.preferred_form",
        token_type="preferred_form",
        raw_value=preferred,
        quote=noisy,
        units_by_id=units_by_id,
        cited_unit_ids=["u_brand_foundation_0_0042"],
        fuzzy_min_ratio=0.85,
    )
    assert result.verification == "unverified"
    assert result.span.match in {"fuzzy", "failed", "normalized"}
    assert result.span.match != "exact"


def test_corrupt_quote_fixture_path_fails(units_by_id: dict[str, SourceUnit]) -> None:
    quote = "Primary Green #DEADBE is mandatory"
    result = verify_value_path(
        field_path="value.default",
        token_type="color",
        raw_value="#01A47E",
        quote=quote,
        units_by_id=units_by_id,
        cited_unit_ids=["u_brand_foundation_0_0004"],
    )
    assert result.verification == "unverified"
    assert result.value_check.status == "fail"


def test_span_verified_for_non_value_path(units_by_id: dict[str, SourceUnit]) -> None:
    result = verify_value_path(
        field_path="",
        token_type="color",
        raw_value=None,
        quote="sentence case",
        units_by_id=units_by_id,
        cited_unit_ids=["u_brand_foundation_0_0022"],
    )
    assert result.verification == "span_verified"
    assert result.value_check.status == "n/a"


def test_ref_value_is_na(units_by_id: dict[str, SourceUnit]) -> None:
    result = verify_value_path(
        field_path="value.default",
        token_type="color",
        raw_value={"$ref": "tok_x"},
        quote="ignored",
        units_by_id=units_by_id,
        cited_unit_ids=["u_brand_foundation_0_0004"],
    )
    assert result.value_check.status == "n/a"


def test_alignment_result_typed() -> None:
    assert AlignmentResult.__dataclass_fields__["span"]


def test_stage_version_present() -> None:
    assert STAGE_VERSION


def test_no_cross_doc_neighbor_join(units_by_id: dict[str, SourceUnit]) -> None:
    quote = "Primary Green #01A47E"
    span = align_quote(
        quote,
        units_by_id,
        ["u_layout_constraints_0_0030"],
    )
    if span.match != "failed":
        unit = units_by_id[span.unit_ids[0]]
        assert unit.doc_ref == units_by_id["u_layout_constraints_0_0030"].doc_ref


def test_failed_hull_uses_only_first_cited_document() -> None:
    first = SourceUnit(
        unit_id="u_first_0000",
        brand_id="minibible",
        doc_ref="first[0]",
        ordinal=0,
        start=100,
        end=105,
        kind="sentence",
        text="alpha",
    )
    second = SourceUnit(
        unit_id="u_second_0000",
        brand_id="minibible",
        doc_ref="second[0]",
        ordinal=0,
        start=0,
        end=4,
        kind="sentence",
        text="beta",
    )
    units = {first.unit_id: first, second.unit_id: second}
    span = align_quote("not present", units, [first.unit_id, second.unit_id])
    assert span.match == "failed"
    assert span.doc_ref == first.doc_ref
    assert span.unit_ids == [first.unit_id]
    assert (span.start, span.end) == (first.start, first.end)


def test_fuzzy_alignment_spans_consecutive_cited_units() -> None:
    first_text = "The button is bright "
    second_text = "green #ABC today."
    first = SourceUnit(
        unit_id="u_cross_0000",
        brand_id="minibible",
        doc_ref="cross[0]",
        ordinal=0,
        start=0,
        end=len(first_text),
        kind="sentence",
        text=first_text,
    )
    second = SourceUnit(
        unit_id="u_cross_0001",
        brand_id="minibible",
        doc_ref="cross[0]",
        ordinal=1,
        start=first.end,
        end=first.end + len(second_text),
        kind="sentence",
        text=second_text,
    )
    units = {first.unit_id: first, second.unit_id: second}
    quote = "button is bright green #ABC today"
    span = align_quote(quote, units, [second.unit_id, first.unit_id])
    assert span.match == "fuzzy"
    assert span.unit_ids == [first.unit_id, second.unit_id]
    assert (span.start, span.end) == (
        first.start + first.text.index("button"),
        second.start + second.text.index("today") + len("today"),
    )
    assert _blob_slice(units, span) == quote
    assert check_value_in_span("color", "#aabbcc", span, units).status == "pass"
