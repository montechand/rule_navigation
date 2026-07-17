"""§5.4.1 value normalization registry for KB Extraction v2.

Usage: call ``normalize_value`` for canonical keys and ``value_patterns`` for evidence checks.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

STAGE_VERSION = "1.1.0"

_HEX3_RE = re.compile(r"^#([0-9a-fA-F]{3})$")
_HEX6_RE = re.compile(r"^#([0-9a-fA-F]{6})$")
_RGB_RE = re.compile(
    r"^rgb\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$",
    re.IGNORECASE,
)
_DIM_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*(px|pt|em|rem|%)?$", re.IGNORECASE)
_RATIO_RE = re.compile(r"^\s*(\d+)\s*:\s*(\d+)\s*$")
_PERCENT_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*%\s*$")

_WEIGHT_NAMES: dict[str, str] = {
    "thin": "100",
    "extralight": "200",
    "ultralight": "200",
    "light": "300",
    "regular": "400",
    "normal": "400",
    "medium": "500",
    "semibold": "600",
    "demibold": "600",
    "bold": "700",
    "extrabold": "800",
    "ultrabold": "800",
    "black": "900",
    "heavy": "900",
}

_COLOR_TYPES = frozenset({"color"})
_DIMENSION_TYPES = frozenset(
    {"dimension", "spacing", "padding", "margin", "size", "radius", "breakpoint"}
)
_WEIGHT_TYPES = frozenset({"fontweight", "weight", "font_weight"})
_NUMBER_TYPES = frozenset({"number", "opacity", "line_height", "letter_spacing"})
_RATIO_TYPES = frozenset({"ratio", "usage_ratio"})
_GRADIENT_TYPES = frozenset({"gradient"})
_VERBATIM_TYPES = frozenset({"preferred_form", "body", "template_body"})
_ENUM_STRING_TYPES = frozenset(
    {
        "case",
        "alignment",
        "icon_style",
        "image_treatment",
        "motion",
        "font",
        "fontfamily",
        "type_scale",
        "shadow",
        "border",
    }
)


@dataclass(frozen=True, slots=True)
class NormalizedValue:
  """Canonical scalar for ensemble keys and value verification."""

  canon: str
  kind: str


def _expand_hex3(hex3: str) -> str:
    return "#" + "".join(ch * 2 for ch in hex3.lower())


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def _normalize_color(raw: Any) -> NormalizedValue:
    if isinstance(raw, dict):
        raise TypeError("color normalization expects a scalar, not a mapping")
    text = str(raw).strip()
    m3 = _HEX3_RE.match(text)
    if m3:
        return NormalizedValue(canon=_expand_hex3(m3.group(1)), kind="color")
    m6 = _HEX6_RE.match(text)
    if m6:
        return NormalizedValue(canon="#" + m6.group(1).lower(), kind="color")
    rgb = _RGB_RE.match(text)
    if rgb:
        parts = (int(rgb.group(1)), int(rgb.group(2)), int(rgb.group(3)))
        if any(p < 0 or p > 255 for p in parts):
            raise ValueError(f"rgb components out of range: {text!r}")
        return NormalizedValue(canon=_rgb_to_hex(*parts), kind="color")
    return NormalizedValue(canon=text, kind="color_name")


def _normalize_dimension(raw: Any) -> NormalizedValue:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return NormalizedValue(canon=f"{raw:g}px", kind="dimension")
    text = re.sub(r"\s+", " ", str(raw).strip())
    if not text:
        raise ValueError("empty dimension")
    # Multi-value radius / shorthand: preserve token order, collapse whitespace only.
    if " " in text and not _DIM_RE.match(text):
        return NormalizedValue(canon=text, kind="dimension")
    m = _DIM_RE.match(text)
    if not m:
        return NormalizedValue(canon=text, kind="dimension")
    number, unit = m.group(1), (m.group(2) or "px").lower()
    if "." in number:
        number = number.rstrip("0").rstrip(".") or "0"
    return NormalizedValue(canon=f"{number}{unit}", kind="dimension")


def _normalize_weight(raw: Any) -> NormalizedValue:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return NormalizedValue(canon=str(int(raw)), kind="fontWeight")
    text = str(raw).strip()
    if text.isdigit():
        return NormalizedValue(canon=str(int(text)), kind="fontWeight")
    key = re.sub(r"[\s_-]+", "", text.casefold())
    if key in _WEIGHT_NAMES:
        return NormalizedValue(canon=_WEIGHT_NAMES[key], kind="fontWeight")
    return NormalizedValue(canon=text, kind="fontWeight")


def _normalize_numberish(raw: Any, *, kind: str) -> NormalizedValue:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return NormalizedValue(canon=str(raw) if kind != "opacity" else str(float(raw)), kind=kind)
    text = str(raw).strip()
    pct = _PERCENT_RE.match(text)
    if pct:
        return NormalizedValue(canon=str(float(pct.group(1)) / 100.0), kind=kind)
    if kind == "ratio":
        m = _RATIO_RE.match(text)
        if m:
            return NormalizedValue(canon=f"{int(m.group(1))}:{int(m.group(2))}", kind=kind)
    if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return NormalizedValue(
            canon=str(float(text)) if "." in text else text,
            kind=kind,
        )
    return NormalizedValue(canon=text, kind=kind)


def _normalize_stop_color(stop: Any) -> Any:
    if isinstance(stop, dict) and "color" in stop:
        out = dict(stop)
        out["color"] = _normalize_color(stop["color"]).canon
        return out
    if isinstance(stop, str):
        return _normalize_color(stop).canon
    return stop


def _normalize_gradient(raw: Any) -> NormalizedValue:
    if not isinstance(raw, dict):
        raise TypeError("gradient normalization expects a mapping")
    stops = raw.get("stops")
    if not isinstance(stops, list):
        raise ValueError("gradient.stops must be a list")
    angle_raw = raw.get("angle", 0)
    angle = int(angle_raw)
    payload = {
        "angle": angle,
        "stops": [_normalize_stop_color(s) for s in stops],
    }
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return NormalizedValue(canon=canon, kind="gradient")


def _nfc_outer_trim(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip()


def _normalize_enum_string(raw: Any) -> NormalizedValue:
    text = unicodedata.normalize("NFC", str(raw).strip())
    text = re.sub(r"[\s_-]+", "_", text)
    return NormalizedValue(canon=text.casefold(), kind="string")


def _normalize_verbatim_string(raw: Any) -> NormalizedValue:
    return NormalizedValue(canon=_nfc_outer_trim(str(raw)), kind="verbatim")


def normalize_value(token_type: str, raw: Any) -> NormalizedValue:
    """Return the canonical scalar for ``token_type`` (idempotent)."""
    if isinstance(raw, NormalizedValue):
        return raw

    key = token_type.casefold()

    if key in _GRADIENT_TYPES and isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            raw = parsed

    if key in _COLOR_TYPES:
        out = _normalize_color(raw)
    elif key in _DIMENSION_TYPES:
        out = _normalize_dimension(raw)
    elif key in _WEIGHT_TYPES:
        out = _normalize_weight(raw)
    elif key in _NUMBER_TYPES:
        out = _normalize_numberish(raw, kind=key)
    elif key in _RATIO_TYPES:
        out = _normalize_numberish(raw, kind="ratio")
    elif key in _GRADIENT_TYPES:
        out = _normalize_gradient(raw)
    elif key in _VERBATIM_TYPES:
        out = _normalize_verbatim_string(raw)
    elif key.startswith("other.") or key in _ENUM_STRING_TYPES:
        out = _normalize_enum_string(raw)
    else:
        out = _normalize_enum_string(raw)

    if isinstance(raw, str) and raw == out.canon:
        return out
    if isinstance(raw, (int, float)) and not isinstance(raw, bool) and str(raw) == out.canon:
        return out
    return out


def value_patterns(token_type: str, canon: str) -> list[re.Pattern[str]]:
    """Regexes that accept source literals equivalent to ``canon``."""
    key = token_type.casefold()
    if key in _COLOR_TYPES and canon.startswith("#"):
        body = canon[1:]
        forms = [body]
        if len(body) == 6 and all(body[i] == body[i + 1] for i in range(0, 6, 2)):
            forms.append(body[::2])
        alternatives = "|".join(re.escape(form) for form in forms)
        return [re.compile(rf"#(?:{alternatives})(?![0-9a-f])", re.IGNORECASE)]
    if key in _DIMENSION_TYPES and canon.endswith("px"):
        num_pat = re.escape(canon[:-2])
        return [
            re.compile(rf"\b{num_pat}\s*px\b", re.IGNORECASE),
            re.compile(rf"\b{num_pat}px\b", re.IGNORECASE),
            re.compile(rf"\b{num_pat}\b"),
        ]
    if key in _DIMENSION_TYPES and canon.endswith("%"):
        num_pat = re.escape(canon[:-1])
        return [re.compile(rf"\b{num_pat}\s*%(?!\w)")]
    if key in _WEIGHT_TYPES:
        names = [re.escape(name) for name, val in _WEIGHT_NAMES.items() if val == canon]
        patterns = [re.compile(rf"\b{re.escape(canon)}\b")]
        if names:
            alt = "|".join(sorted(set(names), key=len, reverse=True))
            patterns.append(re.compile(rf"\b(?:{alt})\b", re.IGNORECASE))
        return patterns
    if key in _NUMBER_TYPES and re.fullmatch(r"-?\d+(?:\.\d+)?", canon):
        numeric = float(canon)
        pct_text = f"{numeric * 100.0:g}"
        return [
            re.compile(rf"\b{re.escape(canon)}\b"),
            re.compile(rf"\b{re.escape(pct_text)}\s*%(?!\w)"),
        ]
    if key in _RATIO_TYPES:
        return [re.compile(re.escape(canon))]
    if key in _GRADIENT_TYPES:
        return [re.compile(re.escape(canon))]
    # "other"/"other.*" values are enum-normalized (spaces -> underscores) by
    # normalize_value, so their patterns must accept the original separators too.
    if key in _ENUM_STRING_TYPES or key == "other" or key.startswith("other."):
        words = [re.escape(word) for word in canon.split("_") if word]
        joined = r"[\s_-]+".join(words)
        return [re.compile(rf"(?<!\w){joined}(?!\w)", re.IGNORECASE)]
    escaped = re.escape(canon)
    return [re.compile(escaped, re.IGNORECASE if key not in _VERBATIM_TYPES else 0)]
