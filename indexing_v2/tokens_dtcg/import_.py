"""Import the §5.8 DTCG JSON projection into canonical token dictionaries.

Use :func:`import_tokens` for an on-disk bundle or :func:`dtcg_to_tokens`
for an in-memory bundle. Namespaced canonical extensions are authoritative;
plain DTCG leaves are imported as ``source='dtcg_manual'`` dictionaries.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from indexing_v2.settings import DTCG_NAMESPACE

from .export import (
    DtcgBijectionError,
    DtcgError,
    TokenCollection,
    _iter_leaves,
    _verify_map,
    tokens_to_dtcg,
    validate_dtcg_tree,
)

_MANUAL_TYPES = {
    "color": "color",
    "dimension": "dimension",
    "fontFamily": "font",
    "fontWeight": "weight",
    "number": "ratio",
    "gradient": "gradient",
    "typography": "type_scale",
    "shadow": "shadow",
    "border": "border",
}


def _extension(leaf: dict[str, Any], namespace: str) -> dict[str, Any] | None:
    extensions = leaf.get("$extensions")
    if not isinstance(extensions, dict):
        return None
    bucket = extensions.get(namespace)
    return copy.deepcopy(bucket) if isinstance(bucket, dict) else None


def _resolve_manual_alias(value: Any, paths_to_ids: dict[str, str]) -> Any:
    if not isinstance(value, str) or not value.startswith("{") or not value.endswith("}"):
        return copy.deepcopy(value)
    path = value[1:-1]
    if path not in paths_to_ids:
        raise DtcgError(f"unknown DTCG alias path: {path}")
    return {"$ref": paths_to_ids[path]}


def _manual_id(brand_id: str, path: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_")[:48] or "token"
    return f"tok_{brand_id}_{slug}"


def _manual_token(
    path: str,
    leaf: dict[str, Any],
    brand_id: str,
    paths_to_ids: dict[str, str],
) -> dict[str, Any]:
    if "$value" not in leaf:
        raise DtcgError(f"malformed leaf without $value at {path!r}")
    dtcg_type = leaf.get("$type")
    token_type = _MANUAL_TYPES.get(str(dtcg_type), "other")
    token: dict[str, Any] = {
        "id": paths_to_ids.get(path, _manual_id(brand_id, path)),
        "brand_id": brand_id,
        "token_type": token_type,
        "kind": "primitive",
        "key": path,
        "value": {
            "default": _resolve_manual_alias(leaf["$value"], paths_to_ids),
            "variants": None,
        },
        "aliases": [],
        "scope": "global",
        "status": "active",
        "version": 1,
        "source": "dtcg_manual",
    }
    if "$description" in leaf:
        token["notes"] = str(leaf["$description"])
    return token


def _canonical_token(
    path: str,
    leaf: dict[str, Any],
    namespace: str,
    expected_id: str | None,
) -> dict[str, Any] | None:
    extension = _extension(leaf, namespace)
    if extension is None:
        return None
    canonical = extension.get("canonical")
    if not isinstance(canonical, dict):
        raise DtcgError(f"{path}: namespace extension missing canonical token object")
    token = copy.deepcopy(canonical)
    token_id = str(extension.get("token_id", token.get("id", "")))
    if not token_id or str(token.get("id", "")) != token_id:
        raise DtcgError(f"{path}: extension token_id does not match canonical id")
    if expected_id is not None and token_id != expected_id:
        raise DtcgBijectionError(
            f"{path}: map id {expected_id!r} does not match extension id {token_id!r}"
        )
    return token


def dtcg_to_tokens(
    bundle: dict[str, Any],
    brand_id: str,
    *,
    namespace: str = DTCG_NAMESPACE,
) -> list[dict[str, Any]]:
    """Return canonical token dictionaries from an in-memory DTCG bundle."""
    map_data = bundle.get("map")
    base = bundle.get("base")
    modes = bundle.get("modes", {})
    if not isinstance(map_data, dict) or not isinstance(base, dict):
        raise DtcgError("bundle requires object-valued base and map entries")
    if not isinstance(modes, dict):
        raise DtcgError("bundle modes must be an object")

    ids_to_paths, paths_to_ids = _verify_map(map_data)
    validate_dtcg_tree(base)
    for filename, mode in modes.items():
        if not isinstance(mode, dict):
            raise DtcgError(f"mode {filename!r} must be an object")
        validate_dtcg_tree(mode)

    imported: dict[str, dict[str, Any]] = {}
    seen_mapped_paths: set[str] = set()
    for path, leaf in _iter_leaves(base):
        expected_id = paths_to_ids.get(path)
        token = _canonical_token(path, leaf, namespace, expected_id)
        if token is None:
            token = _manual_token(path, leaf, brand_id, paths_to_ids)
        token_id = str(token["id"])
        if token_id in imported:
            raise DtcgBijectionError(f"duplicate token id on import: {token_id}")
        imported[token_id] = token
        if expected_id is not None:
            seen_mapped_paths.add(path)

    missing_paths = sorted(set(paths_to_ids) - seen_mapped_paths)
    if missing_paths:
        raise DtcgError(f"map references missing token paths: {', '.join(missing_paths)}")
    missing_ids = sorted(set(ids_to_paths) - imported.keys())
    if missing_ids:
        raise DtcgError(f"map references missing token ids: {', '.join(missing_ids)}")
    return [imported[token_id] for token_id in sorted(imported)]


def import_tokens(
    input_dir: str | Path,
    brand_id: str,
    *,
    namespace: str = DTCG_NAMESPACE,
) -> list[dict[str, Any]]:
    """Read a DTCG bundle below ``input_dir`` and return canonical token dicts."""
    root = Path(input_dir)
    base_path = root / "tokens.base.json"
    map_path = root / "_map.json"
    if not base_path.exists() or not map_path.exists():
        raise FileNotFoundError(f"missing DTCG tokens.base.json or _map.json under {root}")

    modes: dict[str, Any] = {}
    modes_dir = root / "modes"
    if modes_dir.exists():
        for path in sorted(modes_dir.glob("*.tokens.json")):
            modes[path.name] = json.loads(path.read_text(encoding="utf-8"))
    bundle = {
        "base": json.loads(base_path.read_text(encoding="utf-8")),
        "map": json.loads(map_path.read_text(encoding="utf-8")),
        "modes": modes,
    }
    return dtcg_to_tokens(bundle, brand_id, namespace=namespace)


def roundtrip_tokens(
    tokens: TokenCollection,
    brand_id: str,
    *,
    namespace: str = DTCG_NAMESPACE,
) -> list[dict[str, Any]]:
    """Project tokens to memory and import them back without field loss."""
    return dtcg_to_tokens(
        tokens_to_dtcg(tokens, namespace=namespace),
        brand_id,
        namespace=namespace,
    )
