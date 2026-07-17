"""LLM runner, prompt rendering, and disk cache for KB extraction v2 (§5.3).

Hand-off surfaces for sibling workers:
- WP-06: ``RunOutput``, ``run_extraction(...)``, ``render_units``, ``select_units``
- WP-08: ``load_prompt``, ``PromptTemplate.render``; prompt files under ``extraction/prompts/*.md``
- WP-10: ``complete_json_cached``, ``chat_cached``, ``make_cache_key``, ``clear_brand_cache``
- WP-11: ``LLMClient`` protocol, ``SharedLLMClient`` for production wiring

Only ``SharedLLMClient`` in v2 may import ``shared.llm`` call helpers.
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable

from pydantic import BaseModel, Field

from shared.llm import Usage
from shared.llm import chat as shared_chat
from shared.llm import complete_json as shared_complete_json

from .. import settings
from ..contracts import (
    SCHEMA_VERSION,
    FrozenCatalog,
    RunVariant,
    SourceUnit,
    UnitLabel,
    atomic_write_json,
    slugify,
    stable_hash,
)
from .prompts import PromptTemplate, load_prompt

STAGE_VERSION = "extraction-v2.1.1"
# Cache keys deliberately do not track STAGE_VERSION: template_hash + content
# hash already bust the cache whenever a prompt or its inputs change, so
# code-only stage bumps can replay cached LLM responses instead of re-paying
# the full extraction.
CACHE_VERSION = "extraction-v2.1.0"

DEFAULT_CACHE_ROOT = Path(__file__).resolve().parent.parent / "_cache"

PROMPT_TOKENS_PRIMITIVE = "tokens_primitive"
PROMPT_TOKENS_SEMANTIC = "tokens_semantic"
PROMPT_CATALOG_REST = "catalog_rest"
PROMPT_RULES_CLUSTER = "rules_cluster"
PROMPT_LINKER_ADJUDICATE = "linker_adjudicate"

@runtime_checkable
class LLMClient(Protocol):
    async def complete_json(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 128_000,
        usage: Optional[Usage] = None,
        *,
        prompt_name: str,
        cache_key: Optional[str] = None,
    ) -> Any: ...

    async def chat(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        *,
        prompt_name: str,
        cache_key: Optional[str] = None,
        usage: Optional[Usage] = None,
        max_tokens: int = 128_000,
        **kwargs: Any,
    ) -> dict[str, Any]: ...


class MalformedModelJSONError(RuntimeError):
    """Model returned unparseable JSON on every attempt."""


_JSON_PARSE_ATTEMPTS = 3


class SharedLLMClient:
    """Production adapter; the only v2 entry point that touches ``shared.llm``."""

    async def complete_json(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 128_000,
        usage: Optional[Usage] = None,
        *,
        prompt_name: str,
        cache_key: Optional[str] = None,
    ) -> Any:
        del cache_key
        last_exc: Exception | None = None
        for _attempt in range(_JSON_PARSE_ATTEMPTS):
            try:
                return await shared_complete_json(
                    model,
                    system,
                    user,
                    max_tokens=max_tokens,
                    usage=usage,
                )
            except (json.JSONDecodeError, ValueError) as exc:
                # Malformed model text (truncated/invalid JSON) is transient:
                # sampling is stochastic, so re-asking usually yields a parseable
                # response. Bounded retry, then raise typed so callers see a
                # deliberate failure instead of a raw parse traceback.
                last_exc = exc
        raise MalformedModelJSONError(
            f"model {model} returned unparseable JSON for prompt={prompt_name} "
            f"after {_JSON_PARSE_ATTEMPTS} attempts: {last_exc}"
        ) from last_exc

    async def chat(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        *,
        prompt_name: str,
        cache_key: Optional[str] = None,
        usage: Optional[Usage] = None,
        max_tokens: int = 128_000,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del prompt_name, cache_key
        turn = await shared_chat(
            model,
            system,
            messages,
            max_tokens=max_tokens,
            usage=usage,
            **kwargs,
        )
        return {
            "role": "assistant",
            "content": turn.text,
            "tool_calls": [
                {"id": tc.id, "name": tc.name, "args": tc.args} for tc in turn.tool_calls
            ],
            "stop_reason": turn.stop_reason,
            "thinking_blocks": turn.thinking_blocks,
        }


class RuleGroupOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    group_id: str
    doc_ref: str
    original_text: str
    rules: list[dict[str, Any]] = Field(default_factory=list)
    relations: list[dict[str, Any]] = Field(default_factory=list)
    missing_token_requests: list[dict[str, Any]] = Field(default_factory=list)


class RefViolation(BaseModel):
    rule_slug: str
    unknown_ids: list[str]


class RunOutput(BaseModel):
    """Typed stage boundary between extraction and downstream cascade/consistency."""

    schema_version: str = SCHEMA_VERSION
    variant: RunVariant
    primitive_tokens: list[dict[str, Any]] = Field(default_factory=list)
    semantic_tokens: list[dict[str, Any]] = Field(default_factory=list)
    catalog_rest: dict[str, Any] = Field(default_factory=dict)
    rules_by_doc_ref: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    rule_groups: list[RuleGroupOutput] = Field(default_factory=list)


@dataclass(frozen=True)
class CacheContext:
    brand: str
    variant: RunVariant
    prompt_name: str
    template: PromptTemplate
    content_hash: str
    cache_root: Path


def render_units(units: Sequence[SourceUnit]) -> str:
    """Deterministic ``[id] (kind) text`` rendering; unit ``text`` is preserved verbatim."""
    parts: list[str] = []
    for unit in units:
        if parts and not parts[-1].endswith("\n"):
            parts.append("\n")
        parts.append(f"[{unit.unit_id}] ({unit.kind}) {unit.text}")
    return "".join(parts)


def select_units(
    units: Sequence[SourceUnit],
    *,
    exclude_unit_ids: set[str] | None = None,
) -> list[SourceUnit]:
    """Return all canonical units except explicit caller exclusions."""
    excluded = exclude_unit_ids or set()
    return [unit for unit in units if unit.unit_id not in excluded]


def make_content_hash(
    *,
    system: str,
    user: str,
    gap_round: int | None = None,
    cache_bust: str | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {"system": system, "user": user}
    if gap_round is not None:
        payload["gap_round"] = gap_round
    if cache_bust is not None:
        payload["cache_bust"] = cache_bust
    if extra:
        payload["extra"] = extra
    return stable_hash(payload)


def make_cache_key(
    *,
    prompt_name: str,
    template_hash: str,
    variant: RunVariant,
    content_hash: str,
) -> str:
    parts = [
        CACHE_VERSION,
        prompt_name,
        template_hash,
        variant.model,
        str(variant.temperature),
        str(variant.replicate),
        content_hash,
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def cache_path(ctx: CacheContext, key: str) -> Path:
    return ctx.cache_root / ctx.brand / ctx.prompt_name / f"{key}.json"


def clear_brand_cache(brand: str, cache_root: Path | None = None) -> None:
    """Remove all cached LLM payloads for ``brand`` under the v2 cache root."""
    root = (cache_root or DEFAULT_CACHE_ROOT) / brand
    if root.exists():
        shutil.rmtree(root)


def _serialize_chat_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    text = getattr(result, "text", "") or ""
    tool_calls = [
        {"id": tc.id, "name": tc.name, "args": tc.args}
        for tc in getattr(result, "tool_calls", []) or []
    ]
    return {
        "role": "assistant",
        "content": text,
        "tool_calls": tool_calls,
        "stop_reason": getattr(result, "stop_reason", ""),
        "thinking_blocks": getattr(result, "thinking_blocks", []) or [],
    }


def _read_cache(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


async def complete_json_cached(
    client: LLMClient,
    ctx: CacheContext,
    rendered_system: str,
    rendered_user: str,
    usage: Usage,
    *,
    max_tokens: int = 128_000,
    force: bool = False,
    gap_round: int | None = None,
    cache_bust: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Any:
    content_hash = make_content_hash(
        system=rendered_system,
        user=rendered_user,
        gap_round=gap_round,
        cache_bust=cache_bust,
        extra=extra,
    )
    key = make_cache_key(
        prompt_name=ctx.prompt_name,
        template_hash=ctx.template.template_hash,
        variant=ctx.variant,
        content_hash=content_hash,
    )
    path = cache_path(ctx, key)
    if not force and path.is_file():
        return _read_cache(path)
    result = await client.complete_json(
        ctx.variant.model,
        rendered_system,
        rendered_user,
        max_tokens=max_tokens,
        usage=usage,
        prompt_name=ctx.prompt_name,
        cache_key=key,
    )
    atomic_write_json(path, result)
    return result


async def chat_cached(
    client: LLMClient,
    ctx: CacheContext,
    rendered_system: str,
    messages: list[dict[str, Any]],
    usage: Usage,
    *,
    max_tokens: int = 128_000,
    force: bool = False,
    gap_round: int | None = None,
    cache_bust: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rendered_user = "\n".join(
        str(message.get("content", ""))
        for message in messages
        if message.get("role") == "user"
    )
    content_hash = make_content_hash(
        system=rendered_system,
        user=rendered_user,
        gap_round=gap_round,
        cache_bust=cache_bust,
        extra=extra,
    )
    key = make_cache_key(
        prompt_name=ctx.prompt_name,
        template_hash=ctx.template.template_hash,
        variant=ctx.variant,
        content_hash=content_hash,
    )
    path = cache_path(ctx, key)
    if not force and path.is_file():
        cached = _read_cache(path)
        if isinstance(cached, dict):
            return cached
        return _serialize_chat_result(cached)
    raw = await client.chat(
        ctx.variant.model,
        rendered_system,
        messages,
        max_tokens=max_tokens,
        usage=usage,
        prompt_name=ctx.prompt_name,
        cache_key=key,
    )
    payload = _serialize_chat_result(raw)
    atomic_write_json(path, payload)
    return payload


def _group_id(brand: str, doc_ref: str) -> str:
    match = re.match(r"^(.+)\[(\d+)\]$", doc_ref)
    if match:
        category, index = match.group(1), int(match.group(2))
        return f"grp_{brand}_{slugify(category)}_{index:02d}"
    return f"grp_{brand}_{slugify(doc_ref)}_00"


def _inject_umbrella_rules(
    brand: str,
    rule_groups: list[RuleGroupOutput],
    compiled_tables: Sequence[Any],
    units_by_doc_ref: Mapping[str, list[SourceUnit]],
) -> list[RuleGroupOutput]:
    """Append deterministic table umbrella rules to their doc_ref's rule group.

    The umbrella rule is byte-identical in every ensemble run, so it merges
    with support = K without any ensemble special-casing.
    """
    groups_by_id = {group.group_id: group for group in rule_groups}
    out = list(rule_groups)
    for item in compiled_tables:
        doc_ref = str(item.table.get("doc_ref") or "")
        group_id = _group_id(brand, doc_ref)
        rule = copy.deepcopy(item.umbrella_rule)
        group = groups_by_id.get(group_id)
        if group is None:
            original_text = "".join(
                unit.text for unit in units_by_doc_ref.get(doc_ref, [])
            )
            group = RuleGroupOutput(
                group_id=group_id,
                doc_ref=doc_ref,
                original_text=original_text,
                rules=[rule],
            )
            groups_by_id[group_id] = group
            out.append(group)
            continue
        if any(str(existing.get("id")) == str(rule["id"]) for existing in group.rules):
            continue
        group.rules.append(rule)
    return out


def _assign_rule_id(brand: str, raw: dict[str, Any], used_ids: set[str]) -> dict[str, Any]:
    """Mirror v1 validate_rule id minting: rule_{brand}_{slug} with _2/_3 collision suffixes."""
    rule = dict(raw)
    existing = rule.get("id")
    if isinstance(existing, str) and existing:
        used_ids.add(existing)
        return rule
    slug = slugify(str(rule.get("slug") or str(rule.get("rule_text") or "rule")[:40]))
    rule_id = f"rule_{brand}_{slug}"
    n = 2
    while rule_id in used_ids:
        rule_id = f"rule_{brand}_{slug}_{n}"
        n += 1
    used_ids.add(rule_id)
    rule["id"] = rule_id
    if not rule.get("slug"):
        rule["slug"] = slug
    return rule


def _map_relation_endpoints(
    relation: dict[str, Any], slug_to_id: dict[str, str]
) -> dict[str, Any]:
    mapped = dict(relation)
    for src_key, dst_key in (
        ("src_rule_id", "dst_rule_id"),
        ("from_id", "to_id"),
        ("from", "to"),
    ):
        src = mapped.get(src_key)
        dst = mapped.get(dst_key)
        if isinstance(src, str) and isinstance(dst, str) and src and dst:
            return mapped
    src_slug = mapped.get("src_slug")
    dst_slug = mapped.get("dst_slug")
    if not isinstance(src_slug, str) or not isinstance(dst_slug, str):
        return mapped
    src = slug_to_id.get(slugify(src_slug))
    dst = slug_to_id.get(slugify(dst_slug))
    if src and dst:
        mapped["src_rule_id"] = src
        mapped["dst_rule_id"] = dst
    return mapped


def normalize_rule_groups(
    brand: str,
    rule_groups: Sequence[RuleGroupOutput],
    *,
    used_ids: set[str] | None = None,
) -> list[RuleGroupOutput]:
    """Assign stable rule ids and rewrite slug relations to id endpoints.

    The rules_cluster prompt emits slug-only rules; provenance and Pass C require ``id``.
    """
    assigned_ids = set(used_ids or ())
    normalized: list[RuleGroupOutput] = []
    for group in rule_groups:
        rules = [
            _assign_rule_id(brand, rule, assigned_ids)
            for rule in group.rules
            if isinstance(rule, dict)
        ]
        slug_to_id: dict[str, str] = {}
        for rule in rules:
            slug = rule.get("slug")
            rule_id = rule.get("id")
            if isinstance(slug, str) and slug and isinstance(rule_id, str) and rule_id:
                slug_to_id[slugify(slug)] = rule_id
        relations = [
            _map_relation_endpoints(relation, slug_to_id)
            for relation in group.relations
            if isinstance(relation, dict)
        ]
        normalized.append(
            group.model_copy(update={"rules": rules, "relations": relations})
        )
    return normalized


def _token_id_from_key(brand: str, token: Mapping[str, Any]) -> str:
    key = token.get("key")
    if not isinstance(key, str) or not key.strip():
        paths = token.get("element_paths")
        if isinstance(paths, list) and paths and isinstance(paths[0], str) and paths[0].strip():
            key = paths[0]
        else:
            key = "token"
    return f"tok_{brand}_{slugify(key)}"


def _rewrite_ref_value(
    value: Any, *, aliases: Mapping[str, str], primitive_ids: set[str]
) -> Any:
    if not isinstance(value, dict) or "$ref" not in value:
        return value
    ref = value.get("$ref")
    if not isinstance(ref, str) or not ref or ref in primitive_ids:
        return value
    mapped = aliases.get(ref)
    if mapped is None:
        return value
    rewritten = dict(value)
    rewritten["$ref"] = mapped
    return rewritten


def _rewrite_token_refs(
    token: dict[str, Any], *, aliases: Mapping[str, str], primitive_ids: set[str]
) -> dict[str, Any]:
    value = token.get("value")
    if not isinstance(value, dict):
        return token
    updated = dict(value)
    updated["default"] = _rewrite_ref_value(
        updated.get("default"), aliases=aliases, primitive_ids=primitive_ids
    )
    variants = updated.get("variants")
    if isinstance(variants, list):
        rewritten_variants = []
        for variant in variants:
            if not isinstance(variant, dict):
                rewritten_variants.append(variant)
                continue
            item = dict(variant)
            item["value"] = _rewrite_ref_value(
                item.get("value"), aliases=aliases, primitive_ids=primitive_ids
            )
            rewritten_variants.append(item)
        updated["variants"] = rewritten_variants
    token["value"] = updated
    return token


def normalize_token_ids(
    brand: str,
    primitive_tokens: Sequence[dict[str, Any]],
    semantic_tokens: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Repair semantic token ids/refs against the primitive catalog.

    - Rename semantic tokens that collide with primitive ids (LLM self-$ref bug).
    - Rewrite ``$ref`` targets that used ``tok_{brand}_{slugify(key)}`` when the
      primitive's actual ``id`` differs (LLM invented the key-derived id).
    """
    primitives = [dict(token) for token in primitive_tokens]
    primitive_ids = {
        token_id
        for token in primitives
        if isinstance((token_id := token.get("id")), str) and token_id
    }
    aliases: dict[str, str] = {}
    for token in primitives:
        token_id = token.get("id")
        if not isinstance(token_id, str) or not token_id:
            continue
        key_id = _token_id_from_key(brand, token)
        if key_id != token_id and key_id not in primitive_ids and key_id not in aliases:
            aliases[key_id] = token_id

    used_ids = set(primitive_ids)
    normalized_semantics: list[dict[str, Any]] = []
    for raw in semantic_tokens:
        token = dict(raw)
        token_id = token.get("id")
        if isinstance(token_id, str) and token_id in primitive_ids:
            base_id = _token_id_from_key(brand, token)
            new_id = base_id
            n = 2
            while new_id in used_ids:
                new_id = f"{base_id}_{n}"
                n += 1
            # $ref already targets the colliding id (= primitive); leave it alone.
            token["id"] = new_id
            token_id = new_id
        if isinstance(token_id, str) and token_id:
            used_ids.add(token_id)
        normalized_semantics.append(
            _rewrite_token_refs(token, aliases=aliases, primitive_ids=primitive_ids)
        )
    return primitives, normalized_semantics


