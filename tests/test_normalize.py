"""Tests for §5.4.1 value normalization."""

from __future__ import annotations

import json

import pytest

from indexing_v2.extraction.normalize import (
    STAGE_VERSION,
    normalize_value,
    value_patterns,
)

_COLOR_TYPES = ["color"]
_DIMENSION_TYPES = ["dimension", "spacing", "padding", "margin"]
_WEIGHT_TYPES = ["weight", "fontWeight"]
_NUMBER_TYPES = ["number", "opacity"]
_RATIO_TYPES = ["ratio"]
_GRADIENT_TYPES = ["gradient"]
_STRING_TYPES = ["alignment", "case", "other.motion"]
_VERBATIM_TYPES = ["preferred_form", "body"]


@pytest.mark.parametrize(
    ("raw", "canon"),
    [
        ("#ABC", "#aabbcc"),
        ("#01A47E", "#01a47e"),
        ("rgb(1,164,126)", "#01a47e"),
        ("Primary Green", "Primary Green"),
    ],
)
def test_normalize_color(raw: str, canon: str) -> None:
    out = normalize_value("color", raw)
    assert out.canon == canon
    assert out.kind in {"color", "color_name"}


@pytest.mark.parametrize(
    ("raw", "canon"),
    [
        ("24 px", "24px"),
        ("24px", "24px"),
        (24, "24px"),
        ("50%", "50%"),
        ("49.52px  1.76px  40px 1.76px", "49.52px 1.76px 40px 1.76px"),
    ],
)
def test_normalize_dimension(raw: object, canon: str) -> None:
    assert normalize_value("dimension", raw).canon == canon


@pytest.mark.parametrize(
    ("raw", "canon"),
    [
        ("regular", "400"),
        ("bold", "700"),
        (700, "700"),
    ],
)
def test_normalize_weight(raw: object, canon: str) -> None:
    assert normalize_value("weight", raw).canon == canon


@pytest.mark.parametrize(
    ("token_type", "raw", "canon"),
    [
        ("opacity", "80%", "0.8"),
        ("number", 5, "5"),
        ("ratio", "5:1", "5:1"),
    ],
)
def test_normalize_number_and_ratio(token_type: str, raw: object, canon: str) -> None:
    assert normalize_value(token_type, raw).canon == canon


def test_normalize_gradient_compact_sorted_json() -> None:
    raw = {
        "angle": 90.0,
        "stops": [{"color": "#ABC", "position": 0}, {"color": "rgb(0,0,0)", "position": 1}],
    }
    out = normalize_value("gradient", raw)
    assert out.kind == "gradient"
    parsed = json.loads(out.canon)
    assert parsed["angle"] == 90
    assert parsed["stops"][0]["color"] == "#aabbcc"
    assert parsed["stops"][1]["color"] == "#000000"
    assert out.canon == json.dumps(parsed, sort_keys=True, separators=(",", ":"))


def test_normalize_enum_string() -> None:
    assert normalize_value("alignment", "  Left  ").canon == "left"


def test_normalize_verbatim_outer_trim_only() -> None:
    inner = "  Ask  your doctor.  "
    out = normalize_value("preferred_form", inner)
    assert out.canon == "Ask  your doctor."
    assert "  " in out.canon


@pytest.mark.parametrize("token_type", _COLOR_TYPES + _DIMENSION_TYPES + _WEIGHT_TYPES)
def test_value_patterns_accept_variants(token_type: str) -> None:
    if token_type == "color":
        canon = "#01a47e"
        haystacks = ["Primary Green #01A47E is mandatory", "#01a47e"]
    elif token_type in _DIMENSION_TYPES:
        canon = "24px"
        haystacks = ["Body text uses 24 px on desktop", "margin 24px", "step 24"]
    else:
        canon = "700"
        haystacks = ["weight bold", "700"]
    patterns = value_patterns(token_type, canon)
    assert any(p.search(text) for p in patterns for text in haystacks)


@pytest.mark.parametrize(
    "cases",
    [
        *[(t, v) for t in _COLOR_TYPES for v in ("#ABC", "#112233", "rgb(1,2,3)")],
        *[(t, v) for t in _DIMENSION_TYPES for v in ("24 px", "24px", 18, "12%")],
        *[(t, v) for t in _WEIGHT_TYPES for v in ("bold", 600)],
        *[(t, v) for t in _NUMBER_TYPES for v in ("80%", 0.5, 3)],
        *[(t, v) for t in _RATIO_TYPES for v in ("5:1",)],
        *[
            (
                "gradient",
                {
                    "angle": 45,
                    "stops": [{"color": "#fff", "position": 0}, {"color": "#000", "position": 1}],
                },
            )
        ],
        *[(t, v) for t in _STRING_TYPES for v in ("  Center  ",)],
        *[(t, v) for t in _VERBATIM_TYPES for v in ("  verbatim  text  ",)],
    ],
)
def test_normalize_idempotent(cases: tuple[str, object]) -> None:
    token_type, raw = cases
    once = normalize_value(token_type, raw)
    twice = normalize_value(token_type, once)
    thrice = normalize_value(token_type, once.canon)
    assert twice == once
    assert thrice == once


def test_normalized_value_object_is_reused() -> None:
    first = normalize_value("color", "#ABC")
    assert normalize_value("color", first) is first


def test_stage_version_present() -> None:
    assert STAGE_VERSION


def test_color_pattern_case_insensitive() -> None:
    patterns = value_patterns("color", "#01a47e")
    assert any(p.search("#01A47E") for p in patterns)


def test_color_pattern_accepts_compact_equivalent() -> None:
    canon = normalize_value("color", "#ABC").canon
    patterns = value_patterns("color", canon)
    assert any(pattern.search("#ABC") for pattern in patterns)
    assert any(pattern.search("#aabbcc") for pattern in patterns)


def test_dimension_patterns_cover_spacing_forms() -> None:
    patterns = value_patterns("dimension", "24px")
    samples = ["24px", "24 px", "24"]
    assert all(any(p.search(s) for p in patterns) for s in samples)


def test_percentage_dimension_pattern_matches_end_of_string() -> None:
    patterns = value_patterns("dimension", "24%")
    assert any(pattern.search("24%") for pattern in patterns)
