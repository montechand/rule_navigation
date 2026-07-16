"""Pure markdown renderers for coverage, critic, manifest, and cascade schema docs (WP-17)."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from pydantic import BaseModel, Field

from indexing_v2.contracts import (
    SCHEMA_VERSION,
    SPECIFICITY_DOC,
    CoverageReport,
    Finding,
    SourceUnit,
    TriageItem,
    TriageQueue,
    stable_hash,
)

_MAX_UNIT_TEXT = 160
_TRIAGE_QUEUES: tuple[TriageQueue, ...] = (
    "unclaimed_unit",
    "unverified_value",
    "over_claimed",
    "conflict",
    "orphan_token",
    "needs_rule",
)
_SEVERITY_ORDER = ("critical", "major", "minor", "info")
_RESOLUTION_ORDER = (
    "open",
    "deferred_human",
    "rejected_verification",
    "rejected_mechanical",
    "applied",
)


def escape_md_cell(text: str) -> str:
    """Escape markdown table pipes and newlines for deterministic cells."""
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def truncate_text(text: str, max_len: int = _MAX_UNIT_TEXT) -> str:
    """Truncate to ``max_len`` with a deterministic ``...`` suffix."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


class CoverageReportInput(BaseModel):
    report: CoverageReport
    triage: list[TriageItem] = Field(default_factory=list)
    source_units: dict[str, SourceUnit] = Field(default_factory=dict)


class CriticReportInput(BaseModel):
    findings: list[Finding] = Field(default_factory=list)


class ManifestInputs(BaseModel):
    bible_hash: str
    template_library_hash: str = ""
    prompts_hash: str = ""
    registries_hash: str = ""


class ManifestMetrics(BaseModel):
    units: int = 0
    required_units: int = 0
    coverage: dict[str, float | int] = Field(default_factory=dict)
    verification: dict[str, float | int] = Field(default_factory=dict)
    ensemble: dict[str, int] = Field(default_factory=dict)
    critic: dict[str, int] = Field(default_factory=dict)
    linker: dict[str, int] = Field(default_factory=dict)
    consistency: dict[str, int] = Field(default_factory=dict)
    cascade: dict[str, int] = Field(default_factory=dict)


class ManifestAcceptance(BaseModel):
    invariants: dict[str, str] = Field(default_factory=dict)
    queues: dict[str, dict[str, int]] = Field(default_factory=dict)
    telemetry_deltas: dict[str, str] = Field(default_factory=dict)
    ratchet: str = "skipped (no accepted baseline)"


class ManifestReportInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    brand: str
    built_at: str = ""
    inputs: ManifestInputs
    stages: dict[str, dict[str, str]] = Field(default_factory=dict)
    metrics: ManifestMetrics = Field(default_factory=ManifestMetrics)
    acceptance: ManifestAcceptance = Field(default_factory=ManifestAcceptance)


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _queue_counts(triage: list[TriageItem]) -> dict[TriageQueue, Counter[str]]:
    counts: dict[TriageQueue, Counter[str]] = {
        queue: Counter({"open": 0, "waived": 0, "deferred": 0}) for queue in _TRIAGE_QUEUES
    }
    for item in triage:
        status = item.disposition.status
        if status == "deferred":
            counts[item.queue]["deferred"] += 1
        elif status == "waived":
            counts[item.queue]["waived"] += 1
        else:
            counts[item.queue]["open"] += 1
    return counts


def _unit_doc_ref(unit_id: str, source_units: dict[str, SourceUnit]) -> str:
    unit = source_units.get(unit_id)
    return unit.doc_ref if unit is not None else "(unknown doc_ref)"


def _unit_display_text(unit_id: str, source_units: dict[str, SourceUnit]) -> str:
    unit = source_units.get(unit_id)
    if unit is None:
        return f"(text unavailable for {unit_id})"
    return truncate_text(unit.text)


