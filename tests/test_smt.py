"""WP-15 SMT layer tests."""

from __future__ import annotations

import json
from importlib.util import find_spec
from pathlib import Path
from typing import Any

import pytest

import indexing_v2.consistency.smt as smt_module
from indexing_v2.consistency.pairwise import analyze_pairwise
from indexing_v2.consistency.smt import (
    STAGE_VERSION,
    analyze_smt,
    smt_status,
    solve_context,
    write_analysis_conflicts,
)
from indexing_v2.contracts import ContextKey, KBSnapshot
from shared.schemas import (
    BrandRule,
    BrandToken,
    ContentSubType,
    DesignAsset,
    Predicate,
    Selector,
)

HAS_Z3 = find_spec("z3") is not None


class RecordingConsole:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, *args: Any, **kwargs: Any) -> None:
        self.messages.append(" ".join(str(arg) for arg in args))


def _reset_smt_import_state() -> None:
    smt_module._z3_checked = False
    smt_module._z3_module = None
    smt_module._skip_notified = False


def _require_z3() -> Any:
    if not HAS_Z3:
        pytest.skip("z3-solver not installed")
    z3 = smt_module._load_z3()
    assert z3 is not None
    return z3


def _encoding(
    snapshot: KBSnapshot,
    context: ContextKey | None = None,
) -> tuple[Any, Any]:
    z3 = _require_z3()
    effective_context = context or ContextKey()
    active = smt_module._active_hard_rules(
        snapshot,
        effective_context,
        set(effective_context.content_tags),
    )
    return z3, smt_module._build_solver(z3, snapshot, active)


def _force_section(encoding: Any, slot: int, section: str) -> None:
    encoding.solver.add(
        encoding.section_type[slot] == encoding.section_values.index(section)
    )


def _force_only_section(encoding: Any, slot: int, section: str) -> None:
    index = encoding.section_values.index(section)
    for candidate_slot in range(smt_module.N_SLOTS):
        encoding.solver.add(
            encoding.section_type[candidate_slot]
            == index
            if candidate_slot == slot
            else encoding.section_type[candidate_slot] != index
        )


def _snapshot(
    *,
    rules: dict[str, BrandRule] | None = None,
    tokens: dict[str, BrandToken] | None = None,
    assets: dict[str, DesignAsset] | None = None,
    subtypes: dict[str, ContentSubType] | None = None,
    domains: dict[str, list[str]] | None = None,
) -> KBSnapshot:
    return KBSnapshot(
        brand="minibible",
        rules=rules or {},
        tokens=tokens or {},
        assets=assets or {},
        subtypes=subtypes or {},
        templates={},
        predicate_domains=domains
        or {
            "background_group": ["dark", "light"],
            "campaign": ["none"],
            "theme": ["none"],
            "content_tag": [],
        },
    )


def _cardinality_unsat_rules() -> dict[str, BrandRule]:
    return {
        "rule_minibible_cta_max_one": BrandRule(
            id="rule_minibible_cta_max_one",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            effect={"max": 1, "per": "email", "target": "cta.button.primary"},
            hardness="hard_constraint",
            evaluation_scope="email",
            rule_text="max one",
            selector=Selector(element_path="cta.button.primary"),
        ),
        "rule_minibible_cta_min_two_touchpoints": BrandRule(
            id="rule_minibible_cta_min_two_touchpoints",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            effect={"min": 2, "per": "email", "target": "cta"},
            hardness="hard_constraint",
            evaluation_scope="email",
            rule_text="min two",
            selector=Selector(element_path="cta"),
        ),
    }


def test_stage_version() -> None:
    assert STAGE_VERSION == "1.0.0"


def test_smt_status_available_when_z3_installed() -> None:
    _require_z3()
    _reset_smt_import_state()
    assert smt_status() == "available"


def test_planted_cardinality_unsat_core_exactly_planted_ids() -> None:
    _require_z3()
    snapshot = _snapshot(rules=_cardinality_unsat_rules())
    result = solve_context(snapshot, ContextKey())
    assert result.status == "unsat"
    assert set(result.unsat_core) == {
        "rule_minibible_cta_max_one",
        "rule_minibible_cta_min_two_touchpoints",
    }


