"""WP-06 S1 unit classifier tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from indexing_v2.contracts import RunVariant, SourceUnit, UnitLabel, UnitLabelName, read_jsonl
from indexing_v2.extraction.classify_units import (
    STAGE_VERSION,
    ClassifierResponseError,
    _DIM_RE,
    _MULTI_RADIUS_RE,
    _batch_context_units,
    _merge_label,
    _parse_batch_response,
    _target_batches,
    _units_by_doc_ref,
    classify_units,
    heuristic_labels,
    run_classifier,
)
from indexing_v2.extraction.prompts import load_prompt
from indexing_v2.extraction.runner import CacheContext, complete_json_cached
from shared.llm import Usage
from tests.fakes import FIXTURE_ROOT, FakeLLM, MINIBIBLE_BRAND


def _unit(
    unit_id: str,
    *,
    text: str,
    kind: str = "sentence",
    doc_ref: str = "brand_foundation[0]",
    ordinal: int = 0,
) -> SourceUnit:
    return SourceUnit(
        unit_id=unit_id,
        brand_id=MINIBIBLE_BRAND,
        doc_ref=doc_ref,
        ordinal=ordinal,
        start=0,
        end=len(text),
        kind=kind,  # type: ignore[arg-type]
        text=text,
    )


@pytest.fixture
def minibible_units() -> list[SourceUnit]:
    return read_jsonl(FIXTURE_ROOT / "expected" / "units.jsonl", SourceUnit)


@pytest.fixture
def expected_labels() -> list[UnitLabel]:
    return read_jsonl(FIXTURE_ROOT / "expected" / "labels.jsonl", UnitLabel)


def test_stage_version() -> None:
    assert STAGE_VERSION == "1.0.0"


@pytest.mark.parametrize(
    ("text", "kind", "expected"),
    [
        ("Primary Green #01A47E is approved.\n", "sentence", ["value"]),
        ("Opacity is 80%.\n", "sentence", ["value"]),
        ("Body text uses 18px on desktop and 16px on mobile.\n", "sentence", ["conditional", "value"]),
        ("Contrast ratio must be 5:1 on light backgrounds.\n", "sentence", ["conditional", "normative", "value"]),
        ("Fill rgb(1, 164, 126) for hero backgrounds.\n", "sentence", ["value"]),
        ("Buttons use font-weight: 700 on desktop.\n", "sentence", ["conditional", "value"]),
        ("Corner radius 49.52px 1.76px 40px 1.76px on cards.\n", "sentence", ["value"]),
        ("Corner radius 10% 20% 30% 40%.\n", "sentence", ["value"]),
        ("Headlines must use sentence case only.\n", "sentence", ["normative"]),
        (
            'When campaign is "retired_campaign", use the legacy hero gradient layout.\n',
            "sentence",
            [],
        ),
        (
            'The following sentence must appear exactly as written: "Ask your doctor about treatment options appropriate for you."\n',
            "sentence",
            ["normative", "verbatim"],
        ),
        ("## Color Palette\n", "heading", ["noise", "structural"]),
        ("\n", "blank", ["noise"]),
    ],
)
def test_heuristic_labels_patterns(text: str, kind: str, expected: list[str]) -> None:
    unit = _unit("u_test", text=text, kind=kind)
    assert heuristic_labels(unit) == expected


def test_heuristic_labels_sorted_deduped() -> None:
    unit = _unit(
        "u_test",
        text="On dark backgrounds, primary CTA fill must be white (#FFFFFF).\n",
    )
    assert heuristic_labels(unit) == ["conditional", "normative", "value"]


def test_percentage_regex_end_guards() -> None:
    assert _DIM_RE.search("Opacity is 80%.")
    assert _MULTI_RADIUS_RE.search("Corner radius: 10% 20% 30% 40%.")


def test_merge_preserves_locked_labels_and_sorts() -> None:
    unit = _unit("u_test", text="Primary Green #01A47E\n")
    locked = ["value"]
    merged = _merge_label(
        unit,
        locked,
        {
            "labels": ["noise"],
            "expected_yield": ["token_primitive"],
            "required": False,
            "confidence": 0.2,
        },
    )
    assert merged.labels == ["noise", "value"]
    assert merged.heuristic_locked == ["value"]
    assert merged.required is True


def test_merge_forces_required_false_for_blank() -> None:
    unit = _unit("\n", kind="blank", text="\n")
    merged = _merge_label(
        unit,
        ["noise"],
        {"labels": ["noise"], "expected_yield": [], "required": True, "confidence": 0.9},
    )
    assert merged.required is False


def test_parse_batch_response_rejects_missing_duplicate_unknown() -> None:
    targets = {"u_a", "u_b"}
    with pytest.raises(ClassifierResponseError) as missing:
        _parse_batch_response({"units": []}, target_ids=targets, batch_index=3)
    assert missing.value.batch_index == 3
    assert missing.value.unit_id == "u_a"

    with pytest.raises(ClassifierResponseError):
        _parse_batch_response(
            {"units": [{"unit_id": "u_a"}, {"unit_id": "u_a"}]},
            target_ids={"u_a"},
            batch_index=0,
        )

    with pytest.raises(ClassifierResponseError):
        _parse_batch_response(
            {"units": [{"unit_id": "u_other"}]},
            target_ids={"u_a"},
            batch_index=1,
        )


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("labels", "value"),
        ("expected_yield", "rule"),
        ("required", "false"),
        ("confidence", 1.5),
    ],
)
def test_merge_rejects_invalid_row_values_with_context(field: str, invalid: Any) -> None:
    unit = _unit("u_test", text="hello\n")
    row: dict[str, Any] = {
        "labels": [],
        "expected_yield": [],
        "required": False,
        "confidence": 0.5,
    }
    row[field] = invalid
    with pytest.raises(ClassifierResponseError) as error:
        _merge_label(unit, [], row, batch_index=7)
    assert error.value.batch_index == 7
    assert error.value.unit_id == "u_test"
    assert "batch 7" in str(error.value)
    assert "u_test" in str(error.value)


@pytest.mark.parametrize("confidence", [float("nan"), float("inf"), float("-inf")])
def test_merge_rejects_non_finite_confidence(confidence: float) -> None:
    unit = _unit("u_test", text="hello\n")
    with pytest.raises(ClassifierResponseError) as error:
        _merge_label(
            unit,
            [],
            {
                "labels": [],
                "expected_yield": [],
                "required": False,
                "confidence": confidence,
            },
            batch_index=2,
        )
    assert error.value.batch_index == 2
    assert error.value.unit_id == "u_test"


@pytest.mark.parametrize(
    ("unit", "locked", "required"),
    [
        (_unit("u_locked", text="Color #fff\n"), ["value"], "false"),
        (_unit("u_blank", kind="blank", text="\n"), ["noise"], 1),
    ],
)
def test_required_type_validates_before_forcing(
    unit: SourceUnit,
    locked: list[UnitLabelName],
    required: Any,
) -> None:
    with pytest.raises(ClassifierResponseError) as error:
        _merge_label(
            unit,
            locked,
            {
                "labels": [],
                "expected_yield": [],
                "required": required,
                "confidence": 0.5,
            },
            batch_index=4,
        )
    assert error.value.batch_index == 4
    assert error.value.unit_id == unit.unit_id


def test_neighbor_window_stays_within_doc_ref() -> None:
    units = [
        _unit("u_a", text="a\n", doc_ref="blob_a[0]", ordinal=0),
        _unit("u_b", text="b\n", doc_ref="blob_a[0]", ordinal=1),
        _unit("u_c", text="c\n", doc_ref="blob_b[0]", ordinal=0),
    ]
    grouped = _units_by_doc_ref(units)
    context = _batch_context_units([units[1]], grouped)
    assert {unit.unit_id for unit in context} == {"u_a", "u_b"}


def test_target_batches_split_above_forty() -> None:
    units = [
        _unit(f"u_{index:04d}", text=f"{index}\n", ordinal=index)
        for index in range(45)
    ]
    batches = _target_batches(units, 40)
    assert len(batches) == 2
    assert len(batches[0]) == 40
    assert len(batches[1]) == 5


@pytest.mark.asyncio
async def test_invalid_second_batch_row_reports_batch_and_unit(tmp_path: Path) -> None:
    units = [_unit(f"u_{index:04d}", text="hello\n", ordinal=index) for index in range(41)]

    class InvalidSecondBatchLLM:
        def __init__(self) -> None:
            self.calls = 0

        async def complete_json(
            self,
            model: str,
            system: str,
            user: str,
            max_tokens: int = 16_000,
            usage: Usage | None = None,
            *,
            prompt_name: str,
            cache_key: str | None = None,
        ) -> dict[str, Any]:
            del model, system, max_tokens, usage, prompt_name, cache_key
            self.calls += 1
            rows = []
            for line in user.splitlines():
                if " TARGET" not in line:
                    continue
                unit_id = line.split("]", 1)[0].removeprefix("[")
                rows.append(
                    {
                        "unit_id": unit_id,
                        "labels": [],
                        "expected_yield": [],
                        "required": 1 if unit_id == "u_0040" else False,
                        "confidence": 0.5,
                    }
                )
            return {"units": rows}

    client = InvalidSecondBatchLLM()
    with pytest.raises(ClassifierResponseError) as error:
        await classify_units(
            MINIBIBLE_BRAND,
            units,
            client=client,
            usage=Usage(),
            cache_root=tmp_path,
        )
    assert client.calls == 2
    assert error.value.batch_index == 1
    assert error.value.unit_id == "u_0040"


class AdversarialLLM:
    async def complete_json(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 16_000,
        usage: Usage | None = None,
        *,
        prompt_name: str,
        cache_key: str | None = None,
    ) -> dict[str, Any]:
        del model, system, max_tokens, prompt_name, cache_key
        if usage is not None:
            usage.add("fake", 1, 1)
        rows = []
        for line in user.splitlines():
            if " TARGET" not in line:
                continue
            unit_id = line.split("]", 1)[0].removeprefix("[")
            rows.append(
                {
                    "unit_id": unit_id,
                    "labels": ["noise"],
                    "expected_yield": [],
                    "required": False,
                    "confidence": 0.1,
                }
            )
        return {"units": rows}


@pytest.mark.asyncio
async def test_adversarial_llm_cannot_remove_locked_labels() -> None:
    units = [
        _unit("u_hex", text="Primary Green #01A47E\n"),
        _unit("u_norm", text="Headlines must use sentence case only.\n", ordinal=1),
    ]
    labels = await classify_units(
        MINIBIBLE_BRAND,
        units,
        client=AdversarialLLM(),
        usage=Usage(),
        batch_size=40,
    )
    by_id = {label.unit_id: label for label in labels}
    assert "value" in by_id["u_hex"].labels
    assert "normative" in by_id["u_norm"].labels
    assert by_id["u_hex"].heuristic_locked == ["value"]
    assert by_id["u_norm"].heuristic_locked == ["normative"]
    assert by_id["u_hex"].required is True


class RecordingLLM:
    def __init__(self) -> None:
        self.calls = 0

    async def complete_json(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 16_000,
        usage: Usage | None = None,
        *,
        prompt_name: str,
        cache_key: str | None = None,
    ) -> dict[str, Any]:
        del model, system, user, max_tokens, prompt_name, cache_key
        self.calls += 1
        if usage is not None:
            usage.add("fake", 5, 5)
        return {
            "units": [
                {
                    "unit_id": "u_only",
                    "labels": [],
                    "expected_yield": [],
                    "required": False,
                    "confidence": 0.5,
                }
            ]
        }


@pytest.mark.asyncio
async def test_complete_json_cached_hit_skips_second_call(tmp_path: Path) -> None:
    client = RecordingLLM()
    usage = Usage()
    variant = RunVariant(run_id="classify", model="fake", temperature=0.0, replicate=0)
    template = load_prompt("unit_classifier")
    ctx = CacheContext(
        brand=MINIBIBLE_BRAND,
        variant=variant,
        prompt_name="unit_classifier",
        template=template,
        content_hash="",
        cache_root=tmp_path,
    )
    rendered = template.render(brand=MINIBIBLE_BRAND, units="[u_only] (sentence) TARGET hello\n")
    first = await complete_json_cached(client, ctx, rendered.system, rendered.user, usage, force=True)
    second = await complete_json_cached(client, ctx, rendered.system, rendered.user, usage)
    assert first == second
    assert client.calls == 1
    assert usage.llm_calls == 1


@pytest.mark.asyncio
async def test_classify_units_is_deterministic_offline(minibible_units: list[SourceUnit]) -> None:
    class StaticLLM:
        async def complete_json(
            self,
            model: str,
            system: str,
            user: str,
            max_tokens: int = 16_000,
            usage: Usage | None = None,
            *,
            prompt_name: str,
            cache_key: str | None = None,
        ) -> dict[str, Any]:
            del model, system, max_tokens, prompt_name, cache_key
            rows = []
            for line in user.splitlines():
                if " TARGET" not in line:
                    continue
                unit_id = line.split("]", 1)[0].removeprefix("[")
                rows.append(
                    {
                        "unit_id": unit_id,
                        "labels": [],
                        "expected_yield": [],
                        "required": False,
                        "confidence": 0.5,
                    }
                )
            return {"units": rows}

    usage_a = Usage()
    usage_b = Usage()
    first = await classify_units(MINIBIBLE_BRAND, minibible_units, client=StaticLLM(), usage=usage_a)
    second = await classify_units(MINIBIBLE_BRAND, minibible_units, client=StaticLLM(), usage=usage_b)
    assert first == second
    assert [label.unit_id for label in first] == [unit.unit_id for unit in sorted(minibible_units, key=lambda u: (u.doc_ref, u.ordinal))]


def test_heuristic_locked_matches_fixture_where_pure_heuristic(
    minibible_units: list[SourceUnit],
    expected_labels: list[UnitLabel],
) -> None:
    expected_by_id = {label.unit_id: label for label in expected_labels}
    llm_only = {
        "u_brand_foundation_0_0046",
        "u_brand_foundation_0_0048",
        "u_layout_constraints_0_0012",
        "u_layout_constraints_0_0026",
    }
    for unit in minibible_units:
        if unit.unit_id in llm_only:
            continue
        locked = heuristic_labels(unit)
        expected = expected_by_id[unit.unit_id]
        if locked or expected.heuristic_locked:
            assert locked == expected.heuristic_locked, unit.unit_id


@pytest.mark.asyncio
async def test_run_classifier_writes_sorted_jsonl(tmp_path: Path) -> None:
    units = [
        _unit("u_brand_foundation_0_0004", text="Primary Green #01A47E\n"),
        _unit("u_brand_foundation_0_0022", text="Headlines must use sentence case only.\n", ordinal=1),
    ]
    labels = await run_classifier(
        MINIBIBLE_BRAND,
        units,
        tmp_path,
        client=FakeLLM(),
        usage=Usage(),
    )
    path = tmp_path / "unit_labels.jsonl"
    assert path.is_file()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows == [label.model_dump(mode="json") for label in labels]
    assert [row["unit_id"] for row in rows] == [label.unit_id for label in labels]


@pytest.mark.asyncio
async def test_fake_llm_fixture_subset_merges(minibible_units: list[SourceUnit]) -> None:
    subset = [unit for unit in minibible_units if unit.unit_id in {"u_brand_foundation_0_0004", "u_brand_foundation_0_0022"}]
    labels = await classify_units(MINIBIBLE_BRAND, subset, client=FakeLLM(), usage=Usage())
    by_id = {label.unit_id: label for label in labels}
    assert by_id["u_brand_foundation_0_0004"].labels == ["value"]
    assert by_id["u_brand_foundation_0_0022"].labels == ["normative"]
    assert by_id["u_brand_foundation_0_0004"].expected_yield == ["token_primitive"]
    assert by_id["u_brand_foundation_0_0022"].expected_yield == ["rule"]
