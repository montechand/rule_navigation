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
from ..schemas import PREDICATE_REGISTRY

TOOL_FAMILIES: dict[str, list[str]] = {
    "filesystem": ["list_dir", "read_file", "grep"],
    "schema": ["describe_entity", "get_section_vocab", "get_predicate_registry"],
    "lookup": ["get_rules", "get_entity"],
    "structured": ["query_rules"],
    "tokens": ["query_tokens", "search_tokens", "resolve_token"],
    "templates": ["list_templates", "rules_for_template"],
    "keyword": ["keyword_search"],
    "vector": ["vector_search"],
    "graph": ["rules_for_section", "rules_for_subtype", "rules_for_token", "neighbors",
              "related_rules"],
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
        self._token_bm25 = None
        self._token_bm25_ids: list[str] = []
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
                preferred = (r.governance or {}).get("preferred_form") or ""
                doc = " ".join(filter(None, [r.rule_text, r.summary or "", r.intent or "", preferred]))
                corpus.append(_tokenize(doc))
                ids.append(r.id)
            self._bm25 = BM25Okapi(corpus) if corpus else None
            self._bm25_ids = ids
        return self._bm25

    def _ensure_token_bm25(self):
        if self._token_bm25 is None:
            from rank_bm25 import BM25Okapi

            corpus, ids = [], []
            for t in self.kb.tokens.values():
                doc = " ".join(filter(None, [
                    t.key, " ".join(t.aliases or []), " ".join(t.element_paths or []),
                    t.notes or "", json.dumps(t.value, default=str) if t.value is not None else "",
                ]))
                corpus.append(_tokenize(doc))
                ids.append(t.id)
            self._token_bm25 = BM25Okapi(corpus) if corpus else None
            self._token_bm25_ids = ids
        return self._token_bm25

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
        return {"section_types": self.kb.section_types,
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
        f_subtypes = want(args.get("content_sub_type_ids"))
        f_gov_type = want(args.get("gov_type"))
        f_verdict = want(args.get("verdict"))
        has_gov = args.get("has_governance")
        include_all_section_rules = args.get("include_all_section_rules", True)
        include_all_subtype_rules = args.get("include_all_subtype_rules", True)

        out = []
        for r in self.kb.rules.values():
            gov = r.governance or {}
            if has_gov is not None and bool(r.governance) != bool(has_gov):
                continue
            if f_gov_type and str(gov.get("gov_type", "")).lower() not in f_gov_type:
                continue
            if f_verdict and str(gov.get("verdict", "")).lower() not in f_verdict:
                continue
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
            if f_subtypes is not None:
                subs = r.content_sub_type_ids
                if subs is None:
                    if not include_all_subtype_rules:
                        continue
                elif not (set(subs) & f_subtypes):
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
        offset = max(int(args.get("offset") or 0), 0)
        page = out[offset:offset + 80]
        result: dict[str, Any] = {"count": len(out), "offset": offset, "rules": page}
        if offset + len(page) < len(out):
            result["truncated"] = True
            result["next_offset"] = offset + len(page)
        return result

    # ------------------------------------------------------------------
    # tokens family
    # ------------------------------------------------------------------
    def _short_token(self, t) -> dict[str, Any]:
        v = t.value if isinstance(t.value, dict) else {"default": t.value}
        variants_by = sorted({k for var in (v.get("variants") or [])
                              if isinstance(var, dict) for k in (var.get("when") or {})})
        out = {"id": t.id, "kind": t.kind, "key": t.key, "type": t.token_type,
               "default": v.get("default")}
        if t.element_paths:
            out["element_paths"] = t.element_paths
        if variants_by:
            out["variants_by"] = variants_by
        if t.gated:
            out["gated"] = t.gated
        if t.scope != "global":
            out["scope"] = t.scope
        if t.aliases:
            out["aliases"] = t.aliases
        return out

    async def _query_tokens(self, args: dict[str, Any]) -> Any:
        def want(vals: Any) -> Optional[set]:
            if vals is None:
                return None
            return {str(v).lower() for v in (vals if isinstance(vals, list) else [vals])}

        f_type = want(args.get("token_type"))
        f_kind = args.get("kind")
        f_gated = args.get("gated")
        key_contains = (args.get("key_contains") or "").lower()
        path_contains = (args.get("element_path_contains") or "").lower()
        scope_contains = (args.get("scope_contains") or "").lower()

        out = []
        for t in self.kb.tokens.values():
            if f_type and t.token_type not in f_type:
                continue
            if f_kind and t.kind != f_kind:
                continue
            if f_gated is not None and bool(t.gated) != bool(f_gated):
                continue
            if key_contains and key_contains not in t.key.lower():
                continue
            if path_contains and not any(path_contains in p.lower() for p in (t.element_paths or [])):
                continue
            if scope_contains and scope_contains not in t.scope.lower():
                continue
            out.append(self._short_token(t))
        return {"count": len(out), "tokens": out[:100],
                **({"truncated": True} if len(out) > 100 else {})}

    async def _search_tokens(self, args: dict[str, Any]) -> Any:
        bm25 = self._ensure_token_bm25()
        if bm25 is None:
            raise ToolError("no tokens in KB")
        k = min(int(args.get("k") or 10), 30)
        scores = bm25.get_scores(_tokenize(args["query"]))
        ranked = sorted(zip(self._token_bm25_ids, scores), key=lambda x: -x[1])[:k]
        return {"results": [
            {**self._short_token(self.kb.tokens[tid]), "score": round(float(s), 3)}
            for tid, s in ranked if s > 0
        ]}

    def _resolve_value(self, value: Any, chain: list[str], depth: int = 0) -> Any:
        """Recursively flatten {"$ref": tok_id} references to concrete values."""
        if depth > 6:
            return {"unresolved": "max depth", "value": value}
        if isinstance(value, dict):
            if set(value.keys()) == {"$ref"}:
                ref = value["$ref"]
                tok = self.kb.tokens.get(ref)
                if tok is None or ref in chain:
                    return {"unresolved_ref": ref}
                chain.append(ref)
                inner = tok.value
                if isinstance(inner, dict) and "default" in inner:
                    resolved = self._resolve_value(inner.get("default"), chain, depth + 1)
                    variants = inner.get("variants")
                    if variants:
                        return {"resolved": resolved, "ref": ref,
                                "ref_variants": [
                                    {"when": v.get("when"),
                                     "value": self._resolve_value(v.get("value"), chain, depth + 1)}
                                    for v in variants if isinstance(v, dict)]}
                    return resolved
                return self._resolve_value(inner, chain, depth + 1)
            return {k: self._resolve_value(v, chain, depth) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_value(x, chain, depth) for x in value]
        return value

    async def _resolve_token(self, args: dict[str, Any]) -> Any:
        tid = args["token_id"]
        tok = self.kb.tokens.get(tid)
        if tok is None:
            raise ToolError(f"unknown token id: {tid}")
        chain: list[str] = [tid]
        v = tok.value if isinstance(tok.value, dict) else {"default": tok.value}
        out: dict[str, Any] = {
            "id": tid, "kind": tok.kind, "key": tok.key, "type": tok.token_type,
            "resolved_default": self._resolve_value(v.get("default"), chain),
            "variants": [
                {"when": var.get("when"), "value": self._resolve_value(var.get("value"), chain)}
                for var in (v.get("variants") or []) if isinstance(var, dict)
            ] or None,
        }
        if tok.element_paths:
            out["element_paths"] = tok.element_paths
        if tok.gated:
            out["gated"] = tok.gated
        if tok.derived_from:
            base = tok.derived_from.get("base_token_id") if isinstance(tok.derived_from, dict) else None
            out["derived_from"] = tok.derived_from
            if base and base in self.kb.tokens:
                chain.append(base)
        out["resolution_chain"] = list(dict.fromkeys(chain))
        return out

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
        if section not in self.kb.section_types:
            raise ToolError(f"unknown section_type '{section}'; vocab: {self.kb.section_types}")
        targeted = [self.kb.short_rule(r) for r in self.kb.rules.values()
                    if r.selector.section_types and section in r.selector.section_types]
        filled_by = [{"id": s.id, "name": s.name, "kind": "class",
                      "fills": s.fills_section_types}
                     for s in self.kb.subtypes.values()
                     if s.fills_section_types and section in s.fills_section_types]
        filled_by += [{"id": t.id, "name": t.name, "kind": "template",
                       "fills": t.fills_section_types, "group_id": t.group_id}
                      for t in self.kb.templates.values()
                      if t.fills_section_types and section in t.fills_section_types]
        hosted_by = [{"id": s.id, "name": s.name}
                     for s in self.kb.subtypes.values()
                     if s.hosts_section_types and section in s.hosts_section_types]
        result: dict[str, Any] = {"section": section, "targeted_count": len(targeted),
                                  "targeted_rules": targeted}
        if filled_by:
            result["filled_by"] = filled_by
        if hosted_by:
            result["can_be_hosted_by"] = hosted_by
        if args.get("include_all_section_rules", False):
            allsec = [self.kb.short_rule(r) for r in self.kb.rules.values()
                      if r.selector.section_types is None]
            result["all_section_rules_count"] = len(allsec)
            result["all_section_rules"] = allsec
        else:
            result["note"] = ("rules with selector.section_types=null (apply to ALL sections) not "
                              "included; pass include_all_section_rules=true or query them separately")
        return result

    def _rules_for_sections(self, sections: list[str]) -> dict[str, list[dict[str, Any]]]:
        return {sec: [self.kb.short_rule(r) for r in self.kb.rules.values()
                      if r.selector.section_types and sec in r.selector.section_types]
                for sec in sections}

    async def _rules_for_subtype(self, args: dict[str, Any]) -> Any:
        sid = args["subtype_id"]
        sub = self.kb.subtypes.get(sid)
        if sub is None:
            raise ToolError(f"unknown content_sub_type id: {sid}. See subtypes/_index.json "
                            "(for concrete templates use rules_for_template)")
        directly = [self.kb.short_rule(r) for r in self.kb.rules.values()
                    if r.content_sub_type_ids and sid in r.content_sub_type_ids]
        instances = [{"id": t.id, "name": t.name, "group_id": t.group_id}
                     for t in self.kb.templates.values() if t.instance_of == sid]
        all_subtype_count = sum(1 for r in self.kb.rules.values() if r.content_sub_type_ids is None)
        result: dict[str, Any] = {
            "subtype": {"id": sub.id, "name": sub.name, "kind": sub.kind,
                        "fills_section_types": sub.fills_section_types,
                        "hosts_section_types": sub.hosts_section_types,
                        "locked": bool((sub.assembly or {}).get("locked"))},
            "directly_scoped_rules": directly,
            "rules_via_filled_sections": self._rules_for_sections(sub.fills_section_types or []),
            "note": (f"{all_subtype_count} further rules have content_sub_type_ids=null "
                     "(apply to ALL sub-types); hosts_section_types is an affordance hint — "
                     "hosted-role rules attach to the hosted section, not this class"),
        }
        if instances:
            result["template_instances"] = instances
        return result

    async def _list_templates(self, args: dict[str, Any]) -> Any:
        fills = args.get("fills_section_type")
        group = args.get("group_id")
        out = []
        for t in self.kb.templates.values():
            if fills and fills not in (t.fills_section_types or []):
                continue
            if group and t.group_id != group:
                continue
            out.append({"id": t.id, "name": t.name, "source": t.source,
                        "fills_section_types": t.fills_section_types,
                        "instance_of": t.instance_of, "group_id": t.group_id,
                        "usage_conditions": t.usage_conditions, "file": t.file})
        groups = [{"id": g.id, "name": g.name, "semantics": g.semantics}
                  for g in self.kb.template_groups.values()
                  if not group or g.id == group]
        return {"templates": out, "template_groups": groups}

    async def _rules_for_template(self, args: dict[str, Any]) -> Any:
        tid = args["template_id"]
        tpl = self.kb.templates.get(tid)
        if tpl is None:
            raise ToolError(f"unknown design_template id: {tid}. See templates/_index.json")
        via_class = []
        if tpl.instance_of:
            via_class = [self.kb.short_rule(r) for r in self.kb.rules.values()
                         if r.content_sub_type_ids and tpl.instance_of in r.content_sub_type_ids]
        group = self.kb.template_groups.get(tpl.group_id) if tpl.group_id else None
        siblings = [t.id for t in self.kb.templates.values()
                    if tpl.group_id and t.group_id == tpl.group_id and t.id != tid]
        return {
            "template": {"id": tpl.id, "name": tpl.name, "source": tpl.source,
                         "fills_section_types": tpl.fills_section_types,
                         "instance_of": tpl.instance_of,
                         "usage_conditions": tpl.usage_conditions,
                         "file": tpl.file},
            "group": ({"id": group.id, "name": group.name, "semantics": group.semantics,
                       "alternates": siblings} if group else None),
            "rules_via_class": via_class,
            "rules_via_filled_sections": self._rules_for_sections(tpl.fills_section_types or []),
            "note": ("plus email-wide baseline rules (content_sub_type_ids=null / "
                     "selector=null); usage_conditions above are this instance's own "
                     "selection gates"),
        }

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
              "schema/, rules/, tokens/, assets/, subtypes/, groups/, graph/, "
              "templates/ (concrete approved template bodies), review/.",
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
              "design_template, support_entities, section_vocab, predicate_registry.",
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
            S("get_entity", "Fetch any non-rule entity by id (tok_/ast_/sub_/tpl_/tgr_/grp_/agr_ prefixes).",
              {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
              self._get_entity),
            S("query_rules", "Filter the rule index by structured facets. All filters optional and "
              "AND-ed; list values OR within a filter. section_types matches rules targeting those "
              "sections; rules with section_types=null (apply everywhere) are included unless "
              "include_all_section_rules=false. content_sub_type_ids matches rules scoped to those "
              "components/templates; rules with content_sub_type_ids=null (all sub-types) are "
              "included unless include_all_subtype_rules=false. Governance/compliance rules "
              "(disclosures, required qualifiers, verbatim language, trademark) carry a "
              "governance facet: filter with has_governance / gov_type / verdict. Results "
              "page at 80 rows: when the response has next_offset, call again with "
              "offset=next_offset to see the rest.",
              {"type": "object", "properties": {
                  "rule_class": {"type": "array", "items": {"type": "string"}},
                  "tags": {"type": "array", "items": {"type": "string"}},
                  "section_types": {"type": "array", "items": {"type": "string"}},
                  "content_sub_type_ids": {"type": "array", "items": {"type": "string"}},
                  "scope": {"type": "array", "items": {"type": "string"},
                            "description": "org_baseline|brand|campaign"},
                  "constraint_type": {"type": "array", "items": {"type": "string"}},
                  "audience": {"type": "array", "items": {"type": "string"}},
                  "hardness": {"type": "array", "items": {"type": "string"}},
                  "evaluation_scope": {"type": "array", "items": {"type": "string"}},
                  "has_governance": {"type": "boolean"},
                  "gov_type": {"type": "array", "items": {"type": "string"},
                               "description": "regulatory|legal|mlr_claim|disclosure|trademark"},
                  "verdict": {"type": "array", "items": {"type": "string"}},
                  "include_all_section_rules": {"type": "boolean"},
                  "include_all_subtype_rules": {"type": "boolean"},
                  "offset": {"type": "integer",
                             "description": "pagination offset; use next_offset from a truncated response"}},
               "required": []}, self._query_rules),
            S("query_tokens", "Filter the brand_token layer (the value/IF-ELSE layer: every "
              "concrete styling value is a token; semantic tokens bind element paths with "
              "conditional variants). Filters AND-ed: token_type list, kind "
              "(primitive|semantic), gated, key_contains, element_path_contains, "
              "scope_contains (e.g. 'campaign').",
              {"type": "object", "properties": {
                  "token_type": {"type": "array", "items": {"type": "string"}},
                  "kind": {"type": "string", "enum": ["primitive", "semantic"]},
                  "gated": {"type": "boolean"},
                  "key_contains": {"type": "string"},
                  "element_path_contains": {"type": "string"},
                  "scope_contains": {"type": "string"}},
               "required": []}, self._query_tokens),
            S("search_tokens", "BM25 lexical search over token keys/aliases/element paths/"
              "values/notes. The fastest pivot from a concrete detail ('#01A47E', '80%', "
              "'border-radius', 'left aligned', 'Nunito Sans') to its token — then "
              "rules_for_token gives the governing rules.",
              {"type": "object", "properties": {"query": {"type": "string"},
                                                "k": {"type": "integer", "description": "default 10, max 30"}},
               "required": ["query"]}, self._search_tokens),
            S("resolve_token", "Flatten a token to concrete values: follows $ref chains "
              "(semantic -> primitive) and returns resolved default + variants (the "
              "conditional IF/ELSE) + the resolution chain. Use instead of chained "
              "get_entity hops when you need the actual values behind a binding.",
              {"type": "object", "properties": {"token_id": {"type": "string"}},
               "required": ["token_id"]}, self._resolve_token),
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
            S("rules_for_section", "Graph lookup: all rules whose selector targets a section type "
              "(vocabulary is dynamic per brand — see get_section_vocab), plus which "
              "components/templates cover the section. Set include_all_section_rules=true to also "
              "list rules that apply to every section (email-wide baseline candidates).",
              {"type": "object", "properties": {"section_type": {"type": "string"},
                                                "include_all_section_rules": {"type": "boolean"}},
               "required": ["section_type"]}, self._rules_for_section),
            S("rules_for_subtype", "Class view: rules directly scoped to a structural "
              "component/format (content_sub_type) plus rules for the section roles it FILLS, "
              "and its concrete template instances. Ids in subtypes/_index.json.",
              {"type": "object", "properties": {"subtype_id": {"type": "string"}},
               "required": ["subtype_id"]}, self._rules_for_subtype),
            S("list_templates", "List concrete approved templates (design_template) and "
              "pick-one template_groups. Filter by fills_section_type and/or group_id. Bodies "
              "are readable via read_file on the returned file path.",
              {"type": "object", "properties": {"fills_section_type": {"type": "string"},
                                                "group_id": {"type": "string"}},
               "required": []}, self._list_templates),
            S("rules_for_template", "Instance view: everything one concrete template must obey "
              "— rules via its class (instance_of), rules for the section roles it fills, its "
              "own usage_conditions (selection gates like requires_content_tags), and its "
              "pick-one group alternates. Ids in templates/_index.json.",
              {"type": "object", "properties": {"template_id": {"type": "string"}},
               "required": ["template_id"]}, self._rules_for_template),
            S("rules_for_token", "Graph lookup: rules whose effect references a given token.",
              {"type": "object", "properties": {"token_id": {"type": "string"}}, "required": ["token_id"]},
              self._rules_for_token),
            S("neighbors", "Walk the KB graph from any node (rule/token/asset/section/subtype/"
              "template/group/token_table; token-table ids reserve the ttab_ prefix). Edge types: "
              "applies_to_section, references_token, references_asset, member_of_table, "
              "scoped_to_subtype, fills_section, hosts_section, instance_of, member_of, from_group, "
              "contains_token, requires_pairing_token, resolves_to, derived_from, refines, "
              "conflicts, cross_reference, cluster, co_applies, overrides, mutually_exclusive, "
              "depends_on.",
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
    # Predicates that make a rule applicable to ANY section depending on its position or
    # neighbors (e.g. "adjacent to a locked component"), regardless of what the rule's
    # selector says — such rules must always be accounted for.
    _POSITIONAL_PREDICATES = {"adjacent_section_state", "position_in_email"}

    # Audience these emails target; rules for other audiences are mechanically out of
    # scope for the mandatory baseline (mirrors the task brief's dtp_patient default).
    _RUN_AUDIENCE = "dtp_patient"

    def mandatory_baseline_ids(self) -> list[str]:
        """Rules the agent gets NO discretion over: unconditional (null section_types
        selector, no applies_when gate) AND hard_constraint or governance severity=block,
        on the email surface, for a matching audience. Every mechanically-checkable
        disqualifier the decision policy accepts (audience, surface, failed predicate)
        is already verified false here, so no valid exclusion reason can remain —
        'the governed element may not appear in this section' is not a disqualifier for
        an email-wide baseline. Auto-included by finalize; observed FNs (e.g. the
        blueprint1/2 logo-mark-opacity trademark miss) were exactly this class."""
        out = []
        for r in self.kb.rules.values():
            if r.selector.section_types is not None or r.applies_when:
                continue
            if r.content_sub_type_ids is not None:
                continue  # scoped to specific components (e.g. locked matter), not a section baseline
            gov_block = (r.governance or {}).get("severity") == "block"
            if r.hardness != "hard_constraint" and not gov_block:
                continue
            if r.content_types is not None and "email" not in r.content_types:
                continue
            if r.audience is not None and r.audience != self._RUN_AUDIENCE:
                continue
            out.append(r.id)
        return sorted(out)

    def coverage_candidates(self, section_types: list[str]) -> list[str]:
        """The mechanically-derivable candidate set the finalize payload must account for:
        every rule whose selector targets one of the mapped section types, every rule with
        a null selector (applies to all sections / email-wide baseline pool), and every
        rule conditioned on position/adjacency (applicable to any section in principle)."""
        wanted = set(section_types)
        out = []
        for r in self.kb.rules.values():
            secs = r.selector.section_types
            if secs is None or (wanted and set(secs) & wanted):
                out.append(r.id)
                continue
            if any(p.kind in self._POSITIONAL_PREDICATES for p in (r.applies_when or [])):
                out.append(r.id)
        return out

    def _coverage_line(self, rid: str) -> str:
        r = self.kb.rules[rid]
        gov = r.governance or {}
        bits = [rid,
                f"sections={r.selector.section_types or 'ALL'}",
                f"hardness={r.hardness}"]
        if gov:
            bits.append(f"gov_severity={gov.get('severity')}")
        if r.applies_when:
            bits.append("conditional")
        summary = (r.summary or r.rule_text or "")[:110]
        return "  - " + " | ".join(bits) + f" :: {summary}"

    def finalize_spec(self, name: str = "finalize_section_ruleset") -> ToolSpec:
        async def handler(args: dict[str, Any]) -> dict[str, Any]:
            targeted = args.get("targeted_rule_ids") or []
            email_wide = args.get("email_wide_rule_ids") or []
            rationale = args.get("rationale") or {}
            mapping = args.get("section_type_mapping")
            excluded = args.get("excluded") or {}
            if not isinstance(targeted, list) or not isinstance(email_wide, list):
                raise ToolError("targeted_rule_ids and email_wide_rule_ids must be arrays of rule ids")
            if not isinstance(mapping, list):
                raise ToolError("section_type_mapping is required: the list of section-vocabulary "
                                "types you mapped this blueprint section to (may be empty only if "
                                "the section genuinely maps to no vocab type). "
                                f"Vocabulary: {self.kb.section_types}")
            bad_types = [t for t in mapping if t not in self.kb.section_types]
            if bad_types:
                raise ToolError(f"section_type_mapping contains unknown section types: {bad_types}. "
                                f"Vocabulary: {self.kb.section_types}")
            if not isinstance(excluded, dict):
                raise ToolError("excluded must be an object mapping rule_id -> one-line reason")
            unknown = self.kb.unknown_rule_ids(list(targeted) + list(email_wide) + list(excluded))
            if unknown:
                raise ToolError(f"unknown rule ids: {unknown}. Fix or drop them, then call again.")
            overlap = set(targeted) & set(email_wide)
            if overlap:
                raise ToolError(f"rules in BOTH targeted and email_wide: {sorted(overlap)}. "
                                "Each rule goes in exactly one bucket: email_wide only for rules "
                                "that apply to the whole email / every section.")
            included = set(targeted) | set(email_wide)
            contradicted = included & set(excluded)
            if contradicted:
                raise ToolError(f"rules both included and excluded: {sorted(contradicted)}. "
                                "Remove them from one side.")
            empty_reasons = [rid for rid, why in excluded.items() if not str(why).strip()]
            if empty_reasons:
                raise ToolError(f"excluded rules need a non-empty one-line reason: {empty_reasons}")
            if not targeted and not email_wide:
                raise ToolError("empty result; a section always has at least some applicable rules")

            # Mandatory baseline: unconditional hard_constraint / governance-block rules
            # (email surface, matching audience) are non-excludable. Agents repeatedly
            # rationalized dropping these ("the logo won't appear in this section"),
            # producing the dominant residual FN class — so discretion is removed:
            # excluding one is an error, and any not already included are auto-added
            # to email_wide with a mechanical rationale.
            mandatory = self.mandatory_baseline_ids()
            bad_excluded = [rid for rid in mandatory if rid in excluded]
            if bad_excluded:
                listing = "\n".join(self._coverage_line(rid) for rid in bad_excluded)
                raise ToolError(
                    "NON-EXCLUDABLE RULES in `excluded`: these are unconditional "
                    "hard-constraint/governance-block baseline rules for this surface and "
                    "audience. 'The governed element may not appear in this section' is not "
                    "a valid disqualifier for an email-wide baseline — the downstream "
                    "generator decides what appears. Remove them from `excluded` (they are "
                    f"auto-included email-wide):\n{listing}"
                )
            auto_added = [rid for rid in mandatory
                          if rid not in included and rid not in targeted]
            for rid in auto_added:
                email_wide.append(rid)
                rationale.setdefault(
                    rid, "auto-included: unconditional hard-constraint/governance-block "
                         "email baseline (non-excludable)")
            included = set(targeted) | set(email_wide)

            # FNR-first coverage check: every rule that mechanically matches the declared
            # section-type mapping, plus every null-selector (all-sections) rule, must be
            # either included or explicitly excluded with a reason. Silent drops are the
            # dominant false-negative mode, so they are rejected here.
            accounted = included | set(excluded)
            missing = [rid for rid in self.coverage_candidates(mapping) if rid not in accounted]
            if missing:
                shown = missing[:40]
                listing = "\n".join(self._coverage_line(rid) for rid in shown)
                more = f"\n  ... and {len(missing) - len(shown)} more" if len(missing) > len(shown) else ""
                raise ToolError(
                    f"COVERAGE CHECK FAILED: {len(missing)} rule(s) match your "
                    f"section_type_mapping={mapping} or apply to all sections (selector=null), "
                    "but are neither included nor excluded-with-reason. For each: add it to "
                    "targeted_rule_ids / email_wide_rule_ids, or add it to `excluded` with a "
                    "specific disqualifier (audience mismatch, non-email surface, applies_when "
                    "predicate the blueprint contradicts). Unaccounted rules:\n"
                    f"{listing}{more}"
                )
            out = {
                "targeted_rule_ids": list(dict.fromkeys(targeted)),
                "email_wide_rule_ids": list(dict.fromkeys(email_wide)),
                "section_type_mapping": list(dict.fromkeys(mapping)),
                "excluded": {rid: str(why)[:200] for rid, why in excluded.items()},
                "rationale": {k: str(v) for k, v in rationale.items() if isinstance(k, str)},
            }
            if auto_added:
                out["auto_included_email_wide"] = auto_added
            return out

        return ToolSpec(
            name=name,
            description=(
                "FINAL ANSWER. Call exactly once when done exploring: the precise ruleset for this "
                "section. targeted_rule_ids: rules that specifically constrain THIS section's design/"
                "copy (selector match, conditional rules whose predicates this section satisfies, "
                "component rules for what the section contains). email_wide_rule_ids: baseline rules "
                "that apply email-wide / to every section (selector null, evaluation_scope=email, "
                "global typography/accessibility/assembly). section_type_mapping: the section-vocab "
                "types you mapped this section to (drives a mechanical coverage check). excluded: "
                "rule_id -> one-line reason for every candidate rule you deliberately left out "
                "(candidates = rules matching your mapping + all null-selector rules). The call "
                "FAILS listing any candidate you neither included nor excluded — account for all "
                "of them. Unconditional hard-constraint/governance-block baseline rules are "
                "NON-EXCLUDABLE: putting one in `excluded` is an error, and any you omit are "
                "auto-included email-wide. rationale: one line per included rule id on why it "
                "applies."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "targeted_rule_ids": {"type": "array", "items": {"type": "string"}},
                    "email_wide_rule_ids": {"type": "array", "items": {"type": "string"}},
                    "section_type_mapping": {
                        "type": "array", "items": {"type": "string"},
                        "description": "section-vocabulary types this blueprint section maps to",
                    },
                    "excluded": {
                        "type": "object", "additionalProperties": {"type": "string"},
                        "description": "rule_id -> one-line disqualifier for candidates left out",
                    },
                    "rationale": {"type": "object", "additionalProperties": {"type": "string"}},
                },
                "required": ["targeted_rule_ids", "email_wide_rule_ids", "section_type_mapping"],
            },
            handler=handler,
            terminal=True,
        )
