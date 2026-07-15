"""KB Extraction v2 pipeline driver (WP-16): staged S0–S11 build with manifest acceptance.

Usage:
  python -m indexing_v2.build_kb --brand lisraya ibsrela [--stages s0..s11 | --from s5] \\
      [--no-ensemble] [--no-critic] [--no-gaps] [--strict] [--ratchet] \\
      [--accept-baseline] [--force] [--concurrency N]
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import shutil
import sys
from collections import Counter
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

from pydantic import BaseModel, field_validator
from rich.console import Console

from indexing.build_kb import (
    Warnings,
    dedupe_rules,
    dedupe_tokens,
    ingest_template_library,
    link_templates,
    validate_catalog,
    validate_rule,
    write_kb,
)
from indexing_v2 import settings
from indexing_v2.contracts import (
    SCHEMA_VERSION,
    CoverageReport,
    RunVariant,
    SourceUnit,
    TriageItem,
    UnitLabel,
    atomic_write_json,
    read_jsonl,
    stable_hash,
)
from indexing_v2.extraction.classify_units import STAGE_VERSION as S1_VERSION
from indexing_v2.extraction.classify_units import run_classifier
from indexing_v2.extraction.critic import STAGE_VERSION as S5_VERSION
from indexing_v2.extraction.critic import CandidateSet, CriticResult, run_critic
from indexing_v2.extraction.ensemble import STAGE_VERSION as S4_VERSION
from indexing_v2.extraction.ensemble import (
    EnsembleResult,
    VerifiedRunInput,
    build_verified_run,
    reconcile_ensemble,
    write_candidates,
)
from indexing_v2.extraction.ledger import STAGE_VERSION as S6_VERSION
from indexing_v2.extraction.ledger import (
    CandidatesBundle,
    GapLoopResult,
    LedgerDocument,
    append_triage_items,
    build_ledger,
    compute_s9_triage_items,
    compute_triage_items,
    current_class_a_conflict_keys,
    load_triage_history,
    rebuild_triage,
    run_gap_loop,
    triage_key_conflict,
    write_ledger,
)
from indexing_v2.extraction.provenance import STAGE_VERSION as S3_VERSION
from indexing_v2.extraction.provenance import write_provenance
from indexing_v2.extraction.runner import DEFAULT_CACHE_ROOT, STAGE_VERSION as S2_VERSION
from indexing_v2.extraction.runner import (
    LLMClient,
    normalize_rule_groups,
    normalize_token_ids,
    run_extraction,
)
from indexing_v2.extraction.segmenter import STAGE_VERSION as S0_VERSION
from indexing_v2.extraction.segmenter import run_segmenter
from shared import config
from shared.llm import Usage
from shared.registries import get_registries
from shared.schemas import RuleGroup, RuleRelation

MANIFEST_SCHEMA_VERSION = "2.0"
DRIVER_VERSION = "wp16-1.0.0"
S7_VERSION = "pass-c-v1"
S8_VERSION = "write-kb-v1"
S11_VERSION = "summarize-embed-v1"

STAGE_IDS: tuple[str, ...] = tuple(f"s{i}" for i in range(12))
_STAGE_ORDER = {stage: index for index, stage in enumerate(STAGE_IDS)}

_EVIDENCE_KEYS = frozenset(
    {
        "evidence",
        "default_evidence",
        "effect_evidence",
        "snippets_evidence",
        "body_evidence",
        "preferred_form_evidence",
    }
)
_INVARIANT_KEYS = (
    "verbatim_integrity",
    "no_live_contradictions",
    "no_silent_quarantine",
    "no_open_criticals",
    "determinism",
)
# ponytail: only metrics with an explicit, spec-approved direction gate ratchet;
# everything else (unit counts, ensemble confidence buckets, cascade sizes, etc.) is
# informational and must never fail a build just because it grew or shrank.
_RATCHET_HIGHER_BETTER = frozenset(
    {
        "coverage.value",
        "coverage.normative",
        "coverage.verbatim",
        "verification.value_verified_rate",
    }
)
_RATCHET_LOWER_BETTER = frozenset(
    {
        "verification.quarantined",
        "verification.quarantine_rate",
        "critic.findings",
        "critic.deferred_human",
        "consistency.hard_hard",
        "consistency.equal_specificity",
        "consistency.dead_rules",
        "consistency.global_unsat",
    }
)


class BuildOptions(BaseModel):
    brands: list[str]
    stages: frozenset[str] | None = None
    from_stage: str | None = None
    no_ensemble: bool = False
    no_critic: bool = False
    no_gaps: bool = False
    strict: bool = False
    ratchet: bool = False
    accept_baseline: bool = False
    force: bool = False
    concurrency: int = settings.CONCURRENCY
    skip_summarize_embed: bool = False
    max_critic_rounds: int | None = None
    max_gap_rounds: int | None = None

    @field_validator("concurrency")
    @classmethod
    def _positive_concurrency(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(f"concurrency must be positive, got {value}")
        return value


@runtime_checkable
class ConsoleLike(Protocol):
    def print(self, *args: Any, **kwargs: Any) -> None: ...


@runtime_checkable
class SummarizeEmbedRunner(Protocol):
    async def __call__(self, brand: str, usage: Usage) -> None: ...


@dataclass
class BuildContext:
    brand: str
    options: BuildOptions
    usage: Usage
    console: ConsoleLike
    work_dir: Path
    kb_root: Path
    client: LLMClient
    cache_root: Path
    bible_hash: str
    built_at: str
    input_hashes: dict[str, str]
    summarize_embed: SummarizeEmbedRunner | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    stage_records: dict[str, dict[str, str]] = field(default_factory=dict)


class PassCResult(BaseModel):
    rules: dict[str, Any]
    cat: dict[str, Any]
    groups: dict[str, RuleGroup]
    relations: list[RuleRelation]
    warns: list[str]
    sidecars: dict[str, dict[str, Any]]
    confidence_by_id: dict[str, str]


class BuildOutcome(BaseModel):
    schema_version: str = MANIFEST_SCHEMA_VERSION
    brand: str
    exit_code: int
    acceptance_passed: bool
    manifest_path: Path


@dataclass(frozen=True)
class _StageSpec:
    stage_id: str
    version: str
    outputs: tuple[str, ...]
    depends_on: tuple[str, ...]
    option_inputs: tuple[str, ...] = ()


_STAGE_REGISTRY: dict[str, _StageSpec] = {
    "s0": _StageSpec("s0", S0_VERSION, ("units.jsonl", "blobs.json"), ()),
    "s1": _StageSpec("s1", S1_VERSION, ("unit_labels.jsonl",), ("s0",)),
    "s2": _StageSpec("s2", S2_VERSION, ("runs/",), ("s1",), ("no_ensemble",)),
    "s3": _StageSpec(
        "s3", S3_VERSION, ("verified_runs.json", "provenance_state.json"), ("s2",)
    ),
    "s4": _StageSpec("s4", S4_VERSION, ("ensemble.json",), ("s3",)),
    "s5": _StageSpec(
        "s5",
        S5_VERSION,
        ("findings.jsonl", "audit/", "candidates/", "critic/"),
        ("s4",),
        ("no_critic", "max_critic_rounds"),
    ),
    "s6": _StageSpec(
        "s6",
        S6_VERSION,
        ("ledger.json", "gap_result.json"),
        ("s5",),
        ("no_gaps", "max_gap_rounds"),
    ),
    "s7": _StageSpec("s7", S7_VERSION, ("pass_c.json",), ("s6",)),
    "s8": _StageSpec("s8", S8_VERSION, ("s8_outputs.json",), ("s7",)),
    "s9": _StageSpec(
        "s9",
        "pairwise+smt",
        (
            "../analysis/",
            "../review/conflicts.md",
            "../review/coverage_report.md",
        ),
        ("s8",),
    ),
    "s10": _StageSpec(
        "s10",
        "cascade-compile",
        ("../cascade/", "../schema/cascade.md"),
        ("s9",),
    ),
    "s11": _StageSpec(
        "s11",
        S11_VERSION,
        ("summarize_embed.json", "../rules/"),
        ("s8",),
        ("skip_summarize_embed",),
    ),
}


def _sha_file(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return hashlib.sha1(path.read_bytes()).hexdigest()[:16]


def _hash_json_file(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return stable_hash(payload)


def _hash_jsonl_file(path: Path) -> str:
    rows = read_jsonl(path)
    return stable_hash(rows)


def _hash_work_artifact(work_dir: Path, rel: str) -> str:
    path = work_dir / rel
    if rel.endswith("/"):
        if not path.exists():
            return ""
        parts: list[tuple[str, str]] = []
        for child in sorted(path.rglob("*")):
            if child.is_file():
                rel_path = child.relative_to(path).as_posix()
                if child.suffix == ".json":
                    parts.append((rel_path, _hash_json_file(child)))
                elif child.suffix == ".jsonl":
                    parts.append((rel_path, _hash_jsonl_file(child)))
                else:
                    parts.append((rel_path, _sha_file(child)))
        return stable_hash(parts)
    if not path.exists():
        return ""
    if path.suffix == ".json":
        return _hash_json_file(path)
    if path.suffix == ".jsonl":
        return _hash_jsonl_file(path)
    return _sha_file(path)


def _hash_kb_artifact(kb_root: Path, rel: str) -> str:
    path = kb_root / rel
    if rel.endswith("/"):
        if not path.exists():
            return ""
        parts: list[tuple[str, str]] = []
        for child in sorted(path.rglob("*")):
            if child.is_file() and "vectors" not in child.parts:
                rel_path = child.relative_to(kb_root).as_posix()
                if child.suffix == ".json":
                    parts.append((rel_path, _hash_json_file(child)))
                else:
                    parts.append((rel_path, _sha_file(child)))
        return stable_hash(parts)
    if not path.exists():
        return ""
    if path.suffix == ".json":
        return _hash_json_file(path)
    return _sha_file(path)


def stable_built_at(source_hash: str) -> str:
    # ponytail: wall-clock would break byte determinism; derive UTC stamp from bible hash.
    offset = int(source_hash[:10], 16) % (365 * 24 * 3600)
    moment = datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp() + offset
    return datetime.fromtimestamp(moment, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_bible(brand: str) -> dict[str, list[str]]:
    raw = json.loads(config.DESIGN_BIBLES[brand].read_text(encoding="utf-8"))
    return cast(dict[str, list[str]], raw.get("website", raw))


def hash_bible(brand: str) -> str:
    return _sha_file(config.DESIGN_BIBLES[brand])


def hash_prompts() -> str:
    prompts_dir = Path(__file__).resolve().parent / "extraction" / "prompts"
    parts = [
        (path.name, _sha_file(path))
        for path in sorted(prompts_dir.glob("*.md"))
    ]
    return stable_hash(parts)


def hash_registries() -> str:
    reg_path = Path(__file__).resolve().parent.parent / "shared" / "registries.json"
    return _sha_file(reg_path)


def hash_template_library(brand: str) -> str:
    path = config.TEMPLATE_LIBRARIES.get(brand)
    if path is None or not path.is_file():
        return ""
    return _sha_file(path)


def parse_stage_selection(
    *,
    stages: Sequence[str] | None,
    from_stage: str | None,
) -> list[str]:
    if stages and from_stage:
        raise ValueError("cannot combine --stages and --from")
    if from_stage is not None:
        stage = from_stage.strip().lower()
        if stage not in _STAGE_ORDER:
            raise ValueError(f"unknown stage: {from_stage!r}")
        start = _STAGE_ORDER[stage]
        return list(STAGE_IDS[start:])
    if not stages:
        return list(STAGE_IDS)
    selected: list[str] = []
    for token in stages:
        piece = token.strip().lower()
        if ".." in piece:
            left, right = piece.split("..", 1)
            if left not in _STAGE_ORDER or right not in _STAGE_ORDER:
                raise ValueError(f"unknown stage range token: {token!r}")
            start, end = _STAGE_ORDER[left], _STAGE_ORDER[right]
            if start > end:
                raise ValueError(f"invalid stage range: {token!r}")
            selected.extend(STAGE_IDS[start : end + 1])
            continue
        if piece not in _STAGE_ORDER:
            raise ValueError(f"unknown stage: {piece!r}")
        selected.append(piece)
    return list(dict.fromkeys(selected))


def _stage_state_path(work_dir: Path) -> Path:
    return work_dir / "stage_state.json"


def _load_stage_state(work_dir: Path) -> dict[str, Any]:
    path = _stage_state_path(work_dir)
    if not path.is_file():
        return {"schema_version": MANIFEST_SCHEMA_VERSION, "stages": {}}
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _save_stage_state(work_dir: Path, state: dict[str, Any]) -> None:
    atomic_write_json(_stage_state_path(work_dir), state)


def _effective_option(ctx: BuildContext, name: str) -> Any:
    value = getattr(ctx.options, name)
    if name == "max_critic_rounds" and value is None:
        return settings.MAX_CRITIC_ROUNDS
    if name == "max_gap_rounds" and value is None:
        return settings.MAX_GAP_ROUNDS
    return value


def _local_stage_inputs(ctx: BuildContext, spec: _StageSpec) -> dict[str, Any]:
    local = {name: _effective_option(ctx, name) for name in spec.option_inputs}
    if spec.stage_id == "s1":
        local["model"] = settings.CLASSIFY_MODEL
    elif spec.stage_id == "s2":
        local["variants"] = [
            item.model_dump(mode="json") for item in _ensemble_variants(ctx.options)
        ]
    elif spec.stage_id == "s3":
        local["fuzzy_match_min_ratio"] = settings.FUZZY_MATCH_MIN_RATIO
    elif spec.stage_id == "s5":
        local["model"] = settings.CRITIC_MODEL
    elif spec.stage_id == "s8":
        local["dtcg_namespace"] = settings.DTCG_NAMESPACE
    elif spec.stage_id == "s11":
        local["injected_runner"] = ctx.summarize_embed is not None
    return local


def _inputs_hash(ctx: BuildContext, spec: _StageSpec) -> str:
    saved = _load_stage_state(ctx.work_dir).get("stages", {})
    parts: list[tuple[str, str]] = [
        ("pipeline_inputs", stable_hash(ctx.input_hashes)),
        ("stage_inputs", stable_hash(_local_stage_inputs(ctx, spec))),
    ]
    for stage in spec.depends_on:
        meta = ctx.stage_records.get(stage) or saved.get(stage)
        if meta is None:
            raise KeyError(
                f"stage {stage!r} output hash missing; run prerequisite stages first"
            )
        parts.append(
            (
                stage,
                stable_hash(
                    {
                        "version": meta["version"],
                        "outputs_hash": meta["outputs_hash"],
                    }
                ),
            )
        )
    return stable_hash(parts)


def _record_stage(
    ctx: BuildContext,
    stage_id: str,
    *,
    version: str,
    inputs_hash: str,
    outputs_hash: str,
    skipped: bool,
) -> None:
    ctx.stage_records[stage_id] = {
        "version": version,
        "inputs_hash": inputs_hash,
        "outputs_hash": outputs_hash,
        "skipped": "true" if skipped else "false",
    }
    state = _load_stage_state(ctx.work_dir)
    state.setdefault("stages", {})[stage_id] = ctx.stage_records[stage_id]
    _save_stage_state(ctx.work_dir, state)


def _outputs_present(ctx: BuildContext, spec: _StageSpec) -> bool:
    if spec.stage_id == "s3":
        return _receipt_matches(ctx.work_dir, ctx.work_dir / "provenance_state.json")
    if spec.stage_id == "s4":
        return _receipt_matches(ctx.work_dir, ctx.work_dir / "ensemble_outputs.json")
    if spec.stage_id == "s5":
        candidates_dir = ctx.work_dir / "candidates"
        return (
            candidates_dir.is_dir()
            and any(candidates_dir.iterdir())
            and _receipt_matches(
                ctx.work_dir,
                ctx.work_dir / "critic" / "manifest.json",
                owned=_s5_owned_files,
            )
        )
    if spec.stage_id == "s8":
        return _receipt_matches(
            ctx.kb_root, ctx.work_dir / "s8_outputs.json", owned=_s8_owned_files
        )
    for rel in spec.outputs:
        if rel.startswith("../"):
            target = ctx.kb_root / rel.removeprefix("../")
            if rel.endswith("/"):
                if not target.exists():
                    return False
            elif not target.exists():
                return False
            continue
        target = ctx.work_dir / rel
        if rel.endswith("/"):
            if not target.exists() or not any(target.iterdir()):
                return False
        elif not target.exists():
            return False
    return True


def _compute_outputs_hash(ctx: BuildContext, spec: _StageSpec) -> str:
    if spec.stage_id == "s2":
        return _hash_run_outputs(ctx.work_dir)
    if spec.stage_id == "s3":
        return _receipt_hash(ctx.work_dir, ctx.work_dir / "provenance_state.json")
    if spec.stage_id == "s4":
        return _receipt_hash(ctx.work_dir, ctx.work_dir / "ensemble_outputs.json")
    if spec.stage_id == "s5":
        return _receipt_hash(
            ctx.work_dir, ctx.work_dir / "critic" / "manifest.json", owned=_s5_owned_files
        )
    if spec.stage_id == "s8":
        return _receipt_hash(ctx.kb_root, ctx.work_dir / "s8_outputs.json", owned=_s8_owned_files)
    parts: list[tuple[str, str]] = []
    for rel in spec.outputs:
        if rel.startswith("../"):
            parts.append((rel, _hash_kb_artifact(ctx.kb_root, rel.removeprefix("../"))))
            continue
        parts.append((rel, _hash_work_artifact(ctx.work_dir, rel)))
    return stable_hash(parts)


def _hash_kb_tree(kb_root: Path) -> str:
    if not kb_root.exists():
        return ""
    parts: list[tuple[str, str]] = []
    for child in sorted(kb_root.rglob("*")):
        if not child.is_file():
            continue
        if "_work" in child.parts or "vectors" in child.parts:
            continue
        rel = child.relative_to(kb_root).as_posix()
        if child.suffix == ".json":
            parts.append((rel, _hash_json_file(child)))
        else:
            parts.append((rel, _sha_file(child)))
    return stable_hash(parts)


def _hash_run_outputs(work_dir: Path) -> str:
    runs_dir = work_dir / "runs"
    if not runs_dir.is_dir():
        return ""
    parts: list[tuple[str, str]] = []
    for child in sorted(runs_dir.rglob("*")):
        if not child.is_file():
            continue
        relative = child.relative_to(runs_dir)
        if "provenance" in relative.parts or child.name == "quarantine.json":
            continue
        parts.append((relative.as_posix(), _hash_work_artifact(runs_dir, relative.as_posix())))
    return stable_hash(parts)


def _s8_artifact_hash(path: Path) -> str:
    if path.suffix != ".json":
        return _sha_file(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if path.parent.name == "rules":
        if isinstance(payload, list):
            payload = [
                {key: value for key, value in row.items() if key != "summary"}
                for row in payload
            ]
        elif isinstance(payload, dict):
            payload.pop("summary", None)
    return stable_hash(payload)


def _s8_owned_files(kb_root: Path) -> dict[str, str]:
    owned: dict[str, str] = {}
    if not kb_root.is_dir():
        return owned
    for path in sorted(kb_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(kb_root)
        if relative.parts[0] in {"_work", "analysis", "cascade", "vectors"}:
            continue
        if relative.as_posix() in {
            "manifest.json",
            "manifest.accepted.json",
            "review/conflicts.md",
            "review/coverage_report.md",
            "review/manifest_summary.md",
            "review/triage.jsonl",
            "schema/cascade.md",
        }:
            continue
        owned[relative.as_posix()] = _s8_artifact_hash(path)
    return owned


def _receipt_files(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = payload.get("files")
    if not isinstance(files, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in files.items()
    ):
        return None
    return cast(dict[str, str], files)


def _receipt_current_files(
    root: Path,
    receipt: Path,
    *,
    owned: Callable[[Path], dict[str, str]] | None = None,
) -> dict[str, str]:
    if owned is not None:
        return owned(root)
    recorded = _receipt_files(receipt) or {}
    current: dict[str, str] = {}
    for relative in recorded:
        path = root / relative
        if path.is_file():
            current[relative] = _hash_json_file(path) if path.suffix == ".json" else _sha_file(path)
    return current


def _receipt_matches(
    root: Path,
    receipt: Path,
    *,
    owned: Callable[[Path], dict[str, str]] | None = None,
) -> bool:
    recorded = _receipt_files(receipt)
    return recorded is not None and recorded == _receipt_current_files(root, receipt, owned=owned)


def _receipt_hash(
    root: Path,
    receipt: Path,
    *,
    owned: Callable[[Path], dict[str, str]] | None = None,
) -> str:
    return stable_hash(_receipt_current_files(root, receipt, owned=owned))


def _s5_owned_files(work_dir: Path) -> dict[str, str]:
    """Snapshot stable S5 outputs under ``_work``.

    S6 replaces ``candidates/`` with its gap-patched state, so the immutable
    ``critic/bundle.json`` is the S5 candidate handoff used for cache identity.
    The receipt itself is excluded to avoid a self-referential hash.
    """
    owned: dict[str, str] = {}
    for name in ("findings.jsonl", "audit", "critic"):
        path = work_dir / name
        if not path.exists():
            continue
        if path.is_file():
            owned[name] = _hash_jsonl_file(path) if path.suffix == ".jsonl" else _sha_file(path)
            continue
        for child in sorted(path.rglob("*")):
            if not child.is_file():
                continue
            relative = child.relative_to(work_dir).as_posix()
            if relative == "critic/manifest.json":
                continue
            if child.suffix == ".json":
                owned[relative] = _hash_json_file(child)
            elif child.suffix == ".jsonl":
                owned[relative] = _hash_jsonl_file(child)
            else:
                owned[relative] = _sha_file(child)
    return owned


def _should_skip_stage(ctx: BuildContext, stage_id: str) -> bool:
    if ctx.options.force:
        return False
    spec = _STAGE_REGISTRY[stage_id]
    if not _outputs_present(ctx, spec):
        return False
    prior = _load_stage_state(ctx.work_dir).get("stages", {}).get(stage_id)
    if not prior:
        return False
    if prior.get("version") != spec.version:
        return False
    inputs_hash = _inputs_hash(ctx, spec)
    if prior.get("inputs_hash") != inputs_hash:
        return False
    current_hash = _compute_outputs_hash(ctx, spec)
    return bool(prior.get("outputs_hash") == current_hash)


def _ensemble_variants(options: BuildOptions) -> list[RunVariant]:
    if options.no_ensemble:
        return [settings.ENSEMBLE_RUNS[0]]
    return list(settings.ENSEMBLE_RUNS)


def _persist_bundle(ctx: BuildContext, bundle: CandidatesBundle) -> None:
    atomic_write_json(ctx.work_dir / "candidates_bundle.json", bundle.model_dump(mode="json"))


def _load_bundle(ctx: BuildContext, units: Sequence[SourceUnit]) -> CandidatesBundle:
    cached = ctx.work_dir / "candidates_bundle.json"
    if cached.is_file():
        return CandidatesBundle.model_validate(json.loads(cached.read_text(encoding="utf-8")))
    ensemble = EnsembleResult.model_validate(
        json.loads((ctx.work_dir / "ensemble.json").read_text(encoding="utf-8"))
    )
    champion_variant = RunVariant(run_id=ensemble.champion_run, model=settings.EXTRACT_MODEL)
    return CandidatesBundle.from_ensemble(
        ensemble,
        brand=ctx.brand,
        units=units,
        champion_variant=champion_variant,
    )


def _strip_evidence(entity: dict[str, Any]) -> dict[str, Any]:
    cleaned = copy.deepcopy(entity)
    for key in list(cleaned):
        if key in _EVIDENCE_KEYS or key.endswith("_evidence"):
            cleaned.pop(key, None)
    value = cleaned.get("value")
    if isinstance(value, dict):
        for variant in value.get("variants") or []:
            if isinstance(variant, dict):
                variant.pop("evidence", None)
    governance = cleaned.get("governance")
    if isinstance(governance, dict):
        governance.pop("preferred_form_evidence", None)
    return cleaned


def _prepare_rule_for_pass_c(raw_rule: dict[str, Any], brand: str) -> dict[str, Any]:
    """Strip evidence then backfill v1-required prose fields from authoritative quotes."""
    stripped = _strip_evidence(raw_rule)
    if not str(stripped.get("rule_text") or "").strip():
        evidence = raw_rule.get("evidence")
        quotes = evidence.get("quotes") if isinstance(evidence, dict) else None
        if isinstance(quotes, list) and quotes and isinstance(quotes[0], str):
            stripped["rule_text"] = quotes[0]
        else:
            governance = stripped.get("governance")
            if isinstance(governance, dict) and governance.get("preferred_form"):
                stripped["rule_text"] = str(governance["preferred_form"])
            elif stripped.get("effect") is not None:
                stripped["rule_text"] = json.dumps(stripped["effect"], sort_keys=True)
            else:
                stripped["rule_text"] = str(stripped.get("id") or "rule")
    if not str(stripped.get("intent") or "").strip():
        stripped["intent"] = str(stripped["rule_text"])[:160]
    rule_id = raw_rule.get("id")
    if isinstance(rule_id, str) and rule_id.startswith(f"rule_{brand}_"):
        stripped["slug"] = rule_id[len(f"rule_{brand}_") :]
    return stripped


def _relation_endpoints(rel: Mapping[str, Any]) -> tuple[str | None, str | None]:
    for src_key, dst_key in (
        ("src_rule_id", "dst_rule_id"),
        ("from", "to"),
        ("from_id", "to_id"),
    ):
        src = rel.get(src_key)
        dst = rel.get(dst_key)
        if isinstance(src, str) and isinstance(dst, str) and src and dst:
            return src, dst
    return None, None


def _confidence(entity: Mapping[str, Any]) -> str | None:
    meta = entity.get("extraction_meta")
    if isinstance(meta, dict):
        raw = meta.get("confidence")
        if isinstance(raw, str):
            return raw
    return None


async def _run_s0(ctx: BuildContext) -> None:
    bible = load_bible(ctx.brand)
    units = run_segmenter(ctx.brand, bible, ctx.work_dir)
    ctx.artifacts["units"] = units
    ctx.artifacts["bible"] = bible


async def _run_s1(ctx: BuildContext) -> None:
    units = ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    labels = await run_classifier(
        ctx.brand,
        list(units),
        ctx.work_dir,
        client=ctx.client,
        usage=ctx.usage,
        cache_root=ctx.cache_root,
    )
    ctx.artifacts["labels"] = labels


async def _run_s2(ctx: BuildContext) -> None:
    units = ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    labels = ctx.artifacts.get("labels") or read_jsonl(ctx.work_dir / "unit_labels.jsonl", UnitLabel)
    runs_dir = ctx.work_dir / "runs"
    if runs_dir.exists():
        shutil.rmtree(runs_dir)
    outputs = []
    for variant in _ensemble_variants(ctx.options):
        output = await run_extraction(
            ctx.brand,
            variant,
            list(units),
            list(labels),
            ctx.usage,
            ctx.client,
            cache_root=ctx.cache_root,
            work_dir=ctx.work_dir,
            force=ctx.options.force,
            concurrency=ctx.options.concurrency,
        )
        outputs.append(output)
    ctx.artifacts["run_outputs"] = outputs


async def _run_s3(ctx: BuildContext) -> None:
    units = ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    run_outputs = ctx.artifacts.get("run_outputs")
    if run_outputs is None:
        run_outputs = []
        for run_dir in sorted((ctx.work_dir / "runs").iterdir()):
            if not run_dir.is_dir():
                continue
            # ponytail: S3 only needs variant metadata from directory name + provenance recompute.
            variant = RunVariant(run_id=run_dir.name, model=settings.EXTRACT_MODEL)
            from indexing_v2.extraction.runner import RunOutput

            primitive = json.loads((run_dir / "tokens_primitive.json").read_text(encoding="utf-8"))
            semantic = json.loads((run_dir / "tokens_semantic.json").read_text(encoding="utf-8"))
            catalog_rest = json.loads((run_dir / "catalog_rest.json").read_text(encoding="utf-8"))
            # ponytail: repair cross-kind id collisions before provenance uniqueness check.
            primitive, semantic = normalize_token_ids(ctx.brand, primitive, semantic)
            rule_groups = []
            rules_path = run_dir / "rules"
            if rules_path.is_dir():
                for group_file in sorted(rules_path.glob("*.json")):
                    group = json.loads(group_file.read_text(encoding="utf-8"))
                    from indexing_v2.extraction.runner import RuleGroupOutput

                    rule_groups.append(RuleGroupOutput.model_validate(group))
            # ponytail: disk runs may predate id assignment; normalize before provenance.
            rule_groups = normalize_rule_groups(ctx.brand, rule_groups)
            rules_by_doc_ref = {group.doc_ref: group.rules for group in rule_groups}
            run_outputs.append(
                RunOutput(
                    variant=variant,
                    primitive_tokens=primitive,
                    semantic_tokens=semantic,
                    catalog_rest=catalog_rest,
                    rules_by_doc_ref=rules_by_doc_ref,
                    rule_groups=sorted(rule_groups, key=lambda item: item.doc_ref),
                )
            )
    else:
        # In-memory s2 handoff: re-normalize so slug-only groups still clear provenance.
        from indexing_v2.extraction.runner import RunOutput

        normalized_outputs = []
        for output in run_outputs:
            primitive, semantic = normalize_token_ids(
                ctx.brand, output.primitive_tokens, output.semantic_tokens
            )
            rule_groups = normalize_rule_groups(ctx.brand, output.rule_groups)
            normalized_outputs.append(
                RunOutput(
                    variant=output.variant,
                    primitive_tokens=primitive,
                    semantic_tokens=semantic,
                    catalog_rest=output.catalog_rest,
                    rules_by_doc_ref={group.doc_ref: group.rules for group in rule_groups},
                    rule_groups=sorted(rule_groups, key=lambda item: item.doc_ref),
                )
            )
        run_outputs = normalized_outputs
    verified: list[VerifiedRunInput] = []
    for output in run_outputs:
        verified_run = build_verified_run(output, units)
        run_dir = ctx.work_dir / "runs" / output.variant.run_id
        write_provenance(verified_run.provenance, run_dir)
        verified.append(verified_run)
    atomic_write_json(
        ctx.work_dir / "verified_runs.json",
        [item.model_dump(mode="json") for item in verified],
    )
    provenance_files: dict[str, str] = {}
    for path in sorted((ctx.work_dir / "runs").rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ctx.work_dir)
        if "provenance" in relative.parts or path.name == "quarantine.json":
            provenance_files[relative.as_posix()] = (
                _hash_json_file(path) if path.suffix == ".json" else _sha_file(path)
            )
    atomic_write_json(
        ctx.work_dir / "provenance_state.json",
        {"schema_version": SCHEMA_VERSION, "files": provenance_files},
    )
    ctx.artifacts["verified_runs"] = verified


async def _run_s4(ctx: BuildContext) -> None:
    units = ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    labels = ctx.artifacts.get("labels") or read_jsonl(ctx.work_dir / "unit_labels.jsonl", UnitLabel)
    verified = ctx.artifacts.get("verified_runs")
    if verified is None:
        verified = [
            VerifiedRunInput.model_validate(item)
            for item in json.loads((ctx.work_dir / "verified_runs.json").read_text(encoding="utf-8"))
        ]
    ensemble = reconcile_ensemble(verified, units, labels)
    write_candidates(ensemble, ctx.work_dir)
    atomic_write_json(ctx.work_dir / "ensemble.json", ensemble.model_dump(mode="json"))
    # ponytail: S5 legitimately rewrites work_dir/candidates in place, so S4's cache
    # identity is scoped to its one durable handoff file (ensemble.json) rather than
    # the shared scratch directory S5 will overwrite next.
    atomic_write_json(
        ctx.work_dir / "ensemble_outputs.json",
        {
            "schema_version": SCHEMA_VERSION,
            "files": {"ensemble.json": _hash_json_file(ctx.work_dir / "ensemble.json")},
        },
    )
    champion_variant = next(
        run.output.variant
        for run in verified
        if run.output.variant.run_id == ensemble.champion_run
    )
    bundle = CandidatesBundle.from_ensemble(
        ensemble,
        brand=ctx.brand,
        units=units,
        champion_variant=champion_variant,
    )
    ctx.artifacts["ensemble"] = ensemble
    ctx.artifacts["candidates_bundle"] = bundle


def _s5_reconstruct_bundle(ctx: BuildContext) -> tuple[EnsembleResult, CandidatesBundle]:
    ensemble_obj = ctx.artifacts.get("ensemble")
    if isinstance(ensemble_obj, EnsembleResult):
        ensemble = ensemble_obj
    else:
        ensemble = EnsembleResult.model_validate(
            json.loads((ctx.work_dir / "ensemble.json").read_text(encoding="utf-8"))
        )
    units = ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    champion_variant = RunVariant(run_id=ensemble.champion_run, model=settings.EXTRACT_MODEL)
    bundle = CandidatesBundle.from_ensemble(
        ensemble,
        brand=ctx.brand,
        units=list(units),
        champion_variant=champion_variant,
    )
    return ensemble, bundle


async def _run_s5(ctx: BuildContext) -> None:
    """Wire S5 to WP-10's native artifact contract: ``findings.jsonl``, ``audit/patches.jsonl``,
    and patched ``candidates/*.json`` all live directly under ``_work``, matching S4's own
    candidate layout. Only minimal driver handoff files (``bundle.json``, ``result.json``/
    ``skipped.json``, and the caching receipt) are kept under ``_work/critic``.
    """
    critic_dir = ctx.work_dir / "critic"
    if critic_dir.exists():
        shutil.rmtree(critic_dir)
    critic_dir.mkdir(parents=True)
    # ponytail: root findings/audit are stage-owned by S5 only; always start from a clean
    # slate so toggling --no-critic never leaves a stale critique behind.
    (ctx.work_dir / "findings.jsonl").unlink(missing_ok=True)
    audit_dir = ctx.work_dir / "audit"
    if audit_dir.exists():
        shutil.rmtree(audit_dir)

    bundle = ctx.artifacts.get("candidates_bundle")
    if bundle is None:
        _, bundle = _s5_reconstruct_bundle(ctx)

    if ctx.options.no_critic:
        ensemble, bundle = _s5_reconstruct_bundle(ctx)
        # ponytail: rewrite candidates/ from the plain ensemble so it never carries a
        # stale critic patch from a prior --no-critic=False run.
        write_candidates(ensemble, ctx.work_dir)
        atomic_write_json(
            critic_dir / "skipped.json",
            {"schema_version": SCHEMA_VERSION, "skipped": True, "reason": "--no-critic"},
        )
        ctx.artifacts["candidates_bundle"] = bundle
        ctx.artifacts["critic_result"] = None
        atomic_write_json(critic_dir / "bundle.json", bundle.model_dump(mode="json"))
        atomic_write_json(
            critic_dir / "manifest.json",
            {"schema_version": SCHEMA_VERSION, "files": _s5_owned_files(ctx.work_dir)},
        )
        return

    units = ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    ensemble = ctx.artifacts.get("ensemble") or EnsembleResult.model_validate(
        json.loads((ctx.work_dir / "ensemble.json").read_text(encoding="utf-8"))
    )
    critic_input = CandidateSet.from_ensemble(ensemble)
    result = await run_critic(
        ctx.brand,
        list(units),
        critic_input,
        ctx.usage,
        ctx.client,
        work_dir=ctx.work_dir,
        cache_root=ctx.cache_root,
        champion_run_id=bundle.champion_variant.run_id if bundle.champion_variant else None,
        concurrency=ctx.options.concurrency,
        max_rounds=ctx.options.max_critic_rounds,
    )
    bundle = bundle.with_critic_candidates(result.candidates)
    ctx.artifacts["candidates_bundle"] = bundle
    ctx.artifacts["critic_result"] = result
    atomic_write_json(critic_dir / "bundle.json", bundle.model_dump(mode="json"))
    atomic_write_json(critic_dir / "result.json", result.model_dump(mode="json"))
    atomic_write_json(
        critic_dir / "manifest.json",
        {"schema_version": SCHEMA_VERSION, "files": _s5_owned_files(ctx.work_dir)},
    )


async def _run_s6(ctx: BuildContext) -> None:
    units = ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    labels = ctx.artifacts.get("labels") or read_jsonl(ctx.work_dir / "unit_labels.jsonl", UnitLabel)
    bundle = ctx.artifacts.get("candidates_bundle")
    if bundle is None:
        bundle = CandidatesBundle.model_validate(
            json.loads((ctx.work_dir / "critic" / "bundle.json").read_text(encoding="utf-8"))
        )
    triage_path = ctx.kb_root / settings.TRIAGE_FILE
    if ctx.options.no_gaps:
        from indexing_v2.extraction.provenance import verify_entities

        provenance_result = verify_entities(bundle.entities_by_kind(), units)
        report, soft = build_ledger(labels, provenance_result, bundle, rounds=0)
        computed = compute_triage_items(
            report,
            labels_by_id={label.unit_id: label for label in labels},
            candidates=bundle,
            provenance=provenance_result,
        )
        history = load_triage_history(triage_path)
        merged, to_append = rebuild_triage(computed, history)
        append_only = to_append
        if append_only:
            from indexing_v2.extraction.ledger import append_triage_items

            append_triage_items(triage_path, append_only)
        write_ledger(ctx.work_dir, LedgerDocument(coverage=report, soft_mismatches=soft))
        gap_result = GapLoopResult(
            coverage=report,
            soft_mismatches=soft,
            triage=merged,
            rounds_run=0,
            stopped_reason="empty_queue",
            candidates=bundle,
            provenance=provenance_result,
        )
    else:
        from indexing_v2.extraction.provenance import verify_entities

        provenance_result = verify_entities(bundle.entities_by_kind(), units)
        gap_result = await run_gap_loop(
            labels,
            bundle,
            provenance_result,
            units=units,
            client=ctx.client,
            usage=ctx.usage,
            work_dir=ctx.work_dir,
            triage_path=triage_path,
            cache_root=ctx.cache_root,
            max_rounds=ctx.options.max_gap_rounds,
        )
        bundle = gap_result.candidates
    ctx.artifacts["gap_result"] = gap_result
    ctx.artifacts["candidates_bundle"] = bundle
    ctx.artifacts["triage"] = gap_result.triage
    ctx.artifacts["coverage"] = gap_result.coverage
    _persist_bundle(ctx, bundle)
    atomic_write_json(ctx.work_dir / "gap_result.json", gap_result.model_dump(mode="json"))


def _build_pass_c(ctx: BuildContext) -> PassCResult:
    units = ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    bundle: CandidatesBundle = ctx.artifacts.get("candidates_bundle") or _load_bundle(ctx, units)
    gap: GapLoopResult | None = ctx.artifacts.get("gap_result")
    if gap is None:
        from indexing_v2.extraction.provenance import verify_entities

        provenance_result = verify_entities(bundle.entities_by_kind(), units)
        gap = GapLoopResult(
            coverage=CoverageReport.model_validate(
                json.loads((ctx.work_dir / "ledger.json").read_text(encoding="utf-8"))["coverage"]
            ),
            candidates=bundle,
            provenance=provenance_result,
            rounds_run=0,
            stopped_reason="empty_queue",
            triage=load_triage_history(ctx.kb_root / settings.TRIAGE_FILE),
        )
    blobs = json.loads((ctx.work_dir / "blobs.json").read_text(encoding="utf-8"))
    warns = Warnings()
    section_vocab = get_registries().section_types(ctx.brand)

    stripped_tokens = [
        _strip_evidence(token) for token in bundle.tokens_primitive + bundle.tokens_semantic
    ]
    raw_catalog = {
        "tokens": stripped_tokens,
        "assets": [_strip_evidence(asset) for asset in bundle.assets],
        "subtypes": [_strip_evidence(sub) for sub in bundle.subtypes],
        "templates": [_strip_evidence(tpl) for tpl in bundle.templates],
        "template_groups": [],
        "asset_groups": [],
    }
    cat = validate_catalog(raw_catalog, ctx.brand, warns)
    ingest_template_library(ctx.brand, cat, warns)
    link_templates(ctx.brand, cat, warns)
    merge_map, near_dupes = dedupe_tokens(cat["tokens"], warns)
    for asset in cat["assets"].values():
        asset.contains_token_ids = [merge_map.get(x, x) for x in asset.contains_token_ids]
        asset.required_pairing_token_ids = [
            merge_map.get(x, x) for x in asset.required_pairing_token_ids
        ]

    catalog_ids = (
        set(cat["tokens"])
        | set(cat["assets"])
        | set(cat["subtypes"])
        | set(cat["asset_groups"])
    )
    groups: dict[str, RuleGroup] = {}
    for group_id, doc_ref in sorted(bundle.rule_group_doc_refs.items()):
        groups[group_id] = RuleGroup(
            id=group_id,
            brand_id=ctx.brand,
            source="design_bible",
            doc_ref=doc_ref,
            original_text=blobs.get(doc_ref, ""),
        )

    rules: dict[str, Any] = {}
    used_ids: set[str] = set()
    relations: list[RuleRelation] = []
    for group_id, doc_ref in sorted(bundle.rule_group_doc_refs.items()):
        for raw_rule in bundle.rules_by_group.get(group_id, []):
            rule = validate_rule(
                _prepare_rule_for_pass_c(raw_rule, ctx.brand),
                ctx.brand,
                group_id,
                doc_ref,
                used_ids,
                catalog_ids,
                warns,
                section_vocab,
            )
            if rule is not None:
                rules[rule.id] = rule
        for rel in bundle.relations_by_group.get(group_id, []):
            src, dst = _relation_endpoints(rel)
            rel_type = rel.get("relation") or rel.get("kind")
            if src and dst and src in rules and dst in rules and isinstance(rel_type, str):
                relations.append(
                    RuleRelation(
                        src_rule_id=src,
                        dst_rule_id=dst,
                        relation=rel_type,
                        note=str(rel.get("note") or ""),
                    )
                )

    dedupe_rules(rules, relations, warns)
    sidecars: dict[str, dict[str, Any]] = {}
    confidence_by_id: dict[str, str] = {}
    for bucket in (
        bundle.tokens_primitive,
        bundle.tokens_semantic,
        bundle.assets,
        bundle.subtypes,
        bundle.templates,
        (rule for rules_list in bundle.rules_by_group.values() for rule in rules_list),
    ):
        for entity in bucket:
            entity_id = str(entity.get("id", ""))
            if not entity_id:
                continue
            conf = _confidence(entity)
            if conf:
                confidence_by_id[entity_id] = conf
            records = gap.provenance.records_by_entity.get(entity_id, [])
            if records or entity.get("extraction_meta") is not None:
                sidecars[entity_id] = {
                    "schema_version": SCHEMA_VERSION,
                    "entity_id": entity_id,
                    "extraction_meta": entity.get("extraction_meta"),
                    "provenance": [record.model_dump(mode="json") for record in records],
                }

    return PassCResult(
        rules=rules,
        cat=cat,
        groups=groups,
        relations=relations,
        warns=warns.items,
        sidecars=sidecars,
        confidence_by_id=confidence_by_id,
    )


def _serialize_pass_c(result: PassCResult) -> dict[str, Any]:
    return {
        "rules": {
            rule_id: rule.model_dump(mode="json", exclude_none=True)
            for rule_id, rule in sorted(result.rules.items())
        },
        "cat": {
            key: (
                {entity_id: entity.model_dump(mode="json", exclude_none=True) for entity_id, entity in value.items()}
                if key in {"tokens", "assets", "subtypes", "templates", "template_groups", "asset_groups"}
                and isinstance(value, dict)
                else value
            )
            for key, value in result.cat.items()
        },
        "groups": {
            group_id: group.model_dump(mode="json", exclude_none=True)
            for group_id, group in sorted(result.groups.items())
        },
        "relations": [rel.model_dump(mode="json", exclude_none=True) for rel in result.relations],
        "warns": list(result.warns),
        "sidecars": result.sidecars,
        "confidence_by_id": dict(sorted(result.confidence_by_id.items())),
    }


async def _run_s7(ctx: BuildContext) -> None:
    result = _build_pass_c(ctx)
    atomic_write_json(ctx.work_dir / "pass_c.json", _serialize_pass_c(result))
    ctx.artifacts["pass_c"] = result


async def _run_s8(ctx: BuildContext) -> None:
    from indexing_v2.tokens_dtcg.export import export_tokens

    pass_c = ctx.artifacts.get("pass_c")
    if pass_c is None:
        pass_c = _build_pass_c(ctx)
        ctx.artifacts["pass_c"] = pass_c
    warns = Warnings()
    warns.items.extend(pass_c.warns)
    near_dupes: list[str] = []
    rule_merge_notes: list[str] = []

    work_backup: Path | None = None
    triage_path = ctx.kb_root / settings.TRIAGE_FILE
    triage_bytes = triage_path.read_bytes() if triage_path.is_file() else None
    if ctx.work_dir.exists():
        work_backup = ctx.kb_root.parent / f".{ctx.brand}_work_backup"
        if work_backup.exists():
            shutil.rmtree(work_backup)
        shutil.move(str(ctx.work_dir), str(work_backup))

    try:
        write_kb(
            ctx.brand,
            pass_c.rules,
            pass_c.cat,
            pass_c.groups,
            pass_c.relations,
            warns,
            near_dupes,
            rule_merge_notes,
        )
    finally:
        if work_backup is not None and work_backup.exists():
            if ctx.work_dir.exists():
                shutil.rmtree(ctx.work_dir)
            shutil.move(str(work_backup), str(ctx.work_dir))
    if triage_bytes is not None:
        triage_path.parent.mkdir(parents=True, exist_ok=True)
        triage_path.write_bytes(triage_bytes)
    provenance_dir = ctx.kb_root / "provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    expected = {f"{entity_id}.json" for entity_id in pass_c.sidecars}
    if provenance_dir.exists():
        for stale in sorted(provenance_dir.glob("*.json")):
            if stale.name not in expected:
                stale.unlink()
    for entity_id in sorted(pass_c.sidecars):
        atomic_write_json(provenance_dir / f"{entity_id}.json", pass_c.sidecars[entity_id])

    index_path = ctx.kb_root / "rules" / "_index.json"
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        for row in index:
            entity_id = str(row.get("id", ""))
            if entity_id in pass_c.confidence_by_id:
                row["confidence"] = pass_c.confidence_by_id[entity_id]
        atomic_write_json(index_path, index)

    legacy_dtcg_dir = ctx.kb_root / "tokens_dtcg"
    if legacy_dtcg_dir.exists():
        shutil.rmtree(legacy_dtcg_dir)
    export_tokens(pass_c.cat["tokens"], ctx.kb_root / "design_tokens")
    _write_review_analysis_docs(ctx)
    get_registries().save()
    atomic_write_json(
        ctx.work_dir / "s8_outputs.json",
        {"schema_version": SCHEMA_VERSION, "files": _s8_owned_files(ctx.kb_root)},
    )


async def _run_s9(ctx: BuildContext) -> None:
    from indexing_v2.consistency.pairwise import analyze_pairwise
    from indexing_v2.consistency.smt import analyze_smt, smt_status, write_analysis_conflicts
    from indexing_v2.contracts import KBSnapshot

    snapshot = KBSnapshot.load(ctx.brand)
    pairwise = analyze_pairwise(snapshot)
    smt = analyze_smt(snapshot, console=ctx.console)
    analysis_dir = ctx.kb_root / "analysis"
    if analysis_dir.exists():
        shutil.rmtree(analysis_dir)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    artifact = write_analysis_conflicts(
        analysis_dir / "conflicts.json",
        pairwise=pairwise,
        smt=smt,
    )
    atomic_write_json(analysis_dir / "dead_rules.json", [item.model_dump(mode="json") for item in pairwise.dead_entries])
    atomic_write_json(
        analysis_dir / "precedence_log.json",
        [item.model_dump(mode="json") for item in pairwise.precedence_proposals],
    )
    atomic_write_json(analysis_dir / "smt.json", smt.model_dump(mode="json"))
    ctx.artifacts["pairwise"] = pairwise
    ctx.artifacts["smt"] = smt
    ctx.artifacts["analysis_artifact"] = artifact
    ctx.artifacts["smt_status"] = smt_status()
    gap: GapLoopResult | None = ctx.artifacts.get("gap_result")
    gap_result_path = ctx.work_dir / "gap_result.json"
    if gap is None and gap_result_path.is_file():
        gap = GapLoopResult.model_validate(
            json.loads(gap_result_path.read_text(encoding="utf-8"))
        )
    s6_triage = (
        gap.triage
        if gap is not None
        else list(ctx.artifacts.get("triage") or [])
    )
    computed = [
        *s6_triage,
        *compute_s9_triage_items(pairwise, smt),
    ]
    triage_path = ctx.kb_root / settings.TRIAGE_FILE
    merged, to_append = rebuild_triage(
        computed,
        load_triage_history(triage_path),
    )
    append_triage_items(triage_path, to_append)
    ctx.artifacts["triage"] = merged
    _write_review_analysis_docs(ctx)


async def _run_s10(ctx: BuildContext) -> None:
    from indexing_v2.cascade.compile import compile_cascade
    from indexing_v2.contracts import KBSnapshot
    from indexing_v2.reports import render_cascade_schema

    snapshot = KBSnapshot.load(ctx.brand)
    kb_hash = compute_kb_hash(ctx.kb_root)
    cascade_root = ctx.kb_root / "cascade"
    index = compile_cascade(snapshot, cascade_root, kb_hash)
    schema_dir = ctx.kb_root / "schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "cascade.md").write_text(render_cascade_schema(), encoding="utf-8")
    ctx.artifacts["cascade_index"] = index
    ctx.artifacts["kb_hash"] = kb_hash


async def _run_s11(ctx: BuildContext) -> None:
    completion_path = ctx.work_dir / "summarize_embed.json"
    completion_path.unlink(missing_ok=True)
    if ctx.options.skip_summarize_embed:
        atomic_write_json(
            completion_path,
            {
                "schema_version": SCHEMA_VERSION,
                "status": "skipped",
                "rules_hash": _hash_kb_artifact(ctx.kb_root, "rules/"),
            },
        )
        return
    runner: SummarizeEmbedRunner
    if ctx.summarize_embed is not None:
        runner = ctx.summarize_embed
    else:
        from indexing.summarize_embed import process_brand as summarize_embed_process

        runner = summarize_embed_process
    await runner(ctx.brand, ctx.usage)
    atomic_write_json(
        completion_path,
        {
            "schema_version": SCHEMA_VERSION,
            "status": "completed",
            "rules_hash": _hash_kb_artifact(ctx.kb_root, "rules/"),
        },
    )


_STAGE_RUNNERS: dict[str, Callable[[BuildContext], Awaitable[None]]] = {
    "s0": _run_s0,
    "s1": _run_s1,
    "s2": _run_s2,
    "s3": _run_s3,
    "s4": _run_s4,
    "s5": _run_s5,
    "s6": _run_s6,
    "s7": _run_s7,
    "s8": _run_s8,
    "s9": _run_s9,
    "s10": _run_s10,
    "s11": _run_s11,
}


def compute_kb_hash(kb_root: Path) -> str:
    return stable_hash(
        {
            "entities": _receipt_hash(
                kb_root,
                kb_root / "_work" / "s8_outputs.json",
                owned=_s8_owned_files,
            ),
            "analysis": _hash_kb_artifact(kb_root, "analysis/"),
        }
    )


def _queue_counts(triage: Sequence[TriageItem]) -> dict[str, dict[str, int]]:
    counts = {
        queue: {"open": 0, "waived": 0, "deferred": 0}
        for queue in ("unclaimed_unit", "unverified_value", "over_claimed", "conflict")
    }
    for item in triage:
        status = item.disposition.status
        bucket = counts[item.queue]
        if status == "waived":
            bucket["waived"] += 1
        elif status == "deferred":
            bucket["deferred"] += 1
        else:
            bucket["open"] += 1
    return counts


def _evaluate_acceptance(ctx: BuildContext) -> tuple[dict[str, str], bool]:
    gap: GapLoopResult | None = ctx.artifacts.get("gap_result")
    critic: CriticResult | None = ctx.artifacts.get("critic_result")
    pairwise = ctx.artifacts.get("pairwise")
    smt = ctx.artifacts.get("smt")
    triage = ctx.artifacts.get("triage") or []
    invariants: dict[str, str] = {}

    open_conflict_keys = {
        item.key
        for item in triage
        if item.queue == "conflict"
        and item.disposition.status == "open"
    }
    live_verbatim_keys = {
        triage_key_conflict(conflict)
        for conflict in (pairwise.conflicts if pairwise else [])
        if conflict.kind == "verbatim_clash"
    } & open_conflict_keys
    invariants["verbatim_integrity"] = (
        "pass" if not live_verbatim_keys else "fail"
    )
    live_class_a_keys = current_class_a_conflict_keys(
        triage,
        pairwise=pairwise,
        smt=smt,
    )
    invariants["no_live_contradictions"] = (
        "pass" if not live_class_a_keys else "fail"
    )

    quarantined: set[str] = set()
    if gap is not None:
        quarantined = {entry.entity_id for entry in gap.provenance.quarantine}
    triage_subjects = {item.subject_id for item in triage if item.queue != "conflict"}
    silent = sorted(quarantined - triage_subjects)
    invariants["no_silent_quarantine"] = "pass" if not silent else "fail"

    open_critical = [
        finding
        for finding in (critic.findings if critic else [])
        if finding.severity == "critical" and finding.resolution == "open"
    ]
    invariants["no_open_criticals"] = "pass" if not open_critical else "fail"
    invariants["determinism"] = str(ctx.artifacts.get("determinism_status", "fail"))

    passed = all(status == "pass" for status in invariants.values())
    open_triage = any(item.disposition.status == "open" for item in triage)
    if open_triage:
        passed = False
    return invariants, passed


def _metric_snapshot(ctx: BuildContext) -> dict[str, Any]:
    gap: GapLoopResult | None = ctx.artifacts.get("gap_result")
    ensemble: EnsembleResult | None = ctx.artifacts.get("ensemble")
    critic: CriticResult | None = ctx.artifacts.get("critic_result")
    pairwise = ctx.artifacts.get("pairwise")
    smt = ctx.artifacts.get("smt")
    cascade_index = ctx.artifacts.get("cascade_index")
    units = ctx.artifacts.get("units") or []
    labels = ctx.artifacts.get("labels") or []
    coverage = gap.coverage if gap else None
    verification_rate = 0.0
    quarantine_count = 0
    quarantine_rate = 0.0
    if gap is not None:
        quarantine_count = len(gap.provenance.quarantine)
        total_records = sum(len(rows) for rows in gap.provenance.records_by_entity.values())
        verified = sum(
            1
            for rows in gap.provenance.records_by_entity.values()
            for record in rows
            if record.verification in {"value_verified", "span_verified"}
        )
        verification_rate = verified / total_records if total_records else 1.0
        # ponytail: denominator is every entity provenance actually considered
        # (``records_by_entity`` covers quarantined and clean entities alike),
        # so the rate is well-defined even before any entity is quarantined.
        total_entities = len(gap.provenance.records_by_entity)
        quarantine_rate = quarantine_count / total_entities if total_entities else 0.0
    ensemble_runs = len(_ensemble_variants(ctx.options))
    high = medium = low = 0
    if ensemble is not None:
        for bucket in (
            ensemble.tokens_primitive,
            ensemble.tokens_semantic,
            ensemble.assets,
            ensemble.subtypes,
            ensemble.templates,
        ):
            for entity in bucket:
                meta = entity.get("extraction_meta") or {}
                conf = meta.get("confidence")
                if conf == "high":
                    high += 1
                elif conf == "medium":
                    medium += 1
                elif conf == "low":
                    low += 1
        for rules in ensemble.rule_groups.values():
            for rule in rules:
                meta = rule.get("extraction_meta") or {}
                conf = meta.get("confidence")
                if conf == "high":
                    high += 1
                elif conf == "medium":
                    medium += 1
                elif conf == "low":
                    low += 1
    critic_counts = Counter(finding.resolution for finding in (critic.findings if critic else []))
    consistency = {
        "hard_hard": sum(1 for c in (pairwise.conflicts if pairwise else []) if c.kind == "hard_hard"),
        "equal_specificity": sum(
            1 for c in (pairwise.conflicts if pairwise else []) if c.kind == "equal_specificity"
        ),
        "dead_rules": len(pairwise.dead_entries) if pairwise else 0,
        "global_unsat": len(smt.global_unsat) if smt else 0,
    }
    return {
        "units": len(units),
        "required_units": sum(1 for label in labels if label.required),
        "coverage": {
            "value": coverage.value_coverage if coverage else 0.0,
            "normative": coverage.normative_coverage if coverage else 0.0,
            "verbatim": coverage.verbatim_coverage if coverage else 0.0,
            "rounds": coverage.rounds if coverage else 0,
        },
        "verification": {
            "value_verified_rate": verification_rate,
            "quarantined": quarantine_count,
            "quarantine_rate": quarantine_rate,
        },
        "ensemble": {
            "runs": ensemble_runs,
            "high": high,
            "medium": medium,
            "low": low,
        },
        "critic": {
            "findings": len(critic.findings) if critic else 0,
            "applied": critic_counts.get("applied", 0),
            "deferred_human": critic_counts.get("deferred_human", 0),
        },
        "consistency": consistency,
        "cascade": {
            "contexts": len(cascade_index.contexts) if cascade_index else 0,
            "distinct_sheets": len(
                {entry.sheet_hash for entry in cascade_index.contexts.values()}
            )
            if cascade_index
            else 0,
        },
    }


def _flatten_metrics(metrics: dict[str, Any], prefix: str = "") -> dict[str, float | int]:
    flat: dict[str, float | int] = {}
    for key, value in metrics.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            flat.update(_flatten_metrics(value, path))
        elif isinstance(value, (int, float)):
            flat[path] = value
    return flat


def _load_accepted_baseline(ctx: BuildContext) -> dict[str, Any] | None:
    """Load ``manifest.accepted.json`` when it is comparable to the current build.

    A baseline is only comparable when its bible hash matches the current bible
    hash; a bible edit invalidates every metric's meaning (units/rules shift), so
    there is nothing honest to ratchet or delta against.
    """
    baseline_path = ctx.kb_root / "manifest.accepted.json"
    if not baseline_path.is_file():
        return None
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if baseline.get("inputs", {}).get("bible_hash") != ctx.bible_hash:
        return None
    return cast(dict[str, Any], baseline)


def _signed_delta(value: float | int, previous: float | int) -> str:
    delta = value - previous
    if isinstance(value, int) and isinstance(previous, int):
        return f"{delta:+d}"
    return f"{round(float(delta), 6):+g}"


def _telemetry_deltas(
    metrics: dict[str, Any], baseline: dict[str, Any] | None
) -> dict[str, str]:
    if baseline is None:
        return {}
    current = _flatten_metrics(metrics)
    accepted = _flatten_metrics(baseline.get("metrics", {}))
    return {
        key: _signed_delta(value, accepted[key])
        for key, value in sorted(current.items())
        if key in accepted
    }


def _ratchet_status(
    ctx: BuildContext, metrics: dict[str, Any], baseline: dict[str, Any] | None
) -> str:
    if not ctx.options.ratchet:
        return "skipped (--ratchet not set)"
    if baseline is None:
        if not (ctx.kb_root / "manifest.accepted.json").is_file():
            return "skipped (no accepted baseline)"
        return "skipped (bible hash changed)"
    current = _flatten_metrics(metrics)
    accepted = _flatten_metrics(baseline.get("metrics", {}))
    worse: list[str] = []
    for key, value in current.items():
        if key not in accepted:
            continue
        previous = accepted[key]
        if not isinstance(previous, (int, float)):
            continue
        if key in _RATCHET_HIGHER_BETTER and value < previous:
            worse.append(f"{key}: {value} < {previous}")
        elif key in _RATCHET_LOWER_BETTER and value > previous:
            worse.append(f"{key}: {value} > {previous}")
    if worse:
        return "fail (" + "; ".join(sorted(worse)) + ")"
    return "pass"


def _write_review_analysis_docs(ctx: BuildContext) -> None:
    from indexing_v2.consistency.report import ConflictsReportInput, render_conflicts_report
    from indexing_v2.reports import CoverageReportInput, CriticReportInput, render_coverage_report, render_critic_findings

    review_dir = ctx.kb_root / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    units = {
        unit.unit_id: unit
        for unit in (ctx.artifacts.get("units") or read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit))
    }
    coverage = ctx.artifacts.get("coverage")
    triage = ctx.artifacts.get("triage") or []
    if coverage is not None:
        (review_dir / "coverage_report.md").write_text(
            render_coverage_report(
                CoverageReportInput(report=coverage, triage=triage, source_units=units)
            ),
            encoding="utf-8",
        )
    critic = ctx.artifacts.get("critic_result")
    if critic is not None:
        (review_dir / "critic_findings.md").write_text(
            render_critic_findings(CriticReportInput(findings=critic.findings)),
            encoding="utf-8",
        )
    pairwise = ctx.artifacts.get("pairwise")
    smt = ctx.artifacts.get("smt")
    artifact = ctx.artifacts.get("analysis_artifact")
    if pairwise is not None:
        (review_dir / "conflicts.md").write_text(
            render_conflicts_report(
                ConflictsReportInput.from_analysis(pairwise, smt=smt, artifact=artifact)
            ),
            encoding="utf-8",
        )


def build_manifest(ctx: BuildContext) -> dict[str, Any]:
    invariants, acceptance_passed = _evaluate_acceptance(ctx)
    metrics = _metric_snapshot(ctx)
    triage = ctx.artifacts.get("triage") or []
    baseline = _load_accepted_baseline(ctx)
    ratchet = _ratchet_status(ctx, metrics, baseline)
    telemetry_deltas = _telemetry_deltas(metrics, baseline)
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "brand": ctx.brand,
        "built_at": ctx.built_at,
        "driver_version": DRIVER_VERSION,
        "inputs": ctx.input_hashes,
        "stages": {
            stage: {
                "version": meta["version"],
                "out_hash": meta["outputs_hash"],
            }
            for stage, meta in sorted(ctx.stage_records.items())
        },
        "metrics": metrics,
        "acceptance": {
            "invariants": invariants,
            "passed": acceptance_passed,
            "queues": _queue_counts(triage),
            "telemetry_deltas": telemetry_deltas,
            "ratchet": ratchet,
        },
    }
    smt_status_value = ctx.artifacts.get("smt_status")
    if smt_status_value == "skipped":
        manifest["smt"] = "skipped"
    return manifest


def _write_manifest_summary(ctx: BuildContext, manifest: dict[str, Any]) -> None:
    from indexing_v2.reports import ManifestReportInput, render_manifest_summary

    validated = ManifestReportInput.model_validate(manifest)
    review_dir = ctx.kb_root / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "manifest_summary.md").write_text(
        render_manifest_summary(validated), encoding="utf-8"
    )


def _write_manifest(ctx: BuildContext) -> tuple[dict[str, Any], bool]:
    manifest = build_manifest(ctx)
    atomic_write_json(ctx.kb_root / "manifest.json", manifest)
    _write_manifest_summary(ctx, manifest)
    if ctx.options.accept_baseline:
        tmp = ctx.kb_root / "manifest.accepted.json.tmp"
        accepted_path = ctx.kb_root / "manifest.accepted.json"
        tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(accepted_path)
    passed = bool(manifest["acceptance"]["passed"])
    ratchet_failed = str(manifest["acceptance"]["ratchet"]).startswith("fail")
    if ctx.options.ratchet and ratchet_failed:
        passed = False
    return manifest, passed


async def _hydrate_artifacts_for_manifest(ctx: BuildContext) -> None:
    if "units" not in ctx.artifacts and (ctx.work_dir / "units.jsonl").is_file():
        ctx.artifacts["units"] = read_jsonl(ctx.work_dir / "units.jsonl", SourceUnit)
    if "labels" not in ctx.artifacts and (ctx.work_dir / "unit_labels.jsonl").is_file():
        ctx.artifacts["labels"] = read_jsonl(ctx.work_dir / "unit_labels.jsonl", UnitLabel)
    if "ensemble" not in ctx.artifacts and (ctx.work_dir / "ensemble.json").is_file():
        ctx.artifacts["ensemble"] = EnsembleResult.model_validate(
            json.loads((ctx.work_dir / "ensemble.json").read_text(encoding="utf-8"))
        )
    critic_result_path = ctx.work_dir / "critic" / "result.json"
    if "critic_result" not in ctx.artifacts and critic_result_path.is_file():
        ctx.artifacts["critic_result"] = CriticResult.model_validate(
            json.loads(critic_result_path.read_text(encoding="utf-8"))
        )
    triage_path = ctx.kb_root / settings.TRIAGE_FILE
    gap_result_path = ctx.work_dir / "gap_result.json"
    gap: GapLoopResult | None = ctx.artifacts.get("gap_result")
    if gap is None and gap_result_path.is_file():
        gap = GapLoopResult.model_validate(
            json.loads(gap_result_path.read_text(encoding="utf-8"))
        )
        ctx.artifacts["gap_result"] = gap
        ctx.artifacts["coverage"] = gap.coverage
        if "triage" not in ctx.artifacts:
            ctx.artifacts["triage"] = gap.triage
    if "pairwise" not in ctx.artifacts:
        conflicts_path = ctx.kb_root / "analysis" / "conflicts.json"
        if conflicts_path.is_file():
            from indexing_v2.consistency.pairwise import PairwiseAnalysisResult
            from indexing_v2.consistency.smt import AnalysisConflictsArtifact
            from indexing_v2.contracts import Conflict

            artifact = AnalysisConflictsArtifact.model_validate(
                json.loads(conflicts_path.read_text(encoding="utf-8"))
            )
            ctx.artifacts["analysis_artifact"] = artifact
            ctx.artifacts["pairwise"] = PairwiseAnalysisResult(
                conflicts=[
                    Conflict.model_validate(item)
                    for item in artifact.conflicts
                    if item.get("kind") != "global_unsat"
                ],
                dead_entries=list(artifact.dead_entries),
                precedence_proposals=list(artifact.precedence_proposals),
            )
    smt_path = ctx.kb_root / "analysis" / "smt.json"
    if "smt" not in ctx.artifacts and smt_path.is_file():
        from indexing_v2.consistency.smt import SmtAnalysisResult

        smt = SmtAnalysisResult.model_validate(
            json.loads(smt_path.read_text(encoding="utf-8"))
        )
        ctx.artifacts["smt"] = smt
        ctx.artifacts["smt_status"] = smt.status
    s6_triage = (
        gap.triage
        if gap is not None
        else list(ctx.artifacts.get("triage") or [])
    )
    computed = [
        *s6_triage,
        *compute_s9_triage_items(
            ctx.artifacts.get("pairwise"),
            ctx.artifacts.get("smt"),
        ),
    ]
    merged, _ = rebuild_triage(
        computed,
        load_triage_history(triage_path),
    )
    ctx.artifacts["triage"] = merged
    contexts_path = ctx.kb_root / "cascade" / "contexts.json"
    if "cascade_index" not in ctx.artifacts and contexts_path.is_file():
        from indexing_v2.cascade.compile import ContextIndex

        ctx.artifacts["cascade_index"] = ContextIndex.model_validate(
            json.loads(contexts_path.read_text(encoding="utf-8"))
        )


def _determinism_input_signature(ctx: BuildContext) -> str:
    return stable_hash(
        {
            "inputs": ctx.input_hashes,
            "stages": {
                stage_id: {
                    "version": _STAGE_REGISTRY[stage_id].version,
                    "local_inputs": _local_stage_inputs(ctx, _STAGE_REGISTRY[stage_id]),
                }
                for stage_id in sorted(ctx.stage_records)
            },
        }
    )


def _determinism_fingerprint(ctx: BuildContext) -> str:
    outputs: dict[str, Any] = {}
    for stage_id in sorted(ctx.stage_records):
        spec = _STAGE_REGISTRY[stage_id]
        outputs[stage_id] = {
            "version": spec.version,
            "outputs_hash": (
                _compute_outputs_hash(ctx, spec) if _outputs_present(ctx, spec) else "missing"
            ),
        }
    return stable_hash(outputs)


def _record_determinism(ctx: BuildContext) -> None:
    state = _load_stage_state(ctx.work_dir)
    signature = _determinism_input_signature(ctx)
    fingerprint = _determinism_fingerprint(ctx)
    prior = state.get("determinism")
    if not isinstance(prior, dict) or prior.get("input_signature") != signature:
        state["determinism"] = {
            "input_signature": signature,
            "fingerprint": fingerprint,
        }
        _save_stage_state(ctx.work_dir, state)
        status = "pass"
    else:
        status = "pass" if prior.get("fingerprint") == fingerprint else "fail"
    ctx.artifacts["determinism_status"] = status


async def run_stages(ctx: BuildContext, stages: Sequence[str]) -> None:
    for stage_id in stages:
        spec = _STAGE_REGISTRY[stage_id]
        inputs_hash = _inputs_hash(ctx, spec)
        if _should_skip_stage(ctx, stage_id):
            # ponytail: a cache hit is a no-op; keep the byte-identical successful record.
            continue
        await _STAGE_RUNNERS[stage_id](ctx)
        outputs_hash = _compute_outputs_hash(ctx, spec)
        _record_stage(
            ctx,
            stage_id,
            version=spec.version,
            inputs_hash=inputs_hash,
            outputs_hash=outputs_hash,
            skipped=False,
        )


async def build_brand(
    brand: str,
    options: BuildOptions,
    *,
    client: LLMClient,
    usage: Usage | None = None,
    console: ConsoleLike | None = None,
    summarize_embed: SummarizeEmbedRunner | None = None,
    cache_root: Path | None = None,
) -> BuildOutcome:
    if options.concurrency <= 0:
        raise ValueError(f"concurrency must be positive, got {options.concurrency}")
    settings.reload_settings()
    usage = usage or Usage()
    console = console or Console(stderr=True)
    kb_root = config.kb_dir(brand)
    work_dir = kb_root / "_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    bible_hash = hash_bible(brand)
    ctx = BuildContext(
        brand=brand,
        options=options,
        usage=usage,
        console=console,
        work_dir=work_dir,
        kb_root=kb_root,
        client=client,
        cache_root=cache_root if cache_root is not None else DEFAULT_CACHE_ROOT,
        bible_hash=bible_hash,
        built_at=stable_built_at(bible_hash),
        input_hashes={
            "bible_hash": bible_hash,
            "template_library_hash": hash_template_library(brand),
            "prompts_hash": hash_prompts(),
            "registries_hash": hash_registries(),
        },
        summarize_embed=summarize_embed,
        stage_records=dict(_load_stage_state(work_dir).get("stages", {})),
    )
    if options.stages is not None:
        parse_stage_selection(stages=sorted(options.stages), from_stage=None)
        stages = [stage_id for stage_id in STAGE_IDS if stage_id in options.stages]
    else:
        stages = parse_stage_selection(stages=None, from_stage=options.from_stage)
    await run_stages(ctx, stages)
    await _hydrate_artifacts_for_manifest(ctx)
    _record_determinism(ctx)
    _, passed = _write_manifest(ctx)
    exit_code = 0
    if options.strict and not passed:
        exit_code = 1
    return BuildOutcome(
        brand=brand,
        exit_code=exit_code,
        acceptance_passed=passed,
        manifest_path=kb_root / "manifest.json",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", nargs="+", default=list(config.BRANDS), choices=list(config.BRANDS))
    parser.add_argument("--stages", nargs="+", help="stage ids or ranges, e.g. s0..s3 s9")
    parser.add_argument("--from", dest="from_stage", help="resume from stage id, e.g. s5")
    parser.add_argument("--no-ensemble", action="store_true")
    parser.add_argument("--no-critic", action="store_true")
    parser.add_argument("--no-gaps", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--ratchet", action="store_true")
    parser.add_argument("--accept-baseline", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--concurrency", type=int, default=settings.CONCURRENCY)
    return parser


async def main_async(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.concurrency <= 0:
        Console(stderr=True).print(
            f"[red]argument error:[/red] concurrency must be positive, got {args.concurrency}"
        )
        return 2
    try:
        selected = None
        if args.stages:
            selected = frozenset(parse_stage_selection(stages=args.stages, from_stage=None))
        options = BuildOptions(
            brands=list(args.brand),
            stages=selected,
            from_stage=args.from_stage,
            no_ensemble=args.no_ensemble,
            no_critic=args.no_critic,
            no_gaps=args.no_gaps,
            strict=args.strict,
            ratchet=args.ratchet,
            accept_baseline=args.accept_baseline,
            force=args.force,
            concurrency=args.concurrency,
        )
    except ValueError as exc:
        Console(stderr=True).print(f"[red]argument error:[/red] {exc}")
        return 2

    from indexing_v2.extraction.runner import SharedLLMClient

    config.require_keys()
    client = SharedLLMClient()
    usage = Usage()
    console = Console(stderr=True)
    exit_code = 0
    for brand in options.brands:
        outcome = await build_brand(brand, options, client=client, usage=usage, console=console)
        exit_code = max(exit_code, outcome.exit_code)
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    return asyncio.run(main_async(argv))


if __name__ == "__main__":
    sys.exit(main())
