"""Run one or more navigation architectures over an email blueprint.

Per architecture: every blueprint section runs in parallel (bounded), each with its own
JSONL trace. Results aggregate into outputs/{run_id}/result.json with:
  - per-section targeted rules (id + why)
  - email-wide rules union-deduped across sections (voted_by = which sections returned it)
  - hydrated rule payloads for everything referenced
  - usage stats (tokens, cost, tool calls, latency)

Architecture E is an exception: one Claude Agent SDK session per whole blueprint, reading
original design-bible passages under simple_kb/{brand}/ (not the structured kb/).

Usage:
  .venv/bin/python -m runner.run_blueprint --arch all --brand ibsrela \\
      --blueprint examples/ibsrela_blueprint.json [--design-concept on|off] \\
      [--model claude-sonnet-4-6] [--section-concurrency 3] [--sections hero cta] \\
      [--thinking-effort none|low|medium|high|xhigh|max] [--max-tokens 128000]

  # Arch D A/B: filesystem-only vs filesystem + structured ToolRepo tools
  .venv/bin/python -m runner.run_blueprint --arch d --d-tools fs --brand ibsrela \\
      --blueprint examples/ibsrela_blueprint.json
  .venv/bin/python -m runner.run_blueprint --arch d --d-tools full --brand ibsrela \\
      --blueprint examples/ibsrela_blueprint.json

  # Arch E: original design bible passages via Claude Agent SDK
  .venv/bin/python -m runner.run_blueprint --arch e --brand lisraya \\
      --blueprint examples/lisraya_blueprint1.json

--thinking-effort / --max-tokens only apply to arch "a" (Anthropic adaptive thinking).
--d-tools only applies to arch "d" (fs = Claude Code FS tools only; full = FS + ToolRepo).
--e-max-turns only applies to arch "e".
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

import arch_a_orchestrator
import arch_b_subagents
import arch_c_schema_network
import arch_d_claude_sdk
import arch_e_claude_sdk
from shared import config
from shared.kb import KB
from shared.llm import Trace, Usage
from shared.schemas import Blueprint, EmailWideRule, RunResult, SectionResult
from shared.simple_kb import SimpleBible
from shared.tool_repo import ToolRepo

console = Console()

ARCHS = {
    "a": arch_a_orchestrator,
    "b": arch_b_subagents,
    "c": arch_c_schema_network,
    "d": arch_d_claude_sdk,
    "e": arch_e_claude_sdk,
}
# arch "d"/"e" (Claude Agent SDK) are experimental — opt in explicitly, not part of "all".
ARCHS_ALL = ("a", "b", "c")


def load_blueprint(path: Path) -> Blueprint:
    data = json.loads(path.read_text())
    return Blueprint(**{k: v for k, v in data.items() if not k.startswith("_")})


def aggregate_email_wide(sections: list[SectionResult]) -> list[EmailWideRule]:
    merged: dict[str, EmailWideRule] = {}
    for s in sections:
        for verdict in s.email_wide_rules:
            entry = merged.setdefault(verdict.id, EmailWideRule(id=verdict.id))
            entry.voted_by.append(s.section_id)
            if verdict.why and not entry.why:
                entry.why = verdict.why
    # Stable order: most-voted first, then id.
    return sorted(merged.values(), key=lambda e: (-len(e.voted_by), e.id))


def hydrate_rules(kb: KB, result: RunResult) -> dict[str, Any]:
    ids: set[str] = {e.id for e in result.email_wide_rules}
    for s in result.sections:
        ids.update(v.id for v in s.targeted_rules)
        ids.update(v.id for v in s.email_wide_rules)
    payloads = {}
    for rid in sorted(ids):
        rule = kb.rules.get(rid)
        if rule is None:
            continue
        payloads[rid] = {
            "rule_class": rule.rule_class,
            "sections": rule.selector.section_types,
            "scope": rule.scope,
            "hardness": rule.hardness,
            "polarity": rule.polarity,
            "constraint_type": rule.constraint_type,
            "applies_when": [p.model_dump(exclude_none=True) for p in rule.applies_when] if rule.applies_when else None,
            "governance": rule.governance,  # incl. preferred_form verbatims for generation
            "summary": rule.summary,
            "rule_text": rule.rule_text,
            # rule_text is deliberately lossy; the resolved token bindings carry the
            # full value tables + conditional variants for downstream consumers.
            "bindings": kb.resolved_bindings(rule) or None,
        }
    return payloads


def hydrate_simple_passages(bible: SimpleBible, result: RunResult) -> dict[str, Any]:
    ids: set[str] = {e.id for e in result.email_wide_rules}
    for s in result.sections:
        ids.update(v.id for v in s.targeted_rules)
        ids.update(v.id for v in s.email_wide_rules)
    return bible.hydrate(ids)


async def run_arch_e(brand: str, blueprint_path: Path, bp: Blueprint,
                     sections_filter: list[str], include_dc: bool, model: str,
                     e_max_turns: int) -> Path:
    """Whole-blueprint Architecture E run against simple_kb original bibles."""
    bible = SimpleBible(brand)
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_e_{brand}_{blueprint_path.stem}"
    out_dir = config.OUTPUTS_DIR / run_id
    (out_dir / "traces").mkdir(parents=True, exist_ok=True)

    sections = [s for s in bp.content_blueprint
                if not sections_filter or s.section_id in sections_filter]
    console.print(f"[bold cyan]== arch e | max_turns={e_max_turns} | {brand} | "
                  f"{len(sections)} sections | model {model} | "
                  f"design_concept={'on' if include_dc else 'off'} | "
                  f"passages={len(bible.refs)} ==[/bold cyan]")

    usage = Usage()
    trace = Trace()
    t0 = time.time()
    try:
        section_results, email_wide, arch_stats = await arch_e_claude_sdk.run_blueprint(
            bible, bp, sections,
            model=model, include_design_concept=include_dc,
            trace=trace, usage=usage, max_turns=e_max_turns,
        )
    except Exception as e:  # noqa: BLE001 — whole-run failure still writes a result artifact
        section_results = [
            SectionResult(section_id=s.section_id, error=repr(e)) for s in sections
        ]
        email_wide = []
        arch_stats = {}

    for s, sec in zip(sections, section_results):
        status = f"[red]ERROR: {sec.error}[/red]" if sec.error else (
            f"targeted={len(sec.targeted_rules)}")
        console.print(f"  [e] {sec.section_id}: {status}")
    console.print(f"  [e] email_wide={len(email_wide)} "
                  f"({arch_stats.get('tool_calls', 0)} tool calls, "
                  f"{arch_stats.get('latency_s', 0)}s)")

    trace.dump(out_dir / "traces" / "00_blueprint.jsonl")
    stats = {
        **usage.as_dict(),
        **arch_stats,
        "wall_s": round(time.time() - t0, 1),
        "model": model,
        "sections_ok": sum(1 for s in section_results if not s.error),
        "e_max_turns": e_max_turns,
        "source": "simple_kb",
    }
    result = RunResult(
        arch="e", brand=brand,
        blueprint_path=str(blueprint_path),
        design_concept_used=include_dc,
        sections=section_results,
        email_wide_rules=email_wide,
        stats=stats,
    )
    payload = result.model_dump()
    payload["rules"] = hydrate_simple_passages(bible, result)
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2))
    console.print(f"  -> {out_dir / 'result.json'}  "
                  f"[dim]{usage.as_dict()} wall={payload['stats']['wall_s']}s[/dim]")
    return out_dir


async def run_arch(arch: str, brand: str, blueprint_path: Path, bp: Blueprint,
                   sections_filter: list[str], include_dc: bool, model: str,
                   section_concurrency: int, thinking_effort: str, max_tokens: int,
                   d_tools: str = "fs", d_max_turns: int = 48,
                   e_max_turns: int = 32) -> Path:
    if arch == "e":
        return await run_arch_e(
            brand, blueprint_path, bp, sections_filter, include_dc, model, e_max_turns,
        )

    module = ARCHS[arch]
    kb = KB(brand)
    repo = ToolRepo(kb)
    arch_tag = f"{arch}-{d_tools}" if arch == "d" else arch
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{arch_tag}_{brand}_{blueprint_path.stem}"
    out_dir = config.OUTPUTS_DIR / run_id
    (out_dir / "traces").mkdir(parents=True, exist_ok=True)

    sections = [s for s in bp.content_blueprint
                if not sections_filter or s.section_id in sections_filter]
    mode_bit = f" | d-tools={d_tools} | max_turns={d_max_turns}" if arch == "d" else ""
    console.print(f"[bold cyan]== arch {arch}{mode_bit} | {brand} | {len(sections)} sections | "
                  f"model {model} | design_concept={'on' if include_dc else 'off'} ==[/bold cyan]")

    usage = Usage()
    sem = asyncio.Semaphore(section_concurrency)
    t0 = time.time()

    async def one(section) -> SectionResult:
        trace = Trace()
        sec_usage = Usage()
        async with sem:
            try:
                # thinking_effort/max_tokens are arch-a-only (Anthropic extended thinking);
                # d_tools / d_max_turns are arch-d-only.
                extra: dict[str, Any] = {}
                if arch == "a":
                    extra = {"thinking_effort": thinking_effort, "max_tokens": max_tokens}
                elif arch == "d":
                    extra = {"tool_mode": d_tools, "max_turns": d_max_turns}
                result = await module.run_section(
                    repo, bp, section,
                    model=model, include_design_concept=include_dc,
                    trace=trace, usage=sec_usage, **extra,
                )
            except Exception as e:  # noqa: BLE001 — one section failing must not sink the run; error is recorded in the result
                result = SectionResult(section_id=section.section_id, error=repr(e))
        result.stats = {**result.stats, **sec_usage.as_dict()}
        usage.merge(sec_usage)
        trace.dump(out_dir / "traces" / f"{section.order:02d}_{section.section_id}.jsonl")
        status = f"[red]ERROR: {result.error}[/red]" if result.error else (
            f"targeted={len(result.targeted_rules)} email_wide={len(result.email_wide_rules)}")
        console.print(f"  [{arch}] {section.section_id}: {status} "
                      f"({result.stats.get('tool_calls', 0)} tool calls, "
                      f"{result.stats.get('latency_s', 0)}s)")
        return result

    section_results = list(await asyncio.gather(*(one(s) for s in sections)))

    stats = {**usage.as_dict(), "wall_s": round(time.time() - t0, 1), "model": model,
             "sections_ok": sum(1 for s in section_results if not s.error)}
    if arch == "d":
        stats["d_tools"] = d_tools
        stats["d_max_turns"] = d_max_turns
    result = RunResult(
        arch=arch_tag if arch == "d" else arch, brand=brand,
        blueprint_path=str(blueprint_path),
        design_concept_used=include_dc,
        sections=section_results,
        email_wide_rules=aggregate_email_wide(section_results),
        stats=stats,
    )
    payload = result.model_dump()
    payload["rules"] = hydrate_rules(kb, result)
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2))
    console.print(f"  -> {out_dir / 'result.json'}  "
                  f"[dim]{usage.as_dict()} wall={payload['stats']['wall_s']}s[/dim]")
    return out_dir


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch", default="all", choices=[*ARCHS, "all"])
    parser.add_argument("--brand", required=True, choices=list(config.BRANDS))
    parser.add_argument("--blueprint", required=True, type=Path)
    parser.add_argument("--design-concept", default="on", choices=["on", "off"])
    parser.add_argument("--model", default=config.AGENT_MODEL)
    parser.add_argument("--section-concurrency", type=int, default=3)
    parser.add_argument("--sections", nargs="*", default=[],
                        help="only run these section_ids")
    parser.add_argument("--thinking-effort", default="medium",
                        choices=["none", "low", "medium", "high", "xhigh", "max"],
                        help="arch 'a' only: Anthropic adaptive-thinking effort level")
    parser.add_argument("--max-tokens", type=int, default=128_000,
                        help="arch 'a' only: max_tokens per LLM call (thinking + response text)")
    parser.add_argument("--d-tools", default="fs", choices=["fs", "full"],
                        help="arch 'd' only: fs = Claude Code FS tools (+finalize); "
                             "full = FS + structured ToolRepo MCP tools (+finalize)")
    parser.add_argument("--d-max-turns", type=int, default=48,
                        help="arch 'd' only: Claude Agent SDK max_turns (default 48; "
                             "FS mode is turn-hungry vs structured tools)")
    parser.add_argument("--e-max-turns", type=int, default=32,
                        help="arch 'e' only: Claude Agent SDK max_turns for the "
                             "whole-blueprint simple_kb session (default 32)")
    args = parser.parse_args()

    config.require_keys()
    bp = load_blueprint(args.blueprint)
    archs = list(ARCHS_ALL) if args.arch == "all" else [args.arch]
    out_dirs = []
    for arch in archs:
        out_dirs.append(await run_arch(
            arch, args.brand, args.blueprint, bp, args.sections,
            args.design_concept == "on", args.model, args.section_concurrency,
            args.thinking_effort, args.max_tokens, args.d_tools, args.d_max_turns,
            args.e_max_turns))

    if len(out_dirs) > 1:
        table = Table(title="runs")
        table.add_column("arch")
        table.add_column("output")
        for arch, d in zip(archs, out_dirs):
            table.add_row(arch, str(d))
        console.print(table)
        console.print("[dim]compare with: .venv/bin/python -m runner.compare "
                      + " ".join(str(d) for d in out_dirs) + "[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
