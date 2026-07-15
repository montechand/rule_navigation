"""Acceptance tests for the §5.8 lossless DTCG projection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from indexing_v2.tokens_dtcg import (
    STAGE_VERSION,
    DtcgBijectionError,
    DtcgError,
    dtcg_to_tokens,
    export_tokens,
    import_tokens,
    roundtrip_tokens,
    tokens_to_dtcg,
    validate_dtcg_tree,
)
from shared.schemas import BrandToken

NS = "com.solstice.kb.acceptance"
BRAND = "dtcg_test"


def _token(
    token_id: str,
    token_type: str,
    key: str,
    default: Any,
    **fields: Any,
) -> dict[str, Any]:
    return {
        "id": token_id,
        "brand_id": BRAND,
        "token_type": token_type,
        "kind": "primitive",
        "key": key,
        "value": {"default": default, "variants": None},
        "aliases": [],
        "scope": "global",
        "status": "active",
        "version": 1,
        **fields,
    }


def _rich_raw_tokens() -> list[dict[str, Any]]:
    tokens = [
        _token(
            "tok_green",
            "color",
            "color.primary.green",
            "#0A4",
            aliases=["Primary Green", "Brand Teal"],
        ),
        _token("tok_white", "color", "color.neutral.white", "#FFFFFF"),
        _token("tok_blue", "color", "color.primary.blue", "rgb(38, 34, 98)"),
        _token("tok_font", "font", "font.brand.primary", "Avenir, Arial, sans-serif"),
        _token("tok_size", "size", "size.type.h1", 24),
        _token("tok_spacing_spaced", "spacing", "spacing.section.large", "24 px"),
        _token("tok_weight", "weight", "weight.heading.bold", "Bold"),
        _token("tok_line", "line_height", "line_height.heading.normal", 1.25),
        _token("tok_tracking", "letter_spacing", "letter_spacing.heading.tight", "-0.02 em"),
        _token(
            "tok_gradient",
            "gradient",
            "gradient.brand.hero",
            {
                "stops": [
                    {"color": "#ABC", "position": 0},
                    {"color": "rgb(1, 164, 126)", "position": "100%"},
                ],
                "angle": 45.0,
            },
            notes="Hero brand gradient.",
            source="manual",
            provenance_digest="sha256:gradient",
            extraction_meta={"confidence": "high"},
        ),
        _token(
            "tok_radius_four",
            "radius",
            "radius.accent.four_value",
            "120px   6px  120px 6px",
        ),
        _token(
            "tok_type_scale",
            "type_scale",
            "type_scale.heading.h1",
            {
                "font_family": {"$ref": "tok_font"},
                "font_size": {"$ref": "tok_size"},
                "font_weight": {"$ref": "tok_weight"},
                "line_height": {"$ref": "tok_line"},
                "letter_spacing": {"$ref": "tok_tracking"},
            },
        ),
        _token(
            "tok_shadow",
            "shadow",
            "shadow.card.default",
            {
                "color": {"$ref": "tok_blue"},
                "offset_x": "0px",
                "offset_y": "4px",
                "blur_radius": "10px",
                "spread_radius": "0px",
            },
        ),
        _token(
            "tok_border",
            "border",
            "border.card.default",
            {"color": {"$ref": "tok_green"}, "width": "1px", "style": "solid"},
        ),
        _token(
            "tok_other_case",
            "other.case",
            "case.heading.upper",
            "  UPPERCASE  ",
            description="Canonical heading casing.",
        ),
        _token("tok_alignment", "alignment", "alignment.text.center", " Center "),
        _token("tok_icon_style", "icon_style", "icon_style.default", " OUTLINE "),
        _token(
            "tok_image_treatment",
            "image_treatment",
            "image_treatment.hero",
            "full-bleed",
        ),
        _token("tok_motion", "motion", "motion.default", "ease-out"),
        _token("tok_opacity", "opacity", "opacity.overlay.default", "80%"),
        _token("tok_ratio", "ratio", "ratio.palette.primary", "0.30"),
        _token("tok_usage_ratio", "usage_ratio", "usage_ratio.palette.accent", "20%"),
        _token("tok_ratio_text", "ratio", "ratio.layout.wide", "16:9"),
        _token("tok_line_px", "line_height", "line_height.legal.fixed", "18 px"),
        _token("tok_tracking_number", "letter_spacing", "letter_spacing.body.normal", 0),
    ]
    tokens.extend(
        [
            {
                "id": "tok_semantic_background",
                "brand_id": BRAND,
                "token_type": "color",
                "kind": "semantic",
                "key": "section.background",
                "value": {
                    "default": {"$ref": "tok_white"},
                    "variants": [
                        {
                            "when": {"theme": "dark"},
                            "value": {"$ref": "tok_blue"},
                        },
                        {
                            "when": {"breakpoint": "mobile"},
                            "value": {"$ref": "tok_green"},
                        },
                        {
                            "when": {"surface": "print", "content_tag": "hero"},
                            "value": {"$ref": "tok_blue"},
                        },
                    ],
                },
                "element_paths": ["section.background"],
                "aliases": [],
                "scope": "global",
                "notes": None,
                "status": "active",
                "version": 1,
            },
            {
                "id": "tok_gated_teal",
                "brand_id": BRAND,
                "token_type": "color",
                "kind": "semantic",
                "key": "campaign.teal.reserved",
                "value": {"default": {"$ref": "tok_green"}, "variants": None},
                "element_paths": ["campaign.teal.reserved"],
                "aliases": [],
                "tier": "campaign",
                "scope": "campaign:lpga",
                "gated": {
                    "is_gated": True,
                    "gate": {"kind": "content_tag", "value": "lpga"},
                },
                "status": "active",
                "version": 1,
            },
            {
                "id": "tok_semantic_case",
                "brand_id": BRAND,
                "token_type": "other.case",
                "kind": "semantic",
                "key": "heading.case",
                "value": {"default": {"$ref": "tok_other_case"}, "variants": None},
                "element_paths": ["heading.case"],
                "aliases": [],
                "scope": "global",
                "status": "active",
                "version": 1,
            },
        ]
    )
    return tokens


def _model_token() -> BrandToken:
    return BrandToken(
        id="tok_model_spacing",
        brand_id=BRAND,
        token_type="spacing",
        key="spacing.model.explicit",
        value={"default": "24 px", "variants": None},
    )


def _by_id(tokens: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(token["id"]): token for token in tokens}


def _leaf(bundle: dict[str, Any], path: str) -> dict[str, Any]:
    node = bundle["base"]
    for part in path.split("."):
        node = node[part]
    return node


def test_exact_roundtrip_for_raw_dicts_and_model_dump() -> None:
    raw = _rich_raw_tokens()
    model = _model_token()
    expected = raw + [model.model_dump(mode="json")]
    imported = roundtrip_tokens(raw + [model], BRAND, namespace=NS)
    assert _by_id(imported) == _by_id(expected)
    assert imported == sorted(imported, key=lambda token: str(token["id"]))


def test_required_dtcg_value_shapes() -> None:
    bundle = tokens_to_dtcg(_rich_raw_tokens(), namespace=NS)

    size = _leaf(bundle, "size.type.h1")
    assert size == {
        "$type": "dimension",
        "$value": "24px",
        "$extensions": size["$extensions"],
    }
    radius = _leaf(bundle, "radius.accent.four_value")
    assert radius["$type"] == "dimension"
    assert radius["$value"] == "120px 6px 120px 6px"
    spacing = _leaf(bundle, "spacing.section.large")
    assert spacing["$type"] == "dimension"
    assert spacing["$value"] == "24px"
    font = _leaf(bundle, "font.brand.primary")
    assert font["$type"] == "fontFamily"
    assert font["$value"] == ["avenir", "arial", "sans-serif"]
    weight = _leaf(bundle, "weight.heading.bold")
    assert weight["$type"] == "fontWeight"
    assert weight["$value"] == 700

    gradient = _leaf(bundle, "gradient.brand.hero")
    assert gradient["$type"] == "gradient"
    assert gradient["$value"] == [
        {"color": "#aabbcc", "position": 0},
        {"color": "#01a47e", "position": "100%"},
    ]
    assert gradient["$extensions"][NS]["gradient_angle"] == 45
    assert gradient["$description"] == "Hero brand gradient."

    typography = _leaf(bundle, "type_scale.heading.h1")
    assert typography["$type"] == "typography"
    assert typography["$value"] == {
        "fontFamily": "{font.brand.primary}",
        "fontSize": "{size.type.h1}",
        "fontWeight": "{weight.heading.bold}",
        "lineHeight": "{line_height.heading.normal}",
        "letterSpacing": "{letter_spacing.heading.tight}",
    }

    shadow = _leaf(bundle, "shadow.card.default")
    assert shadow["$type"] == "shadow"
    assert shadow["$value"] == {
        "color": "{color.primary.blue}",
        "offsetX": "0px",
        "offsetY": "4px",
        "blur": "10px",
        "spread": "0px",
    }
    border = _leaf(bundle, "border.card.default")
    assert border["$type"] == "border"
    assert border["$value"] == {
        "color": "{color.primary.green}",
        "width": "1px",
        "style": "solid",
    }


def test_number_dimension_and_untyped_string_decisions() -> None:
    bundle = tokens_to_dtcg(_rich_raw_tokens(), namespace=NS)
    assert _leaf(bundle, "color.primary.green")["$value"] == "#00aa44"
    assert _leaf(bundle, "color.neutral.white")["$value"] == "#ffffff"
    assert _leaf(bundle, "color.primary.blue")["$value"] == "#262262"
    assert _leaf(bundle, "line_height.heading.normal")["$type"] == "number"
    assert _leaf(bundle, "line_height.legal.fixed")["$type"] == "dimension"
    assert _leaf(bundle, "line_height.legal.fixed")["$value"] == "18px"
    assert _leaf(bundle, "letter_spacing.heading.tight")["$type"] == "dimension"
    assert _leaf(bundle, "letter_spacing.body.normal")["$type"] == "number"
    assert _leaf(bundle, "opacity.overlay.default")["$type"] == "number"
    assert _leaf(bundle, "opacity.overlay.default")["$value"] == 0.8
    assert _leaf(bundle, "ratio.palette.primary")["$type"] == "number"
    assert _leaf(bundle, "ratio.palette.primary")["$value"] == 0.3
    assert _leaf(bundle, "usage_ratio.palette.accent")["$type"] == "number"
    assert _leaf(bundle, "usage_ratio.palette.accent")["$value"] == 0.2
    assert "$type" not in _leaf(bundle, "ratio.layout.wide")
    assert _leaf(bundle, "ratio.layout.wide")["$value"] == "16:9"

    case = _leaf(bundle, "case.heading.upper")
    assert "$type" not in case
    assert case["$value"] == "uppercase"
    assert case["$description"] == "Canonical heading casing."
    enum_values = {
        "alignment.text.center": "center",
        "icon_style.default": "outline",
        "image_treatment.hero": "full-bleed",
        "motion.default": "ease-out",
    }
    for path, expected in enum_values.items():
        assert "$type" not in _leaf(bundle, path)
        assert _leaf(bundle, path)["$value"] == expected


def test_alias_uses_target_type_or_omits_it() -> None:
    bundle = tokens_to_dtcg(_rich_raw_tokens(), namespace=NS)
    color_alias = _leaf(bundle, "section.background")
    assert color_alias["$value"] == "{color.neutral.white}"
    assert color_alias["$type"] == "color"
    assert color_alias["$type"] != "alias"

    case_alias = _leaf(bundle, "heading.case")
    assert case_alias["$value"] == "{case.heading.upper}"
    assert "$type" not in case_alias


def test_modes_contain_only_single_axis_overrides() -> None:
    bundle = tokens_to_dtcg(_rich_raw_tokens(), namespace=NS)
    assert set(bundle["modes"]) == {
        "breakpoint.mobile.tokens.json",
        "theme.dark.tokens.json",
    }
    mobile = bundle["modes"]["breakpoint.mobile.tokens.json"]
    assert mobile == {
        "section": {
            "background": {
                "$type": "color",
                "$value": "{color.primary.green}",
            }
        }
    }
    for mode in bundle["modes"].values():
        validate_dtcg_tree(mode)


def test_structural_validation_rejects_value_less_metadata_leaf() -> None:
    with pytest.raises(DtcgError, match="malformed leaf without"):
        validate_dtcg_tree({"color": {"bad": {"$type": "color"}}})
    with pytest.raises(DtcgError, match="malformed leaf without"):
        validate_dtcg_tree({"color": {"bad": {"$description": "missing value"}}})
    with pytest.raises(DtcgError, match="also contains groups"):
        validate_dtcg_tree(
            {"color": {"bad": {"$value": "#fff", "nested": {"$value": "#000"}}}}
        )


def test_map_collision_and_non_bijection_fail_hard() -> None:
    parent = _token("tok_parent", "color", "color.primary", "#111111")
    child = _token("tok_child", "color", "color.primary.green", "#01A47E")
    bundle = tokens_to_dtcg([parent, child], namespace=NS)
    assert bundle["map"]["ids_to_paths"] == {
        "tok_child": "color.primary.green",
        "tok_parent": "color.primary_value",
    }
    assert _by_id(roundtrip_tokens([parent, child], BRAND, namespace=NS)) == _by_id(
        [parent, child]
    )

    with pytest.raises(DtcgBijectionError, match="duplicate token id"):
        tokens_to_dtcg([parent, parent], namespace=NS)
    with pytest.raises(DtcgBijectionError, match="duplicate DTCG path"):
        tokens_to_dtcg([parent, dict(parent, id="tok_other")], namespace=NS)

    broken = copy_bundle(bundle)
    broken["map"]["paths_to_ids"]["color.primary.green"] = "tok_wrong"
    with pytest.raises(DtcgBijectionError, match="map mismatch"):
        dtcg_to_tokens(broken, BRAND, namespace=NS)


def copy_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(bundle))


def test_plain_manual_leaf_imports_with_manual_source(tmp_path: Path) -> None:
    output = tmp_path / "design_tokens"
    export_tokens([_token("tok_green", "color", "color.green", "#01A47E")], output)
    base_path = output / "tokens.base.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    base["spacing"] = {
        "manual": {
            "gap": {
                "$type": "dimension",
                "$value": "8px",
                "$description": "Manually added gap.",
            }
        }
    }
    base_path.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    imported = import_tokens(output, BRAND)
    manual = next(token for token in imported if token.get("source") == "dtcg_manual")
    assert manual["id"] == "tok_dtcg_test_spacing_manual_gap"
    assert manual["token_type"] == "dimension"
    assert manual["value"] == {"default": "8px", "variants": None}
    assert manual["notes"] == "Manually added gap."


def test_reexport_removes_stale_modes_and_is_byte_identical(tmp_path: Path) -> None:
    output = tmp_path / "design_tokens"
    export_tokens(_rich_raw_tokens(), output, namespace=NS)
    stale = output / "modes" / "stale.old.tokens.json"
    stale.write_text("{}\n", encoding="utf-8")

    minimal = [_token("tok_green", "color", "color.green", "#01A47E")]
    export_tokens(minimal, output, namespace=NS)
    assert not list((output / "modes").glob("*.tokens.json"))
    first = {
        name: (output / name).read_bytes()
        for name in ("tokens.base.json", "_map.json")
    }
    export_tokens(minimal, output, namespace=NS)
    second = {
        name: (output / name).read_bytes()
        for name in ("tokens.base.json", "_map.json")
    }
    assert first == second
    assert not (output / "config.mjs").exists()


def test_static_style_dictionary_config_is_checked_in() -> None:
    package = Path(__file__).parents[1] / "indexing_v2" / "tokens_dtcg"
    config = package / "style_dictionary" / "config.mjs"
    assert config.exists()
    text = config.read_text(encoding="utf-8")
    assert "css/variables" in text
    assert "scss/variables" in text
    assert "json/flat" in text
    assert not (package / "dtcg.py").exists()
    assert STAGE_VERSION