def render_coverage_report(data: CoverageReportInput) -> str:
    """Render ``review/coverage_report.md`` from coverage, triage, and source units."""
    report = data.report
    lines = [
        f"# Coverage Report — {escape_md_cell(report.brand)}",
        "",
        "> Telemetry only — coverage ratios are observability metrics, not acceptance gates.",
        "",
        "## Summary telemetry",
        "",
        "| metric | value |",
        "| --- | --- |",
        f"| value_coverage | {_pct(report.value_coverage)} |",
        f"| normative_coverage | {_pct(report.normative_coverage)} |",
        f"| verbatim_coverage | {_pct(report.verbatim_coverage)} |",
        f"| gap_rounds | {report.rounds} |",
        f"| unclaimed_units | {len(report.unclaimed_unit_ids)} |",
        f"| over_claimed_units | {len(report.over_claimed_unit_ids)} |",
        f"| orphan_entities | {len(report.orphan_entity_ids)} |",
        "",
        "## Per-blob coverage",
        "",
        "| doc_ref | value | normative | verbatim | n_required |",
        "| --- | --- | --- | --- | --- |",
    ]
    for doc_ref in sorted(report.per_blob):
        blob = report.per_blob[doc_ref]
        lines.append(
            "| {doc} | {value} | {norm} | {verb} | {req} |".format(
                doc=escape_md_cell(doc_ref),
                value=_pct(float(blob["value"])),
                norm=_pct(float(blob["normative"])),
                verb=_pct(float(blob["verbatim"])),
                req=int(blob["n_required"]),
            )
        )
    lines.extend(["", "## Required unclaimed units", ""])
    by_blob: dict[str, list[str]] = defaultdict(list)
    for unit_id in report.unclaimed_unit_ids:
        by_blob[_unit_doc_ref(unit_id, data.source_units)].append(unit_id)
    if not by_blob:
        lines.append("_None._")
    else:
        for doc_ref in sorted(by_blob):
            lines.append(f"### {escape_md_cell(doc_ref)}")
            lines.append("")
            for unit_id in sorted(by_blob[doc_ref]):
                text = escape_md_cell(_unit_display_text(unit_id, data.source_units))
                lines.append(f"- `{unit_id}`: {text}")
            lines.append("")
    lines.extend(["## Orphan entities", ""])
    if report.orphan_entity_ids:
        for entity_id in sorted(report.orphan_entity_ids):
            lines.append(f"- `{entity_id}`")
    else:
        lines.append("_None._")
    lines.extend(["", "## Triage queue status", "", "| queue | open | waived | deferred |", "| --- | --- | --- | --- |"])
    counts = _queue_counts(data.triage)
    for queue in _TRIAGE_QUEUES:
        row = counts[queue]
        lines.append(f"| {queue} | {row['open']} | {row['waived']} | {row['deferred']} |")
    return "\n".join(lines).rstrip() + "\n"


