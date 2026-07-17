"""WP-16 build_kb v2 driver tests (FakeLLM, no network)."""

from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from indexing_v2 import build_kb as build_kb_module
from indexing_v2.build_kb import (
    BuildOptions,
    BuildOutcome,
    build_brand,
    parse_stage_selection,
    stable_built_at,
)
from indexing_v2.contracts import (
    Conflict,
    Disposition,
    SourceUnit,
    TriageItem,
    read_jsonl,
)
from indexing_v2.extraction.ledger import (
    append_triage_items,
    triage_key_conflict,
    triage_key_global_unsat,
    triage_key_unclaimed,
)
from shared import config as shared_config
from shared.llm import Usage
from tests.fakes import (
    FIXTURE_ROOT,
    FakeLLM,
    MINIBIBLE_BRAND,
    UnexpectedLLMCallError,
)

FIXTURE_LLM_ROOT = FIXTURE_ROOT / "llm"


@pytest.fixture
def minibible_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    kb_root = tmp_path / "kb"
    monkeypatch.setattr(shared_config, "KB_ROOT", kb_root)
    monkeypatch.setitem(
        shared_config.DESIGN_BIBLES,
        MINIBIBLE_BRAND,
        FIXTURE_ROOT / "bible.json",
    )
    monkeypatch.setitem(shared_config.TEMPLATE_LIBRARIES, MINIBIBLE_BRAND, None)
    return kb_root


@pytest.fixture
def cache_root(tmp_path: Path) -> Path:
    return tmp_path / "llm-cache"


class RepeatingFakeLLM(FakeLLM):
    """Reuse each prompt's fixtures in order for independent K=3/gap runs."""

    def _resolve_path(self, prompt_name: str, cache_key: str | None, seq: int) -> Path:
        try:
            return super()._resolve_path(prompt_name, cache_key, seq)
        except UnexpectedLLMCallError:
            ordered = sorted((self.fixture_root / prompt_name).glob("*.json"))
            if not ordered:
                raise
            return ordered[(seq - 1) % len(ordered)]

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
    ) -> Any:
        if prompt_name not in {"rules_cluster", "gap_patch"}:
            return await super().complete_json(
                model,
                system,
                user,
                max_tokens=max_tokens,
                usage=usage,
                prompt_name=prompt_name,
                cache_key=cache_key,
            )
        self._record(
            prompt_name=prompt_name,
            cache_key=cache_key,
            model=model,
            system=system,
            user=user,
        )
        self._account(usage, model)
        if prompt_name == "rules_cluster":
            fixture = (
                "layout_constraints_001.json"
                if "layout_constraints[0]" in user
                else "brand_foundation_001.json"
            )
        else:
            fixture = (
                "002.json"
                if "layout_constraints[0]" in user
                else "001.json"
            )
        return self._load_fixture(self.fixture_root / prompt_name / fixture)


@pytest.fixture
def fake_client() -> RepeatingFakeLLM:
    return RepeatingFakeLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND)


async def _noop_summarize(brand: str, usage: Usage) -> None:
    del brand, usage


async def _build(
    options: BuildOptions,
    client: FakeLLM,
    cache_root: Path,
    *,
    summarize_embed: Any = None,
) -> Any:
    return await build_brand(
        MINIBIBLE_BRAND,
        options,
        client=client,
        usage=Usage(),
        summarize_embed=summarize_embed,
        cache_root=cache_root,
    )


def _default_options(**overrides: Any) -> BuildOptions:
    base = {
        "brands": [MINIBIBLE_BRAND],
        "concurrency": 2,
        "skip_summarize_embed": True,
        "no_critic": True,
        "no_gaps": True,
        "no_linker": True,
    }
    base.update(overrides)
    return BuildOptions(**base)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        out[path.relative_to(root).as_posix()] = path.read_bytes()
    return out


