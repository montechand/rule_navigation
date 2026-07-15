"""Human-readable consistency analysis reports (WP-17)."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from indexing_v2.cascade.guards import is_satisfiable, witness
from indexing_v2.consistency.pairwise import DeadEntry, PairwiseAnalysisResult, PrecedenceProposal
from indexing_v2.consistency.smt import AnalysisConflictsArtifact, GlobalUnsatConflict, SmtAnalysisResult
from indexing_v2.contracts import Conflict, Guard, GuardTerm
from indexing_v2.reports import conflict_id, escape_md_cell


class ConflictsReportInput(BaseModel):
    conflicts: list[Conflict] = Field(default_factory=list)
    dead_entries: list[DeadEntry] = Field(default_factory=list)
    precedence_proposals: list[PrecedenceProposal] = Field(default_factory=list)
    global_unsat: list[GlobalUnsatConflict] = Field(default_factory=list)
    domains: dict[str, list[str]] = Field(default_factory=dict)
    artifact: AnalysisConflictsArtifact | None = None

    @classmethod
    def from_analysis(
        cls,
        pairwise: PairwiseAnalysisResult,
        *,
        smt: SmtAnalysisResult | None = None,
        domains: dict[str, list[str]] | None = None,
        artifact: AnalysisConflictsArtifact | None = None,
    ) -> ConflictsReportInput:
        global_unsat = list(smt.global_unsat) if smt is not None else []
        return cls(
            conflicts=list(pairwise.conflicts),
            dead_entries=list(pairwise.dead_entries),
            precedence_proposals=list(pairwise.precedence_proposals),
            global_unsat=global_unsat,
            domains=dict(domains or {}),
            artifact=artifact,
        )


def _guard_json(guard: Guard) -> str:
    payload = {
        axis: term.model_dump(mode="json") if isinstance(term, GuardTerm) else term
        for axis, term in sorted(guard.items())
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def _witness_text(conflict: Conflict, domains: dict[str, list[str]]) -> str:
    if not conflict.overlap_guard:
        return "{}"
    if not domains:
        return "(witness unavailable — supply domains)"
    if not is_satisfiable(conflict.overlap_guard, domains):
        return "(no satisfying witness in supplied domains)"
    return json.dumps(witness(conflict.overlap_guard, domains), sort_keys=True, ensure_ascii=False)


def _conflict_block(conflict: Conflict, domains: dict[str, list[str]]) -> list[str]:
    cid = conflict_id(conflict.kind, conflict.element_path, conflict.a_id, conflict.b_id)
    element = conflict.element_path or "(unspecified)"
    return [
        f"### `{cid}`",
        "",
        f"- kind: `{conflict.kind}`",
        f"- element_path: `{element}`",
        f"- sources: `{conflict.a_id}`, `{conflict.b_id}`",
        f"- overlap_guard: `{escape_md_cell(_guard_json(conflict.overlap_guard))}`",
        f"- witness: `{escape_md_cell(_witness_text(conflict, domains))}`",
        f"- detail: {escape_md_cell(conflict.detail)}",
        "",
    ]


def render_conflicts_report(data: ConflictsReportInput) -> str:
    """Render ``review/conflicts.md`` from pairwise/SMT analysis inputs."""
    conflicts = list(data.conflicts)
    dead_entries = list(data.dead_entries)
    proposals = list(data.precedence_proposals)
    global_unsat = list(data.global_unsat)
    if data.artifact is not None:
        if not conflicts:
            conflicts = [
                Conflict.model_validate(item)
                for item in data.artifact.conflicts
                if item.get("kind") != "global_unsat"
            ]
        if not dead_entries:
            dead_entries = list(data.artifact.dead_entries)
        if not proposals:
            proposals = list(data.artifact.precedence_proposals)
        if not global_unsat:
            global_unsat = [
                GlobalUnsatConflict.model_validate(item)
                for item in data.artifact.conflicts
                if item.get("kind") == "global_unsat"
            ]

    lines = ["# Consistency conflicts", "", "## Pairwise conflicts", ""]
    if conflicts:
        for conflict in sorted(
            conflicts,
            key=lambda item: (
                item.kind,
                item.element_path or "",
                item.a_id,
                item.b_id,
            ),
        ):
            lines.extend(_conflict_block(conflict, data.domains))
    else:
        lines.append("_None._")
        lines.append("")

    lines.extend(["## Equal-specificity precedence proposals", ""])
    if proposals:
        for proposal in sorted(proposals, key=lambda item: (item.rule_id, item.precedence)):
            lines.append(
                f"- `{proposal.rule_id}` precedence `{proposal.precedence}`: "
                f"{escape_md_cell(proposal.detail)}"
            )
    else:
        lines.append("_None._")
    lines.append("")

    lines.extend(["## Dead entries", ""])
    if dead_entries:
        for entry in sorted(dead_entries, key=lambda item: item.entry_id):
            lines.append(
                f"- `{entry.entry_id}` ({entry.source_kind}, {entry.reason}): "
                f"{escape_md_cell(entry.detail)}"
            )
    else:
        lines.append("_None._")
    lines.append("")

    lines.extend(["## Global UNSAT", ""])
    if global_unsat:
        for row in sorted(global_unsat, key=lambda item: (item.context_key, item.core)):
            core = json.dumps(row.core, ensure_ascii=False)
            lines.append(f"### `{row.context_key}`")
            lines.append("")
            lines.append(f"- core: `{escape_md_cell(core)}`")
            lines.append(f"- detail: {escape_md_cell(row.detail)}")
            lines.append("")
    else:
        lines.append("_None._")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