def _units_by_doc_ref(units: Sequence[SourceUnit]) -> dict[str, list[SourceUnit]]:
    grouped: dict[str, list[SourceUnit]] = {}
    for unit in units:
        grouped.setdefault(unit.doc_ref, []).append(unit)
    for doc_ref in grouped:
        grouped[doc_ref] = sorted(grouped[doc_ref], key=lambda item: item.ordinal)
    return dict(sorted(grouped.items()))


def _token_lines(tokens: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for token in tokens:
        value = token.get("value") or {}
        default = value.get("default") if isinstance(value, dict) else value
        aliases = token.get("aliases") or []
        lines.append(
            f"  {token.get('id')}  key={token.get('key')}  "
            f"default={json.dumps(default, default=str)}  "
            f"aliases={json.dumps(aliases, ensure_ascii=False, default=str)}"
        )
    return "\n".join(lines)


def _scan_tok_refs(value: Any, refs: set[str]) -> None:
    if isinstance(value, Mapping):
        for child in value.values():
            _scan_tok_refs(child, refs)
    elif isinstance(value, list):
        for child in value:
            _scan_tok_refs(child, refs)
    elif isinstance(value, str) and value.startswith("tok_"):
        refs.add(value)


def validate_rule_refs(
    rules: list[dict[str, Any]],
    catalog_ids: set[str],
) -> list[RefViolation]:
    out: list[RefViolation] = []
    for rule in rules:
        refs: set[str] = set()
        _scan_tok_refs(rule.get("effect"), refs)
        _scan_tok_refs(rule.get("applies_when"), refs)
        unknown = sorted(refs - catalog_ids)
        if unknown:
            out.append(
                RefViolation(
                    rule_slug=str(rule.get("slug", "?")),
                    unknown_ids=unknown,
                )
            )
    return out


def _token_ref_violations(
    tokens: list[dict[str, Any]],
    known_ids: set[str],
) -> dict[str, list[str]]:
    """Map token id -> unknown ``tok_`` ids referenced inside its value.

    ponytail: scans every tok_-prefixed string in the value subtree (including
    evidence quotes); brand documents never contain literal tok_ ids, so the
    broad scan is safe and matches validate_rule_refs semantics.
    """
    out: dict[str, list[str]] = {}
    for token in tokens:
        refs: set[str] = set()
        _scan_tok_refs(token.get("value"), refs)
        unknown = sorted(refs - known_ids)
        if unknown:
            out[str(token.get("id", "?"))] = unknown
    return out


def _null_dangling_refs(value: Any, unknown: set[str]) -> Any:
    """Replace any ``{"$ref": <unknown>}`` node with None, preserving the rest."""
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str) and ref in unknown:
            return None
        return {key: _null_dangling_refs(child, unknown) for key, child in value.items()}
    if isinstance(value, list):
        return [_null_dangling_refs(child, unknown) for child in value]
    return value