def test_sat_fixture_with_compatible_cardinality() -> None:
    _require_z3()
    rules = {
        "rule_cta_max_three": BrandRule(
            id="rule_cta_max_three",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            effect={"max": 3, "per": "email", "target": "cta"},
            hardness="hard_constraint",
            evaluation_scope="email",
            rule_text="max three",
            selector=Selector(element_path="cta"),
        ),
    }
    result = solve_context(_snapshot(rules=rules), ContextKey())
    assert result.status == "sat"


def test_active_context_guard_excludes_inactive_rules() -> None:
    _require_z3()
    rules = {
        **_cardinality_unsat_rules(),
        "rule_launch_only": BrandRule(
            id="rule_launch_only",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            effect={"min": 5, "per": "email", "target": "hero"},
            hardness="hard_constraint",
            evaluation_scope="email",
            applies_when=[Predicate(kind="campaign", value="launch")],
            rule_text="launch hero min",
            selector=Selector(section_types=["hero"]),
        ),
    }
    result = solve_context(_snapshot(rules=rules), ContextKey(campaign="none"))
    assert "rule_launch_only" not in result.active_rule_ids


def test_ordering_and_pairing_rules_sat() -> None:
    _require_z3()
    rules = {
        "rule_order": BrandRule(
            id="rule_order",
            brand_id="minibible",
            rule_class="assembly",
            constraint_type="ordering",
            effect={"sequence": ["top_matter", "hero", "end_matter"], "strict": True},
            hardness="hard_constraint",
            evaluation_scope="email",
            rule_text="order",
        ),
        "rule_pair": BrandRule(
            id="rule_pair",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="pairing",
            effect={"a": "asset_a", "b": "asset_b", "relation": "requires"},
            hardness="hard_constraint",
            evaluation_scope="email",
            rule_text="pair",
        ),
    }
    assets = {
        "asset_a": DesignAsset(
            id="asset_a",
            brand_id="minibible",
            asset_type="icon",
            description="a",
        ),
        "asset_b": DesignAsset(
            id="asset_b",
            brand_id="minibible",
            asset_type="icon",
            description="b",
        ),
    }
    result = solve_context(_snapshot(rules=rules, assets=assets), ContextKey())
    assert result.status == "sat"


def test_exclusivity_and_structural_subtype_axioms() -> None:
    _require_z3()
    rules = {
        "rule_exclusive": BrandRule(
            id="rule_exclusive",
            brand_id="minibible",
            rule_class="color_application",
            constraint_type="exclusivity",
            effect={
                "subject": "tok_panel",
                "reserved_for": "affordability",
            },
            hardness="hard_constraint",
            evaluation_scope="email",
            rule_text="exclusive",
            selector=Selector(section_types=["affordability", "symptom_trio"]),
        ),
    }
    tokens = {
        "tok_panel": BrandToken(
            id="tok_panel",
            brand_id="minibible",
            token_type="color",
            kind="semantic",
            key="panel.fill",
            value={"default": "#01A47E"},
            gated={"gate": {"kind": "content_tag", "value": "lpga"}},
        ),
    }
    subtypes = {
        "sub_top": ContentSubType(
            id="sub_top",
            brand_id="minibible",
            kind="email_component",
            name="Top",
            assembly={"position": "first", "repeatable": False, "locked": True},
            fills_section_types=["top_matter"],
        ),
    }
    result = solve_context(
        _snapshot(rules=rules, tokens=tokens, subtypes=subtypes),
        ContextKey(),
    )
    assert result.status == "sat"


def test_ordering_uses_exact_physical_first_occurrences() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_hero_before_cta",
        brand_id="minibible",
        rule_class="assembly",
        constraint_type="ordering",
        effect={"sequence": ["hero", "cta"], "strict": True},
        hardness="hard_constraint",
        evaluation_scope="email",
        rule_text="hero before cta",
    )
    _, encoding = _encoding(_snapshot(rules={rule.id: rule}))
    _force_only_section(encoding, 2, "hero")
    _force_only_section(encoding, 1, "cta")
    assert encoding.solver.check() == z3.unsat


