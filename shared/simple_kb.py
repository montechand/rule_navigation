"""Original design-bible passage store for Architecture E.

Unlike the structured `kb/{brand}/` atomization, this loads the verbatim design-bible
JSON and exposes each Markdown array entry as a selectable passage with a stable
reference like `website.color_scheme_rules[3]`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from . import config
from .llm import ToolError, ToolSpec

REF_RE = re.compile(r"^website\.([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]$")


@dataclass(frozen=True)
class Passage:
    """One original design-bible Markdown blob."""

    ref: str  # e.g. website.color_scheme_rules[3]
    category: str
    index: int
    text: str

    @property
    def title(self) -> str:
        for line in self.text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                # Drop leading markers like "[IMPORTANT]"
                return stripped[:160]
        return self.ref

    @property
    def preview(self) -> str:
        compact = " ".join(self.text.split())
        return compact[:200]


class SimpleBible:
    """Brand-scoped original design bible under `simple_kb/{brand}/`."""

    def __init__(self, brand: str, root: Optional[Path] = None) -> None:
        if brand not in config.BRANDS:
            raise ValueError(f"unknown brand {brand!r}; expected one of {config.BRANDS}")
        self.brand = brand
        self.root = Path(root) if root is not None else config.simple_kb_dir(brand)
        self.path = self.root / "design_bible.json"
        if not self.path.is_file():
            raise FileNotFoundError(f"missing simple_kb bible at {self.path}")
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        website = raw.get("website")
        if not isinstance(website, dict):
            raise ValueError(f"{self.path} missing top-level 'website' object")
        self._passages: dict[str, Passage] = {}
        self._order: list[str] = []
        for category, blobs in website.items():
            if not isinstance(blobs, list):
                continue
            for i, text in enumerate(blobs):
                if not isinstance(text, str):
                    continue
                ref = f"website.{category}[{i}]"
                passage = Passage(ref=ref, category=category, index=i, text=text)
                self._passages[ref] = passage
                self._order.append(ref)
        if not self._passages:
            raise ValueError(f"{self.path} has no string passages under website.*")

    @property
    def refs(self) -> list[str]:
        return list(self._order)

    def get(self, ref: str) -> Optional[Passage]:
        return self._passages.get(ref)

    def require(self, ref: str) -> Passage:
        passage = self.get(ref)
        if passage is None:
            raise KeyError(ref)
        return passage

    def index_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "ref": p.ref,
                "category": p.category,
                "index": p.index,
                "title": p.title,
                "preview": p.preview,
                "chars": len(p.text),
            }
            for p in (self._passages[r] for r in self._order)
        ]

    def write_index(self) -> Path:
        """Write `_index.json` next to the bible for FS navigation."""
        out = self.root / "_index.json"
        out.write_text(json.dumps(self.index_rows(), indent=2) + "\n", encoding="utf-8")
        return out

    def hydrate(self, refs: set[str]) -> dict[str, Any]:
        payloads: dict[str, Any] = {}
        for ref in sorted(refs):
            passage = self.get(ref)
            if passage is None:
                continue
            payloads[ref] = {
                "ref": passage.ref,
                "category": passage.category,
                "index": passage.index,
                "title": passage.title,
                "rule_text": passage.text,
                "source": "design_bible",
            }
        return payloads


def parse_passage_ref(ref: str) -> tuple[str, int]:
    m = REF_RE.match(ref)
    if not m:
        raise ValueError(
            f"invalid passage ref {ref!r}; expected website.<category>[<index>]"
        )
    return m.group(1), int(m.group(2))


def finalize_blueprint_spec(
    bible: SimpleBible,
    *,
    expected_section_ids: list[str],
    name: str = "finalize_blueprint_ruleset",
) -> ToolSpec:
    """Terminal tool: assign original bible passages across the whole blueprint."""

    expected = list(expected_section_ids)
    expected_set = set(expected)
    known_refs = set(bible.refs)

    async def handler(args: dict[str, Any]) -> dict[str, Any]:
        sections_in = args.get("sections")
        email_wide = args.get("email_wide_rule_ids")
        rationale = args.get("rationale") or {}
        if not isinstance(sections_in, list):
            raise ToolError("sections must be an array of {section_id, targeted_rule_ids}")
        if not isinstance(email_wide, list) or not all(isinstance(x, str) for x in email_wide):
            raise ToolError("email_wide_rule_ids must be an array of passage ref strings")
        if not isinstance(rationale, dict):
            raise ToolError("rationale must be an object of ref -> one-line why")

        if len(email_wide) != len(set(email_wide)):
            raise ToolError("email_wide_rule_ids contains duplicates")

        seen_section_ids: list[str] = []
        normalized_sections: list[dict[str, Any]] = []
        all_targeted: set[str] = set()

        for i, row in enumerate(sections_in):
            if not isinstance(row, dict):
                raise ToolError(f"sections[{i}] must be an object")
            sid = row.get("section_id")
            targeted = row.get("targeted_rule_ids")
            if not isinstance(sid, str) or not sid:
                raise ToolError(f"sections[{i}].section_id must be a non-empty string")
            if not isinstance(targeted, list) or not all(isinstance(x, str) for x in targeted):
                raise ToolError(
                    f"sections[{i}].targeted_rule_ids must be an array of passage ref strings"
                )
            if sid not in expected_set:
                raise ToolError(
                    f"unknown section_id {sid!r}; expected one of {sorted(expected_set)}"
                )
            if sid in seen_section_ids:
                raise ToolError(f"duplicate section_id {sid!r}")
            if len(targeted) != len(set(targeted)):
                raise ToolError(f"sections[{i}] ({sid}) targeted_rule_ids contains duplicates")
            seen_section_ids.append(sid)
            all_targeted.update(targeted)
            normalized_sections.append(
                {
                    "section_id": sid,
                    "targeted_rule_ids": list(targeted),
                }
            )

        missing = [sid for sid in expected if sid not in seen_section_ids]
        extra = [sid for sid in seen_section_ids if sid not in expected_set]
        if missing or extra:
            raise ToolError(
                "section coverage mismatch: "
                f"missing={missing} unexpected={extra}; "
                f"expected exactly {expected}"
            )

        unknown = sorted(
            (set(email_wide) | all_targeted) - known_refs
        )
        if unknown:
            raise ToolError(
                "unknown passage refs (use website.<category>[<index>] from _index.json): "
                + ", ".join(unknown[:20])
                + (f" ... (+{len(unknown) - 20} more)" if len(unknown) > 20 else "")
            )

        overlap = sorted(all_targeted & set(email_wide))
        if overlap:
            raise ToolError(
                "passage refs appear in both targeted and email_wide (must be disjoint): "
                + ", ".join(overlap[:20])
                + (f" ... (+{len(overlap) - 20} more)" if len(overlap) > 20 else "")
            )

        bad_rationale = [k for k in rationale if not isinstance(k, str) or not isinstance(rationale[k], str)]
        if bad_rationale:
            raise ToolError("rationale values must be strings keyed by passage ref")

        return {
            "sections": normalized_sections,
            "email_wide_rule_ids": list(email_wide),
            "rationale": {k: str(v) for k, v in rationale.items() if isinstance(k, str)},
            "known_passage_count": len(known_refs),
        }

    return ToolSpec(
        name=name,
        description=(
            "FINAL ANSWER for the whole email blueprint. Call once when done reading the "
            "original design bible. Assign verbatim passage refs (website.<category>[<index>]) "
            "into per-section targeted_rule_ids and email_wide_rule_ids. Every blueprint "
            "section_id must appear exactly once in `sections`. A passage may be targeted by "
            "multiple sections, but MUST NOT appear in both targeted and email_wide. "
            "rationale: optional ref -> one-line why it applies."
        ),
        parameters={
            "type": "object",
            "properties": {
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section_id": {"type": "string"},
                            "targeted_rule_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["section_id", "targeted_rule_ids"],
                    },
                },
                "email_wide_rule_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "rationale": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["sections", "email_wide_rule_ids"],
        },
        handler=handler,
        terminal=True,
    )