def render_critic_findings(data: CriticReportInput) -> str:
    """Render critic findings grouped by resolution then severity."""
    lines = ["# Critic findings", ""]
    if not data.findings:
        lines.append("_No findings._")
        return "\n".join(lines).rstrip() + "\n"
    grouped: dict[str, dict[str, list[Finding]]] = defaultdict(lambda: defaultdict(list))
    for finding in data.findings:
        grouped[finding.resolution][finding.severity].append(finding)
    for resolution in _RESOLUTION_ORDER:
        if resolution not in grouped:
            continue
        lines.append(f"## {resolution}")
        lines.append("")
        for severity in _SEVERITY_ORDER:
            bucket = grouped[resolution].get(severity, [])
            if not bucket:
                continue
            lines.append(f"### {severity}")
            lines.append("")
            for finding in sorted(bucket, key=lambda item: item.finding_id):
                target = finding.target_entity_id or "(no target)"
                lines.append(
                    f"- `{finding.finding_id}` ({finding.finding_type}) "
                    f"target=`{target}`: {escape_md_cell(finding.description)}"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _metric_block(title: str, metrics: dict[str, Any]) -> list[str]:
    if not metrics:
        return []
    lines = [f"### {title}", ""]
    for key in sorted(metrics):
        lines.append(f"- {key}: {metrics[key]}")
    lines.append("")
    return lines


def render_manifest_summary(data: ManifestReportInput) -> str:
    """Render a concise manifest summary without inventing acceptance thresholds."""
    lines = [
        f"# Build manifest — {escape_md_cell(data.brand)}",
        "",
        f"- schema_version: {data.schema_version}",
        f"- built_at: {data.built_at or '(not recorded)'}",
        "",
        "## Inputs",
        "",
        f"- bible_hash: `{data.inputs.bible_hash}`",
        f"- template_library_hash: `{data.inputs.template_library_hash or '(empty)'}`",
        f"- prompts_hash: `{data.inputs.prompts_hash or '(empty)'}`",
        f"- registries_hash: `{data.inputs.registries_hash or '(empty)'}`",
        "",
    ]
    if data.stages:
        lines.extend(["## Stages", ""])
        for stage in sorted(data.stages):
            meta = data.stages[stage]
            version = meta.get("version", "")
            out_hash = meta.get("out_hash", "")
            lines.append(f"- {stage}: version=`{version}` out_hash=`{out_hash}`")
        lines.append("")
    metrics = data.metrics
    lines.extend(
        [
            "## Metrics",
            "",
            f"- units: {metrics.units}",
            f"- required_units: {metrics.required_units}",
        ]
    )
    lines.extend(_metric_block("coverage", metrics.coverage))
    lines.extend(_metric_block("verification", metrics.verification))
    lines.extend(_metric_block("ensemble", metrics.ensemble))
    lines.extend(_metric_block("critic", metrics.critic))
    lines.extend(_metric_block("linker", metrics.linker))
    minted_delta = data.acceptance.telemetry_deltas.get("linker.minted_edges", "")
    if minted_delta.startswith("+") and minted_delta not in {"+0", "+0.0"}:
        lines.extend(
            [
                "### linker alert",
                "",
                f"- minted_edges increased build-over-build: {minted_delta}",
                "",
            ]
        )
    lines.extend(_metric_block("consistency", metrics.consistency))
    lines.extend(_metric_block("cascade", metrics.cascade))
    acceptance = data.acceptance
    lines.extend(["## Acceptance", ""])
    if acceptance.invariants:
        lines.append("### invariants")
        lines.append("")
        for key in sorted(acceptance.invariants):
            lines.append(f"- {key}: {acceptance.invariants[key]}")
        lines.append("")
    if acceptance.queues:
        lines.extend(["### queues", "", "| queue | open | waived | deferred |", "| --- | --- | --- | --- |"])
        for queue in _TRIAGE_QUEUES:
            row = acceptance.queues.get(queue, {})
            lines.append(
                f"| {queue} | {row.get('open', 0)} | {row.get('waived', 0)} | {row.get('deferred', 0)} |"
            )
        lines.append("")
    if acceptance.telemetry_deltas:
        lines.extend(["### telemetry_deltas", ""])
        for key in sorted(acceptance.telemetry_deltas):
            lines.append(f"- {key}: {acceptance.telemetry_deltas[key]}")
        lines.append("")
    lines.append(f"### ratchet\n\n{acceptance.ratchet}\n")
    return "\n".join(lines).rstrip() + "\n"


def render_cascade_schema() -> str:
    """Pure documentation for cascade on-disk layout and resolution semantics."""
    return "\n".join(
        [
            "# Cascade schema (v2)",
            "",
            "## contexts.json",
            "",
            "Maps each email-level context canonical key to `{axes, sheet_hash}`.",
            "Canonical key format: "
            "`audience=…;campaign=…;surface=…;tags=tag1+tag2|none;theme=…`.",
            "Axes use `content_tags` in models but serialize as `tags` in sheet context.",
            "",
            "## Sheet deduplication",
            "",
            "Sheets are content-addressed: `sheet_hash = stable_hash(payload without context)`.",
            "Identical resolved sheets share one `cascade/sheets/{sheet_hash}.json`.",
            "Index `kb_hash` must match every sheet payload.",
            "",
            "## Sheet layout",
            "",
            "- `email`: hard_constraints, strong_defaults, soft_guidance, governance, structure buckets",
            "- `sections/*`: per-section hard/default/guidance rule ids plus `elements` resolved properties",
            "- `elements.{path}`: `resolved` value when top candidate residual guard is empty; "
            "`candidates` retains trace with residual guards and specificity tuples",
            "",
            "## Resolution",
            "",
            "Email-level axes are partial-evaluated; surviving bindings keep residual guards "
            "on section-level axes only.",
            SPECIFICITY_DOC.strip(),
            "",
            "## Query defaults (`get_sheet`)",
            "",
            "Default axes: audience=dtp_patient, surface=email, campaign=none, theme=none, tags=[].",
            "Unknown axis keys raise `KeyError`; missing context raises `KeyError`; "
            "missing files raise `FileNotFoundError`; kb_hash or sheet hash mismatch raises `ValueError`.",
            "",
        ]
    ).rstrip() + "\n"


def conflict_id(conflict_kind: str, element_path: str | None, a_id: str, b_id: str) -> str:
    """Stable conflict id aligned with ledger triage keys."""
    ids = sorted([a_id, b_id])
    return stable_hash((conflict_kind, element_path, ids))