def test_ordering_requires_missing_device_tail_to_occur() -> None:
    _require_z3()
    rules = {
        "rule_device_order": BrandRule(
            id="rule_device_order",
            brand_id="minibible",
            rule_class="assembly",
            constraint_type="ordering",
            effect={"sequence": ["asset_a", "asset_b"], "strict": True},
            hardness="hard_constraint",
            evaluation_scope="email",
            rule_text="a then b",
        ),
        "rule_no_asset_b": BrandRule(
            id="rule_no_asset_b",
            brand_id="minibible",
            rule_class="assembly",
            constraint_type="cardinality",
            effect={"target": "asset_b", "max": 0, "per": "email"},
            hardness="hard_constraint",
            evaluation_scope="email",
            rule_text="no b",
        ),
    }
    assets = {
        name: DesignAsset(
            id=name,
            brand_id="minibible",
            asset_type="icon",
            description=name,
        )
        for name in ("asset_a", "asset_b")
    }
    result = solve_context(_snapshot(rules=rules, assets=assets), ContextKey())
    assert result.status == "unsat"
    assert result.unsat_core == ["rule_device_order", "rule_no_asset_b"]


def test_pairing_requires_same_slot_presence() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_pair",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="pairing",
        effect={"a": "asset_a", "b": "asset_b", "relation": "requires"},
        hardness="hard_constraint",
        evaluation_scope="email",
        rule_text="pair",
    )
    assets = {
        name: DesignAsset(
            id=name,
            brand_id="minibible",
            asset_type="icon",
            description=name,
        )
        for name in ("asset_a", "asset_b")
    }
    _, encoding = _encoding(_snapshot(rules={rule.id: rule}, assets=assets))
    _force_section(encoding, 1, "hero")
    encoding.solver.add(encoding.device_present["asset_a"][1])
    encoding.solver.add(z3.Not(encoding.device_present["asset_b"][1]))
    assert encoding.solver.check() == z3.unsat


def test_per_section_cardinality_differs_from_email_sum() -> None:
    z3 = _require_z3()

    def snapshot(per: str) -> KBSnapshot:
        rules = {
            "rule_device_min": BrandRule(
                id="rule_device_min",
                brand_id="minibible",
                rule_class="layout",
                constraint_type="cardinality",
                selector=Selector(section_types=["hero", "cta"]),
                effect={"target": "asset_a", "min": 1, "per": per},
                hardness="hard_constraint",
                evaluation_scope="email",
                rule_text="device minimum",
            ),
            "rule_device_global_max": BrandRule(
                id="rule_device_global_max",
                brand_id="minibible",
                rule_class="layout",
                constraint_type="cardinality",
                effect={"target": "asset_a", "max": 1, "per": "email"},
                hardness="hard_constraint",
                evaluation_scope="email",
                rule_text="device max one",
            ),
        }
        asset = DesignAsset(
            id="asset_a",
            brand_id="minibible",
            asset_type="icon",
            description="a",
        )
        return _snapshot(rules=rules, assets={asset.id: asset})

    _, per_section = _encoding(snapshot("section"))
    _force_section(per_section, 1, "hero")
    _force_section(per_section, 2, "cta")
    assert per_section.solver.check() == z3.unsat

    _, per_email = _encoding(snapshot("email"))
    _force_section(per_email, 1, "hero")
    _force_section(per_email, 2, "cta")
    assert per_email.solver.check() == z3.sat


def test_device_per_section_max_uses_integer_count() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_device_max_two",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="cardinality",
        selector=Selector(section_types=["hero"]),
        effect={"target": "asset_a", "max": 2, "per": "section"},
        hardness="hard_constraint",
        rule_text="max two per hero",
    )
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    _, encoding = _encoding(
        _snapshot(rules={rule.id: rule}, assets={asset.id: asset})
    )
    _force_section(encoding, 1, "hero")
    encoding.solver.add(encoding.device_count["asset_a"][1] == 3)
    assert encoding.solver.check() == z3.unsat


