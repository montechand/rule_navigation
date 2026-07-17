"""Deterministic S6b repair of orphan token-to-rule bindings."""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from indexing_v2 import settings
from indexing_v2.contracts import (
    LinkAssignment,
    LinkPatch,
    LinkSignals,
    LinkerResult,
    RunVariant,
    SourceUnit,
    TriageItem,
    atomic_write_json,
    stable_hash,
    write_jsonl,
)
from indexing_v2.extraction.ledger import CandidatesBundle
from indexing_v2.extraction.prompts import load_prompt
from indexing_v2.extraction.provenance import ProvenanceResult
from indexing_v2.extraction.runner import (
    CacheContext,
    LLMClient,
    PROMPT_LINKER_ADJUDICATE,
    complete_json_cached,
)
from shared.llm import Usage

LINKER_VERSION = "linker-v1.0.0"

_AUTO = "AUTO"
_ADJUDICATE = "ADJUDICATE"
_GOVERNANCE_ONLY = frozenset({"cardinality", "exclusivity", "ordering"})
_FRAG_SPLIT = re.compile(r"[.\s_/\-]+")
_FRAG_STOP = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "brand",
        "body",
        "by",
        "color",
        "default",
        "design",
        "for",
        "from",
        "global",
        "icon",
        "in",
        "is",
        "of",
        "on",
        "opacity",
        "or",
        "padding",
        "size",
        "spacing",
        "style",
        "the",
        "text",
        "to",
        "token",
        "use",
        "value",
        "weight",
        "with",
    }
)
_HEX_RE = re.compile(r"(?<![\w])#[0-9a-fA-F]{3,8}\b")
_DIM_RE = re.compile(r"(?<![\w.-])-?(?:\d+(?:\.\d+)?|\.\d+)(?:rem|em|pt|pc|vh|vw|vmin|vmax)\b", re.I)
_PX_RE = re.compile(r"(?<![\w.-])-?(?:\d+(?:\.\d+)?|\.\d+)px\b", re.I)
_PCT_RE = re.compile(r"(?<![\w.-])-?(?:\d+(?:\.\d+)?|\.\d+)%\b")
_RATIO_RE = re.compile(r"(?<![\w.-])(?:\d+(?:\.\d+)?)[x:](?:\d+(?:\.\d+)?)(?![\w.])", re.I)
_TOK_PREFIX = "tok_"


class LinkMatch(BaseModel):
    token_id: str
    rule_id: str
    tier: Literal["AUTO", "ADJUDICATE"] | None
    signals: LinkSignals


def _normalized_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower().replace("×", "x")).strip()


def _extract_literals(value: Any) -> tuple[list[str], list[str]]:
    text = str(value or "")
    strong = sorted(
        {
            match.group(0).lower()
            for regex in (_HEX_RE, _DIM_RE)
            for match in regex.finditer(text)
        }
    )
    weak = sorted(
        {
            match.group(0).lower()
            for regex in (_PX_RE, _PCT_RE, _RATIO_RE)
            for match in regex.finditer(text)
        }
    )
    return strong, weak


def _fragments(value: str) -> set[str]:
    return {
        part
        for part in _FRAG_SPLIT.split(_normalized_text(value))
        if len(part) >= 3 and part not in _FRAG_STOP and not part.isdigit()
    }


def _scan_tok_refs(value: Any, out: set[str]) -> None:
    if isinstance(value, Mapping):
        for child in value.values():
            _scan_tok_refs(child, out)
    elif isinstance(value, list):
        for child in value:
            _scan_tok_refs(child, out)
    elif isinstance(value, str) and value.startswith(_TOK_PREFIX):
        out.add(value)


def scan_tok_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    _scan_tok_refs(value, refs)
    return refs


