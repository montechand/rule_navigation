"""Knowledge-base access layer.

On-disk layout produced by indexing/build_kb.py under kb/{brand}/:
  schema/*.md                      entity docs, section vocab, predicate registry
  rules/{rule_id}.json             one file per brand_rule
  rules/_index.json                compact row per rule
  tokens|assets|subtypes|governance/{id}.json + _index.json
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
    Governance,
    RuleGroup,
    RuleRelation,
)

ENTITY_PREFIXES = {
    "rule_": "rule",
    "tok_": "token",
    "ast_": "asset",
    "gov_": "governance",
    "sub_": "subtype",
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
        self.governance: dict[str, Governance] = {
            k: Governance(**v) for k, v in _load_dir(self.root / "governance").items()
        }

        groups_dir = self.root / "groups"
        self.rule_groups: dict[str, RuleGroup] = {}
        self.asset_groups: dict[str, AssetGroup] = {}
        self.relations: list[RuleRelation] = []
        if (groups_dir / "rule_groups.json").exists():
            for g in json.loads((groups_dir / "rule_groups.json").read_text()):
                self.rule_groups[g["id"]] = RuleGroup(**g)
        if (groups_dir / "asset_groups.json").exists():
            for g in json.loads((groups_dir / "asset_groups.json").read_text()):
                self.asset_groups[g["id"]] = AssetGroup(**g)
        if (groups_dir / "relations.json").exists():
            self.relations = [RuleRelation(**r) for r in json.loads((groups_dir / "relations.json").read_text())]

        graph_path = self.root / "graph" / "graph.json"
        self.graph: dict[str, Any] = json.loads(graph_path.read_text()) if graph_path.exists() else {"nodes": [], "edges": []}

        for r in self.rules.values():
            for s in r.selector.section_types or []:
                if s not in self.section_types:
                    self.section_types.append(s)
        for sub in self.subtypes.values():
            for s in sub.covers_section_types or []:
                if s not in self.section_types:
                    self.section_types.append(s)

    # ------------------------------------------------------------------
    def exists(self, entity_id: str) -> bool:
        return entity_id in self.rules or entity_id in self.tokens or entity_id in self.assets \
            or entity_id in self.subtypes or entity_id in self.governance \
            or entity_id in self.rule_groups or entity_id in self.asset_groups

    def get_any(self, entity_id: str) -> Optional[dict[str, Any]]:
        for store in (self.rules, self.tokens, self.assets, self.subtypes,
                      self.governance, self.rule_groups, self.asset_groups):
            if entity_id in store:
                return store[entity_id].model_dump(exclude_none=True)
        return None

    def unknown_rule_ids(self, ids: list[str]) -> list[str]:
        return [i for i in ids if i not in self.rules]

    # ------------------------------------------------------------------
    def short_rule(self, rule: BrandRule) -> dict[str, Any]:
        """Compact view used in indices/tool results to keep agent context small."""
        return {
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
