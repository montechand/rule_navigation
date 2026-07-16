"""Tests for §5.4.2 alignment and §5.4.3 verification."""

from __future__ import annotations

import random
import time
from difflib import SequenceMatcher
from pathlib import Path

import pytest

from indexing_v2.contracts import EvidenceSpan, SourceUnit, read_jsonl
from indexing_v2.extraction import align as align_module
from indexing_v2.extraction.align import (
    STAGE_VERSION,
    AlignmentResult,
    _best_fuzzy_windows,
    _fuzzy_candidates,
    _normalize_plain,
    _normalize_with_index_map,
    align_quote,
    align_quote_with_detail,
    check_value_in_span,
    verify_value_path,
)
from indexing_v2.extraction.provenance import STAGE_VERSION as PROVENANCE_STAGE_VERSION

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


def _evenly_edited_fuzzy_case() -> tuple[str, str, str]:
    source = (
        "Before approved teams preserve clear space, typography rhythm, accessible "
        "contrast, and consistent logo placement across every campaign template "
        "after review."
    )
    true_window = source[7:107]
    chars = list(true_window)
    edit_count = 7
    positions = [
        round((index + 1) * len(chars) / (edit_count + 1))
        for index in range(edit_count)
    ]
    for position in positions:
        chars[position] = "¤"
    return source, true_window, "".join(chars)


def _long_repetitive_fuzzy_case() -> tuple[str, str]:
    source = "approved language remains clear and accurate " * 7
    chars = list(source)
    positions = [len(source) // 4, len(source) // 2, 3 * len(source) // 4]
    for position in positions:
        chars[position] = "e" if chars[position] != "e" else "a"
    return source, "".join(chars)


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


@pytest.mark.parametrize(
    ("quote", "unit_text", "expected_core"),
    [
        (
            "Use the approved main logo in every email header.",
            "Intro. Use the approved logo in every email header. Outro.",
            "approved logo in every email header",
        ),
        (
            "Use the approved primary logo, in every email header.",
            "Intro. Use the approved primary logo; in every email header. Outro.",
            "approved primary logo; in every email header",
        ),
        (
            "Maintain at least 4.5:1 contrast for all body copy.",
            "Intro. Maintain at least 4.5:1 contrast for all body. Outro.",
            "Maintain at least 4.5:1 contrast for all body",
        ),
        (
            "Always use the approved primary brand logo with generous clear safe "
            "space around every side in all email header layouts and campaign templates.",
            "Intro. Always use the approved primary brand logo with space around every "
            "side in all email header layouts and campaign templates. Outro.",
            "primary brand logo with space around every side",
        ),
    ],
    ids=["dropped-word", "swapped-punctuation", "truncated-tail", "interior-elision"],
)
def test_fuzzy_equivalence_corpus(
    quote: str,
    unit_text: str,
    expected_core: str,
) -> None:
    unit = SourceUnit(
        unit_id="u_fuzzy_0000",
        brand_id="minibible",
        doc_ref="fuzzy[0]",
        ordinal=0,
        start=100,
        end=100 + len(unit_text),
        kind="sentence",
        text=unit_text,
    )
    candidates = _fuzzy_candidates(quote, unit, True, fuzzy_min_ratio=0.92)

    assert candidates
    assert all(candidate.quality == "fuzzy" for candidate in candidates)
    assert all(candidate.ratio >= 0.92 for candidate in candidates)
    assert any(
        expected_core
        in unit_text[candidate.start - unit.start : candidate.end - unit.start]
        for candidate in candidates
    )


def test_curly_quotes_and_double_spaces_use_normalized_rung() -> None:
    text = "Use “trusted  guidance” in every campaign."
    unit = SourceUnit(
        unit_id="u_normalized_0000",
        brand_id="minibible",
        doc_ref="normalized[0]",
        ordinal=0,
        start=30,
        end=30 + len(text),
        kind="sentence",
        text=text,
    )

    span = align_quote(
        'Use "trusted guidance" in every campaign.',
        {unit.unit_id: unit},
        [unit.unit_id],
    )

    assert span.match == "normalized"
    assert text[span.start - unit.start : span.end - unit.start] == text


def test_best_fuzzy_windows_finds_planted_exact_quotes() -> None:
    rng = random.Random(20260715)
    alphabet = "abcdefghijkmnopqrstuvwxyz "
    for _ in range(50):
        quote = "".join(rng.choice(alphabet) for _ in range(rng.randint(20, 80)))
        prefix = "".join(rng.choice(alphabet) for _ in range(rng.randint(10, 60)))
        suffix = "".join(rng.choice(alphabet) for _ in range(rng.randint(10, 60)))
        windows = _best_fuzzy_windows(quote, prefix + quote + suffix, 0.92)

        assert any(
            (start, end, ratio) == (len(prefix), len(prefix) + len(quote), 1.0)
            for start, end, ratio in windows
        )


def test_best_fuzzy_windows_is_deterministic_and_offsets_are_valid() -> None:
    rng = random.Random(7)
    for _ in range(50):
        quote = "".join(rng.choice("abcde ") for _ in range(40))
        text = "".join(rng.choice("vwxyz ") for _ in range(30)) + quote
        text += "".join(rng.choice("vwxyz ") for _ in range(30))

        first = _best_fuzzy_windows(quote, text, 0.92)
        second = _best_fuzzy_windows(quote, text, 0.92)

        assert first == second
        assert first == sorted(first, key=lambda item: (item[0], item[1]))
        assert all(0 <= start < end <= len(text) for start, end, _ in first)


def test_normalize_plain_matches_indexed_normalization() -> None:
    rng = random.Random(20260716)
    alphabet = [
        "a",
        "B",
        "ß",
        "é",
        "e",
        "\u0301",
        " ",
        "\t",
        "\n",
        "\u2003",
        "“",
        "”",
        "‘",
        "’",
        "!",
    ]
    for _ in range(200):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 100)))
        assert _normalize_plain(text) == _normalize_with_index_map(text)[0]