def _entity_unit_ids(
    entity: Mapping[str, Any],
    provenance: ProvenanceResult | None,
) -> set[str]:
    out: set[str] = set()
    for key, value in entity.items():
        if key == "unit_ids" and isinstance(value, list):
            out.update(str(item) for item in value)
        elif isinstance(value, (dict, list)):
            if isinstance(value, dict):
                out.update(_entity_unit_ids(value, None))
            else:
                for item in value:
                    if isinstance(item, dict):
                        out.update(_entity_unit_ids(item, None))
    entity_id = str(entity.get("id") or "")
    if provenance is not None and entity_id:
        for record in provenance.records_by_entity.get(entity_id, []):
            for span in record.spans:
                out.update(span.unit_ids)
    return out


def _rule_text(rule: Mapping[str, Any]) -> str:
    return _normalized_text(
        " ".join(
            str(rule.get(field) or "")
            for field in ("rule_text", "summary", "intent", "snippets")
        )
    )


def _token_values(token: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    value = token.get("value")
    strong: set[str] = set()
    weak: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, (str, int, float)):
            strong_values, weak_values = _extract_literals(str(item))
            strong.update(strong_values)
            weak.update(weak_values)

    visit(value)
    return strong, weak


def match_pair(
    token: Mapping[str, Any],
    rule: Mapping[str, Any],
    provenance: ProvenanceResult | None = None,
) -> LinkMatch:
    token_id = str(token.get("id") or "")
    rule_id = str(rule.get("id") or "")
    text = _rule_text(rule)
    key = str(token.get("key") or "")
    aliases = sorted(
        {
            str(alias)
            for alias in (token.get("aliases") or [])
            if isinstance(alias, str) and len(_normalized_text(alias)) >= 5
        }
    )
    key_norm = _normalized_text(key)
    key_hit = key if key_norm and key_norm in text else None
    alias_hit = next(
        (alias for alias in aliases if _normalized_text(alias) in text),
        None,
    )

    token_units = _entity_unit_ids(token, provenance)
    rule_units = _entity_unit_ids(rule, provenance)
    unit_overlap = sorted(token_units & rule_units)

    token_strong, token_weak = _token_values(token)
    rule_strong, rule_weak = _extract_literals(text)
    strong_values = sorted(token_strong & set(rule_strong))
    weak_values = sorted(token_weak & set(rule_weak))

    key_fragments = _fragments(key)
    alias_fragments = set().union(*(_fragments(alias) for alias in aliases)) if aliases else set()
    text_fragments = _fragments(text)
    key_frag_hits = sorted(key_fragments & text_fragments)
    frag_hits = sorted((key_fragments | alias_fragments) & text_fragments)
    signals = LinkSignals(
        unit_overlap=unit_overlap,
        key_hit=key_hit,
        alias_hit=alias_hit,
        strong_values=strong_values,
        weak_values=weak_values,
        fragments=frag_hits,
        key_fragments=key_frag_hits,
    )

    strong_frag = len(frag_hits) >= 2 and bool(key_frag_hits)
    auto = bool(
        key_hit
        or (
            unit_overlap
            and (
                strong_frag
                or strong_values
                or alias_hit
                or (weak_values and key_frag_hits)
            )
        )
        or (strong_values and (strong_frag or unit_overlap))
    )
    any_signal = bool(
        key_hit
        or alias_hit
        or unit_overlap
        or (
            len(frag_hits) >= 2
            and (strong_values or weak_values)
        )
    )
    if rule.get("constraint_type") in _GOVERNANCE_ONLY and auto:
        auto = bool(key_hit or alias_hit)
    tier: Literal["AUTO", "ADJUDICATE"] | None = (
        _AUTO if auto else _ADJUDICATE if any_signal else None
    )
    return LinkMatch(
        token_id=token_id,
        rule_id=rule_id,
        tier=tier,
        signals=signals,
    )


