"""WP-13 guard algebra tests."""

from __future__ import annotations

import json

import pytest

from indexing_v2.cascade.guards import (
    STAGE_VERSION,
    conjunction,
    is_satisfiable,
    normalize_guard,
    satisfiable,
    witness,
)
from indexing_v2.contracts import GuardTerm
from shared.schemas import Predicate


def test_stage_version() -> None:
    assert STAGE_VERSION == "1.0.0"


def test_normalize_guard_predicate_list_and_canonical_sort() -> None:
    guard = normalize_guard(
        [
            Predicate(kind="breakpoint", value={"breakpoint": "mobile"}),
            Predicate(kind="background_group", value={"group": "dark"}),
        ]
    )
    assert list(guard) == ["background_group", "breakpoint"]
    assert guard["background_group"] == GuardTerm(op="eq", values=["dark"])
    assert guard["breakpoint"] == GuardTerm(op="eq", values=["mobile"])


def test_normalize_guard_variant_when_and_term_objects() -> None:
    guard = normalize_guard(
        {
            "background_group": {"op": "eq", "values": ["light"]},
            "content_tag": {"op": "has_tag", "values": ["lpga", "secondary_cta"]},
        }
    )
    assert guard["background_group"] == GuardTerm(op="eq", values=["light"])
    assert guard["tag:lpga"] == GuardTerm(op="eq", values=["present"])
    assert guard["tag:secondary_cta"] == GuardTerm(op="eq", values=["present"])


def test_normalize_guard_gated_gate_shape() -> None:
    guard = normalize_guard({"kind": "content_tag", "value": {"tag": "lpga"}})
    assert guard == {"tag:lpga": GuardTerm(op="eq", values=["present"])}


def test_normalize_guard_shorthand_when_mapping() -> None:
    guard = normalize_guard({"background_group": "dark", "breakpoint": "mobile"})
    assert guard["background_group"] == GuardTerm(op="eq", values=["dark"])
    assert guard["breakpoint"] == GuardTerm(op="eq", values=["mobile"])


def test_satisfiable_shared_axes_only() -> None:
    a = normalize_guard({"background_group": "light"})
    b = normalize_guard({"breakpoint": "mobile"})
    assert satisfiable(a, b)
    c = normalize_guard({"background_group": "dark"})
    assert not satisfiable(a, c)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ({"campaign": {"op": "eq", "values": []}}, {}),
        ({}, {"campaign": {"op": "in", "values": []}}),
        (
            {"campaign": {"op": "eq", "values": []}},
            {"background_group": "light"},
        ),
    ],
)
def test_satisfiable_empty_term_is_globally_false(
    left: dict[str, object],
    right: dict[str, object],
) -> None:
    a = normalize_guard(left)
    b = normalize_guard(right)
    assert not satisfiable(a, b)
    assert not satisfiable(b, a)


def test_conjunction_none_on_conflict() -> None:
    a = normalize_guard({"background_group": "light"})
    b = normalize_guard({"background_group": "dark"})
    assert conjunction(a, b) is None


def test_conjunction_associative_on_fixtures() -> None:
    a = normalize_guard({"background_group": "light"})
    b = normalize_guard({"breakpoint": "mobile"})
    c = normalize_guard({"campaign": "flip"})
    left = conjunction(conjunction(a, b) or {}, c)
    right = conjunction(a, conjunction(b, c) or {})
    assert left == right


def test_witness_deterministic_sorted_choice() -> None:
    guard = normalize_guard({"background_group": {"op": "in", "values": ["dark", "light"]}})
    domains = {"background_group": ["light", "dark"]}
    first = witness(guard, domains)
    second = witness(guard, domains)
    assert first == second == {"background_group": "dark"}


def test_is_satisfiable_unknown_domain_is_unsat_when_bound() -> None:
    guard = normalize_guard({"campaign": "retired_campaign"})
    domains = {"campaign": ["none", "flip_the_script"]}
    assert not is_satisfiable(guard, domains)


def test_tag_axes_truth_table() -> None:
    guard = normalize_guard({"content_tag": {"op": "has_tag", "values": ["lpga"]}})
    assert is_satisfiable(guard, {"tag:lpga": ["absent", "present"]})
    assert witness(guard, {"tag:lpga": ["absent", "present"]}) == {"tag:lpga": "present"}
    present_only = normalize_guard({"tag:lpga": "present"})
    assert is_satisfiable(present_only, {"tag:lpga": ["present"]})
    assert not is_satisfiable(present_only, {"tag:lpga": []})


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ({"background_group": "light"}, {"background_group": "light"}, True),
        ({"background_group": "light"}, {"background_group": "dark"}, False),
        ({"tag:lpga": "present"}, {"tag:lpga": "present"}, True),
        ({"tag:lpga": "present"}, {"tag:lpga": "absent"}, False),
    ],
)
def test_satisfiable_symmetric_truth_table(left: dict[str, str], right: dict[str, str], expected: bool) -> None:
    a = normalize_guard(left)
    b = normalize_guard(right)
    assert satisfiable(a, b) is expected
    assert satisfiable(b, a) is expected


def test_guard_algebra_determinism_twice() -> None:
    source = [
        Predicate(kind="campaign", value="flip_the_script"),
        Predicate(kind="content_tag", value={"tag": "lpga"}),
    ]
    first = json.dumps(normalize_guard(source), sort_keys=True, default=str)
    second = json.dumps(normalize_guard(source), sort_keys=True, default=str)
    assert first == second