def _apply_token_ref_fallback(
    tokens: list[dict[str, Any]],
    violations: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Terminal degrade: null dangling $refs and record them on the token."""
    out: list[dict[str, Any]] = []
    for raw_token in tokens:
        unknown = set(violations.get(str(raw_token.get("id", "?")), ()))
        if not unknown:
            out.append(raw_token)
            continue
        token = dict(raw_token)
        token["value"] = _null_dangling_refs(token.get("value"), unknown)
        token["unresolved_refs"] = sorted(
            set(token.get("unresolved_refs") or ()) | unknown
        )
        out.append(token)
    return out


def _token_ref_feedback(violations: Mapping[str, list[str]]) -> str:
    lines = ["REFERENCE CONTRACT VIOLATIONS (fix and re-emit the FULL JSON):"]
    lines.extend(
        f"  token '{token_id}' references unknown ids: {', '.join(unknown)}"
        for token_id, unknown in sorted(violations.items())
    )
    lines.append(
        "Every $ref MUST target the exact id of a token you emitted (or a "
        "PRIMITIVE TOKEN id printed above). Do not invent ids."
    )
    return "\n".join(lines)


def _strip_unknown_refs(value: Any, unknown: set[str]) -> Any:
    if isinstance(value, dict):
        direct = {
            ref
            for key in ("token_id", "$ref")
            if isinstance((ref := value.get(key)), str)
        }
        if direct & unknown:
            return None
        return {
            key: cleaned
            for key, child in value.items()
            if (cleaned := _strip_unknown_refs(child, unknown)) is not None
        }
    if isinstance(value, list):
        return [
            cleaned
            for child in value
            if (cleaned := _strip_unknown_refs(child, unknown)) is not None
        ]
    if isinstance(value, str) and value in unknown:
        return None
    return value


def _terminal_ref_fallback(
    rules: list[dict[str, Any]],
    violations: list[RefViolation],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_slug = {violation.rule_slug: set(violation.unknown_ids) for violation in violations}
    requests: list[dict[str, Any]] = []
    cleaned_rules: list[dict[str, Any]] = []
    for raw_rule in rules:
        rule = dict(raw_rule)
        slug = str(rule.get("slug", "?"))
        unknown = by_slug.get(slug, set())
        if unknown:
            rule["effect"] = _strip_unknown_refs(rule.get("effect"), unknown)
            rule["applies_when"] = _strip_unknown_refs(
                rule.get("applies_when"),
                unknown,
            )
            rule["unresolved_refs"] = sorted(unknown)
            evidence = rule.get("evidence")
            unit_ids = (
                list(evidence.get("unit_ids") or [])
                if isinstance(evidence, Mapping)
                else []
            )
            quotes = (
                list(evidence.get("quotes") or [])
                if isinstance(evidence, Mapping)
                else []
            )
            requests.extend(
                {
                    "key_proposal": ref.removeprefix("tok_").replace("_", "."),
                    "value": None,
                    "unit_ids": unit_ids,
                    "quotes": quotes,
                    "for_rule_slug": slug,
                }
                for ref in sorted(unknown)
            )
        cleaned_rules.append(rule)
    return cleaned_rules, requests


def _ref_feedback(violations: Sequence[RefViolation]) -> str:
    lines = ["REFERENCE CONTRACT VIOLATIONS (fix and re-emit the FULL JSON):"]
    lines.extend(
        f"  rule '{violation.rule_slug}' references unknown ids: "
        f"{', '.join(violation.unknown_ids)}"
        for violation in violations
    )
    lines.extend(
        [
            "Use ONLY ids from CANDIDATE TOKEN CATALOG, exactly as printed. If a needed token is",
            'genuinely absent, put it under "missing_token_requests" instead of inventing an id.',
        ]
    )
    return "\n".join(lines)


def _catalog_summary(primitive_tokens: list[dict[str, Any]], semantic_tokens: list[dict[str, Any]]) -> str:
    lines = [
        f"primitive tokens ({len(primitive_tokens)}):",
        _token_lines(primitive_tokens),
        f"semantic tokens ({len(semantic_tokens)}):",
        _token_lines(semantic_tokens),
    ]
    return "\n".join(lines)


def _write_run_artifacts(work_dir: Path, output: RunOutput) -> None:
    run_dir = work_dir / "runs" / output.variant.run_id
    atomic_write_json(run_dir / "tokens_primitive.json", output.primitive_tokens)
    atomic_write_json(run_dir / "tokens_semantic.json", output.semantic_tokens)
    atomic_write_json(run_dir / "catalog_rest.json", output.catalog_rest)
    for group in output.rule_groups:
        atomic_write_json(
            run_dir / "rules" / f"{group.group_id}.json",
            group.model_dump(mode="json"),
        )


async def _extract_tokens_for_variant(
    *,
    brand: str,
    variant: RunVariant,
    units_text: str,
    usage: Usage,
    client: LLMClient,
    prompts_dir: Path | None,
    cache_root: Path,
    force: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tpl_primitive = load_prompt(PROMPT_TOKENS_PRIMITIVE, prompts_dir)
    ctx_primitive = CacheContext(
        brand=brand,
        variant=variant,
        prompt_name=PROMPT_TOKENS_PRIMITIVE,
        template=tpl_primitive,
        content_hash="",
        cache_root=cache_root,
    )
    rendered_a1a = tpl_primitive.render(brand=brand, units=units_text)
    raw_primitives = await complete_json_cached(
        client,
        ctx_primitive,
        rendered_a1a.system,
        rendered_a1a.user,
        usage,
        force=force,
    )
    primitive_tokens = [
        dict(token, kind="primitive")
        for token in raw_primitives.get("tokens", [])
        if isinstance(token, dict)
    ]

    tpl_semantic = load_prompt(PROMPT_TOKENS_SEMANTIC, prompts_dir)
    ctx_semantic = CacheContext(
        brand=brand,
        variant=variant,
        prompt_name=PROMPT_TOKENS_SEMANTIC,
        template=tpl_semantic,
        content_hash="",
        cache_root=cache_root,
    )
    rendered_a1b = tpl_semantic.render(
        brand=brand,
        units=units_text,
        primitives=_token_lines(primitive_tokens),
    )
    feedback = ""
    violations: dict[str, list[str]] = {}
    normalized: tuple[list[dict[str, Any]], list[dict[str, Any]]] = ([], [])
    for attempt in range(settings.REF_RETRIES + 1):
        raw_semantics = await complete_json_cached(
            client,
            ctx_semantic,
            rendered_a1b.system,
            rendered_a1b.user + feedback,
            usage,
            force=force,
            extra={"token_ref_retry": attempt} if attempt else None,
        )
        semantic_tokens = [
            dict(token, kind="semantic")
            for token in raw_semantics.get("tokens", [])
            if isinstance(token, dict)
        ]
        normalized = normalize_token_ids(brand, primitive_tokens, semantic_tokens)
        known_ids = {
            str(token.get("id")) for bucket in normalized for token in bucket
        }
        violations = _token_ref_violations(normalized[1], known_ids)
        if not violations:
            return normalized
        feedback = "\n\n" + _token_ref_feedback(violations)
    norm_primitive, norm_semantic = normalized
    return norm_primitive, _apply_token_ref_fallback(norm_semantic, violations)


async def run_token_phase(
    brand: str,
    variants: Sequence[RunVariant],
    units: list[SourceUnit],
    labels: list[UnitLabel],
    usage: Usage,
    client: LLMClient,
    *,
    prompts_dir: Path | None = None,
    cache_root: Path | None = None,
    work_dir: Path | None = None,
    force: bool = False,
    exclude_unit_ids: set[str] | None = None,
) -> FrozenCatalog:
    """Extract and reconcile one token catalog shared by every rule run."""
    from .ensemble import build_verified_run, reconcile_tokens_only

    resolved_cache_root = cache_root or DEFAULT_CACHE_ROOT
    if force:
        clear_brand_cache(brand, resolved_cache_root)
    selected_units = select_units(units, exclude_unit_ids=exclude_unit_ids)
    units_text = render_units(selected_units)
    compiled_tables = []
    if settings.TABLE_COMPILER:
        from indexing_v2.tables import compile_brand_tables, merge_row_tokens

        compiled_tables = compile_brand_tables(brand, selected_units)
    verified = []
    for variant in variants:
        primitive, semantic = await _extract_tokens_for_variant(
            brand=brand,
            variant=variant,
            units_text=units_text,
            usage=usage,
            client=client,
            prompts_dir=prompts_dir,
            cache_root=resolved_cache_root,
            force=force,
        )
        if compiled_tables:
            # Deterministic row tokens are identical in every run, so they
            # reconcile with support = K and land in the frozen catalog.
            primitive = merge_row_tokens(primitive, compiled_tables)
        verified.append(
            build_verified_run(
                RunOutput(
                    variant=variant,
                    primitive_tokens=primitive,
                    semantic_tokens=semantic,
                ),
                units,
            )
        )
    reconciled = reconcile_tokens_only(verified, units, labels)
    # Closure invariant: the frozen catalog must not contain a $ref whose
    # target is absent (reconciliation can drop a referenced token even when
    # every per-run output was closed). Dangling refs degrade deterministically
    # via the same fallback the per-variant retry uses.
    frozen_ids = {
        str(token.get("id"))
        for token in (*reconciled.tokens_primitive, *reconciled.tokens_semantic)
    }
    payload = {
        "tokens_primitive": _apply_token_ref_fallback(
            reconciled.tokens_primitive,
            _token_ref_violations(reconciled.tokens_primitive, frozen_ids),
        ),
        "tokens_semantic": _apply_token_ref_fallback(
            reconciled.tokens_semantic,
            _token_ref_violations(reconciled.tokens_semantic, frozen_ids),
        ),
    }
    frozen = FrozenCatalog(
        **payload,
        hash=stable_hash(payload),
    )
    if work_dir is not None:
        atomic_write_json(
            work_dir / "catalog_frozen.json",
            frozen.model_dump(mode="json"),
        )
    return frozen


async def run_rules_phase(
    brand: str,
    variant: RunVariant,
    units: list[SourceUnit],
    labels: list[UnitLabel],
    frozen: FrozenCatalog,
    usage: Usage,
    client: LLMClient,
    **kwargs: Any,
) -> RunOutput:
    """Extract non-token catalog entities and rules against a frozen token id set."""
    return await run_extraction(
        brand,
        variant,
        units,
        labels,
        usage,
        client,
        frozen=frozen,
        **kwargs,
    )


async def repair_missing_token_requests(
    *,
    brand: str,
    outputs: Sequence[RunOutput],
    frozen: FrozenCatalog,
    units: list[SourceUnit],
    labels: list[UnitLabel],
    usage: Usage,
    client: LLMClient,
    prompts_dir: Path | None = None,
    cache_root: Path | None = None,
    work_dir: Path | None = None,
    concurrency: int | None = None,
) -> tuple[FrozenCatalog, list[RunOutput]]:
    """Perform the single append-only missing-token repair round."""
    from .provenance import verify_entities

    request_rows: list[tuple[str, str, dict[str, Any]]] = []
    for output in outputs:
        for group in output.rule_groups:
            for request in group.missing_token_requests:
                request_rows.append((group.doc_ref, group.group_id, request))
    if not request_rows:
        return frozen, list(outputs)

    deduped: dict[tuple[str, str, tuple[str, ...]], tuple[str, str, dict[str, Any]]] = {}
    for doc_ref, group_id, request in request_rows:
        unit_ids = tuple(sorted(str(item) for item in (request.get("unit_ids") or [])))
        key = (
            str(request.get("key_proposal") or ""),
            stable_hash(request.get("value")),
            unit_ids,
        )
        deduped.setdefault(key, (doc_ref, group_id, request))

    by_doc: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for doc_ref, group_id, request in deduped.values():
        by_doc.setdefault(doc_ref, []).append((group_id, request))
    resolved_cache = cache_root or DEFAULT_CACHE_ROOT
    variant = outputs[0].variant
    generated: list[dict[str, Any]] = []
    template = load_prompt(PROMPT_TOKENS_PRIMITIVE, prompts_dir)
    units_by_id = {unit.unit_id: unit for unit in units}
    for doc_ref in sorted(by_doc):
        target_ids = {
            str(unit_id)
            for _, request in by_doc[doc_ref]
            for unit_id in (request.get("unit_ids") or [])
            if str(unit_id) in units_by_id
        }
        target_units = [units_by_id[unit_id] for unit_id in sorted(target_ids)]
        if not target_units:
            continue
        rendered = template.render(
            brand=brand,
            units=render_units(target_units),
        )
        ctx = CacheContext(
            brand=brand,
            variant=variant,
            prompt_name=PROMPT_TOKENS_PRIMITIVE,
            template=template,
            content_hash="",
            cache_root=resolved_cache,
        )
        raw = await complete_json_cached(
            client,
            ctx,
            rendered.system,
            rendered.user,
            usage,
            extra={
                "missing_token_repair": 1,
                "doc_ref": doc_ref,
                "unit_ids": sorted(target_ids),
            },
        )
        generated.extend(
            dict(token, kind="primitive")
            for token in (raw.get("tokens") or [])
            if isinstance(token, dict)
        )

    generated_by_id: dict[str, dict[str, Any]] = {}
    for token in sorted(generated, key=stable_hash):
        token_id = str(token.get("id") or "")
        if token_id:
            generated_by_id.setdefault(token_id, token)
    generated = [generated_by_id[token_id] for token_id in sorted(generated_by_id)]
    if generated:
        provenance = verify_entities({"token_primitive": generated}, units)
        quarantined = {entry.entity_id for entry in provenance.quarantine}
        existing_ids = {
            str(token.get("id"))
            for token in [*frozen.tokens_primitive, *frozen.tokens_semantic]
        }
        accepted = [
            token
            for token in generated
            if str(token.get("id") or "") not in quarantined
            and str(token.get("id") or "") not in existing_ids
        ]
    else:
        accepted = []
    primitive = sorted(
        [*copy.deepcopy(frozen.tokens_primitive), *accepted],
        key=lambda token: str(token.get("id") or ""),
    )
    payload = {
        "tokens_primitive": primitive,
        "tokens_semantic": copy.deepcopy(frozen.tokens_semantic),
    }
    repaired = FrozenCatalog(**payload, hash=stable_hash(payload))
    if work_dir is not None:
        atomic_write_json(
            work_dir / "catalog_frozen.json",
            repaired.model_dump(mode="json"),
        )
    if not accepted:
        return repaired, list(outputs)

    affected_groups = {
        group_id
        for rows in by_doc.values()
        for group_id, _ in rows
    }
    rerendered_outputs: list[RunOutput] = []
    for original in outputs:
        refreshed = await run_rules_phase(
            brand,
            original.variant,
            units,
            labels,
            repaired,
            usage,
            client,
            prompts_dir=prompts_dir,
            cache_root=resolved_cache,
            force=False,
            concurrency=concurrency,
        )
        refreshed_by_id = {group.group_id: group for group in refreshed.rule_groups}
        groups = [
            refreshed_by_id.get(group.group_id, group)
            if group.group_id in affected_groups
            else group
            for group in original.rule_groups
        ]
        output = original.model_copy(
            update={
                "primitive_tokens": copy.deepcopy(repaired.tokens_primitive),
                "semantic_tokens": copy.deepcopy(repaired.tokens_semantic),
                "rule_groups": groups,
                "rules_by_doc_ref": {
                    group.doc_ref: group.rules
                    for group in sorted(groups, key=lambda item: item.doc_ref)
                },
            },
            deep=True,
        )
        if work_dir is not None:
            _write_run_artifacts(work_dir, output)
        rerendered_outputs.append(output)
    return repaired, rerendered_outputs


async def run_extraction(
    brand: str,
    variant: RunVariant,
    units: list[SourceUnit],
    labels: list[UnitLabel],
    usage: Usage,
    client: LLMClient,
    *,
    prompts_dir: Path | None = None,
    cache_root: Path | None = None,
    work_dir: Path | None = None,
    force: bool = False,
    concurrency: int | None = None,
    exclude_unit_ids: set[str] | None = None,
    frozen: FrozenCatalog | None = None,
) -> RunOutput:
    """A1a → A1b (same run) → A2 globally, then rules per doc_ref blob (Pass B)."""
    del labels
    sem_limit = concurrency if concurrency is not None else settings.CONCURRENCY
    if sem_limit <= 0:
        raise ValueError(f"concurrency must be greater than zero, got {sem_limit}")

    if force:
        clear_brand_cache(brand, cache_root)

    selected = select_units(units, exclude_unit_ids=exclude_unit_ids)
    all_units_text = render_units(selected)
    grouped_units = _units_by_doc_ref(selected)
    canonical_units_by_doc_ref = _units_by_doc_ref(units)
    resolved_cache_root = cache_root or DEFAULT_CACHE_ROOT
    semaphore = asyncio.Semaphore(sem_limit)

    tpl_catalog = load_prompt(PROMPT_CATALOG_REST, prompts_dir)
    tpl_rules = load_prompt(PROMPT_RULES_CLUSTER, prompts_dir)
    if frozen is None:
        primitive_tokens, semantic_tokens = await _extract_tokens_for_variant(
            brand=brand,
            variant=variant,
            units_text=all_units_text,
            usage=usage,
            client=client,
            prompts_dir=prompts_dir,
            cache_root=resolved_cache_root,
            force=force,
        )
    else:
        primitive_tokens = copy.deepcopy(frozen.tokens_primitive)
        semantic_tokens = copy.deepcopy(frozen.tokens_semantic)

    compiled_tables = []
    if settings.TABLE_COMPILER:
        from indexing_v2.tables import compile_brand_tables, merge_row_tokens

        compiled_tables = compile_brand_tables(brand, selected)
        # Row tokens join the catalog before catalog_ids/prompt rendering so
        # LLM rules can reference them and pass $ref validation.
        primitive_tokens = merge_row_tokens(primitive_tokens, compiled_tables)

    all_tokens = primitive_tokens + semantic_tokens
    catalog_ids = {
        str(token["id"])
        for token in all_tokens
        if isinstance(token.get("id"), str) and token["id"]
    }
    ctx_catalog = CacheContext(
        brand=brand,
        variant=variant,
        prompt_name=PROMPT_CATALOG_REST,
        template=tpl_catalog,
        content_hash="",
        cache_root=resolved_cache_root,
    )
    rendered_a2 = tpl_catalog.render(
        brand=brand,
        units=all_units_text,
        tokens=_token_lines(all_tokens),
    )
    catalog_rest = await complete_json_cached(
        client,
        ctx_catalog,
        rendered_a2.system,
        rendered_a2.user,
        usage,
        force=force,
    )
    if not isinstance(catalog_rest, dict):
        catalog_rest = {}

    catalog_text = _catalog_summary(primitive_tokens, semantic_tokens)

    async def _extract_rules(doc_ref: str, blob_units: list[SourceUnit]) -> RuleGroupOutput:
        async with semaphore:
            group_id = _group_id(brand, doc_ref)
            blob_text = render_units(blob_units)
            original_text = "".join(
                unit.text for unit in canonical_units_by_doc_ref[doc_ref]
            )
            rendered_rules = tpl_rules.render(
                brand=brand,
                doc_ref=doc_ref,
                group_id=group_id,
                units=blob_text,
                catalog=catalog_text,
            )
            ctx_rules = CacheContext(
                brand=brand,
                variant=variant,
                prompt_name=PROMPT_RULES_CLUSTER,
                template=tpl_rules,
                content_hash="",
                cache_root=resolved_cache_root,
            )
            raw_rules: Any = {}
            rules: list[dict[str, Any]] = []
            violations: list[RefViolation] = []
            user_prompt = rendered_rules.user
            attempt = 0
            while True:
                raw_rules = await complete_json_cached(
                    client,
                    ctx_rules,
                    rendered_rules.system,
                    user_prompt,
                    usage,
                    force=force,
                    extra={
                        "doc_ref": doc_ref,
                        "group_id": group_id,
                        "ref_retry": attempt,
                    },
                )
                if not isinstance(raw_rules, Mapping):
                    raw_rules = {}
                rules = [
                    rule
                    for rule in (raw_rules.get("rules") or [])
                    if isinstance(rule, dict)
                ]
                violations = validate_rule_refs(rules, catalog_ids)
                if not violations or attempt >= settings.REF_RETRIES:
                    break
                attempt += 1
                user_prompt = (
                    rendered_rules.user
                    + "\n\n"
                    + _ref_feedback(violations)
                )
            synthesized_requests: list[dict[str, Any]] = []
            if violations:
                rules, synthesized_requests = _terminal_ref_fallback(
                    rules,
                    violations,
                )
            relations = [
                relation
                for relation in (raw_rules.get("relations") or [])
                if isinstance(relation, dict)
            ]
            missing_token_requests = [
                request
                for request in (raw_rules.get("missing_token_requests") or [])
                if isinstance(request, dict)
            ]
            missing_token_requests.extend(synthesized_requests)
            return RuleGroupOutput(
                group_id=group_id,
                doc_ref=doc_ref,
                original_text=original_text,
                rules=rules,
                relations=relations,
                missing_token_requests=missing_token_requests,
            )

    rule_groups = normalize_rule_groups(
        brand,
        await asyncio.gather(
            *(_extract_rules(doc_ref, blob_units) for doc_ref, blob_units in grouped_units.items())
        ),
    )
    if compiled_tables:
        catalog_rest = dict(catalog_rest)
        catalog_rest["token_tables"] = [
            copy.deepcopy(item.table) for item in compiled_tables
        ]
        rule_groups = _inject_umbrella_rules(
            brand,
            rule_groups,
            compiled_tables,
            canonical_units_by_doc_ref,
        )
    rules_by_doc_ref = {
        group.doc_ref: group.rules for group in sorted(rule_groups, key=lambda item: item.doc_ref)
    }

    output = RunOutput(
        variant=variant,
        primitive_tokens=primitive_tokens,
        semantic_tokens=semantic_tokens,
        catalog_rest=catalog_rest,
        rules_by_doc_ref=rules_by_doc_ref,
        rule_groups=sorted(rule_groups, key=lambda item: item.doc_ref),
    )
    if work_dir is not None:
        _write_run_artifacts(work_dir, output)
    return output