def test_device_email_max_sums_counts_across_slots() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_device_max_two",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="cardinality",
        effect={"target": "asset_a", "max": 2, "per": "email"},
        hardness="hard_constraint",
        rule_text="max two per email",
    )
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    _, encoding = _encoding(
        _snapshot(rules={rule.id: rule}, assets={asset.id: asset})
    )
    _force_section(encoding, 1, "hero")
    _force_section(encoding, 2, "cta")
    encoding.solver.add(encoding.device_count["asset_a"][1] == 1)
    encoding.solver.add(encoding.device_count["asset_a"][2] == 2)
    assert encoding.solver.check() == z3.unsat


def test_device_per_section_min_two_accepts_count_three() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_device_min_two",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="cardinality",
        selector=Selector(section_types=["hero"]),
        effect={"target": "asset_a", "min": 2, "per": "section"},
        hardness="hard_constraint",
        rule_text="min two per hero",
    )
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    _, encoding = _encoding(
        _snapshot(rules={rule.id: rule}, assets={asset.id: asset})
    )
    _force_only_section(encoding, 1, "hero")
    encoding.solver.add(encoding.device_count["asset_a"][1] == 3)
    assert encoding.solver.check() == z3.sat
    model = encoding.solver.model()
    assert model.eval(encoding.device_present["asset_a"][1])


def test_background_guard_scopes_cardinality_cells() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_no_dark_device",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="cardinality",
        selector=Selector(section_types=["hero"]),
        applies_when=[Predicate(kind="background_group", value={"group": "dark"})],
        effect={"target": "asset_a", "max": 0, "per": "section"},
        hardness="hard_constraint",
        rule_text="no device on dark hero",
    )
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    snapshot = _snapshot(rules={rule.id: rule}, assets={asset.id: asset})

    _, light = _encoding(snapshot)
    _force_section(light, 1, "hero")
    light.solver.add(light.device_present["asset_a"][1])
    light.solver.add(
        light.background[1] == smt_module._BACKGROUND_VALUES.index("light")
    )
    assert light.solver.check() == z3.sat

    _, dark = _encoding(snapshot)
    _force_section(dark, 1, "hero")
    dark.solver.add(dark.device_present["asset_a"][1])
    dark.solver.add(
        dark.background[1] == smt_module._BACKGROUND_VALUES.index("dark")
    )
    assert dark.solver.check() == z3.unsat


def test_selector_section_guard_scopes_cardinality_cells() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_no_hero_device",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="cardinality",
        selector=Selector(section_types=["hero"]),
        effect={"target": "asset_a", "max": 0, "per": "section"},
        hardness="hard_constraint",
        rule_text="no hero device",
    )
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    snapshot = _snapshot(rules={rule.id: rule}, assets={asset.id: asset})

    _, cta = _encoding(snapshot)
    _force_section(cta, 1, "cta")
    cta.solver.add(cta.device_present["asset_a"][1])
    assert cta.solver.check() == z3.sat

    _, hero = _encoding(snapshot)
    _force_section(hero, 1, "hero")
    hero.solver.add(hero.device_present["asset_a"][1])
    assert hero.solver.check() == z3.unsat


def test_disjoint_breakpoint_cardinality_guards_are_sat() -> None:
    _require_z3()
    rules = {
        "rule_mobile_max_zero": BrandRule(
            id="rule_mobile_max_zero",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            applies_when=[
                Predicate(kind="breakpoint", value={"breakpoint": "mobile"})
            ],
            effect={"target": "asset_a", "max": 0, "per": "email"},
            hardness="hard_constraint",
            rule_text="none on mobile",
        ),
        "rule_desktop_min_one": BrandRule(
            id="rule_desktop_min_one",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            applies_when=[
                Predicate(kind="breakpoint", value={"breakpoint": "desktop"})
            ],
            effect={"target": "asset_a", "min": 1, "per": "email"},
            hardness="hard_constraint",
            rule_text="one on desktop",
        ),
    }
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    result = solve_context(
        _snapshot(rules=rules, assets={asset.id: asset}),
        ContextKey(),
    )
    assert result.status == "sat"


