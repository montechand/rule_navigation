"""Export BrandToken rows to the §5.8 W3C DTCG projection.

Use :func:`export_tokens` for filesystem output or :func:`tokens_to_dtcg`
for a pure in-memory bundle. The exporter only writes JSON token files;
the checked-in Style Dictionary config is documentation/tooling input.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence, TypeAlias, cast

from indexing_v2.contracts import atomic_write_json
from indexing_v2.extraction.normalize import normalize_value
from indexing_v2.settings import DTCG_NAMESPACE
from shared.schemas import BrandToken

STAGE_VERSION = "5.8.1"

TokenInput: TypeAlias = BrandToken | dict[str, Any]
TokenCollection: TypeAlias = Mapping[str, TokenInput] | Sequence[TokenInput]

_DIMENSION_TYPES = frozenset(
    {"spacing", "padding", "margin", "size", "dimension", "radius", "breakpoint"}
)
_UNTYPED_STRING_TYPES = frozenset(
    {"case", "alignment", "icon_style", "image_treatment", "motion"}
)
_UNITFUL_RE = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
    r"(?:px|rem|em|%|vh|vw|vmin|vmax|ch|ex|pt|pc|in|cm|mm|Q|lh|rlh)$",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_TYPE_SCALE_KEYS = {
    "font_family": "fontFamily",
    "fontFamily": "fontFamily",
    "family": "fontFamily",
    "font_size": "fontSize",
    "fontSize": "fontSize",
    "size": "fontSize",
    "font_weight": "fontWeight",
    "fontWeight": "fontWeight",
    "weight": "fontWeight",
    "line_height": "lineHeight",
    "lineHeight": "lineHeight",
    "leading": "lineHeight",
    "letter_spacing": "letterSpacing",
    "letterSpacing": "letterSpacing",
    "tracking": "letterSpacing",
}
_SHADOW_KEYS = {
    "offset_x": "offsetX",
    "offsetX": "offsetX",
    "x": "offsetX",
    "offset_y": "offsetY",
    "offsetY": "offsetY",
    "y": "offsetY",
    "blur_radius": "blur",
    "blur": "blur",
    "spread_radius": "spread",
    "spread": "spread",
    "color": "color",
    "inset": "inset",
}


class DtcgError(ValueError):
    """Raised when token data cannot form a valid §5.8 projection."""


class DtcgBijectionError(DtcgError):
    """Raised when token ids and DTCG paths are not a bijection."""


def _coerce_token(token: TokenInput) -> dict[str, Any]:
    if isinstance(token, BrandToken):
        row: dict[str, Any] = token.model_dump(mode="json")
        return row
    if isinstance(token, dict):
        return copy.deepcopy(token)
    raise TypeError(f"expected BrandToken or dict, got {type(token)!r}")


def _normalize_tokens(tokens: TokenCollection) -> dict[str, dict[str, Any]]:
    values = list(tokens.values()) if isinstance(tokens, Mapping) else list(tokens)
    normalized: dict[str, dict[str, Any]] = {}
    for token in values:
        row = _coerce_token(token)
        token_id = str(row["id"])
        if token_id in normalized:
            raise DtcgBijectionError(f"duplicate token id: {token_id}")
        normalized[token_id] = row
    return dict(sorted(normalized.items()))


def _resolve_paths(tokens: dict[str, dict[str, Any]]) -> dict[str, str]:
    keys = {token_id: str(token["key"]) for token_id, token in tokens.items()}
    distinct = sorted(set(keys.values()))
    group_collisions = {
        key for key in distinct if any(other.startswith(f"{key}.") for other in distinct)
    }
    result: dict[str, str] = {}
    used: set[str] = set()
    for token_id in sorted(tokens):
        key = keys[token_id]
        path = f"{key}_value" if key in group_collisions else key
        if path in used:
            raise DtcgBijectionError(f"duplicate DTCG path: {path}")
        used.add(path)
        result[token_id] = path
    return result


def _build_map(ids_to_paths: dict[str, str]) -> dict[str, dict[str, str]]:
    paths_to_ids = {path: token_id for token_id, path in ids_to_paths.items()}
    if len(paths_to_ids) != len(ids_to_paths):
        raise DtcgBijectionError("token id/path map is not bijective")
    return {
        "ids_to_paths": dict(sorted(ids_to_paths.items())),
        "paths_to_ids": dict(sorted(paths_to_ids.items())),
    }


def _default_value(token: dict[str, Any]) -> Any:
    value = token.get("value")
    if isinstance(value, dict) and "default" in value:
        return value["default"]
    return value


def _variants(token: dict[str, Any]) -> list[dict[str, Any]]:
    value = token.get("value")
    if not isinstance(value, dict) or value.get("variants") is None:
        return []
    variants = value["variants"]
    if not isinstance(variants, list):
        raise DtcgError(f"{token['id']}: value.variants must be a list or null")
    if not all(isinstance(item, dict) for item in variants):
        raise DtcgError(f"{token['id']}: every variant must be an object")
    return cast(list[dict[str, Any]], variants)


def _number(value: str) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _dimension_value(token_type: str, value: Any) -> tuple[str, bool]:
    canon = normalize_value(token_type, value).canon
    valid = bool(canon) and all(_UNITFUL_RE.fullmatch(part) for part in canon.split())
    return canon, valid


def _line_value(token_type: str, value: Any) -> tuple[Any, str | None]:
    if isinstance(value, str) and _UNITFUL_RE.fullmatch(re.sub(r"\s+", "", value)):
        canon, valid = _dimension_value("dimension", value)
        return canon, "dimension" if valid else None
    canon = normalize_value(token_type, value).canon
    if _NUMBER_RE.fullmatch(canon):
        return _number(canon), "number"
    return canon, None


def _numeric_value(token_type: str, value: Any) -> tuple[Any, bool]:
    canon = normalize_value(token_type, value).canon
    if _NUMBER_RE.fullmatch(canon):
        return _number(canon), True
    return canon, False


def _weight_value(value: Any) -> int | str:
    canon = normalize_value("weight", value).canon
    return int(canon) if canon.isdigit() else canon


def _declared_type(token_type: str, value: Any) -> str | None:
    if token_type == "color":
        return "color"
    if token_type in _DIMENSION_TYPES:
        _, valid = _dimension_value(token_type, value)
        return "dimension" if valid else None
    if token_type == "font":
        return "fontFamily"
    if token_type == "weight":
        return "fontWeight"
    if token_type in {"line_height", "letter_spacing"}:
        _, declared_type = _line_value(token_type, value)
        return declared_type
    if token_type in {"opacity", "ratio", "usage_ratio"}:
        _, numeric = _numeric_value(token_type, value)
        return "number" if numeric else None
    if token_type in {"type_scale", "typography"} and isinstance(value, dict):
        # DTCG typography requires all five fields; partial composites (the
        # common "size + line height" brand shorthand) stay untyped.
        return "typography" if _typography_complete(value) else None
    if token_type == "gradient" and (
        isinstance(value, list) or isinstance(value, dict) and isinstance(value.get("stops"), list)
    ):
        return "gradient"
    if token_type == "shadow" and isinstance(value, (dict, list)):
        return "shadow"
    if token_type == "border" and isinstance(value, dict):
        return "border"
    if token_type in _UNTYPED_STRING_TYPES or token_type.startswith("other."):
        return None
    return None


def _replace_refs(value: Any, ids_to_paths: dict[str, str]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"$ref"}:
            token_id = str(value["$ref"])
            if token_id not in ids_to_paths:
                raise DtcgError(f"unknown $ref token id: {token_id}")
            return "{" + ids_to_paths[token_id] + "}"
        return {str(key): _replace_refs(item, ids_to_paths) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_refs(item, ids_to_paths) for item in value]
    return value


def _font_families(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    families: list[str] = []
    for part in value.split(","):
        family = part.strip().strip("'\"")
        if family:
            families.append(normalize_value("font", family).canon)
    return families


_TYPOGRAPHY_REQUIRED = {"fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing"}


def _typography_complete(value: dict[str, Any]) -> bool:
    """Whether a raw composite carries every field DTCG typography requires."""
    mapped = {_TYPE_SCALE_KEYS.get(str(key)) for key in value}
    return _TYPOGRAPHY_REQUIRED.issubset(mapped)


def _typography_value(value: dict[str, Any], ids_to_paths: dict[str, str]) -> dict[str, Any]:
    """Project a typography composite, normalizing whichever fields are present.

    Brand sources routinely specify only size + line height; DTCG requires all
    five fields for a `$type: typography` leaf, so completeness is enforced by
    the caller via _typography_complete (partial composites export untyped)
    rather than by raising here.
    """
    projected: dict[str, Any] = {}
    for key, item in value.items():
        target_key = _TYPE_SCALE_KEYS.get(str(key))
        if target_key is not None:
            projected[target_key] = _replace_refs(item, ids_to_paths)

    def _is_ref(item: Any) -> bool:
        return isinstance(item, str) and item.startswith("{")

    if "fontFamily" in projected and not _is_ref(projected["fontFamily"]):
        projected["fontFamily"] = _font_families(projected["fontFamily"])
    if "fontSize" in projected and isinstance(projected["fontSize"], str) \
            and not _is_ref(projected["fontSize"]):
        projected["fontSize"] = _dimension_value("size", projected["fontSize"])[0]
    if "fontWeight" in projected and not _is_ref(projected["fontWeight"]):
        projected["fontWeight"] = _weight_value(projected["fontWeight"])
    for key, token_type in (
        ("lineHeight", "line_height"),
        ("letterSpacing", "letter_spacing"),
    ):
        if key in projected and not _is_ref(projected[key]):
            projected[key] = _line_value(token_type, projected[key])[0]
    return projected


def _gradient_value(value: Any, ids_to_paths: dict[str, str]) -> tuple[list[Any], Any | None]:
    if isinstance(value, list):
        raw = {"stops": value, "angle": 0}
        has_angle = False
    elif isinstance(value, dict) and isinstance(value.get("stops"), list):
        raw = value
        has_angle = "angle" in value
    else:
        raise DtcgError("gradient must be a stop list or an object containing stops")
    normalized = json.loads(normalize_value("gradient", raw).canon)
    stops = cast(list[Any], _replace_refs(normalized["stops"], ids_to_paths))
    return stops, normalized["angle"] if has_angle else None


def _shadow_value(value: Any, ids_to_paths: dict[str, str]) -> Any:
    if isinstance(value, list):
        return [_shadow_value(item, ids_to_paths) for item in value]
    if not isinstance(value, dict):
        raise DtcgError("shadow must be an object or list of objects")
    projected: dict[str, Any] = {}
    for key, item in value.items():
        target_key = _SHADOW_KEYS.get(str(key), str(key))
        replaced = _replace_refs(item, ids_to_paths)
        if target_key == "color" and not (
            isinstance(replaced, str) and replaced.startswith("{")
        ):
            replaced = normalize_value("color", replaced).canon
        elif target_key in {"offsetX", "offsetY", "blur", "spread"} and not (
            isinstance(replaced, str) and replaced.startswith("{")
        ):
            replaced = _dimension_value("dimension", replaced)[0]
        projected[target_key] = replaced
    return projected


def _border_value(value: dict[str, Any], ids_to_paths: dict[str, str]) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    for key, item in value.items():
        replaced = _replace_refs(item, ids_to_paths)
        if key == "color" and not (isinstance(replaced, str) and replaced.startswith("{")):
            replaced = normalize_value("color", replaced).canon
        elif key == "width" and not (
            isinstance(replaced, str) and replaced.startswith("{")
        ):
            replaced = _dimension_value("dimension", replaced)[0]
        elif key == "style":
            replaced = normalize_value("other.border_style", replaced).canon
        projected[str(key)] = replaced
    return projected


def _project_value(
    token_type: str,
    value: Any,
    ids_to_paths: dict[str, str],
) -> tuple[Any, dict[str, Any]]:
    projection: dict[str, Any] = {}
    if token_type == "color":
        return normalize_value("color", value).canon, projection
    if token_type in _DIMENSION_TYPES:
        return _dimension_value(token_type, value)[0], projection
    if token_type == "weight":
        return _weight_value(value), projection
    if token_type == "gradient":
        stops, angle = _gradient_value(value, ids_to_paths)
        if angle is not None:
            projection["gradient_angle"] = angle
        return stops, projection
    if token_type in {"type_scale", "typography"} and isinstance(value, dict):
        # Partial composites still get field normalization; the leaf's $type
        # (via _declared_type) is only "typography" when all fields exist.
        return _typography_value(value, ids_to_paths), projection
    if token_type == "shadow" and isinstance(value, (dict, list)):
        return _shadow_value(value, ids_to_paths), projection
    if token_type == "border" and isinstance(value, dict):
        return _border_value(value, ids_to_paths), projection
    if token_type == "font":
        return _font_families(value), projection
    if token_type in {"line_height", "letter_spacing"}:
        return _line_value(token_type, value)[0], projection
    if token_type in {"opacity", "ratio", "usage_ratio"}:
        return _numeric_value(token_type, value)[0], projection
    if token_type in _UNTYPED_STRING_TYPES or token_type.startswith("other."):
        return normalize_value(token_type, value).canon, projection
    return _replace_refs(value, ids_to_paths), projection


def _extension(
    token: dict[str, Any],
    namespace: str,
    projection: dict[str, Any],
) -> dict[str, Any]:
    bucket: dict[str, Any] = {
        "token_id": token["id"],
        "canonical": copy.deepcopy(token),
    }
    for key, value in token.items():
        if key != "id" and value is not None:
            bucket[key] = copy.deepcopy(value)
    bucket.update(projection)
    return {namespace: bucket}


def _leaf(
    token: dict[str, Any],
    value: Any,
    ids_to_paths: dict[str, str],
    types_by_id: dict[str, str | None],
    namespace: str,
    *,
    include_extension: bool,
) -> dict[str, Any]:
    token_type = str(token.get("token_type", "other"))
    if isinstance(value, dict) and set(value) == {"$ref"}:
        target_id = str(value["$ref"])
        if target_id not in ids_to_paths:
            raise DtcgError(f"unknown $ref token id: {target_id}")
        projected: Any = "{" + ids_to_paths[target_id] + "}"
        declared_type = types_by_id[target_id]
        projection: dict[str, Any] = {}
    else:
        declared_type = _declared_type(token_type, value)
        projected, projection = _project_value(token_type, value, ids_to_paths)

    leaf: dict[str, Any] = {"$value": projected}
    if declared_type is not None:
        leaf["$type"] = declared_type
    description = token.get("notes")
    if description is None:
        description = token.get("description")
    if include_extension and description is not None:
        leaf["$description"] = str(description)
    if include_extension:
        leaf["$extensions"] = _extension(token, namespace, projection)
    elif projection:
        leaf["$extensions"] = {namespace: projection}
    return leaf


def _nest(tree: dict[str, Any], path: str, leaf: dict[str, Any]) -> None:
    parts = path.split(".")
    group = tree
    for part in parts[:-1]:
        node = group.setdefault(part, {})
        if not isinstance(node, dict) or "$value" in node:
            raise DtcgError(f"path/group collision while nesting {path!r}")
        group = node
    name = parts[-1]
    if name in group:
        raise DtcgBijectionError(f"duplicate DTCG path: {path}")
    group[name] = leaf


def _mode_value(when: dict[str, Any], axis: str) -> str:
    raw = when[axis]
    if isinstance(raw, dict):
        if len(raw) != 1:
            raise DtcgError(f"cannot derive mode value from {when!r}")
        raw = next(iter(raw.values()))
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", str(raw))


def validate_dtcg_tree(tree: dict[str, Any]) -> None:
    """Reject mixed group/leaves and every metadata-only or empty leaf."""

    def walk(node: dict[str, Any], path: str, *, root: bool = False) -> None:
        children = [key for key in node if not key.startswith("$")]
        if "$value" in node:
            if children:
                raise DtcgError(f"leaf at {path!r} also contains groups")
            return
        if not children:
            if node or not root:
                raise DtcgError(f"malformed leaf without $value at {path or '<root>'!r}")
            return
        for key in children:
            child = node[key]
            child_path = f"{path}.{key}" if path else key
            if not isinstance(child, dict):
                raise DtcgError(f"expected object at {child_path!r}")
            walk(child, child_path)

    if not isinstance(tree, dict):
        raise DtcgError("DTCG root must be an object")
    walk(tree, "", root=True)


def _iter_leaves(
    tree: dict[str, Any],
    prefix: str = "",
) -> list[tuple[str, dict[str, Any]]]:
    leaves: list[tuple[str, dict[str, Any]]] = []
    for key in sorted(tree):
        if key.startswith("$"):
            continue
        node = tree[key]
        path = f"{prefix}.{key}" if prefix else key
        if not isinstance(node, dict):
            raise DtcgError(f"expected object at {path!r}")
        if "$value" in node:
            leaves.append((path, node))
        else:
            leaves.extend(_iter_leaves(node, path))
    return leaves


def _verify_map(data: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    raw_ids = data.get("ids_to_paths")
    raw_paths = data.get("paths_to_ids")
    if not isinstance(raw_ids, dict) or not isinstance(raw_paths, dict):
        raise DtcgBijectionError("_map.json requires ids_to_paths and paths_to_ids objects")
    ids_to_paths = {str(key): str(value) for key, value in raw_ids.items()}
    paths_to_ids = {str(key): str(value) for key, value in raw_paths.items()}
    if len(ids_to_paths) != len(paths_to_ids):
        raise DtcgBijectionError("ids_to_paths and paths_to_ids differ in size")
    if set(ids_to_paths.values()) != set(paths_to_ids):
        raise DtcgBijectionError("ids_to_paths values do not match paths_to_ids keys")
    for path, token_id in paths_to_ids.items():
        if ids_to_paths.get(token_id) != path:
            raise DtcgBijectionError(f"map mismatch for {token_id!r} <-> {path!r}")
    return ids_to_paths, paths_to_ids


def _projected_types(tokens: dict[str, dict[str, Any]]) -> dict[str, str | None]:
    projected: dict[str, str | None] = {}

    def resolve(token_id: str, stack: set[str]) -> str | None:
        if token_id in projected:
            return projected[token_id]
        if token_id in stack:
            raise DtcgError(f"cyclic token alias involving {token_id}")
        token = tokens[token_id]
        value = _default_value(token)
        if isinstance(value, dict) and set(value) == {"$ref"}:
            target_id = str(value["$ref"])
            if target_id not in tokens:
                raise DtcgError(f"unknown $ref token id: {target_id}")
            declared = resolve(target_id, stack | {token_id})
        else:
            declared = _declared_type(str(token.get("token_type", "other")), value)
        projected[token_id] = declared
        return declared

    for token_id in tokens:
        resolve(token_id, set())
    return projected


def tokens_to_dtcg(
    tokens: TokenCollection,
    *,
    namespace: str = DTCG_NAMESPACE,
    tables_by_token: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return deterministic in-memory ``base``, ``modes``, and ``map`` objects."""
    normalized = _normalize_tokens(tokens)
    ids_to_paths = _resolve_paths(normalized)
    types_by_id = _projected_types(normalized)
    base: dict[str, Any] = {}
    modes: dict[str, dict[str, Any]] = {}

    for token_id, token in normalized.items():
        path = ids_to_paths[token_id]
        leaf = _leaf(
            token,
            _default_value(token),
            ids_to_paths,
            types_by_id,
            namespace,
            include_extension=True,
        )
        table_id = (tables_by_token or {}).get(token_id)
        if table_id is not None:
            # E2: keep table membership visible in Style Dictionary output.
            leaf.setdefault("$extensions", {}).setdefault(namespace, {})["table"] = table_id
        _nest(base, path, leaf)
        for variant in _variants(token):
            when = variant.get("when")
            if not isinstance(when, dict) or len(when) != 1:
                continue
            axis = str(next(iter(when)))
            filename = f"{axis}.{_mode_value(when, axis)}.tokens.json"
            _nest(
                modes.setdefault(filename, {}),
                path,
                _leaf(
                    token,
                    variant.get("value"),
                    ids_to_paths,
                    types_by_id,
                    namespace,
                    include_extension=False,
                ),
            )

    validate_dtcg_tree(base)
    for mode in modes.values():
        validate_dtcg_tree(mode)
    return {
        "base": base,
        "modes": dict(sorted(modes.items())),
        "map": _build_map(ids_to_paths),
    }


def export_tokens(
    tokens: TokenCollection,
    output_dir: str | Path,
    *,
    namespace: str = DTCG_NAMESPACE,
    tables_by_token: dict[str, str] | None = None,
) -> dict[str, str]:
    """Atomically write the §5.8 JSON bundle below ``output_dir``."""
    bundle = tokens_to_dtcg(tokens, namespace=namespace, tables_by_token=tables_by_token)
    root = Path(output_dir)
    modes_dir = root / "modes"
    root.mkdir(parents=True, exist_ok=True)
    modes_dir.mkdir(parents=True, exist_ok=True)

    expected_modes = set(bundle["modes"])
    for stale in modes_dir.glob("*.tokens.json"):
        if stale.name not in expected_modes:
            stale.unlink()

    written = {
        "base": str(root / "tokens.base.json"),
        "map": str(root / "_map.json"),
    }
    atomic_write_json(root / "tokens.base.json", bundle["base"])
    atomic_write_json(root / "_map.json", bundle["map"])
    for filename, tree in bundle["modes"].items():
        path = modes_dir / filename
        atomic_write_json(path, tree)
        written[f"mode:{filename}"] = str(path)
    return written
