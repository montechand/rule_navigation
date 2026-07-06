"""The shared tool repository: every navigation tool an agent can draw, bound to one
brand's KB. Architectures pick subsets by name via ToolRepo.specs(...).

Tool families:
  filesystem : list_dir, read_file, grep
  schema     : describe_entity, get_section_vocab, get_predicate_registry
  lookup     : get_rules, get_entity
  structured : query_rules
  keyword    : keyword_search
  vector     : vector_search
  graph      : rules_for_section, rules_for_token, neighbors, related_rules
  finalize   : finalize_section_ruleset (terminal; built per-run via finalize_spec)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from ..kb import KB
from ..llm import ToolError, ToolSpec
from ..schemas import PREDICATE_REGISTRY, SECTION_TYPES

TOOL_FAMILIES: dict[str, list[str]] = {
    "filesystem": ["list_dir", "read_file", "grep"],
    "schema": ["describe_entity", "get_section_vocab", "get_predicate_registry"],
    "lookup": ["get_rules", "get_entity"],
    "structured": ["query_rules"],
    "keyword": ["keyword_search"],
    "vector": ["vector_search"],
    "graph": ["rules_for_section", "rules_for_token", "neighbors", "related_rules"],
}

_SKIP_DIRS = {"vectors", "_build_cache"}
_MAX_FILE_CHARS = 40_000
_MAX_GREP_MATCHES = 80


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9#]+", text.lower())


class ToolRepo:
    def __init__(self, kb: KB):
        self.kb = kb
        self._bm25 = None
        self._bm25_ids: list[str] = []
        self._chroma = None
        self._openai = None
        # Graph adjacency: id -> [(other_id, edge_type, direction)]
        self._adj: dict[str, list[tuple[str, str, str]]] = {}
        self._node_labels: dict[str, dict[str, Any]] = {}
        for n in kb.graph.get("nodes", []):
            self._node_labels[n["id"]] = n
        for e in kb.graph.get("edges", []):
            self._adj.setdefault(e["src"], []).append((e["dst"], e["type"], "out"))
            self._adj.setdefault(e["dst"], []).append((e["src"], e["type"], "in"))

    # ------------------------------------------------------------------
    # lazy heavyweight deps
    # ------------------------------------------------------------------
    def _ensure_bm25(self):
        if self._bm25 is None:
            from rank_bm25 import BM25Okapi

            corpus, ids = [], []
            for r in self.kb.rules.values():
                doc = " ".join(filter(None, [r.rule_text, r.summary or "", r.intent or ""]))
                corpus.append(_tokenize(doc))
                ids.append(r.id)
            self._bm25 = BM25Okapi(corpus) if corpus else None
            self._bm25_ids = ids
        return self._bm25

    def _ensure_chroma(self):
        if self._chroma is None:
            import chromadb

            path = self.kb.root / "vectors" / "chroma"
            if not path.exists():
                raise ToolError("vector index not built for this brand (run indexing/summarize_embed.py)")
            self._chroma = chromadb.PersistentClient(path=str(path))
        return self._chroma

    def _ensure_openai(self):
        if self._openai is None:
            from openai import AsyncOpenAI

            self._openai = AsyncOpenAI()
        return self._openai

    # ------------------------------------------------------------------
    # filesystem family
    # ------------------------------------------------------------------
    def _safe_path(self, rel: str) -> Path:
        p = (self.kb.root / rel.lstrip("/")).resolve()
        if not str(p).startswith(str(self.kb.root.resolve())):
            raise ToolError(f"path escapes the KB root: {rel}")
        return p

    async def _list_dir(self, args: dict[str, Any]) -> Any:
        p = self._safe_path(args.get("path") or ".")
        if not p.exists():
            raise ToolError(f"no such path: {args.get('path')}")
        if p.is_file():
            return {"file": str(p.relative_to(self.kb.root)), "chars": p.stat().st_size}
        entries = []
        for child in sorted(p.iterdir()):
            if child.name in _SKIP_DIRS:
                continue
            entries.append(child.name + "/" if child.is_dir() else f"{child.name} ({child.stat().st_size}B)")
        return {"dir": str(p.relative_to(self.kb.root)) or ".", "entries": entries}

    async def _read_file(self, args: dict[str, Any]) -> Any:
        p = self._safe_path(args["path"])
        if not p.exists() or not p.is_file():
            raise ToolError(f"no such file: {args['path']}")
        text = p.read_text()
        offset = int(args.get("offset") or 0)
        chunk = text[offset : offset + _MAX_FILE_CHARS]
        note = ""
        if offset + len(chunk) < len(text):
            note = f"\n... [truncated; file is {len(text)} chars, continue with offset={offset + len(chunk)}]"
        return chunk + note

    async def _grep(self, args: dict[str, Any]) -> Any:
        pattern = args["pattern"]
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ToolError(f"bad regex: {e}")
        glob = args.get("glob") or "**/*"
        matches = []
        for f in sorted(self.kb.root.glob(glob)):
            if not f.is_file() or any(part in _SKIP_DIRS for part in f.parts):
                continue
            try:
                lines = f.read_text().splitlines()
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(lines, 1):
                if rx.search(line):
                    matches.append(f"{f.relative_to(self.kb.root)}:{i}: {line.strip()[:200]}")
                    if len(matches) >= _MAX_GREP_MATCHES:
                        return {"matches": matches, "truncated": True}
        return {"matches": matches, "truncated": False}

    # ------------------------------------------------------------------
    # schema family
    # ------------------------------------------------------------------
    async def _describe_entity(self, args: dict[str, Any]) -> Any:
        name = args["entity"]
        doc = self.kb.schema_doc(name)
        if doc is None:
            raise ToolError(f"unknown schema doc '{name}'. Available: {self.kb.schema_doc_names()}")
        return doc

    async def _get_section_vocab(self, args: dict[str, Any]) -> Any:
        return {"section_types": SECTION_TYPES,
                "doc": self.kb.schema_doc("section_vocab") or ""}

    async def _get_predicate_registry(self, args: dict[str, Any]) -> Any:
        return {"predicates": PREDICATE_REGISTRY,
                "doc": self.kb.schema_doc("predicate_registry") or ""}

    # ------------------------------------------------------------------
    # lookup family
    # ------------------------------------------------------------------
    async def _get_rules(self, args: dict[str, Any]) -> Any:
        ids = args.get("ids") or []
        view = args.get("view") or "short"
        out, missing = [], []
        for i in ids[:50]:
            rule = self.kb.rules.get(i)
            if rule is None:
                missing.append(i)
                continue
            out.append(self.kb.full_rule(rule) if view == "full" else self.kb.short_rule(rule))
        result: dict[str, Any] = {"rules": out}
        if missing:
            result["unknown_ids"] = missing
        return result

    async def _get_entity(self, args: dict[str, Any]) -> Any:
        entity = self.kb.get_any(args["id"])
        if entity is None:
            raise ToolError(f"unknown entity id: {args['id']}")
        return entity

    # ------------------------------------------------------------------
    # structured family
    # ------------------------------------------------------------------
    async def _query_rules(self, args: dict[str, Any]) -> Any:
        def want(vals: Any) -> Optional[set]:
            if vals is None:
                return None
            return {v for v in (vals if isinstance(vals, list) else [vals])}

        f_class = want(args.get("rule_class"))
        f_tags = want(args.get("tags"))
        f_sections = want(args.get("section_types"))
        f_scope = want(args.get("scope"))
        f_ct = want(args.get("constraint_type"))
        f_aud = want(args.get("audience"))
        f_hard = want(args.get("hardness"))
        f_eval = want(args.get("evaluation_scope"))
        include_all_section_rules = args.get("include_all_section_rules", True)

        out = []
        for r in self.kb.rules.values():
            facets = {r.rule_class} | set(r.tags or [])
            if f_class and not (facets & f_class):
                continue
            if f_tags and not (set(r.tags or []) & f_tags):
                continue
            if f_sections is not None:
                secs = r.selector.section_types
                if secs is None:
                    if not include_all_section_rules:
                        continue
                elif not (set(secs) & f_sections):
                    continue
            if f_scope and r.scope not in f_scope:
                continue
            if f_ct and (r.constraint_type or "") not in f_ct:
                continue
            if f_aud and r.audience is not None and r.audience not in f_aud:
                continue
            if f_hard and r.hardness not in f_hard:
                continue
            if f_eval and r.evaluation_scope not in f_eval:
                continue
            out.append(self.kb.short_rule(r))
        return {"count": len(out), "rules": out[:80],
                **({"truncated": True} if len(out) > 80 else {})}

    # ------------------------------------------------------------------
    # keyword family
    # ------------------------------------------------------------------
    async def _keyword_search(self, args: dict[str, Any]) -> Any:
        bm25 = self._ensure_bm25()
        if bm25 is None:
            raise ToolError("no rules in KB")
        k = min(int(args.get("k") or 10), 25)
        scores = bm25.get_scores(_tokenize(args["query"]))
        ranked = sorted(zip(self._bm25_ids, scores), key=lambda x: -x[1])[:k]
        return {"results": [
            {**self.kb.short_rule(self.kb.rules[rid]), "score": round(float(s), 3)}
            for rid, s in ranked if s > 0
        ]}

    # ------------------------------------------------------------------
    # vector family
    # ------------------------------------------------------------------
    async def _vector_search(self, args: dict[str, Any]) -> Any:
        collection = args.get("collection") or "rule_summary"
        if collection not in ("rule_summary", "rule_intent", "rule_text"):
            raise ToolError("collection must be one of rule_summary|rule_intent|rule_text")
        chroma = self._ensure_chroma()
        try:
            col = chroma.get_collection(collection)
        except Exception:
            raise ToolError(f"collection '{collection}' missing; run indexing/summarize_embed.py")
        k = min(int(args.get("k") or 10), 25)
        client = self._ensure_openai()
        from .. import config as _config

        emb = (await client.embeddings.create(model=_config.EMBED_MODEL,
                                              input=[args["query"][:6000]])).data[0].embedding
        res = col.query(query_embeddings=[emb], n_results=min(k * 3, col.count()),
                        include=["metadatas", "distances", "documents"])
        section = args.get("section_type")
        rule_class = args.get("rule_class")
        out = []
        for rid, meta, dist in zip(res["ids"][0], res["metadatas"][0], res["distances"][0]):
            if section:
                secs = meta.get("sections", "*")
                if secs != "*" and section not in secs.split(","):
                    continue
            if rule_class and meta.get("rule_class") != rule_class:
                continue
            rule = self.kb.rules.get(rid)
            if rule is None:
                continue
            out.append({**self.kb.short_rule(rule), "similarity": round(1 - dist, 3)})
            if len(out) >= k:
                break
        return {"results": out}

    # ------------------------------------------------------------------
    # graph family
    # ------------------------------------------------------------------
    async def _rules_for_section(self, args: dict[str, Any]) -> Any:
        section = args["section_type"]
        if section not in SECTION_TYPES:
            raise ToolError(f"unknown section_type '{section}'; vocab: {SECTION_TYPES}")
        targeted = [self.kb.short_rule(r) for r in self.kb.rules.values()
                    if r.selector.section_types and section in r.selector.section_types]
        result: dict[str, Any] = {"section": section, "targeted_count": len(targeted),
                                  "targeted_rules": targeted}
        if args.get("include_all_section_rules", False):
            allsec = [self.kb.short_rule(r) for r in self.kb.rules.values()
                      if r.selector.section_types is None]
            result["all_section_rules_count"] = len(allsec)
            result["all_section_rules"] = allsec
        else:
            result["note"] = ("rules with selector.section_types=null (apply to ALL sections) not "
                              "included; pass include_all_section_rules=true or query them separately")
        return result

    async def _rules_for_token(self, args: dict[str, Any]) -> Any:
        tid = args["token_id"]
        if tid not in self.kb.tokens:
            raise ToolError(f"unknown token id: {tid}")
        rule_ids = {other for other, etype, direction in self._adj.get(tid, [])
                    if etype == "references_token" and direction == "in"}
        return {"token_id": tid,
                "rules": [self.kb.short_rule(self.kb.rules[r]) for r in sorted(rule_ids) if r in self.kb.rules]}

    async def _neighbors(self, args: dict[str, Any]) -> Any:
        node = args["node_id"]
        if node not in self._adj and node not in self._node_labels:
            raise ToolError(f"unknown graph node: {node}")
        edge_types = set(args.get("edge_types") or [])
        depth = min(int(args.get("depth") or 1), 2)
        seen = {node}
        frontier = [node]
        edges_out = []
        for _ in range(depth):
            nxt = []
            for cur in frontier:
                for other, etype, direction in self._adj.get(cur, []):
                    if edge_types and etype not in edge_types:
                        continue
                    edges_out.append({"from": cur, "to": other, "type": etype, "direction": direction})
                    if other not in seen:
                        seen.add(other)
                        nxt.append(other)
            frontier = nxt
        nodes_out = {nid: {"kind": self._node_labels.get(nid, {}).get("kind"),
                           "label": self._node_labels.get(nid, {}).get("label")}
                     for nid in seen}
        return {"edges": edges_out[:150], "nodes": nodes_out}

    async def _related_rules(self, args: dict[str, Any]) -> Any:
        rid = args["rule_id"]
        rule = self.kb.rules.get(rid)
        if rule is None:
            raise ToolError(f"unknown rule id: {rid}")
        relations = [
            {"rule": self.kb.short_rule(self.kb.rules[rel.dst_rule_id if rel.src_rule_id == rid else rel.src_rule_id]),
             "relation": rel.relation, "note": rel.note}
            for rel in self.kb.relations
            if (rel.src_rule_id == rid or rel.dst_rule_id == rid)
            and (rel.dst_rule_id if rel.src_rule_id == rid else rel.src_rule_id) in self.kb.rules
        ]
        same_group = [self.kb.short_rule(r) for r in self.kb.rules.values()
                      if r.group_id and r.group_id == rule.group_id and r.id != rid]
        return {"rule_id": rid, "explicit_relations": relations,
                "same_source_group": same_group[:30], "group_id": rule.group_id}

    # ------------------------------------------------------------------
    # spec registry
    # ------------------------------------------------------------------
    def specs(self, names: Optional[list[str]] = None,
              families: Optional[list[str]] = None) -> list[ToolSpec]:
        selected: Optional[set[str]] = None
        if names is not None or families is not None:
            selected = set(names or [])
            for fam in families or []:
                selected.update(TOOL_FAMILIES[fam])
        all_specs = self._all_specs()
        if selected is None:
            return all_specs
        return [s for s in all_specs if s.name in selected]

    def _all_specs(self) -> list[ToolSpec]:
        S = ToolSpec
        return [
            S("list_dir", "List a directory inside this brand's knowledge base. Root layout: "
              "schema/, rules/, tokens/, assets/, subtypes/, governance/, groups/, graph/, review/.",
              {"type": "object", "properties": {"path": {"type": "string", "description": "relative path, default '.'"}},
               "required": []}, self._list_dir),
            S("read_file", "Read a file from the KB (relative path). Large files are chunked; "
              "pass offset to continue.",
              {"type": "object", "properties": {"path": {"type": "string"},
                                                "offset": {"type": "integer"}},
               "required": ["path"]}, self._read_file),
            S("grep", "Regex search (case-insensitive) across KB files. Great for exact strings: "
              "hex codes, px values, component names, phrases.",
              {"type": "object", "properties": {"pattern": {"type": "string"},
                                                "glob": {"type": "string", "description": "e.g. 'rules/*.json', default all files"}},
               "required": ["pattern"]}, self._grep),
            S("describe_entity", "Read the schema documentation for one entity/topic. Available: "
              "overview, conventions, brand_rule, brand_token, design_asset, content_sub_type, "
              "governance, support_entities, section_vocab, predicate_registry.",
              {"type": "object", "properties": {"entity": {"type": "string"}}, "required": ["entity"]},
              self._describe_entity),
            S("get_section_vocab", "The closed section-type vocabulary rules attach to, with definitions.",
              {"type": "object", "properties": {}, "required": []}, self._get_section_vocab),
            S("get_predicate_registry", "The closed applies_when predicate registry, with definitions.",
              {"type": "object", "properties": {}, "required": []}, self._get_predicate_registry),
            S("get_rules", "Fetch rules by id. view='short' (default: id, class, sections, conditions, "
              "summary) or 'full' (adds rule_text, effect, tokens, snippets...).",
              {"type": "object", "properties": {"ids": {"type": "array", "items": {"type": "string"}},
                                                "view": {"type": "string", "enum": ["short", "full"]}},
               "required": ["ids"]}, self._get_rules),
            S("get_entity", "Fetch any non-rule entity by id (tok_/ast_/gov_/sub_/grp_/agr_ prefixes).",
              {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
              self._get_entity),
            S("query_rules", "Filter the rule index by structured facets. All filters optional and "
              "AND-ed; list values OR within a filter. section_types matches rules targeting those "
              "sections; rules with section_types=null (apply everywhere) are included unless "
              "include_all_section_rules=false.",
              {"type": "object", "properties": {
                  "rule_class": {"type": "array", "items": {"type": "string"}},
                  "tags": {"type": "array", "items": {"type": "string"}},
                  "section_types": {"type": "array", "items": {"type": "string"}},
                  "scope": {"type": "array", "items": {"type": "string"},
                            "description": "org_baseline|brand|campaign"},
                  "constraint_type": {"type": "array", "items": {"type": "string"}},
                  "audience": {"type": "array", "items": {"type": "string"}},
                  "hardness": {"type": "array", "items": {"type": "string"}},
                  "evaluation_scope": {"type": "array", "items": {"type": "string"}},
                  "include_all_section_rules": {"type": "boolean"}},
               "required": []}, self._query_rules),
            S("keyword_search", "BM25 lexical search over rule_text+summary+intent. Use for exact "
              "terminology ('border-radius', 'Nunito Sans', 'LPGA', '#01A47E').",
              {"type": "object", "properties": {"query": {"type": "string"},
                                                "k": {"type": "integer", "description": "default 10, max 25"}},
               "required": ["query"]}, self._keyword_search),
            S("vector_search", "Semantic search over rule embeddings. collection: rule_summary "
              "(default, compressed), rule_intent (the WHY), rule_text (full statements). Optional "
              "section_type / rule_class metadata filters.",
              {"type": "object", "properties": {"query": {"type": "string"},
                                                "collection": {"type": "string",
                                                               "enum": ["rule_summary", "rule_intent", "rule_text"]},
                                                "k": {"type": "integer"},
                                                "section_type": {"type": "string"},
                                                "rule_class": {"type": "string"}},
               "required": ["query"]}, self._vector_search),
            S("rules_for_section", "Graph lookup: all rules whose selector targets a section type. "
              "Set include_all_section_rules=true to also list rules that apply to every section "
              "(email-wide baseline candidates).",
              {"type": "object", "properties": {"section_type": {"type": "string"},
                                                "include_all_section_rules": {"type": "boolean"}},
               "required": ["section_type"]}, self._rules_for_section),
            S("rules_for_token", "Graph lookup: rules whose effect references a given token.",
              {"type": "object", "properties": {"token_id": {"type": "string"}}, "required": ["token_id"]},
              self._rules_for_token),
            S("neighbors", "Walk the KB graph from any node (rule/token/asset/governance/section/"
              "group). Edge types: applies_to_section, references_token, references_asset, "
              "governed_by, scoped_to_subtype, from_group, contains_token, requires_pairing_token, "
              "member_of, derived_from, refines, conflicts, cross_reference, cluster, co_applies.",
              {"type": "object", "properties": {"node_id": {"type": "string"},
                                                "edge_types": {"type": "array", "items": {"type": "string"}},
                                                "depth": {"type": "integer", "description": "1 (default) or 2"}},
               "required": ["node_id"]}, self._neighbors),
            S("related_rules", "Rules explicitly related to a rule (refines/conflicts/...) plus rules "
              "atomized from the same source blob.",
              {"type": "object", "properties": {"rule_id": {"type": "string"}}, "required": ["rule_id"]},
              self._related_rules),
        ]

    # ------------------------------------------------------------------
    # finalize (terminal tool factory)
    # ------------------------------------------------------------------
    def finalize_spec(self, name: str = "finalize_section_ruleset") -> ToolSpec:
        async def handler(args: dict[str, Any]) -> dict[str, Any]:
            targeted = args.get("targeted_rule_ids") or []
            email_wide = args.get("email_wide_rule_ids") or []
            rationale = args.get("rationale") or {}
            if not isinstance(targeted, list) or not isinstance(email_wide, list):
                raise ToolError("targeted_rule_ids and email_wide_rule_ids must be arrays of rule ids")
            unknown = self.kb.unknown_rule_ids(list(targeted) + list(email_wide))
            if unknown:
                raise ToolError(f"unknown rule ids: {unknown}. Fix or drop them, then call again.")
            overlap = set(targeted) & set(email_wide)
            if overlap:
                raise ToolError(f"rules in BOTH targeted and email_wide: {sorted(overlap)}. "
                                "Each rule goes in exactly one bucket: email_wide only for rules "
                                "that apply to the whole email / every section.")
            if not targeted and not email_wide:
                raise ToolError("empty result; a section always has at least some applicable rules")
            return {
                "targeted_rule_ids": list(dict.fromkeys(targeted)),
                "email_wide_rule_ids": list(dict.fromkeys(email_wide)),
                "rationale": {k: str(v) for k, v in rationale.items() if isinstance(k, str)},
            }

        return ToolSpec(
            name=name,
            description=(
                "FINAL ANSWER. Call exactly once when done exploring: the precise ruleset for this "
                "section. targeted_rule_ids: rules that specifically constrain THIS section's design/"
                "copy (selector match, conditional rules whose predicates this section satisfies, "
                "component rules for what the section contains). email_wide_rule_ids: baseline rules "
                "that apply email-wide / to every section (selector null, evaluation_scope=email, "
                "global typography/accessibility/assembly). rationale: one line per rule id on why "
                "it applies."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "targeted_rule_ids": {"type": "array", "items": {"type": "string"}},
                    "email_wide_rule_ids": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "object", "additionalProperties": {"type": "string"}},
                },
                "required": ["targeted_rule_ids", "email_wide_rule_ids"],
            },
            handler=handler,
            terminal=True,
        )