def test_same_breakpoint_cardinality_conflict_has_exact_core() -> None:
    _require_z3()
    rules = {
        "rule_mobile_max_zero": BrandRule(
            id="rule_mobile_max_zero",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            applies_when=[
                Predicate(kind="breakpoint", value={"breakpoint": "mobile"})
            ],
            effect={"target": "asset_a", "max": 0, "per": "email"},
            hardness="hard_constraint",
            rule_text="none on mobile",
        ),
        "rule_mobile_min_one": BrandRule(
            id="rule_mobile_min_one",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            applies_when=[
                Predicate(kind="breakpoint", value={"breakpoint": "mobile"})
            ],
            effect={"target": "asset_a", "min": 1, "per": "email"},
            hardness="hard_constraint",
            rule_text="one on mobile",
        ),
    }
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    result = solve_context(
        _snapshot(rules=rules, assets={asset.id: asset}),
        ContextKey(),
    )
    assert result.status == "unsat"
    assert result.unsat_core == [
        "rule_mobile_max_zero",
        "rule_mobile_min_one",
    ]


def test_first_and_last_position_guards_stay_disjoint() -> None:
    _require_z3()
    rules = {
        "rule_first_max_zero": BrandRule(
            id="rule_first_max_zero",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            applies_when=[
                Predicate(
                    kind="position_in_email",
                    value={"position": "first"},
                )
            ],
            effect={"target": "asset_a", "max": 0, "per": "email"},
            hardness="hard_constraint",
            rule_text="none first",
        ),
        "rule_last_min_one": BrandRule(
            id="rule_last_min_one",
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            applies_when=[
                Predicate(
                    kind="position_in_email",
                    value={"position": "last"},
                )
            ],
            effect={"target": "asset_a", "min": 1, "per": "email"},
            hardness="hard_constraint",
            rule_text="one last",
        ),
    }
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    result = solve_context(
        _snapshot(rules=rules, assets={asset.id: asset}),
        ContextKey(),
    )
    assert result.status == "sat"


def test_exclusivity_counts_subject_only_outside_exact_reserved_sections() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_subject_exclusive",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="exclusivity",
        effect={"subject": "asset_a", "reserved_for": ["hero"]},
        hardness="hard_constraint",
        evaluation_scope="email",
        rule_text="reserve subject",
    )
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    _, encoding = _encoding(
        _snapshot(rules={rule.id: rule}, assets={asset.id: asset})
    )
    for slot, section in ((1, "hero"), (2, "cta")):
        _force_section(encoding, slot, section)
        encoding.solver.add(encoding.device_present["asset_a"][slot])
    assert encoding.solver.check() == z3.sat

    _force_section(encoding, 3, "intro")
    encoding.solver.add(encoding.device_present["asset_a"][3])
    assert encoding.solver.check() == z3.unsat


def test_exclusivity_does_not_substring_match_reserved_sections() -> None:
    z3 = _require_z3()
    rule = BrandRule(
        id="rule_subject_exclusive",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="exclusivity",
        effect={"subject": "asset_a", "reserved_for": "hero block"},
        hardness="hard_constraint",
        evaluation_scope="email",
        rule_text="not an exact section name",
    )
    asset = DesignAsset(
        id="asset_a",
        brand_id="minibible",
        asset_type="icon",
        description="a",
    )
    _, encoding = _encoding(
        _snapshot(rules={rule.id: rule}, assets={asset.id: asset})
    )
    for slot, section in ((1, "hero"), (2, "cta")):
        _force_section(encoding, slot, section)
        encoding.solver.add(encoding.device_present["asset_a"][slot])
    assert encoding.solver.check() == z3.unsat