def _element_path(
    token: Mapping[str, Any],
    *,
    semantic: bool,
) -> tuple[str | None, str]:
    paths = token.get("element_paths")
    if semantic and isinstance(paths, list):
        first = next((str(path) for path in paths if str(path).strip()), None)
        if first:
            return first, "token.element_paths"
    key = str(token.get("key") or "").strip()
    parts = [part for part in key.split(".") if part]
    if len(parts) >= 3:
        rest = re.sub(r"(?:_\d+(?:_\d+)*)+$", "", "_".join(parts[2:]))
        path = ".".join(part for part in (parts[1], parts[0], rest) if part)
        return path or key, "heuristic_from_key"
    if key:
        return key, "heuristic_from_key"
    return None, "none"


def _all_rules(bundle: CandidatesBundle) -> list[dict[str, Any]]:
    return [
        rule
        for group_id in sorted(bundle.rules_by_group)
        for rule in bundle.rules_by_group[group_id]
        if isinstance(rule, dict) and rule.get("id")
    ]


def _token_index(bundle: CandidatesBundle) -> dict[str, dict[str, Any]]:
    return {
        str(token["id"]): token
        for token in [*bundle.tokens_primitive, *bundle.tokens_semantic]
        if isinstance(token.get("id"), str) and token["id"]
    }


def _reachable_token_ids(bundle: CandidatesBundle) -> set[str]:
    tokens = _token_index(bundle)
    reachable: set[str] = set()
    for rule in _all_rules(bundle):
        _scan_tok_refs(rule.get("effect"), reachable)
        _scan_tok_refs(rule.get("token_ids"), reachable)
    reachable &= set(tokens)
    pending = list(sorted(reachable))
    while pending:
        token_id = pending.pop()
        refs = scan_tok_refs(tokens[token_id]) & set(tokens)
        for ref in sorted(refs - reachable):
            reachable.add(ref)
            pending.append(ref)
    return reachable


def _existing_rule_refs(rule: Mapping[str, Any]) -> set[str]:
    refs = scan_tok_refs(rule.get("effect"))
    refs.update(scan_tok_refs(rule.get("token_ids")))
    return refs


def _append_assignment(
    rule: dict[str, Any],
    assignment: LinkAssignment,
    linked_by: str,
    token_key: str,
) -> bool:
    if assignment.token_id in _existing_rule_refs(rule):
        return False
    effect = rule.get("effect")
    if effect is None:
        effect = {"assignments": []}
        rule["effect"] = effect
    elif isinstance(effect, list):
        effect = {"assignments": effect}
        rule["effect"] = effect
    elif not isinstance(effect, dict):
        effect = {"assignments": []}
        rule["effect"] = effect
    assignments = effect.setdefault("assignments", [])
    if not isinstance(assignments, list):
        assignments = []
        effect["assignments"] = assignments
    assignments.append(
        {
            "element_path": assignment.element_path or token_key,
            "token_id": assignment.token_id,
            "linked_by": linked_by,
        }
    )
    return True


