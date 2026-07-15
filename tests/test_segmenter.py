"""WP-03 S0 Markdown segmenter tests."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from indexing_v2.contracts import SourceUnit, read_jsonl
from indexing_v2.extraction.segmenter import (
    STAGE_VERSION,
    normalize_line_endings,
    run_segmenter,
    segment_bible,
)
from tests.fakes import FIXTURE_ROOT, MINIBIBLE_BRAND

FIXTURE_BIBLE = json.loads((FIXTURE_ROOT / "bible.json").read_text(encoding="utf-8"))["website"]
EXPECTED_UNITS_PATH = FIXTURE_ROOT / "expected" / "units.jsonl"
EXPECTED_BLOBS_PATH = FIXTURE_ROOT / "blobs.json"


def _load_expected_units() -> list[SourceUnit]:
    return read_jsonl(EXPECTED_UNITS_PATH, SourceUnit)


def _load_expected_blobs() -> dict[str, str]:
    return json.loads(EXPECTED_BLOBS_PATH.read_text(encoding="utf-8"))


def _reconstruct(blob: str, units: list[SourceUnit]) -> str:
    doc_units = sorted(units, key=lambda u: u.ordinal)
    return "".join(blob[u.start : u.end] for u in doc_units)


@pytest.fixture
def expected_units() -> list[SourceUnit]:
    return _load_expected_units()


@pytest.fixture
def expected_blobs() -> dict[str, str]:
    return _load_expected_blobs()


def test_stage_version_is_semver() -> None:
    assert STAGE_VERSION == "1.0.0"


def test_normalize_line_endings_crlf_and_cr() -> None:
    assert normalize_line_endings("a\r\nb\rc") == "a\nb\nc"


def test_minibible_matches_expected_units_and_blobs(expected_units: list[SourceUnit], expected_blobs: dict[str, str]) -> None:
    units = segment_bible(MINIBIBLE_BRAND, FIXTURE_BIBLE)
    blobs = {
        doc_ref: normalize_line_endings(text)
        for category, texts in FIXTURE_BIBLE.items()
        for index, text in enumerate(texts)
        for doc_ref in [f"{category}[{index}]"]
    }
    assert units == expected_units
    assert blobs == expected_blobs


def test_exact_blob_reconstruction(expected_units: list[SourceUnit], expected_blobs: dict[str, str]) -> None:
    units = segment_bible(MINIBIBLE_BRAND, FIXTURE_BIBLE)
    for doc_ref, blob in expected_blobs.items():
        doc_units = [u for u in units if u.doc_ref == doc_ref]
        assert _reconstruct(blob, doc_units) == blob


def test_segmentation_is_deterministic() -> None:
    first = segment_bible(MINIBIBLE_BRAND, FIXTURE_BIBLE)
    second = segment_bible(MINIBIBLE_BRAND, FIXTURE_BIBLE)
    assert first == second


def test_reversed_category_order_produces_identical_artifact_order(tmp_path: Path) -> None:
    forward = {"alpha": ["Alpha.\n"], "zeta": ["Zeta.\n"]}
    reversed_order = dict(reversed(list(forward.items())))

    assert segment_bible(MINIBIBLE_BRAND, forward) == segment_bible(
        MINIBIBLE_BRAND, reversed_order
    )
    run_segmenter(MINIBIBLE_BRAND, forward, tmp_path / "forward")
    run_segmenter(MINIBIBLE_BRAND, reversed_order, tmp_path / "reversed")
    for artifact in ("units.jsonl", "blobs.json"):
        assert (tmp_path / "forward" / artifact).read_bytes() == (
            tmp_path / "reversed" / artifact
        ).read_bytes()


def test_run_segmenter_writes_canonical_artifacts(tmp_path: Path, expected_units: list[SourceUnit], expected_blobs: dict[str, str]) -> None:
    units = run_segmenter(MINIBIBLE_BRAND, FIXTURE_BIBLE, tmp_path)
    assert units == expected_units
    assert read_jsonl(tmp_path / "units.jsonl", SourceUnit) == expected_units
    assert json.loads((tmp_path / "blobs.json").read_text(encoding="utf-8")) == expected_blobs


def test_crlf_input_normalizes_before_offsets() -> None:
    bible = {"notes": ["Line one.\r\nLine two.\r\n"]}
    units = segment_bible(MINIBIBLE_BRAND, bible)
    blob = normalize_line_endings(bible["notes"][0])
    assert _reconstruct(blob, units) == blob
    assert "\r" not in blob
    assert [u.kind for u in units] == ["sentence", "sentence"]


def test_nested_and_wrapped_list_items() -> None:
    bible = {
        "lists": [
            "- outer one\n  wrapped line\n  - nested item\n- outer two\n",
        ]
    }
    units = segment_bible(MINIBIBLE_BRAND, bible)
    blob = bible["lists"][0]
    texts = [u.text for u in units if u.kind == "list_item"]
    assert texts == [
        "- outer one\n  wrapped line\n",
        "  - nested item\n",
        "- outer two\n",
    ]
    assert _reconstruct(blob, units) == blob


def test_multiline_blank_run_after_wrapped_list_is_standalone() -> None:
    blob = "- item\n  wrapped line\n\n\nNext paragraph.\n"
    units = segment_bible(MINIBIBLE_BRAND, {"lists": [blob]})

    assert [(u.kind, u.text) for u in units] == [
        ("list_item", "- item\n  wrapped line\n"),
        ("blank", "\n\n"),
        ("sentence", "Next paragraph.\n"),
    ]
    assert _reconstruct(blob, units) == blob


def test_multiline_blank_run_after_paragraph_is_standalone() -> None:
    blob = "First paragraph.\n\n\nNext paragraph.\n"
    units = segment_bible(MINIBIBLE_BRAND, {"paragraphs": [blob]})

    assert [(u.kind, u.text) for u in units] == [
        ("sentence", "First paragraph.\n"),
        ("blank", "\n\n"),
        ("sentence", "Next paragraph.\n"),
    ]
    assert _reconstruct(blob, units) == blob


def test_escaped_pipe_table_rows() -> None:
    bible = {"tables": ["| col \\| escaped | value |\n| plain | row |\n"]}
    units = segment_bible(MINIBIBLE_BRAND, bible)
    rows = [u.text for u in units if u.kind == "table_row"]
    assert rows == ["| col \\| escaped | value |\n", "| plain | row |\n"]
    assert _reconstruct(bible["tables"][0], units) == bible["tables"][0]


def test_unterminated_code_fence_covers_rest() -> None:
    bible = {"code": ["Intro line.\n\n```python\nprint('x')\nno close\n"]}
    units = segment_bible(MINIBIBLE_BRAND, bible)
    kinds = [u.kind for u in units]
    assert kinds == ["sentence", "blank", "code_block"]
    assert units[-1].text == "```python\nprint('x')\nno close\n"


def test_unicode_headings_and_text() -> None:
    bible = {"intl": ["# Café Rules\n\nUse naïve spacing for 日本語 copy.\n"]}
    units = segment_bible(MINIBIBLE_BRAND, bible)
    assert units[0].text == "# Café Rules\n"
    assert units[0].heading_path == []
    assert units[2].text == "Use naïve spacing for 日本語 copy.\n"
    assert _reconstruct(bible["intl"][0], units) == bible["intl"][0]


def test_sentence_guards_for_abbreviations_quotes_parentheses_backticks_and_decimals() -> None:
    bible = {
        "guards": [
            (
                'Dr. Smith met Fig. 2. Next sentence starts here.\n'
                'Version 2.0 ships soon. Another begins.\n'
                'He said "Stop. Now" loudly. Final line ends.\n'
                'Use `code. token` literally. Done here.\n'
                '(see i.e. nested) Rule applies. After paren.\n'
            )
        ]
    }
    units = segment_bible(MINIBIBLE_BRAND, bible)
    sentences = [u.text for u in units if u.kind == "sentence"]
    assert sentences == [
        "Dr. Smith met Fig. 2. Next sentence starts here.\n",
        "Version 2.0 ships soon. ",
        "Another begins.\n",
        'He said "Stop. Now" loudly. ',
        "Final line ends.\n",
        "Use `code. token` literally. ",
        "Done here.\n",
        "(see i.e. nested) Rule applies. ",
        "After paren.\n",
    ]
    assert _reconstruct(bible["guards"][0], units) == bible["guards"][0]


def test_intra_word_apostrophe_does_not_block_sentence_split() -> None:
    blob = "Don't do this. Next sentence starts.\n"
    units = segment_bible(MINIBIBLE_BRAND, {"apostrophes": [blob]})

    assert [u.text for u in units] == ["Don't do this. ", "Next sentence starts.\n"]
    assert _reconstruct(blob, units) == blob


@pytest.mark.parametrize("possessive", ["brand's", "users'"])
def test_possessive_apostrophe_does_not_block_sentence_split(possessive: str) -> None:
    blob = f"The {possessive} rule applies. Next sentence starts.\n"
    units = segment_bible(MINIBIBLE_BRAND, {"apostrophes": [blob]})

    assert [u.text for u in units] == [
        f"The {possessive} rule applies. ",
        "Next sentence starts.\n",
    ]
    assert _reconstruct(blob, units) == blob


def test_giant_paragraph_splits_without_gaps() -> None:
    chunk = "Alpha beta gamma. " * 200 + "Omega end.\n"
    bible = {"giant": [chunk]}
    units = segment_bible(MINIBIBLE_BRAND, bible)
    blob = chunk
    assert all(u.kind == "sentence" for u in units)
    assert _reconstruct(blob, units) == blob
    assert len(units) == 201


def test_random_substring_reconstruction_property() -> None:
    rng = random.Random(0)
    bible = {
        "mix": [
            "# Title\n\n"
            "Para one. Para two!\n\n"
            "- item\n"
            "| a | b |\n"
            "```js\nx++;\n```\n"
            "Tail sentence?\n"
        ]
    }
    units = segment_bible(MINIBIBLE_BRAND, bible)
    blob = bible["mix"][0]
    for _ in range(40):
        unit = rng.choice(units)
        assert blob[unit.start : unit.end] == unit.text
    assert _reconstruct(blob, units) == blob