def test_locked_subtype_is_required_exactly_once() -> None:
    _require_z3()
    subtype = ContentSubType(
        id="sub_locked_hero",
        brand_id="minibible",
        kind="email_component",
        name="Locked hero",
        assembly={"position": "any", "repeatable": False, "locked": True},
        fills_section_types=["hero"],
    )
    rule = BrandRule(
        id="rule_no_hero",
        brand_id="minibible",
        rule_class="assembly",
        constraint_type="cardinality",
        effect={"target": "hero", "max": 0, "per": "email"},
        hardness="hard_constraint",
        evaluation_scope="email",
        rule_text="no hero",
    )
    result = solve_context(
        _snapshot(
            rules={rule.id: rule},
            subtypes={subtype.id: subtype},
        ),
        ContextKey(),
    )
    assert result.status == "unsat"
    assert result.unsat_core == ["rule_no_hero", "struct:sub_locked_hero"]


def test_structural_unsat_core_excludes_unrelated_rules() -> None:
    _require_z3()
    subtype = ContentSubType(
        id="sub_custom_first",
        brand_id="minibible",
        kind="email_component",
        name="Custom first",
        assembly={"position": "first", "repeatable": False, "locked": True},
        fills_section_types=["other.custom_first"],
    )
    unrelated = BrandRule(
        id="rule_unrelated",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="cardinality",
        effect={"target": "asset_unused", "max": 12, "per": "email"},
        hardness="hard_constraint",
        rule_text="unrelated",
    )
    result = solve_context(
        _snapshot(
            rules={unrelated.id: unrelated},
            subtypes={subtype.id: subtype},
        ),
        ContextKey(),
    )
    assert result.status == "unsat"
    assert result.unsat_core == [
        "struct:base:top_matter",
        "struct:sub_custom_first",
    ]
    assert "rule_unrelated" not in result.unsat_core


def test_custom_section_enum_is_sorted_and_deterministic() -> None:
    _require_z3()
    rules = {
        name: BrandRule(
            id=name,
            brand_id="minibible",
            rule_class="layout",
            constraint_type="cardinality",
            selector=Selector(section_types=[section]),
            effect={"target": section, "max": 1, "per": "email"},
            hardness="hard_constraint",
            rule_text=name,
        )
        for name, section in (
            ("rule_z", "other.zeta"),
            ("rule_a", "other.alpha"),
        )
    }
    snapshot = _snapshot(rules=rules)
    first = smt_module._section_enum(snapshot)
    second = smt_module._section_enum(snapshot)
    assert first == second == sorted(first)
    assert {"other.alpha", "other.zeta"} <= set(first)


@pytest.mark.parametrize(
    ("kind", "effect", "message"),
    [
        (
            "cardinality",
            {"target": "asset_a", "max": 1, "per": "sections"},
            "per must be",
        ),
        (
            "cardinality",
            {"target": "asset_a", "min": True, "per": "email"},
            "nonnegative integer",
        ),
        (
            "cardinality",
            {"target": "asset_a", "max": -1, "per": "email"},
            "nonnegative integer",
        ),
        (
            "cardinality",
            {"target": "asset_a", "min": 2, "max": 1, "per": "email"},
            "min cannot exceed max",
        ),
        (
            "pairing",
            {"a": "asset_a", "b": "asset_b", "relation": "require"},
            "pairing relation",
        ),
        (
            "ordering",
            {"sequence": [], "strict": True},
            "sequence must contain",
        ),
        (
            "ordering",
            {"sequence": ["hero", ""], "strict": True},
            "sequence must contain",
        ),
    ],
)
def test_invalid_effect_controls_raise_typed_encoding_error(
    kind: str,
    effect: dict[str, Any],
    message: str,
) -> None:
    _require_z3()
    rule = BrandRule(
        id="rule_invalid",
        brand_id="minibible",
        rule_class="layout",
        constraint_type=kind,
        effect=effect,
        hardness="hard_constraint",
        rule_text="invalid",
    )
    with pytest.raises(smt_module.SmtEncodingError, match=message):
        solve_context(_snapshot(rules={rule.id: rule}), ContextKey())


def test_unsupported_position_value_raises_typed_guard_error() -> None:
    _require_z3()
    rule = BrandRule(
        id="rule_middle",
        brand_id="minibible",
        rule_class="layout",
        constraint_type="cardinality",
        applies_when=[
            Predicate(
                kind="position_in_email",
                value={"position": "middle"},
            )
        ],
        effect={"target": "asset_a", "max": 1, "per": "email"},
        hardness="hard_constraint",
        rule_text="middle",
    )
    with pytest.raises(smt_module.SmtUnsupportedGuardError, match="middle"):
        solve_context(_snapshot(rules={rule.id: rule}), ContextKey())