def test_best_fuzzy_windows_returns_all_sorted_maximal_ties() -> None:
    windows = _best_fuzzy_windows("aaaaba", "ababbaabb", 0.6)

    assert windows == [
        (2, 8, 2 / 3),
        (5, 8, 2 / 3),
    ]
    assert _best_fuzzy_windows("aaaaba", "ababbaabb", 2 / 3) == windows
    assert _best_fuzzy_windows("aaaaba", "ababbaabb", (2 / 3) + 0.001) == []


def test_best_fuzzy_windows_rejects_scattered_short_runs() -> None:
    quote = "abcdefghijklmno"
    text = "a1b2c3d4e5f6g7h8i9j0k"

    assert _best_fuzzy_windows(quote, text, 0.1) == []


@pytest.mark.parametrize(
    ("quote_length", "text_length"),
    [(300, 2_000)],
    ids=["300-by-2000"],
)
def test_best_fuzzy_windows_performance_smoke(
    quote_length: int,
    text_length: int,
) -> None:
    quote = "".join(chr(0x1000 + index) for index in range(quote_length))
    filler_length = (text_length - quote_length) // 2
    text = "x" * filler_length
    text += quote[:149] + "x" + quote[150:]
    text += "y" * (text_length - len(text))

    started = time.perf_counter()
    windows = _best_fuzzy_windows(quote, text, 0.92)
    elapsed = time.perf_counter() - started

    assert len(text) == text_length
    assert windows
    assert elapsed < 1.0


def test_long_repetitive_quote_scores_without_autojunk() -> None:
    source, quote = _long_repetitive_fuzzy_case()
    default_ratio = SequenceMatcher(None, quote, source).ratio()
    no_junk_ratio = SequenceMatcher(
        None,
        quote,
        source,
        autojunk=False,
    ).ratio()

    assert len(quote) >= 220
    assert len(source) >= 200
    assert max(source.count(char) for char in set(source)) / len(source) > 0.01
    assert default_ratio < 0.92
    assert no_junk_ratio >= 0.92

    windows = _best_fuzzy_windows(quote, source, 0.92)
    assert windows == [(0, len(source), no_junk_ratio)]


