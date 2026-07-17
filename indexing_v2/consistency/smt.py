"""SMT global satisfiability layer (S9 layer 2, optional Z3).

Usage: ``from indexing_v2.consistency.smt import analyze_smt, solve_context, smt_status, write_analysis_conflicts``
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from indexing_v2.cascade.contexts import enumerate_contexts, observed_content_tag_combos
from indexing_v2.cascade.guards import normalize_guard
from indexing_v2.cascade.resolve import partial_eval_guard
from indexing_v2.consistency.pairwise import DeadEntry, PairwiseAnalysisResult, PrecedenceProposal
from indexing_v2.contracts import SCHEMA_VERSION, ContextKey, Guard, KBSnapshot, atomic_write_json
from shared.schemas import BrandRule, SECTION_TYPES

STAGE_VERSION = "1.0.0"
N_SLOTS = 12

_EMPTY_SECTION = "empty"
_BACKGROUND_VALUES = ("dark", "light")
# ponytail: planted minibible max-1/min-2 CTA pair counts the same email-level touchpoint var.
_CTA_TOUCHPOINT_TARGETS = frozenset({"cta", "cta.button.primary"})


@runtime_checkable
class ConsoleLike(Protocol):
    def print(self, *args: Any, **kwargs: Any) -> None: ...


class ContextSolveResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    context_key: str
    status: Literal["sat", "unsat", "skipped"]
    unsat_core: list[str] = Field(default_factory=list)
    active_rule_ids: list[str] = Field(default_factory=list)
    # Hard rules whose effect payload could not be encoded; excluded from the
    # model (weakens the check for those rules, never corrupts results).
    unencodable_rule_ids: list[str] = Field(default_factory=list)


class GlobalUnsatConflict(BaseModel):
    schema_version: str = SCHEMA_VERSION
    kind: Literal["global_unsat"] = "global_unsat"
    context_key: str
    core: list[str]
    detail: str


class SmtAnalysisResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    status: Literal["completed", "skipped"]
    context_results: list[ContextSolveResult] = Field(default_factory=list)
    global_unsat: list[GlobalUnsatConflict] = Field(default_factory=list)


class AnalysisConflictsArtifact(BaseModel):
    schema_version: str = SCHEMA_VERSION
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    dead_entries: list[DeadEntry] = Field(default_factory=list)
    precedence_proposals: list[PrecedenceProposal] = Field(default_factory=list)


class SmtSolverUnknownError(RuntimeError):
    """Raised when Z3 cannot decide a finite context model."""


class SmtEncodingError(ValueError):
    """Raised when a hard rule cannot be encoded faithfully."""


class SmtUnsupportedGuardError(SmtEncodingError):
    """Raised when a residual guard cannot be represented by the finite model."""


@dataclass(frozen=True)
class _ActiveRule:
    rule: BrandRule
    residual_guard: Guard


@dataclass(frozen=True)
class _SolverEncoding:
    solver: Any
    tracked: dict[str, Any]
    section_type: list[Any]
    background: list[Any]
    device_present: dict[str, list[Any]]
    device_count: dict[str, list[Any]]
    residual_axes: dict[str, list[Any]]
    residual_axis_values: dict[str, list[str]]
    section_values: list[str]


_z3_module: Any | None = None
_z3_checked = False
_skip_notified = False


def smt_status() -> Literal["available", "skipped"]:
    """Return whether the optional Z3 solver is importable."""
    return "available" if _load_z3() is not None else "skipped"


def solve_context(
    snapshot: KBSnapshot,
    context: ContextKey,
    *,
    observed_tags: Optional[set[str]] = None,
) -> ContextSolveResult:
    """Check global SAT for one email-level context under hard structural rules."""
    z3 = _load_z3()
    if z3 is None:
        return ContextSolveResult(
            context_key=context.canonical(),
            status="skipped",
        )
    tags = observed_tags if observed_tags is not None else set(context.content_tags)
    active_rules = _active_hard_rules(snapshot, context, tags)
    # Extraction can emit hard rules whose effect payload doesn't satisfy the
    # encoding contract (e.g. exclusivity with no subject). Excluding them
    # weakens the check for those rules only — recorded on the result so the
    # gap is visible — instead of failing the whole consistency stage.
    encodable: list[_ActiveRule] = []
    unencodable: list[str] = []
    for item in active_rules:
        try:
            _validate_effect(item.rule)
        except SmtEncodingError:
            unencodable.append(item.rule.id)
        else:
            encodable.append(item)
    encoding = _build_solver(z3, snapshot, encodable)
    outcome = encoding.solver.check()
    if outcome == z3.sat:
        return ContextSolveResult(
            context_key=context.canonical(),
            status="sat",
            active_rule_ids=sorted(item.rule.id for item in encodable),
            unencodable_rule_ids=sorted(unencodable),
        )
    if outcome == z3.unknown:
        raise SmtSolverUnknownError(
            f"Z3 returned unknown for {context.canonical()}: {encoding.solver.reason_unknown()}"
        )
    core = _extract_unsat_core(encoding.solver, encoding.tracked)
    return ContextSolveResult(
        context_key=context.canonical(),
        status="unsat",
        unsat_core=core,
        active_rule_ids=sorted(item.rule.id for item in encodable),
        unencodable_rule_ids=sorted(unencodable),
    )


def analyze_smt(
    snapshot: KBSnapshot,
    *,
    console: ConsoleLike | None = None,
) -> SmtAnalysisResult:
    """Run layer-2 SMT over every enumerated email-level context."""
    z3 = _load_z3()
    if z3 is None:
        _emit_skip_note(console)
        return SmtAnalysisResult(status="skipped")
    observed_tags = _observed_tags(snapshot)
    context_results: list[ContextSolveResult] = []
    global_unsat: list[GlobalUnsatConflict] = []
    for context in enumerate_contexts(snapshot):
        result = solve_context(snapshot, context, observed_tags=observed_tags)
        context_results.append(result)
        if result.status == "unsat":
            global_unsat.append(
                GlobalUnsatConflict(
                    context_key=result.context_key,
                    core=list(result.unsat_core),
                    detail=(
                        f"global_unsat in {result.context_key}: "
                        f"core={json.dumps(result.unsat_core, ensure_ascii=False)}"
                    ),
                )
            )
    global_unsat.sort(key=lambda item: (item.context_key, item.core))
    context_results.sort(key=lambda item: item.context_key)
    return SmtAnalysisResult(
        status="completed",
        context_results=context_results,
        global_unsat=global_unsat,
    )


def write_analysis_conflicts(
    path: Path,
    *,
    pairwise: PairwiseAnalysisResult | None = None,
    smt: SmtAnalysisResult | None = None,
) -> AnalysisConflictsArtifact:
    """Write ``analysis/conflicts.json``, preserving pairwise rows and appending global_unsat."""
    existing = _read_conflicts_artifact(path)
    if pairwise is not None:
        base_conflicts = [item.model_dump(mode="json") for item in pairwise.conflicts]
        dead_entries = list(pairwise.dead_entries)
        proposals = list(pairwise.precedence_proposals)
    else:
        base_conflicts = [
            item for item in existing.conflicts if item.get("kind") != "global_unsat"
        ]
        dead_entries = list(existing.dead_entries)
        proposals = list(existing.precedence_proposals)

    global_rows: list[dict[str, Any]] = []
    if smt is not None and smt.status == "completed":
        global_rows = [item.model_dump(mode="json") for item in smt.global_unsat]

    merged_conflicts = _dedupe_conflicts(base_conflicts + global_rows)
    artifact = AnalysisConflictsArtifact(
        conflicts=merged_conflicts,
        dead_entries=sorted(dead_entries, key=lambda item: item.entry_id),
        precedence_proposals=sorted(proposals, key=lambda item: (item.rule_id, item.precedence)),
    )
    atomic_write_json(path, artifact.model_dump(mode="json"))
    return artifact


def _load_z3() -> Any | None:
    global _z3_module, _z3_checked
    if _z3_checked:
        return _z3_module
    try:
        import z3  # type: ignore[import-untyped]
    except ModuleNotFoundError as exc:
        if exc.name != "z3":
            raise
        _z3_module = None
    else:
        _z3_module = z3
    _z3_checked = True
    return _z3_module


def _emit_skip_note(console: ConsoleLike | None) -> None:
    global _skip_notified
    if console is None or _skip_notified:
        return
    message = "SMT layer skipped: z3-solver not installed (optional requirements-solver.txt)"
    console.print(message)
    _skip_notified = True


def _observed_tags(snapshot: KBSnapshot) -> set[str]:
    return {tag for combo in observed_content_tag_combos(snapshot) for tag in combo}


def _active_hard_rules(
    snapshot: KBSnapshot,
    context: ContextKey,
    observed_tags: set[str],
) -> list[_ActiveRule]:
    active: list[_ActiveRule] = []
    for rule in sorted(snapshot.rules.values(), key=lambda item: item.id):
        if rule.hardness != "hard_constraint":
            continue
        if rule.constraint_type not in {
            "cardinality",
            "ordering",
            "pairing",
            "exclusivity",
        }:
            continue
        residual = _rule_residual_guard(rule, context, observed_tags)
        if residual is None or any(not term.values for term in residual.values()):
            continue
        active.append(_ActiveRule(rule=rule, residual_guard=residual))
    return active


def _rule_residual_guard(
    rule: BrandRule,
    context: ContextKey,
    observed_tags: set[str],
) -> Guard | None:
    guards: list[Any] = [rule.applies_when]
    if rule.audience is not None:
        guards.append({"audience": rule.audience})
    if rule.content_types is not None:
        guards.append({"surface": rule.content_types})
    if rule.selector.section_types is not None:
        guards.append({"section": rule.selector.section_types})
    merged = normalize_guard(guards)
    return partial_eval_guard(merged, context, observed_tags)


def _validate_effect(rule: BrandRule) -> None:
    effect = rule.effect if isinstance(rule.effect, dict) else {}
    kind = rule.constraint_type
    if kind == "cardinality":
        target = effect.get("target")
        if not isinstance(target, str) or not target.strip():
            raise SmtEncodingError(f"{rule.id}: cardinality target must be a non-empty string")
        per = effect.get("per")
        if per not in {"email", "section"}:
            raise SmtEncodingError(
                f"{rule.id}: cardinality per must be 'email' or 'section', got {per!r}"
            )
        minimum = effect.get("min")
        maximum = effect.get("max")
        for name, value in (("min", minimum), ("max", maximum)):
            if value is not None and (type(value) is not int or value < 0):
                raise SmtEncodingError(
                    f"{rule.id}: cardinality {name} must be a nonnegative integer"
                )
        if minimum is None and maximum is None:
            raise SmtEncodingError(f"{rule.id}: cardinality requires min or max")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise SmtEncodingError(f"{rule.id}: cardinality min cannot exceed max")
        return
    if kind == "pairing":
        for key in ("a", "b"):
            if not isinstance(effect.get(key), str) or not str(effect[key]).strip():
                raise SmtEncodingError(
                    f"{rule.id}: pairing {key} must be a non-empty string"
                )
        relation = effect.get("relation")
        if relation not in {"requires", "forbids"}:
            raise SmtEncodingError(
                f"{rule.id}: pairing relation must be 'requires' or 'forbids', "
                f"got {relation!r}"
            )
        return
    if kind == "ordering":
        sequence = effect.get("sequence")
        if (
            not isinstance(sequence, list)
            or not sequence
            or any(not isinstance(item, str) or not item.strip() for item in sequence)
        ):
            raise SmtEncodingError(
                f"{rule.id}: ordering sequence must contain non-empty strings"
            )
        strict = effect.get("strict")
        if not isinstance(strict, bool):
            raise SmtEncodingError(f"{rule.id}: ordering strict must be a boolean")
        return
    if kind == "exclusivity":
        subject = effect.get("subject")
        if not isinstance(subject, str) or not subject.strip():
            raise SmtEncodingError(
                f"{rule.id}: exclusivity subject must be a non-empty string"
            )


def _residual_axis_values(active_rules: list[_ActiveRule]) -> dict[str, list[str]]:
    values: dict[str, set[str]] = {}
    special = {
        "section",
        "section_type",
        "background_group",
        "position_in_email",
    }
    for active in active_rules:
        for axis, term in sorted(active.residual_guard.items()):
            if axis == "position_in_email":
                unsupported = set(term.values) - {"first", "last"}
                if unsupported:
                    raise SmtUnsupportedGuardError(
                        f"{active.rule.id}: unsupported position_in_email values "
                        f"{sorted(unsupported)}"
                    )
            elif axis not in special:
                values.setdefault(axis, set()).update(term.values)
    return {axis: sorted(axis_values) for axis, axis_values in sorted(values.items())}


def _section_enum(snapshot: KBSnapshot) -> list[str]:
    names = set(SECTION_TYPES)
    for rule in snapshot.rules.values():
        for item in rule.selector.section_types or []:
            names.add(item)
    for subtype in snapshot.subtypes.values():
        for item in subtype.fills_section_types or []:
            names.add(item)
    device_ids = _catalog_device_ids(snapshot)
    for rule in snapshot.rules.values():
        effect = rule.effect if isinstance(rule.effect, dict) else {}
        if rule.constraint_type == "ordering" and isinstance(effect.get("sequence"), list):
            for item in effect["sequence"]:
                name = str(item)
                if name not in device_ids:
                    names.add(name)
    return sorted(names)


def _build_solver(
    z3: Any,
    snapshot: KBSnapshot,
    active_rules: list[_ActiveRule],
) -> _SolverEncoding:
    for active in active_rules:
        _validate_effect(active.rule)
    section_values = _section_enum(snapshot) + [_EMPTY_SECTION]
    solver = z3.Solver()
    solver.set("core.minimize", True)
    tracked: dict[str, Any] = {}

    section_type: list[Any] = []
    background: list[Any] = []
    empty_idx = section_values.index(_EMPTY_SECTION)
    for slot in range(N_SLOTS):
        section_type.append(z3.Int(f"section_type::{slot}"))
        background.append(z3.Int(f"background::{slot}"))
        solver.add(section_type[slot] >= 0, section_type[slot] < len(section_values))
        solver.add(background[slot] >= 0, background[slot] < len(_BACKGROUND_VALUES))

    _assert_structural_axioms(
        z3,
        solver,
        tracked,
        snapshot,
        section_type,
        section_values,
    )

    devices = _collect_devices(snapshot, section_values)
    device_present: dict[str, list[Any]] = {}
    device_count: dict[str, list[Any]] = {}
    for device_id in sorted(devices):
        device_present[device_id] = [
            z3.Bool(f"device::{device_id}::{slot}") for slot in range(N_SLOTS)
        ]
        device_count[device_id] = [
            z3.Int(f"device_count::{device_id}::{slot}") for slot in range(N_SLOTS)
        ]
        for slot in range(N_SLOTS):
            solver.add(
                device_count[device_id][slot] >= 0,
                device_count[device_id][slot] <= N_SLOTS,
            )
            solver.add(
                device_present[device_id][slot]
                == (device_count[device_id][slot] > 0)
            )
            solver.add(
                z3.Implies(
                    device_present[device_id][slot],
                    section_type[slot] != empty_idx,
                )
            )

    residual_axis_values = _residual_axis_values(active_rules)
    residual_axes: dict[str, list[Any]] = {}
    for axis, values in sorted(residual_axis_values.items()):
        residual_axes[axis] = [
            z3.Int(f"residual::{axis}::{slot}") for slot in range(N_SLOTS)
        ]
        for var in residual_axes[axis]:
            solver.add(var >= 0, var < len(values))

    for active in active_rules:
        constraint = _encode_rule(
            z3,
            active,
            section_type,
            background,
            section_values,
            device_present,
            device_count,
            residual_axes,
            residual_axis_values,
        )
        _assert_tracked(z3, solver, tracked, active.rule.id, constraint)

    return _SolverEncoding(
        solver=solver,
        tracked=tracked,
        section_type=section_type,
        background=background,
        device_present=device_present,
        device_count=device_count,
        residual_axes=residual_axes,
        residual_axis_values=residual_axis_values,
        section_values=section_values,
    )


def _assert_structural_axioms(
    z3: Any,
    solver: Any,
    tracked: dict[str, Any],
    snapshot: KBSnapshot,
    section_type: list[Any],
    section_values: list[str],
) -> None:
    if "top_matter" in section_values:
        idx = section_values.index("top_matter")
        _assert_tracked(
            z3,
            solver,
            tracked,
            "struct:base:top_matter",
            z3.And(
                _sum_bools(
                    z3,
                    [section_type[slot] == idx for slot in range(N_SLOTS)],
                )
                == 1,
                section_type[0] == idx,
            ),
        )
    if "end_matter" in section_values:
        idx = section_values.index("end_matter")
        _assert_tracked(
            z3,
            solver,
            tracked,
            "struct:base:end_matter",
            z3.And(
                _sum_bools(
                    z3,
                    [section_type[slot] == idx for slot in range(N_SLOTS)],
                )
                == 1,
                section_type[N_SLOTS - 1] == idx,
            ),
        )

    for subtype in sorted(snapshot.subtypes.values(), key=lambda item: item.id):
        assembly = subtype.assembly if isinstance(subtype.assembly, dict) else {}
        fills = subtype.fills_section_types or []
        if not fills:
            continue
        fill_indices = [section_values.index(name) for name in fills if name in section_values]
        if not fill_indices:
            continue
        clauses: list[Any] = []
        if assembly.get("position") == "first":
            clauses.append(z3.Or(*[section_type[0] == idx for idx in fill_indices]))
        if assembly.get("position") == "last":
            clauses.append(
                z3.Or(*[section_type[N_SLOTS - 1] == idx for idx in fill_indices])
            )
        if assembly.get("locked"):
            clauses.append(
                _sum_bools(
                    z3,
                    [
                        z3.Or(*[section_type[slot] == idx for idx in fill_indices])
                        for slot in range(N_SLOTS)
                    ],
                )
                == 1
            )
        if clauses:
            _assert_tracked(
                z3,
                solver,
                tracked,
                f"struct:{subtype.id}",
                z3.And(*clauses),
            )


def _assert_tracked(
    z3: Any,
    solver: Any,
    tracked: dict[str, Any],
    constraint_id: str,
    constraint: Any,
) -> None:
    tracker = z3.Bool(f"track::{constraint_id}")
    tracked[constraint_id] = tracker
    solver.assert_and_track(constraint, tracker)


def _catalog_device_ids(snapshot: KBSnapshot) -> set[str]:
    devices = set(snapshot.assets) | set(snapshot.templates)
    devices.update(
        token.id
        for token in snapshot.tokens.values()
        if token.gated
        and isinstance(token.gated, dict)
        and token.gated.get("gate") is not None
    )
    for rule in snapshot.rules.values():
        effect = rule.effect if isinstance(rule.effect, dict) else {}
        for key in ("a", "b", "subject"):
            value = effect.get(key)
            if isinstance(value, str):
                devices.add(value)
    return devices


def _collect_devices(snapshot: KBSnapshot, section_values: list[str]) -> set[str]:
    devices = _catalog_device_ids(snapshot)
    for rule in snapshot.rules.values():
        effect = rule.effect if isinstance(rule.effect, dict) else {}
        target = effect.get("target")
        if (
            isinstance(target, str)
            and target not in section_values
            and target not in _CTA_TOUCHPOINT_TARGETS
        ):
            devices.add(target)
        sequence = effect.get("sequence")
        if isinstance(sequence, list):
            devices.update(str(item) for item in sequence if str(item) not in section_values)
    return devices


def _target_slot_presence(
    z3: Any,
    target: str,
    section_type: list[Any],
    section_values: list[str],
    device_present: dict[str, list[Any]],
) -> list[Any]:
    normalized = "cta" if target in _CTA_TOUCHPOINT_TARGETS else target
    if normalized in section_values:
        idx = section_values.index(normalized)
        return [section_type[slot] == idx for slot in range(N_SLOTS)]
    if normalized in device_present:
        return device_present[normalized]
    return [z3.BoolVal(False) for _ in range(N_SLOTS)]


def _target_slot_count(
    z3: Any,
    target: str,
    section_type: list[Any],
    section_values: list[str],
    device_count: dict[str, list[Any]],
) -> list[Any]:
    normalized = "cta" if target in _CTA_TOUCHPOINT_TARGETS else target
    if normalized in section_values:
        idx = section_values.index(normalized)
        return [
            z3.If(section_type[slot] == idx, 1, 0)
            for slot in range(N_SLOTS)
        ]
    if normalized in device_count:
        return device_count[normalized]
    return [z3.IntVal(0) for _ in range(N_SLOTS)]


def _slot_scope(
    z3: Any,
    residual_guard: Guard,
    slot: int,
    section_type: list[Any],
    background: list[Any],
    section_values: list[str],
    residual_axes: dict[str, list[Any]],
    residual_axis_values: dict[str, list[str]],
    *,
    include_section: bool = True,
) -> Any:
    clauses: list[Any] = [
        section_type[slot] != section_values.index(_EMPTY_SECTION)
    ]
    for axis, term in sorted(residual_guard.items()):
        if axis in {"section", "section_type"}:
            if include_section:
                clauses.append(
                    z3.Or(
                        *[
                            section_type[slot] == section_values.index(value)
                            for value in term.values
                            if value in section_values
                        ]
                    )
                )
        elif axis == "background_group":
            clauses.append(
                z3.Or(
                    *[
                        background[slot] == _BACKGROUND_VALUES.index(value)
                        for value in term.values
                        if value in _BACKGROUND_VALUES
                    ]
                )
            )
        elif axis == "position_in_email":
            positions = [
                slot == 0
                for value in term.values
                if value == "first"
            ]
            positions.extend(
                slot == N_SLOTS - 1
                for value in term.values
                if value == "last"
            )
            if len(positions) != len(term.values):
                raise SmtUnsupportedGuardError(
                    f"unsupported position_in_email values {term.values}"
                )
            clauses.append(z3.Or(*positions))
        elif axis in residual_axes:
            values = residual_axis_values[axis]
            clauses.append(
                z3.Or(
                    *[
                        residual_axes[axis][slot] == values.index(value)
                        for value in term.values
                    ]
                )
            )
        else:
            raise SmtUnsupportedGuardError(f"unmodeled residual guard axis {axis!r}")
    return z3.And(*clauses)


def _sum_bools(z3: Any, expressions: list[Any]) -> Any:
    return z3.Sum(*[z3.If(expression, 1, 0) for expression in expressions])


def _first_occurrence(z3: Any, presence: list[Any]) -> Any:
    first = z3.IntVal(N_SLOTS)
    for slot in reversed(range(N_SLOTS)):
        first = z3.If(presence[slot], z3.IntVal(slot), first)
    return first


def _encode_rule(
    z3: Any,
    active: _ActiveRule,
    section_type: list[Any],
    background: list[Any],
    section_values: list[str],
    device_present: dict[str, list[Any]],
    device_count: dict[str, list[Any]],
    residual_axes: dict[str, list[Any]],
    residual_axis_values: dict[str, list[str]],
) -> Any:
    rule = active.rule
    effect = rule.effect if isinstance(rule.effect, dict) else {}
    kind = rule.constraint_type
    if kind == "cardinality":
        return _encode_cardinality(
            z3,
            effect,
            active.residual_guard,
            section_type,
            background,
            section_values,
            device_count,
            residual_axes,
            residual_axis_values,
        )
    if kind == "ordering":
        return _encode_ordering(
            z3,
            effect,
            active.residual_guard,
            section_type,
            background,
            section_values,
            device_present,
            residual_axes,
            residual_axis_values,
        )
    if kind == "pairing":
        return _encode_pairing(
            z3,
            effect,
            active.residual_guard,
            section_type,
            background,
            section_values,
            device_present,
            residual_axes,
            residual_axis_values,
        )
    if kind == "exclusivity":
        return _encode_exclusivity(
            z3,
            effect,
            active,
            section_type,
            background,
            section_values,
            device_present,
            residual_axes,
            residual_axis_values,
        )
    return z3.BoolVal(True)


def _encode_cardinality(
    z3: Any,
    effect: dict[str, Any],
    residual_guard: Guard,
    section_type: list[Any],
    background: list[Any],
    section_values: list[str],
    device_count: dict[str, list[Any]],
    residual_axes: dict[str, list[Any]],
    residual_axis_values: dict[str, list[str]],
) -> Any:
    target = str(effect.get("target") or "")
    per = str(effect.get("per") or "email")
    target_counts = _target_slot_count(
        z3,
        target,
        section_type,
        section_values,
        device_count,
    )
    scopes = [
        _slot_scope(
            z3,
            residual_guard,
            slot,
            section_type,
            background,
            section_values,
            residual_axes,
            residual_axis_values,
        )
        for slot in range(N_SLOTS)
    ]
    minimum = effect.get("min")
    maximum = effect.get("max")
    if per == "email":
        total = z3.Sum(
            *[
                z3.If(scopes[slot], target_counts[slot], 0)
                for slot in range(N_SLOTS)
            ]
        )
        return _bounded_count(z3, total, minimum, maximum)
    per_slot: list[Any] = []
    for slot in range(N_SLOTS):
        per_slot.append(
            z3.Implies(
                scopes[slot],
                _bounded_count(z3, target_counts[slot], minimum, maximum),
            )
        )
    return z3.And(*per_slot)


def _bounded_count(
    z3: Any,
    count: Any,
    minimum: Any,
    maximum: Any,
) -> Any:
    clauses: list[Any] = []
    if isinstance(minimum, int):
        clauses.append(count >= minimum)
    if isinstance(maximum, int):
        clauses.append(count <= maximum)
    return z3.And(*clauses) if clauses else z3.BoolVal(True)


def _encode_ordering(
    z3: Any,
    effect: dict[str, Any],
    residual_guard: Guard,
    section_type: list[Any],
    background: list[Any],
    section_values: list[str],
    device_present: dict[str, list[Any]],
    residual_axes: dict[str, list[Any]],
    residual_axis_values: dict[str, list[str]],
) -> Any:
    sequence = effect.get("sequence")
    if not isinstance(sequence, list):
        return z3.BoolVal(True)
    strict = bool(effect.get("strict"))
    targets = [str(item) for item in sequence]
    clauses: list[Any] = []
    first: list[Any] = []
    for target in targets:
        raw_presence = _target_slot_presence(
            z3,
            target,
            section_type,
            section_values,
            device_present,
        )
        scoped_presence = [
            z3.And(
                _slot_scope(
                    z3,
                    residual_guard,
                    slot,
                    section_type,
                    background,
                    section_values,
                    residual_axes,
                    residual_axis_values,
                ),
                raw_presence[slot],
            )
            for slot in range(N_SLOTS)
        ]
        first.append(_first_occurrence(z3, scoped_presence))
        clauses.append(first[-1] < N_SLOTS)
    for left, right in zip(first, first[1:]):
        clauses.append(left < right if strict else left <= right)
    return z3.And(*clauses)


def _encode_pairing(
    z3: Any,
    effect: dict[str, Any],
    residual_guard: Guard,
    section_type: list[Any],
    background: list[Any],
    section_values: list[str],
    device_present: dict[str, list[Any]],
    residual_axes: dict[str, list[Any]],
    residual_axis_values: dict[str, list[str]],
) -> Any:
    left = str(effect.get("a") or "")
    right = str(effect.get("b") or "")
    relation = str(effect.get("relation") or "requires")
    left_presence = _target_slot_presence(
        z3,
        left,
        section_type,
        section_values,
        device_present,
    )
    right_presence = _target_slot_presence(
        z3,
        right,
        section_type,
        section_values,
        device_present,
    )
    clauses: list[Any] = []
    for slot in range(N_SLOTS):
        scope = _slot_scope(
            z3,
            residual_guard,
            slot,
            section_type,
            background,
            section_values,
            residual_axes,
            residual_axis_values,
        )
        if relation == "forbids":
            clauses.append(
                z3.Implies(
                    scope,
                    z3.Not(z3.And(left_presence[slot], right_presence[slot])),
                )
            )
        else:
            clauses.append(
                z3.Implies(
                    z3.And(scope, left_presence[slot]),
                    right_presence[slot],
                )
            )
    return z3.And(*clauses)


def _encode_exclusivity(
    z3: Any,
    effect: dict[str, Any],
    active: _ActiveRule,
    section_type: list[Any],
    background: list[Any],
    section_values: list[str],
    device_present: dict[str, list[Any]],
    residual_axes: dict[str, list[Any]],
    residual_axis_values: dict[str, list[str]],
) -> Any:
    subject = str(effect.get("subject") or "")
    subject_presence = _target_slot_presence(
        z3,
        subject,
        section_type,
        section_values,
        device_present,
    )
    reserved_sections = _reserved_sections(
        effect.get("reserved_for"),
        active.rule.selector.section_types,
        section_values,
    )
    outside: list[Any] = []
    for slot in range(N_SLOTS):
        reserved_slot = z3.Or(
            *[
                section_type[slot] == section_values.index(name)
                for name in reserved_sections
            ]
        )
        outside.append(
            z3.And(
                _slot_scope(
                    z3,
                    active.residual_guard,
                    slot,
                    section_type,
                    background,
                    section_values,
                    residual_axes,
                    residual_axis_values,
                    include_section=False,
                ),
                subject_presence[slot],
                z3.Not(reserved_slot),
            )
        )
    return _sum_bools(z3, outside) <= 1


def _reserved_sections(
    raw: Any,
    selector_sections: list[str] | None,
    section_values: list[str],
) -> list[str]:
    known = set(section_values) - {_EMPTY_SECTION}
    reserved = set(selector_sections or []) & known
    candidates: list[str] = []
    if isinstance(raw, list):
        candidates = [str(item).strip() for item in raw]
    elif isinstance(raw, str):
        candidates = [
            item.strip()
            for item in re.split(r"\s*(?:,|\||\bOR\b|\bor\b)\s*", raw)
        ]
    reserved.update(item for item in candidates if item in known)
    return sorted(reserved)


def _extract_unsat_core(solver: Any, tracked: dict[str, Any]) -> list[str]:
    core_names = {item.decl().name() for item in solver.unsat_core()}
    return sorted(
        constraint_id
        for constraint_id, tracker in tracked.items()
        if tracker.decl().name() in core_names
    )


def _read_conflicts_artifact(path: Path) -> AnalysisConflictsArtifact:
    if not path.exists():
        return AnalysisConflictsArtifact()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AnalysisConflictsArtifact.model_validate(payload)


def _dedupe_conflicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in sorted(rows, key=_conflict_sort_key):
        key = json.dumps(row, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _conflict_sort_key(row: dict[str, Any]) -> tuple[str, ...]:
    kind = str(row.get("kind", ""))
    if kind == "global_unsat":
        core = row.get("core") or []
        return (kind, str(row.get("context_key", "")), ",".join(core))
    return (
        kind,
        str(row.get("element_path") or ""),
        str(row.get("a_id", "")),
        str(row.get("b_id", "")),
    )