def _rule_literal_rows(
    rules: Sequence[Mapping[str, Any]],
    tokens: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    catalog_literals: set[str] = set()
    for token in tokens:
        strong, weak = _token_values(token)
        catalog_literals.update(strong)
        catalog_literals.update(weak)
    out: list[dict[str, str]] = []
    for rule in rules:
        strong, weak = _extract_literals(_rule_text(rule))
        for literal in sorted((set(strong) | set(weak)) - catalog_literals):
            out.append(
                {
                    "rule_id": str(rule.get("id") or ""),
                    "literal": literal,
                }
            )
    return out


def _token_quotes(
    token_id: str,
    token: Mapping[str, Any],
    provenance: ProvenanceResult | None,
) -> list[str]:
    quotes: set[str] = set()
    evidence = token.get("evidence")
    if isinstance(evidence, Mapping):
        quotes.update(str(quote) for quote in (evidence.get("quotes") or []))
    if provenance is not None:
        for record in provenance.records_by_entity.get(token_id, []):
            quotes.update(span.quote for span in record.spans)
    return sorted(quote for quote in quotes if quote)


async def _adjudicate_rule(
    *,
    bundle: CandidatesBundle,
    rule: Mapping[str, Any],
    pairs: Sequence[LinkMatch],
    tokens: Mapping[str, dict[str, Any]],
    provenance: ProvenanceResult | None,
    client: LLMClient,
    usage: Usage,
    cache_root: Path,
) -> dict[str, dict[str, Any]]:
    template = load_prompt(PROMPT_LINKER_ADJUDICATE)
    pair_payload = [
        {
            "token_id": pair.token_id,
            "key": tokens[pair.token_id].get("key"),
            "value_preview": tokens[pair.token_id].get("value"),
            "aliases": tokens[pair.token_id].get("aliases") or [],
            "quotes": _token_quotes(pair.token_id, tokens[pair.token_id], provenance),
            "signals": pair.signals.model_dump(mode="json"),
        }
        for pair in pairs
    ]
    rendered = template.render(
        brand=bundle.brand,
        rule_id=str(rule.get("id") or ""),
        rule_excerpt=str(rule.get("rule_text") or rule.get("summary") or "")[:2000],
        pairs=json.dumps(pair_payload, sort_keys=True, ensure_ascii=False),
    )
    variant = RunVariant(run_id="linker", model=settings.LINKER_MODEL)
    ctx = CacheContext(
        brand=bundle.brand,
        variant=variant,
        prompt_name=PROMPT_LINKER_ADJUDICATE,
        template=template,
        content_hash="",
        cache_root=cache_root,
    )
    raw = await complete_json_cached(
        client,
        ctx,
        rendered.system,
        rendered.user,
        usage,
        extra={
            "rule_id": str(rule.get("id") or ""),
            "token_ids": [pair.token_id for pair in pairs],
        },
    )
    rows = raw.get("decisions") if isinstance(raw, Mapping) else None
    if not isinstance(rows, list):
        rows = [raw] if isinstance(raw, Mapping) else []
    return {
        str(row.get("token_id") or (pairs[0].token_id if len(pairs) == 1 else "")): dict(row)
        for row in rows
        if isinstance(row, Mapping)
    }


def _empty_result() -> LinkerResult:
    return LinkerResult(
        metrics={
            "tokens_total": 0,
            "orphans_before": 0,
            "orphans_after_transitive": 0,
            "orphans_auto_bound": 0,
            "adjudicated_binds": 0,
            "minted_edges": 0,
            "orphans_needs_rule": 0,
            "unresolved_rule_literals": 0,
            "remaining_orphan_ids": [],
        },
        patches=[],
        adjudication_open=[],
        needs_rule_tokens=[],
        unresolved_rule_literals=[],
    )


def _write_result(work_dir: Path, result: LinkerResult) -> None:
    linker_dir = work_dir / "linker"
    atomic_write_json(linker_dir / "linker_result.json", result.model_dump(mode="json"))
    write_jsonl(linker_dir / "patches.jsonl", result.patches)
    write_jsonl(linker_dir / "adjudication.jsonl", result.adjudication_open)
    atomic_write_json(linker_dir / "needs_rule.json", result.needs_rule_tokens)


async def run_linker_stage(
    *,
    bundle: CandidatesBundle,
    provenance: ProvenanceResult | None,
    units: Sequence[SourceUnit],
    client: LLMClient | None,
    usage: Usage,
    work_dir: Path,
    cache_root: Path,
    no_linker: bool = False,
    console: Any | None = None,
) -> tuple[LinkerResult, CandidatesBundle]:
    """Match orphan tokens, apply approved assignments, and persist deterministic artifacts."""
    del units
    if no_linker:
        result = _empty_result()
        _write_result(work_dir, result)
        return result, bundle.model_copy(deep=True)

    patched = bundle.model_copy(deep=True)
    tokens = _token_index(patched)
    rules = _all_rules(patched)
    rules_by_id = {str(rule["id"]): rule for rule in rules}
    semantic_ids = {
        str(token.get("id"))
        for token in patched.tokens_semantic
        if token.get("id")
    }
    reachable_before = _reachable_token_ids(patched)
    orphan_ids = sorted(set(tokens) - reachable_before)
    matches: dict[str, list[LinkMatch]] = {}
    for token_id in orphan_ids:
        matches[token_id] = [
            match
            for rule in rules
            if (match := match_pair(tokens[token_id], rule, provenance)).tier is not None
        ]

    patches_by_rule: dict[tuple[str, str], list[LinkAssignment]] = {}
    auto_token_ids: set[str] = set()
    for token_id in orphan_ids:
        token = tokens[token_id]
        for match in sorted(
            (row for row in matches[token_id] if row.tier == _AUTO),
            key=lambda row: row.rule_id,
        ):
            path, source = _element_path(token, semantic=token_id in semantic_ids)
            assignment = LinkAssignment(
                token_id=token_id,
                element_path=path,
                element_path_source=source,  # type: ignore[arg-type]
                signals=match.signals,
            )
            linked_by = f"{LINKER_VERSION}:auto"
            if _append_assignment(
                rules_by_id[match.rule_id],
                assignment,
                linked_by,
                str(token.get("key") or token_id),
            ):
                patches_by_rule.setdefault((match.rule_id, linked_by), []).append(assignment)
                auto_token_ids.add(token_id)

    adjudication_open: list[dict[str, Any]] = []
    adjudicated_token_ids: set[str] = set()
    adjudicate_pairs = [
        match
        for token_id in orphan_ids
        if token_id not in auto_token_ids
        for match in matches[token_id]
        if match.tier == _ADJUDICATE
    ]
    adjudicate_pairs.sort(key=lambda row: (row.rule_id, row.token_id))
    budget = max(0, settings.LINKER_MAX_ADJUDICATIONS)
    if budget == 0 and adjudicate_pairs and client is not None:
        # A zero budget silently skips every adjudication-tier pair; this is
        # almost always a stray RULE_NAV_LINKER_MAX_ADJUDICATIONS=0 override.
        if console is not None:
            console.print(
                f"[yellow]s6b: LINKER_MAX_ADJUDICATIONS=0 — "
                f"{len(adjudicate_pairs)} pairs skipped[/yellow]"
            )
    selected = adjudicate_pairs[:budget] if client is not None else []
    overflow = adjudicate_pairs[len(selected) :]
    for match in overflow:
        adjudication_open.append(
            {
                "rule_id": match.rule_id,
                "token_id": match.token_id,
                "decision": "budget_exhausted" if client is not None else "skipped_no_client",
                "signals": match.signals.model_dump(mode="json"),
            }
        )

    by_rule: dict[str, list[LinkMatch]] = {}
    for match in selected:
        by_rule.setdefault(match.rule_id, []).append(match)
    for rule_id in sorted(by_rule):
        decisions = await _adjudicate_rule(
            bundle=patched,
            rule=rules_by_id[rule_id],
            pairs=by_rule[rule_id],
            tokens=tokens,
            provenance=provenance,
            client=client,  # type: ignore[arg-type]
            usage=usage,
            cache_root=cache_root,
        )
        for match in by_rule[rule_id]:
            row = decisions.get(match.token_id, {})
            if row.get("decision") != "bind":
                adjudication_open.append(
                    {
                        "rule_id": rule_id,
                        "token_id": match.token_id,
                        "decision": str(row.get("decision") or "no_bind"),
                        "reason": str(row.get("reason") or ""),
                        "signals": match.signals.model_dump(mode="json"),
                    }
                )
                continue
            path = row.get("element_path")
            if not isinstance(path, str) or not path.strip():
                path, _ = _element_path(
                    tokens[match.token_id],
                    semantic=match.token_id in semantic_ids,
                )
            assignment = LinkAssignment(
                token_id=match.token_id,
                element_path=path,
                element_path_source="adjudicated",
                signals=match.signals,
            )
            linked_by = f"{LINKER_VERSION}:adjudicated"
            if _append_assignment(
                rules_by_id[rule_id],
                assignment,
                linked_by,
                str(tokens[match.token_id].get("key") or match.token_id),
            ):
                patches_by_rule.setdefault((rule_id, linked_by), []).append(assignment)
                adjudicated_token_ids.add(match.token_id)

    from indexing_v2.tables import resolve_literal_against_tables, table_row_token_ids

    table_token_ids = table_row_token_ids(patched.tables)
    needs_rule_tokens = [
        {
            "token_id": token_id,
            "unit_ids": sorted(_entity_unit_ids(tokens[token_id], provenance)),
            "key": str(tokens[token_id].get("key") or ""),
        }
        for token_id in orphan_ids
        if not matches[token_id] and token_id not in table_token_ids
    ]
    member_of_table_tokens = [
        {
            "token_id": token_id,
            "note": "member_of_table",
            "key": str(tokens[token_id].get("key") or ""),
        }
        for token_id in orphan_ids
        if not matches[token_id] and token_id in table_token_ids
    ]
    patches = [
        LinkPatch(
            rule_id=rule_id,
            assignments=sorted(assignments, key=lambda row: row.token_id),
            linked_by=linked_by,
        )
        for (rule_id, linked_by), assignments in sorted(patches_by_rule.items())
    ]
    unresolved = [
        row
        for row in _rule_literal_rows(rules, list(tokens.values()))
        if resolve_literal_against_tables(row["literal"], patched.tables) is None
    ]
    reachable_after = _reachable_token_ids(patched)
    remaining_orphan_ids = sorted(set(tokens) - reachable_after)
    result = LinkerResult(
        metrics={
            "tokens_total": len(tokens),
            "orphans_before": len(orphan_ids),
            "orphans_after_transitive": len(remaining_orphan_ids),
            "orphans_auto_bound": len(auto_token_ids),
            "adjudicated_binds": len(adjudicated_token_ids),
            "minted_edges": sum(len(patch.assignments) for patch in patches),
            "orphans_needs_rule": len(needs_rule_tokens),
            "unresolved_rule_literals": len(unresolved),
            "remaining_orphan_ids": remaining_orphan_ids,
        },
        patches=patches,
        adjudication_open=sorted(
            adjudication_open,
            key=lambda row: (str(row.get("token_id")), str(row.get("rule_id"))),
        ),
        needs_rule_tokens=needs_rule_tokens,
        unresolved_rule_literals=unresolved,
        member_of_table_tokens=member_of_table_tokens,
    )
    _write_result(work_dir, result)
    return result, patched


def compute_linker_triage(result: LinkerResult) -> list[TriageItem]:
    items = [
        TriageItem(
            queue="needs_rule",
            key=stable_hash(("needs_rule", row["token_id"], row.get("unit_ids", []))),
            subject_id=str(row["token_id"]),
            context=(
                "orphan token; units "
                f"{', '.join(row.get('unit_ids') or []) or '(none)'} claimed by no rule"
            ),
        )
        for row in result.needs_rule_tokens
    ]
    needs_rule_ids = {item.subject_id for item in items}
    remaining = {
        str(row.get("token_id"))
        for row in result.adjudication_open
        if row.get("token_id")
    } - needs_rule_ids
    items.extend(
        TriageItem(
            queue="orphan_token",
            key=stable_hash(("orphan_token", token_id)),
            subject_id=token_id,
            context="orphan token has candidate rule links requiring adjudication",
        )
        for token_id in sorted(remaining)
    )
    return sorted(items, key=lambda item: (item.queue, item.key))