def test_long_repetitive_non_value_quote_is_fuzzy_verified() -> None:
    source, quote = _long_repetitive_fuzzy_case()
    unit = SourceUnit(
        unit_id="u_autojunk_e2e_0000",
        brand_id="minibible",
        doc_ref="autojunk-e2e[0]",
        ordinal=0,
        start=125,
        end=125 + len(source),
        kind="sentence",
        text=source,
    )

    result = verify_value_path(
        field_path="rule_text",
        token_type="rule",
        raw_value=None,
        quote=quote,
        units_by_id={unit.unit_id: unit},
        cited_unit_ids=[unit.unit_id],
    )

    assert result.verification == "span_verified"
    assert result.span.match == "fuzzy"
    assert (result.span.start, result.span.end) == (unit.start, unit.end)


def test_multi_anchor_recalls_evenly_distributed_sparse_edits() -> None:
    source, true_window, quote = _evenly_edited_fuzzy_case()
    matcher = SequenceMatcher(None, quote, true_window, autojunk=False)
    anchor = matcher.find_longest_match(0, len(quote), 0, len(true_window))
    assert len(quote) == 100
    assert matcher.ratio() >= 0.93
    assert anchor.size < len(quote) // 4

    unit = SourceUnit(
        unit_id="u_multi_anchor_0000",
        brand_id="minibible",
        doc_ref="multi-anchor[0]",
        ordinal=0,
        start=200,
        end=200 + len(source),
        kind="sentence",
        text=source,
    )
    candidates = _fuzzy_candidates(quote, unit, True, fuzzy_min_ratio=0.92)

    assert candidates
    assert all(candidate.ratio >= 0.92 for candidate in candidates)
    assert any(
        true_window[15:-15]
        in source[candidate.start - unit.start : candidate.end - unit.start]
        for candidate in candidates
    )


def test_multi_anchor_rejects_blocks_scattered_over_wide_extent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blocks = [
        "".join(chr(0x1000 + block_index * 6 + offset) for offset in range(6))
        for block_index in range(10)
    ]
    quote = "|".join(blocks)
    text = ("~" * 30).join(blocks)
    matcher = SequenceMatcher(None, quote, text, autojunk=False)
    counted = [block for block in matcher.get_matching_blocks() if block.size >= 3]
    assert sum(block.size for block in counted) >= 0.75 * len(quote)
    for first_index, first in enumerate(counted):
        for last_index in range(first_index, len(counted)):
            last = counted[last_index]
            coverage = sum(
                block.size
                for block in counted[first_index : last_index + 1]
            )
            if coverage >= 0.75 * len(quote):
                assert (last.b + last.size) - first.b > 1.2 * len(quote)

    def refine_forbidden(
        quote_norm: str,
        text_norm: str,
        fuzzy_min_ratio: float,
        projected_start: int,
        projected_end: int,
    ) -> list[tuple[int, int, float]]:
        raise AssertionError("spread blocks must be rejected before scoring")

    monkeypatch.setattr(align_module, "_refine_window", refine_forbidden)
    assert _best_fuzzy_windows(quote, text, 0.5) == []


def test_multi_anchor_rejects_insufficient_local_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = "".join(chr(0x2000 + offset) for offset in range(8))
    second = "".join(chr(0x2100 + offset) for offset in range(8))
    quote = first + ("q" * 12) + second + ("r" * 12)
    text = first + ("x" * 12) + second + ("y" * 12)
    matcher = SequenceMatcher(None, quote, text, autojunk=False)
    counted = [block for block in matcher.get_matching_blocks() if block.size >= 3]
    assert len(counted) == 2
    assert (counted[-1].b + counted[-1].size) - counted[0].b <= 1.2 * len(quote)
    assert sum(block.size for block in counted) < 0.75 * len(quote)

    def refine_forbidden(
        quote_norm: str,
        text_norm: str,
        fuzzy_min_ratio: float,
        projected_start: int,
        projected_end: int,
    ) -> list[tuple[int, int, float]]:
        raise AssertionError("low-coverage blocks must be rejected before scoring")

    monkeypatch.setattr(align_module, "_refine_window", refine_forbidden)
    assert _best_fuzzy_windows(quote, text, 0.1) == []


