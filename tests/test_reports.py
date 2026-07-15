"""Golden and unit tests for WP-17 pure report renderers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from indexing_v2.consistency.report import ConflictsReportInput, render_conflicts_report
from indexing_v2.contracts import (
    Conflict,
    CoverageReport,
    Finding,
    GuardTerm,
    SourceUnit,
)
from indexing_v2.reports import (
    CoverageReportInput,
    CriticReportInput,
    ManifestAcceptance,
    ManifestInputs,
    ManifestMetrics,
    ManifestReportInput,
    escape_md_cell,
    render_cascade_schema,
    render_coverage_report,
    render_critic_findings,
    render_manifest_summary,
    truncate_text,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "reports"
EXPECTED = FIXTURE_ROOT / "expected"


def _load_json(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _assert_deterministic(render_fn, payload) -> str:
    first = render_fn(payload)
    second = render_fn(payload)
    assert first == second
    return first


def test_coverage_report_golden_matches_fixture() -> None:
    payload = CoverageReportInput.model_validate(_load_json("coverage_input.json"))
    rendered = _assert_deterministic(render_coverage_report, payload)
    expected = (EXPECTED / "coverage_report.md").read_text(encoding="utf-8")
    assert rendered == expected


def test_conflicts_report_golden_matches_fixture() -> None:
    payload = ConflictsReportInput.model_validate(_load_json("conflicts_input.json"))
    rendered = _assert_deterministic(render_conflicts_report, payload)
    expected = (EXPECTED / "conflicts_report.md").read_text(encoding="utf-8")
    assert rendered == expected


@pytest.mark.parametrize(
    ("length", "expected_len"),
    [
        (159, 159),
        (160, 160),
        (161, 160),
    ],
)
def test_truncate_text_ascii_boundaries(length: int, expected_len: int) -> None:
    text = "x" * length
    result = truncate_text(text)
    assert len(result) == expected_len
    if length > 160:
        assert result.endswith("...")
        assert result == text[:157] + "..."


def test_truncate_text_unicode_boundary() -> None:
    text = "café☕" * 40
    result = truncate_text(text)
    assert len(result) == 160
    assert result.endswith("...")


def test_escape_md_cell_handles_pipes_and_newlines() -> None:
    assert escape_md_cell("a|b\nc") == "a\\|b c"


def test_coverage_groups_unclaimed_by_blob_and_truncates() -> None:
    long_text = "z" * 200
    payload = CoverageReportInput(
        report=CoverageReport(
            brand="b",
            rounds=0,
            value_coverage=0.0,
            normative_coverage=0.0,
            verbatim_coverage=0.0,
            per_blob={},
            unclaimed_unit_ids=["u1"],
            over_claimed_unit_ids=[],
            orphan_entity_ids=[],
            rows=[],
        ),
        source_units={
            "u1": SourceUnit(
                unit_id="u1",
                brand_id="b",
                doc_ref="blob[0]",
                ordinal=0,
                start=0,
                end=1,
                kind="sentence",
                text=long_text,
            )
        },
    )
    rendered = render_coverage_report(payload)
    assert "### blob[0]" in rendered
    assert truncate_text(long_text) in rendered
    assert len(truncate_text(long_text)) == 160


def test_queue_counts_include_all_statuses() -> None:
    payload = CoverageReportInput.model_validate(_load_json("coverage_input.json"))
    rendered = render_coverage_report(payload)
    assert "| unclaimed_unit | 1 | 0 | 0 |" in rendered
    assert "| unverified_value | 0 | 1 | 0 |" in rendered
    assert "| over_claimed | 0 | 0 | 1 |" in rendered
    assert "| conflict | 0 | 1 | 0 |" in rendered


def test_conflicts_witness_requires_domains() -> None:
    conflict = Conflict(
        kind="hard_hard",
        element_path="x",
        a_id="a",
        b_id="b",
        overlap_guard={"background_group": GuardTerm(op="eq", values=["dark"])},
        detail="detail",
    )
    without = render_conflicts_report(ConflictsReportInput(conflicts=[conflict]))
    assert "(witness unavailable — supply domains)" in without
    with_domains = render_conflicts_report(
        ConflictsReportInput(
            conflicts=[conflict],
            domains={"background_group": ["dark", "light"]},
        )
    )
    assert '"background_group": "dark"' in with_domains


def test_critic_findings_grouped_by_resolution_and_severity() -> None:
    payload = CriticReportInput(
        findings=[
            Finding(
                finding_id="f_open_major",
                round=1,
                finding_type="omission",
                severity="major",
                target_entity_id="tok_a",
                description="missing token",
            ),
            Finding(
                finding_id="f_applied_minor",
                round=1,
                finding_type="other",
                severity="minor",
                target_entity_id="tok_b",
                description="fixed",
                resolution="applied",
            ),
        ]
    )
    rendered = _assert_deterministic(render_critic_findings, payload)
    assert rendered.index("## open") < rendered.index("## applied")
    assert rendered.index("### major") < rendered.index("## applied")
    assert "f_open_major" in rendered and "tok_a" in rendered


def test_manifest_summary_shows_invariants_queues_ratchet() -> None:
    payload = ManifestReportInput(
        brand="minibible",
        built_at="2026-07-14T00:00:00Z",
        inputs=ManifestInputs(bible_hash="abc123"),
        metrics=ManifestMetrics(
            units=10,
            required_units=8,
            coverage={"value": 0.9},
            consistency={"hard_hard": 1},
        ),
        acceptance=ManifestAcceptance(
            invariants={"verbatim_integrity": "pass"},
            queues={"conflict": {"open": 0, "waived": 1, "deferred": 0}},
            telemetry_deltas={"coverage.value": "+0.01"},
            ratchet="pass",
        ),
    )
    rendered = _assert_deterministic(render_manifest_summary, payload)
    assert "verbatim_integrity: pass" in rendered
    assert "| conflict | 0 | 1 | 0 |" in rendered
    assert "ratchet" in rendered
    assert "0.9" in rendered


def test_render_cascade_schema_is_deterministic() -> None:
    first = render_cascade_schema()
    second = render_cascade_schema()
    assert first == second
    assert "contexts.json" in first and "get_sheet" in first


def test_renderers_do_not_write_files(monkeypatch: pytest.MonkeyPatch) -> None:
    coverage = CoverageReportInput.model_validate(_load_json("coverage_input.json"))
    conflicts = ConflictsReportInput.model_validate(_load_json("conflicts_input.json"))

    def fail_write(*_args, **_kwargs):
        raise AssertionError("renderer attempted to write a file")

    monkeypatch.setattr(Path, "write_text", fail_write)
    monkeypatch.setattr(Path, "open", fail_write)
    render_coverage_report(coverage)
    render_conflicts_report(conflicts)
    render_critic_findings(CriticReportInput(findings=[]))
    render_manifest_summary(
        ManifestReportInput(brand="b", inputs=ManifestInputs(bible_hash="h"))
    )
    render_cascade_schema()