def _append_human_dispositions(path: Path, items: list[TriageItem]) -> None:
    """Simulate reviewed append-only entries; the pipeline only appends opens."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for item in items:
            handle.write(
                json.dumps(
                    item.model_dump(mode="json"),
                    sort_keys=True,
                    ensure_ascii=False,
                )
                + "\n"
            )


def _waive_current_triage(path: Path) -> None:
    current = read_jsonl(path, TriageItem)
    _append_human_dispositions(
        path,
        [
            item.model_copy(
                update={
                    "disposition": Disposition(
                        status="waived",
                        note="accepted for isolated acceptance test",
                    )
                }
            )
            for item in current
        ],
    )


def _seed_cp4_waivers(brand_root: Path) -> None:
    units = read_jsonl(
        FIXTURE_ROOT / "expected" / "units.jsonl",
        SourceUnit,
    )
    illustrative = next(
        unit
        for unit in units
        if unit.unit_id == "u_brand_foundation_0_0048"
    )
    core = [
        "rule_minibible_cta_max_one",
        "rule_minibible_cta_min_two_touchpoints",
    ]
    contexts = [
        "audience=dtp_patient;campaign=none;surface=email;tags=lpga;theme=none",
        "audience=dtp_patient;campaign=none;surface=email;tags=none;theme=none",
    ]
    color_conflict = Conflict(
        kind="hard_hard",
        element_path="cta.button.fill",
        a_id="rule_minibible_cta_fill_green",
        b_id="rule_minibible_cta_fill_orange",
        overlap_guard={},
        detail="intentional Plant 8 color contradiction",
    )
    waivers = [
        TriageItem(
            queue="unclaimed_unit",
            key=triage_key_unclaimed(illustrative.doc_ref, illustrative.text),
            subject_id=illustrative.unit_id,
            context="illustrative example, explicitly not a requirement",
            disposition=Disposition(
                status="waived",
                note="Plant 7 is illustrative-only source text",
            ),
        ),
        *[
            TriageItem(
                queue="conflict",
                key=triage_key_global_unsat(context, core),
                subject_id=context,
                context="intentional Plant 8 contradiction",
                disposition=Disposition(
                    status="waived",
                    note="Plant 8 intentionally exercises SMT contradiction reporting",
                ),
            )
            for context in contexts
        ],
        TriageItem(
            queue="conflict",
            key=triage_key_conflict(color_conflict),
            subject_id=color_conflict.a_id,
            context=color_conflict.detail,
            disposition=Disposition(
                status="waived",
                note="Plant 8 intentionally exercises pairwise conflict reporting",
            ),
        ),
    ]
    _append_human_dispositions(
        brand_root / "review" / "triage.jsonl",
        waivers,
    )


def test_parse_stage_range_and_subset() -> None:
    assert parse_stage_selection(stages=["s0..s2"], from_stage=None) == ["s0", "s1", "s2"]
    assert parse_stage_selection(stages=["s4", "s6"], from_stage=None) == ["s4", "s6"]
    assert parse_stage_selection(stages=None, from_stage="s6") == [
        "s6",
        "s6b",
        "s7",
        "s8",
        "s9",
        "s10",
        "s11",
    ]
    with pytest.raises(ValueError, match="unknown stage"):
        parse_stage_selection(stages=["s99"], from_stage=None)
    with pytest.raises(ValueError, match="cannot combine"):
        parse_stage_selection(stages=["s0"], from_stage="s1")


def test_cli_rejects_nonpositive_concurrency() -> None:
    with pytest.raises(ValueError, match="concurrency must be positive"):
        BuildOptions(brands=[MINIBIBLE_BRAND], concurrency=0)


@pytest.mark.asyncio
async def test_no_ensemble_uses_single_run(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options(no_ensemble=True, stages=frozenset({"s0", "s1", "s2", "s3", "s4"}))
    await _build(options, fake_client, cache_root)
    run_dirs = list((minibible_env / MINIBIBLE_BRAND / "_work" / "runs").iterdir())
    assert len(run_dirs) == 1
    assert run_dirs[0].name == "r0"


@pytest.mark.asyncio
async def test_two_phase_freezes_one_catalog_across_runs(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RULE_NAV_TWO_PHASE", "1")
    options = _default_options(stages=frozenset({"s0", "s1", "s2"}))
    await _build(options, fake_client, cache_root)
    work = minibible_env / MINIBIBLE_BRAND / "_work"
    frozen = json.loads(
        (work / "catalog_frozen.json").read_text(encoding="utf-8")
    )
    assert frozen["hash"]
    primitive_runs = {
        (run_dir / "tokens_primitive.json").read_bytes()
        for run_dir in (work / "runs").iterdir()
    }
    semantic_runs = {
        (run_dir / "tokens_semantic.json").read_bytes()
        for run_dir in (work / "runs").iterdir()
    }
    assert len(primitive_runs) == len(semantic_runs) == 1


@pytest.mark.asyncio
async def test_no_critic_writes_explicit_skip(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options(no_critic=True, stages=frozenset({"s0", "s1", "s2", "s3", "s4", "s5"}))
    await _build(options, fake_client, cache_root)
    skipped = minibible_env / MINIBIBLE_BRAND / "_work" / "critic" / "skipped.json"
    assert skipped.is_file()
    payload = json.loads(skipped.read_text(encoding="utf-8"))
    assert payload["skipped"] is True


@pytest.mark.asyncio
async def test_resume_from_s6_rebuilds_s6_plus_only(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options(no_gaps=True)
    await _build(options, fake_client, cache_root)
    work = minibible_env / MINIBIBLE_BRAND / "_work"
    first_ledger = (work / "ledger.json").read_bytes()

    (work / "ledger.json").unlink()
    fake_client.reset()
    resume = _default_options(from_stage="s6", no_gaps=True)
    await _build(resume, fake_client, cache_root)
    assert (work / "ledger.json").read_bytes() == first_ledger
    assert not fake_client.calls()


@pytest.mark.asyncio
async def test_manifest_written_on_pass_and_fail(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options()
    outcome = await _build(options, fake_client, cache_root)
    manifest_path = minibible_env / MINIBIBLE_BRAND / "manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "2.0"
    assert manifest["acceptance"]["passed"] is outcome.acceptance_passed
    assert "stages" in manifest
    assert "inputs" in manifest


@pytest.mark.asyncio
async def test_strict_nonzero_on_open_triage(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options()
    await _build(options, fake_client, cache_root)
    triage_path = minibible_env / MINIBIBLE_BRAND / "review" / "triage.jsonl"
    append_triage_items(
        triage_path,
        [
            TriageItem(
                queue="unclaimed_unit",
                key="planted-open",
                subject_id="u_planted",
                context="test open item",
            )
        ],
    )
    strict = _default_options(strict=True, stages=frozenset({"s11"}))
    outcome = await _build(strict, fake_client, cache_root)
    assert outcome.exit_code == 1
    manifest = json.loads((minibible_env / MINIBIBLE_BRAND / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["acceptance"]["passed"] is False


@pytest.mark.asyncio
async def test_strict_zero_when_all_queues_dispositioned(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    # Isolate queue acceptance from S9's independently tested Class-A conflicts.
    options = _default_options(
        stages=frozenset({"s0", "s1", "s2", "s3", "s4", "s5", "s6", "s6b", "s7", "s8"})
    )
    await _build(options, fake_client, cache_root)
    triage_path = minibible_env / MINIBIBLE_BRAND / "review" / "triage.jsonl"
    _waive_current_triage(triage_path)
    strict = _default_options(strict=True, stages=frozenset({"s11"}))
    outcome = await _build(strict, fake_client, cache_root)
    assert outcome.exit_code == 0


@pytest.mark.asyncio
async def test_ratchet_skips_without_baseline(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options(ratchet=True)
    await _build(options, fake_client, cache_root)
    manifest = json.loads((minibible_env / MINIBIBLE_BRAND / "manifest.json").read_text(encoding="utf-8"))
    assert "skipped (no accepted baseline)" in manifest["acceptance"]["ratchet"]


@pytest.mark.asyncio
async def test_ratchet_fails_when_metrics_worsen(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options()
    await _build(options, fake_client, cache_root)
    manifest_path = minibible_env / MINIBIBLE_BRAND / "manifest.json"
    accepted = json.loads(manifest_path.read_text(encoding="utf-8"))
    accepted["metrics"]["coverage"]["value"] = 1.0
    atomic_path = minibible_env / MINIBIBLE_BRAND / "manifest.accepted.json"
    atomic_path.write_text(json.dumps(accepted, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ratchet = _default_options(ratchet=True, strict=True, stages=frozenset({"s11"}))
    outcome = await _build(ratchet, fake_client, cache_root)
    assert outcome.exit_code == 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["acceptance"]["ratchet"].startswith("fail")


@pytest.mark.asyncio
async def test_ratchet_ignores_informational_metric_increase(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    """An increase in a neutral/informational metric (unit counts, ensemble confidence
    buckets, etc.) must never gate ratchet -- only metrics with an explicit direction do."""
    options = _default_options()
    await _build(options, fake_client, cache_root)
    manifest_path = minibible_env / MINIBIBLE_BRAND / "manifest.json"
    accepted = json.loads(manifest_path.read_text(encoding="utf-8"))
    accepted["metrics"]["units"] = -1
    accepted["metrics"]["required_units"] = -1
    accepted["metrics"]["ensemble"]["high"] = -1
    accepted["metrics"]["critic"]["applied"] = -1
    accepted["metrics"]["cascade"]["contexts"] = -1
    atomic_path = minibible_env / MINIBIBLE_BRAND / "manifest.accepted.json"
    atomic_path.write_text(json.dumps(accepted, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # ponytail: check the ratchet field directly rather than the overall exit code --
    # a plain build can already have unrelated open triage, which is a separate invariant.
    ratchet = _default_options(ratchet=True, stages=frozenset({"s11"}))
    await _build(ratchet, fake_client, cache_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["acceptance"]["ratchet"] == "pass"


@pytest.mark.asyncio
async def test_ratchet_fails_when_lower_better_metric_worsens(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    """A genuine regression in a lower-is-better metric (quarantine) must still fail ratchet."""
    options = _default_options()
    await _build(options, fake_client, cache_root)
    manifest_path = minibible_env / MINIBIBLE_BRAND / "manifest.json"
    accepted = json.loads(manifest_path.read_text(encoding="utf-8"))
    accepted["metrics"]["verification"]["quarantined"] = -1
    accepted["metrics"]["verification"]["quarantine_rate"] = -1.0
    atomic_path = minibible_env / MINIBIBLE_BRAND / "manifest.accepted.json"
    atomic_path.write_text(json.dumps(accepted, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ratchet = _default_options(ratchet=True, stages=frozenset({"s11"}))
    await _build(ratchet, fake_client, cache_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["acceptance"]["ratchet"].startswith("fail")
    assert "verification.quarantined" in manifest["acceptance"]["ratchet"]


@pytest.mark.asyncio
async def test_telemetry_deltas_empty_without_comparable_baseline(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options()
    await _build(options, fake_client, cache_root)
    manifest = json.loads(
        (minibible_env / MINIBIBLE_BRAND / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["acceptance"]["telemetry_deltas"] == {}


@pytest.mark.asyncio
async def test_telemetry_deltas_signed_when_baseline_comparable(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options()
    await _build(options, fake_client, cache_root)
    manifest_path = minibible_env / MINIBIBLE_BRAND / "manifest.json"
    accepted = json.loads(manifest_path.read_text(encoding="utf-8"))
    accepted["metrics"]["units"] = accepted["metrics"]["units"] - 1
    atomic_path = minibible_env / MINIBIBLE_BRAND / "manifest.accepted.json"
    atomic_path.write_text(json.dumps(accepted, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rebuilt = _default_options(stages=frozenset({"s11"}))
    await _build(rebuilt, fake_client, cache_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["acceptance"]["telemetry_deltas"]["units"] == "+1"


@pytest.mark.asyncio
async def test_manifest_matches_reports_contract(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    """WP-16 item 3: the manifest must validate against WP-17's ManifestReportInput
    contract (indexing_v2.reports) with the exact §6.4 metric names/shapes."""
    from indexing_v2.reports import ManifestReportInput

    options = _default_options()
    await _build(options, fake_client, cache_root)
    manifest = json.loads(
        (minibible_env / MINIBIBLE_BRAND / "manifest.json").read_text(encoding="utf-8")
    )
    validated = ManifestReportInput.model_validate(manifest)
    assert validated.brand == MINIBIBLE_BRAND

    assert "required_units" in manifest["metrics"]
    assert "required" not in manifest["metrics"]
    assert set(manifest["metrics"]["verification"]) == {
        "value_verified_rate",
        "quarantined",
        "quarantine_rate",
    }
    assert "deferred_human" in manifest["metrics"]["critic"]
    assert "deferred" not in manifest["metrics"]["critic"]
    assert set(manifest["acceptance"]) >= {
        "invariants",
        "queues",
        "telemetry_deltas",
        "ratchet",
    }


@pytest.mark.asyncio
async def test_strict_nonzero_on_class_a_global_unsat(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    """WP-16 item 5: a planted class-A violation (SMT global UNSAT) must fail
    ``no_live_contradictions`` and make ``--strict`` exit nonzero -- not just open triage."""
    options = _default_options()
    await _build(options, fake_client, cache_root)
    smt_path = minibible_env / MINIBIBLE_BRAND / "analysis" / "smt.json"
    smt_payload = json.loads(smt_path.read_text(encoding="utf-8"))
    smt_payload["status"] = "completed"
    smt_payload["global_unsat"] = [
        {
            "schema_version": smt_payload.get("schema_version", "1.0"),
            "kind": "global_unsat",
            "context_key": "planted-context",
            "core": ["rule_planted"],
            "detail": "planted class-A violation for strict-mode regression test",
        }
    ]
    smt_path.write_text(json.dumps(smt_payload, sort_keys=True) + "\n", encoding="utf-8")

    strict = _default_options(strict=True, stages=frozenset({"s11"}))
    outcome = await _build(strict, fake_client, cache_root)
    assert outcome.exit_code == 1
    manifest = json.loads(
        (minibible_env / MINIBIBLE_BRAND / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["acceptance"]["invariants"]["no_live_contradictions"] == "fail"
    assert manifest["acceptance"]["passed"] is False


@pytest.mark.asyncio
async def test_strict_zero_when_class_a_global_unsat_is_waived(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    await _build(
        _default_options(
            stages=frozenset(
                {"s0", "s1", "s2", "s3", "s4", "s5", "s6", "s6b", "s7", "s8"}
            )
        ),
        fake_client,
        cache_root,
    )
    triage_path = minibible_env / MINIBIBLE_BRAND / "review" / "triage.jsonl"
    _waive_current_triage(triage_path)

    context_key = "planted-waived-context"
    core = ["rule_planted_a", "rule_planted_b"]
    analysis_dir = minibible_env / MINIBIBLE_BRAND / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "smt.json").write_text(
        json.dumps(
            {
                "schema_version": "2.0",
                "status": "completed",
                "context_results": [],
                "global_unsat": [
                    {
                        "schema_version": "2.0",
                        "kind": "global_unsat",
                        "context_key": context_key,
                        "core": core,
                        "detail": "planted waived contradiction",
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _append_human_dispositions(
        triage_path,
        [
            TriageItem(
                queue="conflict",
                key=triage_key_global_unsat(context_key, core),
                subject_id=context_key,
                context="planted waived contradiction",
                disposition=Disposition(
                    status="waived",
                    note="reviewed and accepted for this fixture",
                ),
            )
        ],
    )

    outcome = await _build(
        _default_options(
            strict=True,
            stages=frozenset({"s11"}),
        ),
        fake_client,
        cache_root,
    )
    assert outcome.exit_code == 0
    manifest = json.loads(
        (minibible_env / MINIBIBLE_BRAND / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["acceptance"]["invariants"]["no_live_contradictions"] == "pass"


@pytest.mark.asyncio
async def test_accept_baseline_snapshots_manifest(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    await _build(_default_options(), fake_client, cache_root)
    options = _default_options(accept_baseline=True, stages=frozenset({"s11"}))
    await _build(options, fake_client, cache_root)
    manifest = minibible_env / MINIBIBLE_BRAND / "manifest.json"
    accepted = minibible_env / MINIBIBLE_BRAND / "manifest.accepted.json"
    assert accepted.is_file()
    assert json.loads(accepted.read_text(encoding="utf-8")) == json.loads(
        manifest.read_text(encoding="utf-8")
    )


@pytest.mark.asyncio
async def test_two_invocations_are_byte_identical(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options()
    await _build(options, fake_client, cache_root)
    first = _tree_bytes(minibible_env / MINIBIBLE_BRAND)

    calls_before = len(fake_client.calls())
    await _build(options, fake_client, cache_root)
    second = _tree_bytes(minibible_env / MINIBIBLE_BRAND)
    assert first == second
    assert len(fake_client.calls()) == calls_before
    # WP-16 item 6: manifest_summary.md must be byte-identical too, and not force S8 to rerun.
    assert "review/manifest_summary.md" in first
    assert first["review/manifest_summary.md"] == second["review/manifest_summary.md"]


@pytest.mark.asyncio
async def test_golden_write_kb_rule_fields_compatible(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options(
        stages=frozenset(
            {"s0", "s1", "s2", "s3", "s4", "s5", "s6", "s6b", "s7", "s8"}
        )
    )
    await _build(options, fake_client, cache_root)
    golden_rule = json.loads(
        (FIXTURE_ROOT / "kb" / MINIBIBLE_BRAND / "rules" / "rule_minibible_sentence_case_headlines.json").read_text(
            encoding="utf-8"
        )
    )
    built_rule = json.loads(
        (
            minibible_env
            / MINIBIBLE_BRAND
            / "rules"
            / "rule_minibible_sentence_case_headlines.json"
        ).read_text(encoding="utf-8")
    )
    for field in (
        "id",
        "brand_id",
        "rule_class",
        "selector",
        "constraint_type",
        "effect",
        "hardness",
        "polarity",
        "scope",
        "rule_text",
        "source",
        "doc_ref",
        "status",
        "version",
    ):
        assert field in built_rule, field
    assert built_rule["id"] == golden_rule["id"]
    assert built_rule["rule_text"]


def test_built_at_is_stable_for_same_bible_hash() -> None:
    sample = "abc123deadbeef"
    assert stable_built_at(sample) == stable_built_at(sample)


@pytest.mark.asyncio
async def test_cli_main_async_wires_brands_and_options_to_build_brand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise the real ``main_async`` CLI wiring (parser -> BuildOptions -> build_brand)
    end to end, without touching the network or requiring API keys."""
    calls: list[tuple[str, BuildOptions]] = []

    async def fake_build_brand(
        brand: str,
        options: BuildOptions,
        *,
        client: Any,
        usage: Any = None,
        console: Any = None,
        summarize_embed: Any = None,
        cache_root: Any = None,
    ) -> BuildOutcome:
        del client, usage, console, summarize_embed, cache_root
        calls.append((brand, options))
        exit_code = 1 if brand == "ibsrela" else 0
        return BuildOutcome(
            brand=brand,
            exit_code=exit_code,
            acceptance_passed=exit_code == 0,
            manifest_path=Path("manifest.json"),
        )

    class _DummyClient:
        pass

    monkeypatch.setattr(build_kb_module, "build_brand", fake_build_brand)
    monkeypatch.setattr(shared_config, "require_keys", lambda *_: None)
    monkeypatch.setattr("indexing_v2.extraction.runner.SharedLLMClient", _DummyClient)

    exit_code = await build_kb_module.main_async(
        ["--brand", "lisraya", "ibsrela", "--no-critic", "--strict"]
    )

    assert exit_code == 1, "exit code must be the max of all per-brand exit codes"
    assert [brand for brand, _ in calls] == ["lisraya", "ibsrela"]
    assert all(options.no_critic and options.strict for _, options in calls)


