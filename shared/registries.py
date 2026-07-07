"""Dynamic closed-vocabulary registries with model-driven discovery.

shared/registries.json is the committed, versioned source of truth (seeded from the v0.2
dictionary). Extraction may propose new entries with the `other.<name>` convention; the
build validates, slug-normalizes, and registers truly novel entries permanently (the file
is checked in, so a discovery survives across runs and appears in future prompts).

Scoping:
  - section_types: brand-scoped — a discovered section device (e.g. symptom_trio) only
    enters the vocabulary of brands it was seen in.
  - relations / token_types: global — structural vocabularies shared across brands.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

REGISTRY_PATH = Path(__file__).parent / "registries.json"

_DOMAINS = ("section_types", "relations", "token_types")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


class Registries:
    def __init__(self, path: Path = REGISTRY_PATH):
        self.path = path
        self.data = json.loads(path.read_text())
        self.dirty = False

    # ------------------------------------------------------------------
    def vocab(self, domain: str, brand: Optional[str] = None) -> list[str]:
        d = self.data[domain]
        out = list(d["core"])
        for name, meta in d.get("discovered", {}).items():
            if domain == "section_types" and brand is not None:
                if brand in (meta.get("brands") or []):
                    out.append(name)
            else:
                out.append(name)
        return out

    def section_types(self, brand: Optional[str] = None) -> list[str]:
        return self.vocab("section_types", brand)

    def relations(self) -> list[str]:
        return self.vocab("relations")

    def token_types(self) -> list[str]:
        return self.vocab("token_types")

    def discovered(self, domain: str) -> dict:
        return self.data[domain].get("discovered", {})

    # ------------------------------------------------------------------
    def register(self, domain: str, name: str, brand: Optional[str] = None,
                 note: str = "") -> tuple[str, bool]:
        """Register a proposed entry. Returns (normalized_name, newly_added).

        Already-known entries (core or discovered) are returned as-is; for brand-scoped
        domains an existing discovered entry gains the brand.
        """
        assert domain in _DOMAINS
        norm = _slug(name)
        if not norm:
            raise ValueError(f"unregisterable name: {name!r}")
        d = self.data[domain]
        if norm in d["core"]:
            return norm, False
        disc = d.setdefault("discovered", {})
        if norm in disc:
            if brand and brand not in (disc[norm].get("brands") or []):
                disc[norm].setdefault("brands", []).append(brand)
                self.dirty = True
            return norm, False
        entry: dict = {"note": note or f"discovered during extraction"}
        if domain == "section_types":
            entry["brands"] = [brand] if brand else []
        disc[norm] = entry
        self.dirty = True
        return norm, True

    def save(self) -> None:
        if self.dirty:
            self.path.write_text(json.dumps(self.data, indent=2) + "\n")
            self.dirty = False


_singleton: Optional[Registries] = None


def get_registries() -> Registries:
    global _singleton
    if _singleton is None:
        _singleton = Registries()
    return _singleton


OTHER_RE = re.compile(r"^other\.([a-z0-9_]+)$")


def parse_other(value: str) -> Optional[str]:
    """'other.<name>' -> normalized name, else None."""
    m = OTHER_RE.match(str(value).strip().lower().replace(" ", "_"))
    return _slug(m.group(1)) if m else None