def test_multi_anchor_attempt_still_requires_final_ratio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, true_window, quote = _evenly_edited_fuzzy_case()
    matcher = SequenceMatcher(None, quote, true_window, autojunk=False)
    assert matcher.ratio() == pytest.approx(0.93)
    anchor = matcher.find_longest_match(0, len(quote), 0, len(true_window))
    assert anchor.size < len(quote) // 4
    refine_calls = 0
    original_refine = align_module._refine_window

    def recording_refine(
        quote_norm: str,
        text_norm: str,
        fuzzy_min_ratio: float,
        projected_start: int,
        projected_end: int,
    ) -> list[tuple[int, int, float]]:
        nonlocal refine_calls
        refine_calls += 1
        return original_refine(
            quote_norm,
            text_norm,
            fuzzy_min_ratio,
            projected_start,
            projected_end,
        )

    monkeypatch.setattr(align_module, "_refine_window", recording_refine)
    assert _best_fuzzy_windows(quote, source, 0.99) == []
    assert refine_calls == 1


@pytest.mark.parametrize(
    ("quote", "text", "expected"),
    [
        (
            "Use the approved main logo in every email header.",
            "Intro. Use the approved logo in every email header. Outro.",
            [(6, 51, 0.9361702127659575)],
        ),
        (
            "Use the approved primary logo, in every email header.",
            "Intro. Use the approved primary logo; in every email header. Outro.",
            [(7, 60, 0.9811320754716981)],
        ),
        (
            "Maintain at least 4.5:1 contrast for all body copy.",
            "Intro. Maintain at least 4.5:1 contrast for all body. Outro.",
            [(7, 55, 0.9494949494949495)],
        ),
    ],
    ids=["dropped-word", "swapped-punctuation", "truncated-tail"],
)
def test_single_anchor_fast_path_is_byte_equivalent(
    quote: str,
    text: str,
    expected: list[tuple[int, int, float]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quote_norm, _ = _normalize_with_index_map(quote)
    text_norm, _ = _normalize_with_index_map(text)
    matcher = SequenceMatcher(None, quote_norm, text_norm, autojunk=False)
    anchor = matcher.find_longest_match(
        0,
        len(quote_norm),
        0,
        len(text_norm),
    )
    assert anchor.size >= max(3, len(quote_norm) // 4)

    def cluster_forbidden(
        matcher: SequenceMatcher[str],
        quote_len: int,
        text_len: int,
    ) -> tuple[int, int] | None:
        raise AssertionError("single-anchor fast path must not use cluster fallback")

    monkeypatch.setattr(align_module, "_multi_anchor_projection", cluster_forbidden)
    assert _best_fuzzy_windows(quote_norm, text_norm, 0.92) == expected


def test_multi_anchor_results_are_deterministic_valid_and_above_threshold() -> None:
    source, _, quote = _evenly_edited_fuzzy_case()
    first = _best_fuzzy_windows(quote, source, 0.92)
    second = _best_fuzzy_windows(quote, source, 0.92)

    assert first == second
    assert first
    assert all(
        0 <= start < end <= len(source) and ratio >= 0.92
        for start, end, ratio in first
    )


def test_passing_single_anchor_is_never_rejected() -> None:
    rng = random.Random(20260717)
    for _ in range(50):
        quote = "".join(rng.choice("abcdefghijk ") for _ in range(60))
        prefix = "".join(rng.choice("uvwxyz ") for _ in range(20))
        suffix = "".join(rng.choice("uvwxyz ") for _ in range(20))
        text = prefix + quote + suffix
        matcher = SequenceMatcher(None, quote, text, autojunk=False)
        anchor = matcher.find_longest_match(0, len(quote), 0, len(text))

        assert anchor.size >= max(3, len(quote) // 4)
        assert _best_fuzzy_windows(quote, text, 0.92)


def test_non_value_evenly_edited_quote_uses_fuzzy_last_resort() -> None:
    source, _, quote = _evenly_edited_fuzzy_case()
    unit = SourceUnit(
        unit_id="u_multi_anchor_e2e_0000",
        brand_id="minibible",
        doc_ref="multi-anchor-e2e[0]",
        ordinal=0,
        start=75,
        end=75 + len(source),
        kind="sentence",
        text=source,
    )

    result = verify_value_path(
        field_path="rule_text",
        token_type="rule",
        raw_value=None,
        quote=quote,
        units_by_id={unit.unit_id: unit},
        cited_unit_ids=[unit.unit_id],
    )

    assert result.verification == "span_verified"
    assert result.span.match == "fuzzy"


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
    assert result.span.match == "exact"
    unit = units_by_id["u_brand_foundation_0_0004"]
    assert result.span.start == unit.start + unit.text.index(quote)
    assert result.span.end == result.span.start + len(quote)


def test_value_with_sparse_quote_edit_is_verified_at_unit_granularity() -> None:
    text = "Primary Green #01A47E is the approved brand color."
    unit = SourceUnit(
        unit_id="u_value_sparse_0000",
        brand_id="minibible",
        doc_ref="value-sparse[0]",
        ordinal=0,
        start=100,
        end=100 + len(text),
        kind="sentence",
        text=text,
    )

    result = verify_value_path(
        field_path="value.default",
        token_type="color",
        raw_value="#01A47E",
        quote="Primary Grene #01A47E is the approved brand color.",
        units_by_id={unit.unit_id: unit},
        cited_unit_ids=[unit.unit_id],
    )

    assert result.verification == "value_verified"
    assert result.value_check.status == "pass"
    assert result.span.match == "unit"
    assert result.span.unit_ids == [unit.unit_id]
    assert (result.span.start, result.span.end) == (unit.start, unit.end)


def test_value_containment_miss_never_consults_fuzzy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = "Primary Green #01A47E is the approved brand color."
    unit = SourceUnit(
        unit_id="u_value_miss_0000",
        brand_id="minibible",
        doc_ref="value-miss[0]",
        ordinal=0,
        start=0,
        end=len(text),
        kind="sentence",
        text=text,
    )
    quote = "Primary Green #01A47F is the approved brand color."
    assert (
        align_quote(
            quote,
            {unit.unit_id: unit},
            [unit.unit_id],
        ).match
        == "fuzzy"
    )

    def fuzzy_forbidden(
        quote_norm: str,
        text_norm: str,
        fuzzy_min_ratio: float,
    ) -> list[tuple[int, int, float]]:
        raise AssertionError("value verification must not consult fuzzy alignment")

    monkeypatch.setattr(align_module, "_best_fuzzy_windows", fuzzy_forbidden)
    result = verify_value_path(
        field_path="value.default",
        token_type="color",
        raw_value="#01A47F",
        quote=quote,
        units_by_id={unit.unit_id: unit},
        cited_unit_ids=[unit.unit_id],
    )

    assert result.verification == "unverified"
    assert result.value_check.status == "fail"
    assert result.span.match == "failed"


def test_value_present_in_unit_but_absent_from_quote_fails_witness_check() -> None:
    text = "Primary Green is approved. Color #01A47E."
    unit = SourceUnit(
        unit_id="u_value_witness_0000",
        brand_id="minibible",
        doc_ref="value-witness[0]",
        ordinal=0,
        start=40,
        end=40 + len(text),
        kind="sentence",
        text=text,
    )

    result = verify_value_path(
        field_path="value.default",
        token_type="color",
        raw_value="#01A47E",
        quote="Primary Green is approved.",
        units_by_id={unit.unit_id: unit},
        cited_unit_ids=[unit.unit_id],
    )

    assert result.verification == "unverified"
    assert result.value_check.status == "fail"
    assert result.value_check.detail == "quote missing normalized value literal"
    assert result.span.match == "unit"


def test_value_widens_to_actual_neighbor_unit() -> None:
    first_text = "Typography guidance only."
    second_text = "Primary Green #01A47E is approved."
    first = SourceUnit(
        unit_id="u_value_widen_0000",
        brand_id="minibible",
        doc_ref="value-widen[0]",
        ordinal=0,
        start=0,
        end=len(first_text),
        kind="sentence",
        text=first_text,
    )
    second = SourceUnit(
        unit_id="u_value_widen_0001",
        brand_id="minibible",
        doc_ref="value-widen[0]",
        ordinal=1,
        start=first.end,
        end=first.end + len(second_text),
        kind="sentence",
        text=second_text,
    )

    result = verify_value_path(
        field_path="value.default",
        token_type="color",
        raw_value="#01A47E",
        quote=second_text,
        units_by_id={first.unit_id: first, second.unit_id: second},
        cited_unit_ids=[first.unit_id],
    )

    assert result.verification == "value_verified"
    assert result.value_check.status == "pass"
    assert result.span.match == "exact"
    assert result.span.unit_ids == [second.unit_id]
    assert (result.span.start, result.span.end) == (second.start, second.end)
    assert result.detail == "widened"


def test_non_value_cross_unit_containment_skips_fuzzy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_text = "The approved logo "
    second_text = "usage is mandatory."
    first = SourceUnit(
        unit_id="u_witness_cross_0000",
        brand_id="minibible",
        doc_ref="witness-cross[0]",
        ordinal=0,
        start=10,
        end=10 + len(first_text),
        kind="sentence",
        text=first_text,
    )
    second = SourceUnit(
        unit_id="u_witness_cross_0001",
        brand_id="minibible",
        doc_ref="witness-cross[0]",
        ordinal=1,
        start=first.end,
        end=first.end + len(second_text),
        kind="sentence",
        text=second_text,
    )

    def fuzzy_forbidden(
        quote_norm: str,
        text_norm: str,
        fuzzy_min_ratio: float,
    ) -> list[tuple[int, int, float]]:
        raise AssertionError("contained non-value quote must not consult fuzzy")

    monkeypatch.setattr(align_module, "_best_fuzzy_windows", fuzzy_forbidden)
    result = verify_value_path(
        field_path="",
        token_type="asset",
        raw_value=None,
        quote="approved logo usage",
        units_by_id={first.unit_id: first, second.unit_id: second},
        cited_unit_ids=[second.unit_id, first.unit_id],
    )

    assert result.verification == "span_verified"
    assert result.span.match == "unit"
    assert result.span.unit_ids == [first.unit_id, second.unit_id]
    assert (result.span.start, result.span.end) == (first.start, second.end)


def test_non_value_sparse_edit_uses_fuzzy_last_resort() -> None:
    text = "Always retain clear space around the approved logo."
    unit = SourceUnit(
        unit_id="u_witness_fuzzy_0000",
        brand_id="minibible",
        doc_ref="witness-fuzzy[0]",
        ordinal=0,
        start=25,
        end=25 + len(text),
        kind="sentence",
        text=text,
    )

    result = verify_value_path(
        field_path="",
        token_type="rule",
        raw_value=None,
        quote="Always retain cler space around the approved logo.",
        units_by_id={unit.unit_id: unit},
        cited_unit_ids=[unit.unit_id],
    )

    assert result.verification == "span_verified"
    assert result.span.match == "fuzzy"


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
    assert STAGE_VERSION == "2.1.1"
    assert PROVENANCE_STAGE_VERSION == "1.1.4"


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


def test_fuzzy_alignment_with_typo_spans_two_consecutive_units() -> None:
    first_text = "The approved primary logo must "
    second_text = "retain clear space in every email."
    first = SourceUnit(
        unit_id="u_cross_typo_0000",
        brand_id="minibible",
        doc_ref="cross-typo[0]",
        ordinal=0,
        start=0,
        end=len(first_text),
        kind="sentence",
        text=first_text,
    )
    second = SourceUnit(
        unit_id="u_cross_typo_0001",
        brand_id="minibible",
        doc_ref="cross-typo[0]",
        ordinal=1,
        start=first.end,
        end=first.end + len(second_text),
        kind="sentence",
        text=second_text,
    )
    units = {first.unit_id: first, second.unit_id: second}

    span = align_quote(
        "approved primary logo must retain clear spase in every email",
        units,
        [second.unit_id, first.unit_id],
    )

    assert span.match == "fuzzy"
    assert span.unit_ids == [first.unit_id, second.unit_id]
    assert len(span.unit_ids) == 2