def test_solver_unknown_raises_typed_error(monkeypatch: pytest.MonkeyPatch) -> None:
    z3 = _require_z3()

    class UnknownSolver:
        def check(self) -> Any:
            return z3.unknown

        def reason_unknown(self) -> str:
            return "test unknown"

    encoding = smt_module._SolverEncoding(
        solver=UnknownSolver(),
        tracked={},
        section_type=[],
        background=[],
        device_present={},
        device_count={},
        residual_axes={},
        residual_axis_values={},
        section_values=[],
    )
    monkeypatch.setattr(smt_module, "_build_solver", lambda *_args: encoding)
    with pytest.raises(smt_module.SmtSolverUnknownError, match="test unknown"):
        solve_context(_snapshot(), ContextKey())


def test_analyze_smt_determinism_twice() -> None:
    _require_z3()
    snapshot = _snapshot(rules=_cardinality_unsat_rules())
    first = analyze_smt(snapshot).model_dump(mode="json")
    second = analyze_smt(snapshot).model_dump(mode="json")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_write_analysis_conflicts_preserves_pairwise_and_appends_global_unsat(
    tmp_path: Path,
) -> None:
    _require_z3()
    snapshot = _snapshot(rules=_cardinality_unsat_rules())
    bindings: list[Any] = []
    pairwise = analyze_pairwise(snapshot, bindings)
    smt = analyze_smt(snapshot)
    path = tmp_path / "analysis" / "conflicts.json"
    artifact = write_analysis_conflicts(path, pairwise=pairwise, smt=smt)
    assert path.exists()
    assert artifact.conflicts
    kinds = {row["kind"] for row in artifact.conflicts}
    assert "global_unsat" in kinds
    global_rows = [row for row in artifact.conflicts if row["kind"] == "global_unsat"]
    assert global_rows[0]["core"] == sorted(global_rows[0]["core"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "2.0"

    stale_pairwise = analyze_pairwise(snapshot, bindings)
    write_analysis_conflicts(path, pairwise=stale_pairwise, smt=smt)
    rewritten = json.loads(path.read_text(encoding="utf-8"))
    assert len(rewritten["conflicts"]) >= len(stale_pairwise.conflicts)


def test_import_guard_skip_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_smt_import_state()
    monkeypatch.setattr(smt_module, "_load_z3", lambda: None)
    console = RecordingConsole()
    result = analyze_smt(_snapshot(rules=_cardinality_unsat_rules()), console=console)
    assert result.status == "skipped"
    assert console.messages
    assert "skipped" in console.messages[0].lower()
    analyze_smt(_snapshot(), console=console)
    assert len(console.messages) == 1
    assert solve_context(_snapshot(), ContextKey()).status == "skipped"


def test_import_guard_module_not_found_via_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    _reset_smt_import_state()
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: Any = (),
        level: Any = 0,
    ) -> Any:
        if name == "z3":
            raise ModuleNotFoundError("No module named 'z3'", name="z3")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert smt_module._load_z3() is None
    assert smt_status() == "skipped"


def test_import_guard_does_not_swallow_other_import_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    _reset_smt_import_state()
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: Any = (),
        level: Any = 0,
    ) -> Any:
        if name == "z3":
            raise RuntimeError("broken z3 install")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="broken z3 install"):
        smt_module._load_z3()


def test_import_guard_reraises_nested_module_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins

    _reset_smt_import_state()
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: Any = (),
        level: Any = 0,
    ) -> Any:
        if name == "z3":
            raise ModuleNotFoundError(
                "No module named 'z3_nested_dependency'",
                name="z3_nested_dependency",
            )
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ModuleNotFoundError) as exc_info:
        smt_module._load_z3()
    assert exc_info.value.name == "z3_nested_dependency"
    assert smt_module._z3_checked is False
