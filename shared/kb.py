"""Knowledge-base access layer.

On-disk layout produced by indexing/build_kb.py under kb/{brand}/:
  schema/*.md                      entity docs, section vocab, predicate registry
  rules/{rule_id}.json             one file per brand_rule
  rules/_index.json                compact row per rule
  tokens|assets|subtypes/{id}.json + _index.json
  groups/rule_groups.json, asset_groups.json, relations.json
  graph/graph.json                 {nodes:[{id,kind,label}], edges:[{src,dst,type}]}
  review/*.md                      original blob vs extracted rules
  vectors/chroma/                  persistent Chroma store (3 collections)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .config import kb_dir
from .registries import get_registries
from .schemas import (
    AssetGroup,
    BrandRule,
    BrandToken,
    ContentSubType,
    DesignAsset,
    DesignTemplate,
    RuleGroup,
    RuleRelation,
    TemplateGroup,
)

ENTITY_PREFIXES = {
    "rule_": "rule",
    "tok_": "token",
    "ast_": "asset",
    "sub_": "subtype",
    "tpl_": "template",
    "tgr_": "template_group",
    "grp_": "rule_group",
    "agr_": "asset_group",
}


def entity_kind(entity_id: str) -> Optional[str]:
    for prefix, kind in ENTITY_PREFIXES.items():
        if entity_id.startswith(prefix):
            return kind
    return None


def _load_dir(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    for f in sorted(path.glob("*.json")):
        if f.name.startswith("_"):
            continue
        data = json.loads(f.read_text())
        out[data["id"]] = data
    return out


class KB:
    """In-memory view of one brand's knowledge base."""

    def __init__(self, brand: str):
        self.brand = brand
        self.root = kb_dir(brand)
        if not self.root.exists():
            raise FileNotFoundError(f"KB for brand '{brand}' not built yet: {self.root}")
        # Dynamic vocabulary: registry core + discoveries for this brand, plus anything
        # actually present in the KB (robust to registry edits after a build).
        self.section_types: list[str] = list(get_registries().section_types(brand))

        self.rules: dict[str, BrandRule] = {
            k: BrandRule(**v) for k, v in _load_dir(self.root / "rules").items()
        }
        self.tokens: dict[str, BrandToken] = {
            k: BrandToken(**v) for k, v in _load_dir(self.root / "tokens").items()
        }
        self.assets: dict[str, DesignAsset] = {
            k: DesignAsset(**v) for k, v in _load_dir(self.root / "assets").items()
        }
        self.subtypes: dict[str, ContentSubType] = {
            k: ContentSubType(**v) for k, v in _load_dir(self.root / "subtypes").items()
        }
        # design_template metadata lives in templates/_meta/*.json; bodies are the
        # sibling .mjml files referenced by DesignTemplate.file.
        self.templates: dict[str, DesignTemplate] = {
            k: DesignTemplate(**v) for k, v in _load_dir(self.root / "templates" / "_meta").items()
        }

        groups_dir = self.root / "groups"
        self.rule_groups: dict[str, RuleGroup] = {}
        self.asset_groups: dict[str, AssetGroup] = {}
        self.template_groups: dict[str, TemplateGroup] = {}
        self.relations: list[RuleRelation] = []
        if (groups_dir / "rule_groups.json").exists():
            for g in json.loads((groups_dir / "rule_groups.json").read_text()):
                self.rule_groups[g["id"]] = RuleGroup(**g)
        if (groups_dir / "asset_groups.json").exists():
            for g in json.loads((groups_dir / "asset_groups.json").read_text()):
                self.asset_groups[g["id"]] = AssetGroup(**g)
        if (groups_dir / "template_groups.json").exists():
            for g in json.loads((groups_dir / "template_groups.json").read_text()):
                self.template_groups[g["id"]] = TemplateGroup(**g)
        if (groups_dir / "relations.json").exists():
            self.relations = [RuleRelation(**r) for r in json.loads((groups_dir / "relations.json").read_text())]

        graph_path = self.root / "graph" / "graph.json"
        self.graph: dict[str, Any] = json.loads(graph_path.read_text()) if graph_path.exists() else {"nodes": [], "edges": []}

        for r in self.rules.values():
            for s in r.selector.section_types or []:
                if s not in self.section_types:
                    self.section_types.append(s)
        for sub in self.subtypes.values():
            for s in (sub.fills_section_types or []) + (sub.hosts_section_types or []):
                if s not in self.section_types:
                    self.section_types.append(s)
        for tpl in self.templates.values():
            for s in tpl.fills_section_types or []:
                if s not in self.section_types:
                    self.section_types.append(s)

    # ------------------------------------------------------------------
    def exists(self, entity_id: str) -> bool:
        return any(entity_id in store for store in (
            self.rules, self.tokens, self.assets, self.subtypes,
            self.templates, self.template_groups, self.rule_groups, self.asset_groups))

    def get_any(self, entity_id: str) -> Optional[dict[str, Any]]:
        for store in (self.rules, self.tokens, self.assets, self.subtypes,
                      self.templates, self.template_groups, self.rule_groups, self.asset_groups):
            if entity_id in store:
                return store[entity_id].model_dump(exclude_none=True)
        return None

    def unknown_rule_ids(self, ids: list[str]) -> list[str]:
        return [i for i in ids if i not in self.rules]

    # ------------------------------------------------------------------
    def short_rule(self, rule: BrandRule) -> dict[str, Any]:
        """Compact view used in indices/tool results to keep agent context small."""
        out = {
            "id": rule.id,
            "rule_class": rule.rule_class,
            "tags": rule.tags or [],
            "sections": rule.selector.section_types,  # null = all sections
            "element_path": rule.selector.element_path,
            "scope": rule.scope,
            "hardness": rule.hardness,
            "polarity": rule.polarity,
            "constraint_type": rule.constraint_type,
            "applies_when": [p.model_dump(exclude_none=True) for p in rule.applies_when] if rule.applies_when else None,
            "summary": rule.summary or (rule.rule_text[:160] + ("..." if len(rule.rule_text) > 160 else "")),
        }
        if rule.governance:
            out["governance"] = {k: rule.governance.get(k) for k in ("gov_type", "verdict", "severity")
                                 if rule.governance.get(k)}
        return out

    def full_rule(self, rule: BrandRule) -> dict[str, Any]:
        return rule.model_dump(exclude_none=True)

    def rules_matching_section(self, section_type: str) -> list[BrandRule]:
        """Rules whose selector targets the section, plus null-selector (all-section) rules."""
        out = []
        for r in self.rules.values():
            secs = r.selector.section_types
            if secs is None or section_type in secs:
                out.append(r)
        return out

    def schema_doc(self, name: str) -> Optional[str]:
        p = self.root / "schema" / f"{name}.md"
        return p.read_text() if p.exists() else None

    def schema_doc_names(self) -> list[str]:
        d = self.root / "schema"
        return sorted(p.stem for p in d.glob("*.md")) if d.exists() else []

    # ------------------------------------------------------------------
    # Boundary resolution.
    #
    # rule_text deliberately carries only representative values; the full value
    # tables AND their conditional switching live in the token layer (semantic
    # tokens with variants -> $ref -> primitives). Consumers of a targeting
    # result (IF/THEN/WHY prompt blocks, result.json) have no KB access, so the
    # bindings must be flattened to literals at this boundary or the concrete
    # values are lost. resolved_bindings() is that flattener.
    # ------------------------------------------------------------------
    def _resolve_literal(self, value: Any, hoisted: list[dict[str, Any]],
                         path: frozenset = frozenset(), depth: int = 0) -> Any:
        """Resolve a token-value fragment to a JSON literal, following {'$ref': ...}
        chains. Variants found on referenced tokens are hoisted into `hoisted` so
        conditional switching survives the flattening. The cycle guard is
        per-resolution-path (a token legitimately appears in several branches)."""
        if depth > 6 or value is None:
            return value
        if isinstance(value, dict):
            if set(value.keys()) == {"$ref"}:
                ref = value["$ref"]
                tok = self.tokens.get(ref)
                if tok is None or ref in path:
                    return {"unresolved_ref": ref}
                branch = path | {ref}
                inner = tok.value
                if isinstance(inner, dict) and "default" in inner:
                    for var in inner.get("variants") or []:
                        if isinstance(var, dict):
                            hoisted.append({
                                "when": var.get("when"),
                                "value": self._resolve_literal(var.get("value"), hoisted, branch, depth + 1),
                            })
                    return self._resolve_literal(inner.get("default"), hoisted, branch, depth + 1)
                return self._resolve_literal(inner, hoisted, branch, depth + 1)
            return {k: self._resolve_literal(v, hoisted, path, depth) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_literal(x, hoisted, path, depth) for x in value]
        return value

    def flatten_token(self, token_id: str) -> Optional[dict[str, Any]]:
        """Flatten one token to `{'default': literal, 'variants': [{'when','value'}]}`."""
        tok = self.tokens.get(token_id)
        if tok is None:
            return None
        v = tok.value if isinstance(tok.value, dict) else {"default": tok.value}
        if "default" not in v:  # bare structured value (e.g. gradient spec) without wrapper
            v = {"default": v}
        variants: list[dict[str, Any]] = []
        root = frozenset({token_id})
        default = self._resolve_literal(v.get("default"), variants, root)
        for var in v.get("variants") or []:
            if isinstance(var, dict):
                variants.append({"when": var.get("when"),
                                 "value": self._resolve_literal(var.get("value"), variants, root)})
        # Hoisting can surface the same (when, value) twice; keep first occurrence.
        seen: set = set()
        deduped = []
        for var in variants:
            key = json.dumps(var, sort_keys=True, default=str)
            if key not in seen:
                seen.add(key)
                deduped.append(var)
        return {"default": default, "variants": deduped}

    def resolved_bindings(self, rule: BrandRule) -> list[dict[str, Any]]:
        """One entry per token the rule binds: element path, resolved default
        literal, conditional variants (the IF/ELSE demoted from prose into
        tokens), plus gates and derivation notes."""
        path_by_token: dict[str, str] = {}
        assignments = (rule.effect or {}).get("assignments") if isinstance(rule.effect, dict) else None
        for a in assignments or []:
            if isinstance(a, dict) and a.get("token_id") and a.get("element_path"):
                path_by_token.setdefault(a["token_id"], a["element_path"])

        out: list[dict[str, Any]] = []
        for tid in rule.token_ids:
            tok = self.tokens.get(tid)
            flat = self.flatten_token(tid) if tok else None
            if tok is None or flat is None:
                continue
            entry: dict[str, Any] = {
                "path": path_by_token.get(tid)
                        or (tok.element_paths[0] if tok.element_paths else tok.key),
                "token": tid,
                "default": flat["default"],
            }
            if flat["variants"]:
                entry["variants"] = flat["variants"]
            gate = (tok.gated or {}).get("gate") if tok.gated else None
            if gate:
                entry["gated"] = gate
            if isinstance(tok.derived_from, dict) and tok.derived_from.get("base_token_id"):
                base = self.tokens.get(tok.derived_from["base_token_id"])
                base_label = base.key if base else tok.derived_from["base_token_id"]
                op = tok.derived_from.get("op", "derived")
                amount = tok.derived_from.get("amount")
                entry["note"] = f"{op} of {base_label}" + (f" @ {amount}" if amount is not None else "")
            out.append(entry)
        return out
