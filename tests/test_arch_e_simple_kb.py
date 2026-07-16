"""Architecture E: simple_kb source fidelity, passage refs, finalize validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from shared import config
from shared.llm import ToolError
from shared.prompts import render_full_blueprint_context
from shared.schemas import Blueprint, BlueprintSection
from shared.simple_kb import SimpleBible, finalize_blueprint_spec, parse_passage_ref

RULE_NAV_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_BIBLES = {
    "lisraya": config.DESIGN_BIBLES["lisraya"],
    "ibsrela": config.DESIGN_BIBLES["ibsrela"],
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("brand", ["lisraya", "ibsrela"])
def test_simple_kb_matches_canonical_byte_for_byte(brand: str) -> None:
    simple = config.simple_kb_dir(brand) / "design_bible.json"
    canonical = CANONICAL_BIBLES[brand]
    assert simple.is_file()
    assert canonical.is_file()
    assert _sha256(simple) == _sha256(canonical)


@pytest.mark.parametrize(
    ("brand", "expected_count"),
    [("lisraya", 28), ("ibsrela", 21)],
)
def test_simple_bible_loads_stable_refs(brand: str, expected_count: int) -> None:
    bible = SimpleBible(brand)
    assert len(bible.refs) == expected_count
    assert bible.refs[0].startswith("website.")
    assert "[" in bible.refs[0] and bible.refs[0].endswith("]")
    # Index rows round-trip to known refs
    rows = bible.index_rows()
    assert {r["ref"] for r in rows} == set(bible.refs)
    first = bible.require(bible.refs[0])
    assert first.text
    assert first.category
    cat, idx = parse_passage_ref(first.ref)
    assert cat == first.category
    assert idx == first.index


def test_parse_passage_ref_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        parse_passage_ref("rule_lisraya_foo")
    with pytest.raises(ValueError):
        parse_passage_ref("website.color_scheme_rules")


@pytest.mark.asyncio
async def test_finalize_blueprint_happy_path() -> None:
    bible = SimpleBible("lisraya")
    refs = bible.refs
    spec = finalize_blueprint_spec(bible, expected_section_ids=["intro", "cta"])
    out = await spec.handler(
        {
            "sections": [
                {"section_id": "intro", "targeted_rule_ids": [refs[5], refs[6]]},
                {"section_id": "cta", "targeted_rule_ids": [refs[7]]},
            ],
            "email_wide_rule_ids": [refs[0], refs[1]],
            "rationale": {refs[0]: "baseline accessibility"},
        }
    )
    assert out["email_wide_rule_ids"] == [refs[0], refs[1]]
    assert [s["section_id"] for s in out["sections"]] == ["intro", "cta"]
    assert out["known_passage_count"] == 28


@pytest.mark.asyncio
async def test_finalize_rejects_unknown_ref_and_overlap() -> None:
    bible = SimpleBible("lisraya")
    refs = bible.refs
    spec = finalize_blueprint_spec(bible, expected_section_ids=["intro"])

    with pytest.raises(ToolError, match="unknown passage"):
        await spec.handler(
            {
                "sections": [
                    {"section_id": "intro", "targeted_rule_ids": ["website.nope[0]"]},
                ],
                "email_wide_rule_ids": [],
            }
        )

    with pytest.raises(ToolError, match="both targeted and email_wide"):
        await spec.handler(
            {
                "sections": [
                    {"section_id": "intro", "targeted_rule_ids": [refs[0]]},
                ],
                "email_wide_rule_ids": [refs[0]],
            }
        )


@pytest.mark.asyncio
async def test_finalize_requires_exact_section_coverage() -> None:
    bible = SimpleBible("lisraya")
    refs = bible.refs
    spec = finalize_blueprint_spec(bible, expected_section_ids=["intro", "cta"])

    with pytest.raises(ToolError, match="section coverage mismatch"):
        await spec.handler(
            {
                "sections": [
                    {"section_id": "intro", "targeted_rule_ids": [refs[0]]},
                ],
                "email_wide_rule_ids": [],
            }
        )

    with pytest.raises(ToolError, match="unknown section_id"):
        await spec.handler(
            {
                "sections": [
                    {"section_id": "intro", "targeted_rule_ids": []},
                    {"section_id": "ghost", "targeted_rule_ids": []},
                ],
                "email_wide_rule_ids": [],
            }
        )


def test_render_full_blueprint_respects_design_concept_toggle() -> None:
    bp = Blueprint(
        content_blueprint=[
            BlueprintSection(
                order=1,
                section_id="intro",
                headline="Hello",
                design_concept="Use Accent Shape and Brand Blue #00529b",
            ),
            BlueprintSection(
                order=2,
                section_id="cta",
                headline="Go",
                design_concept="Gradient Callout CTA",
            ),
        ]
    )
    with_dc = render_full_blueprint_context(bp, bp.content_blueprint, True)
    without_dc = render_full_blueprint_context(bp, bp.content_blueprint, False)
    assert "design_concept: Use Accent Shape" in with_dc
    assert "Gradient Callout CTA" in with_dc
    assert "design_concept:" not in without_dc
    assert "section_id: intro" in without_dc
    assert "section_id: cta" in without_dc
    assert "sections (in order): 1:intro, 2:cta" in with_dc


def test_hydrate_returns_verbatim_passage() -> None:
    bible = SimpleBible("lisraya")
    ref = "website.color_scheme_rules[5]"  # Gradient Callout CTA
    payloads = bible.hydrate({ref})
    assert ref in payloads
    assert "Gradient Callout" in payloads[ref]["rule_text"]
    assert payloads[ref]["category"] == "color_scheme_rules"
    assert payloads[ref]["index"] == 5


def test_arch_e_not_in_archs_all() -> None:
    from runner import run_blueprint as rb

    assert "e" in rb.ARCHS
    assert "e" not in rb.ARCHS_ALL
    assert rb.ARCHS["e"].ARCH_ID == "e"