@pytest.mark.asyncio
async def test_cli_main_async_propagates_zero_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_build_brand(brand: str, options: BuildOptions, **_: Any) -> BuildOutcome:
        calls.append(brand)
        return BuildOutcome(
            brand=brand,
            exit_code=0,
            acceptance_passed=True,
            manifest_path=Path("manifest.json"),
        )

    class _DummyClient:
        pass

    monkeypatch.setattr(build_kb_module, "build_brand", fake_build_brand)
    monkeypatch.setattr(shared_config, "require_keys", lambda *_: None)
    monkeypatch.setattr("indexing_v2.extraction.runner.SharedLLMClient", _DummyClient)

    exit_code = await build_kb_module.main_async(["--brand", "lisraya"])
    assert exit_code == 0
    assert calls == ["lisraya"]


@pytest.mark.asyncio
async def test_bible_change_invalidates_s0(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    del minibible_env
    bible_path = tmp_path / "bible.json"
    shutil.copyfile(FIXTURE_ROOT / "bible.json", bible_path)
    monkeypatch.setitem(shared_config.DESIGN_BIBLES, MINIBIBLE_BRAND, bible_path)
    options = _default_options(stages=frozenset({"s0"}))
    await _build(options, fake_client, cache_root)

    original = build_kb_module._STAGE_RUNNERS["s0"]
    calls = 0

    async def tracked(ctx: Any) -> None:
        nonlocal calls
        calls += 1
        await original(ctx)

    monkeypatch.setitem(build_kb_module._STAGE_RUNNERS, "s0", tracked)
    payload = json.loads(bible_path.read_text(encoding="utf-8"))
    payload["website"]["brand_foundation"][0] += "\nNew source sentence."
    bible_path.write_text(json.dumps(payload), encoding="utf-8")
    await _build(options, fake_client, cache_root)
    assert calls == 1


@pytest.mark.asyncio
async def test_prior_stage_version_mismatch_reruns_stage(
    monkeypatch: pytest.MonkeyPatch,
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options(stages=frozenset({"s0"}))
    await _build(options, fake_client, cache_root)
    state_path = minibible_env / MINIBIBLE_BRAND / "_work" / "stage_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["stages"]["s0"]["version"] = "stale-version"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    original = build_kb_module._STAGE_RUNNERS["s0"]
    calls = 0

    async def tracked(ctx: Any) -> None:
        nonlocal calls
        calls += 1
        await original(ctx)

    monkeypatch.setitem(build_kb_module._STAGE_RUNNERS, "s0", tracked)
    await _build(options, fake_client, cache_root)
    assert calls == 1


@pytest.mark.asyncio
async def test_critic_toggle_invalidates_and_removes_stale_outputs(
    monkeypatch: pytest.MonkeyPatch,
    minibible_env: Path,
    fake_client: RepeatingFakeLLM,
    cache_root: Path,
) -> None:
    through_s5 = frozenset({"s0", "s1", "s2", "s3", "s4", "s5"})
    enabled = _default_options(
        stages=through_s5,
        no_critic=False,
        max_critic_rounds=1,
    )
    await _build(enabled, fake_client, cache_root)
    work_dir = minibible_env / MINIBIBLE_BRAND / "_work"
    critic_dir = work_dir / "critic"
    assert (work_dir / "findings.jsonl").is_file()
    assert (work_dir / "audit" / "patches.jsonl").is_file()
    assert (work_dir / "candidates" / "tokens.json").is_file()
    assert (critic_dir / "result.json").is_file()

    original = build_kb_module._STAGE_RUNNERS["s5"]
    calls = 0

    async def tracked(ctx: Any) -> None:
        nonlocal calls
        calls += 1
        await original(ctx)

    monkeypatch.setitem(build_kb_module._STAGE_RUNNERS, "s5", tracked)
    disabled = _default_options(stages=frozenset({"s5"}), no_critic=True)
    await _build(disabled, fake_client, cache_root)
    assert calls == 1
    assert (critic_dir / "skipped.json").is_file()
    assert not (work_dir / "findings.jsonl").exists()
    assert not (work_dir / "audit").exists()
    assert not (critic_dir / "result.json").exists()


@pytest.mark.asyncio
async def test_s4_cache_survives_s5_critic_mutating_shared_candidates(
    monkeypatch: pytest.MonkeyPatch,
    minibible_env: Path,
    fake_client: RepeatingFakeLLM,
    cache_root: Path,
) -> None:
    """WP-16 item 7: S5 legitimately overwrites work_dir/candidates in place; that must
    not make S4 look 'changed' and force a spurious rerun on the very next invocation."""
    through_s5 = frozenset({"s0", "s1", "s2", "s3", "s4", "s5"})
    enabled = _default_options(stages=through_s5, no_critic=False, max_critic_rounds=1)
    await _build(enabled, fake_client, cache_root)

    original = build_kb_module._STAGE_RUNNERS["s4"]
    calls = 0

    async def tracked(ctx: Any) -> None:
        nonlocal calls
        calls += 1
        await original(ctx)

    monkeypatch.setitem(build_kb_module._STAGE_RUNNERS, "s4", tracked)
    fake_client.reset()
    await _build(enabled, fake_client, cache_root)
    assert calls == 0


@pytest.mark.asyncio
async def test_s8_skips_unchanged_and_reruns_for_tampered_owned_output(
    monkeypatch: pytest.MonkeyPatch,
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    options = _default_options()
    await _build(options, fake_client, cache_root)
    original = build_kb_module._STAGE_RUNNERS["s8"]
    calls = 0

    async def tracked(ctx: Any) -> None:
        nonlocal calls
        calls += 1
        await original(ctx)

    monkeypatch.setitem(build_kb_module._STAGE_RUNNERS, "s8", tracked)
    await _build(options, fake_client, cache_root)
    assert calls == 0

    token_path = next(
        path
        for path in (minibible_env / MINIBIBLE_BRAND / "tokens").glob("*.json")
        if path.name != "_index.json"
    )
    token = json.loads(token_path.read_text(encoding="utf-8"))
    token["key"] = "tampered"
    token_path.write_text(json.dumps(token), encoding="utf-8")
    await _build(options, fake_client, cache_root)
    assert calls == 1


@pytest.mark.asyncio
async def test_s9_version_change_invalidates_s10(
    monkeypatch: pytest.MonkeyPatch,
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    del minibible_env
    options = _default_options()
    await _build(options, fake_client, cache_root)
    monkeypatch.setitem(
        build_kb_module._STAGE_REGISTRY,
        "s9",
        replace(build_kb_module._STAGE_REGISTRY["s9"], version="test-version"),
    )
    original = build_kb_module._STAGE_RUNNERS["s10"]
    calls = 0

    async def tracked(ctx: Any) -> None:
        nonlocal calls
        calls += 1
        await original(ctx)

    monkeypatch.setitem(build_kb_module._STAGE_RUNNERS, "s10", tracked)
    await _build(_default_options(from_stage="s9"), fake_client, cache_root)
    assert calls == 1


@pytest.mark.asyncio
async def test_s11_toggle_has_truthful_completion_artifact(
    monkeypatch: pytest.MonkeyPatch,
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    await _build(_default_options(), fake_client, cache_root)
    original = build_kb_module._STAGE_RUNNERS["s11"]
    calls = 0

    async def tracked(ctx: Any) -> None:
        nonlocal calls
        calls += 1
        await original(ctx)

    monkeypatch.setitem(build_kb_module._STAGE_RUNNERS, "s11", tracked)
    enabled = _default_options(
        stages=frozenset({"s11"}),
        skip_summarize_embed=False,
    )
    await _build(enabled, fake_client, cache_root, summarize_embed=_noop_summarize)
    completion_path = (
        minibible_env / MINIBIBLE_BRAND / "_work" / "summarize_embed.json"
    )
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    assert calls == 1
    assert completion["status"] == "completed"
    assert "rules_hash" in completion


@pytest.mark.asyncio
async def test_determinism_invariant_detects_same_input_divergence(
    minibible_env: Path,
    fake_client: FakeLLM,
    cache_root: Path,
) -> None:
    await _build(_default_options(), fake_client, cache_root)
    units_path = minibible_env / MINIBIBLE_BRAND / "_work" / "units.jsonl"
    rows = [json.loads(line) for line in units_path.read_text(encoding="utf-8").splitlines()]
    rows[0]["text"] += " tampered"
    units_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    await _build(
        _default_options(stages=frozenset({"s11"})),
        fake_client,
        cache_root,
    )
    manifest = json.loads(
        (minibible_env / MINIBIBLE_BRAND / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["acceptance"]["invariants"]["determinism"] == "fail"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_minibible_s0_through_s11(
    minibible_env: Path,
    fake_client: RepeatingFakeLLM,
    cache_root: Path,
) -> None:
    brand_root = minibible_env / MINIBIBLE_BRAND
    _seed_cp4_waivers(brand_root)
    options = _default_options(
        no_critic=False,
        no_gaps=False,
        skip_summarize_embed=False,
        strict=True,
        max_critic_rounds=1,
        max_gap_rounds=2,
    )
    outcome = await _build(
        options,
        fake_client,
        cache_root,
        summarize_embed=_noop_summarize,
    )
    work = brand_root / "_work"
    assert (work / "units.jsonl").is_file()
    assert (work / "unit_labels.jsonl").is_file()
    assert (work / "ensemble.json").is_file()
    assert (work / "ledger.json").is_file()
    assert (brand_root / "rules" / "_index.json").is_file()
    assert (brand_root / "analysis" / "conflicts.json").is_file()
    assert (brand_root / "cascade" / "contexts.json").is_file()
    assert (brand_root / "schema" / "cascade.md").is_file()
    assert (brand_root / "manifest.json").is_file()
    assert len(list((work / "runs").iterdir())) == 3

    # WP-16 item 7: S5 native artifact contract lives directly under _work, not
    # nested under _work/critic (only driver handoff files live there).
    assert (work / "findings.jsonl").is_file()
    assert (work / "audit" / "patches.jsonl").is_file()
    assert (work / "candidates" / "tokens.json").is_file()
    critic = json.loads((work / "critic" / "result.json").read_text(encoding="utf-8"))
    gap = json.loads((work / "gap_result.json").read_text(encoding="utf-8"))
    assert critic["rounds_completed"] == 1
    assert gap["rounds_run"] <= 2
    assert gap["coverage"]["unclaimed_unit_ids"] == [
        "u_brand_foundation_0_0048"
    ]
    assert {"critic_catalog", "critic_rules"} <= {
        call.prompt_name for call in fake_client.calls()
    }
    assert any(call.prompt_name == "gap_patch" for call in fake_client.calls())
    completion = json.loads(
        (work / "summarize_embed.json").read_text(encoding="utf-8")
    )
    assert completion["status"] == "completed"
    assert (brand_root / "review" / "conflicts.md").is_file()

    # WP-16 item 1: DTCG output lives at design_tokens/, not the legacy tokens_dtcg/.
    assert (brand_root / "design_tokens" / "_map.json").is_file()
    assert (brand_root / "design_tokens" / "tokens.base.json").is_file()
    assert not (brand_root / "tokens_dtcg").exists()

    # WP-16 item 2: full required S9 artifact set, with the renamed precedence log.
    assert (brand_root / "analysis" / "conflicts.json").is_file()
    assert (brand_root / "analysis" / "dead_rules.json").is_file()
    assert (brand_root / "analysis" / "precedence_log.json").is_file()
    assert (brand_root / "analysis" / "smt.json").is_file()
    assert not (brand_root / "analysis" / "precedence.json").exists()

    # WP-16 item 6: manifest summary is rendered from the validated manifest contract.
    assert (brand_root / "review" / "manifest_summary.md").is_file()

    units = read_jsonl(work / "units.jsonl", SourceUnit)
    assert units
    assert outcome.exit_code == 0
    manifest = json.loads((brand_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["acceptance"]["passed"] is True
    assert all(
        counts["open"] == 0
        for counts in manifest["acceptance"]["queues"].values()
    )

    first = _tree_bytes(brand_root)
    calls_before = len(fake_client.calls())
    second_outcome = await _build(
        options,
        fake_client,
        cache_root,
        summarize_embed=_noop_summarize,
    )
    assert second_outcome.exit_code == 0
    assert _tree_bytes(brand_root) == first
    assert len(fake_client.calls()) == calls_before
