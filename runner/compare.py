"""Side-by-side comparison of architecture runs over the same blueprint.

Reads two or more outputs/{run_id}/result.json, prints per-section rule-set overlap
(Jaccard), unique-to-arch rules, email-wide agreement, and a cost/latency table.
Writes comparison.json next to the first run.

Usage:
  .venv/bin/python -m runner.compare outputs/<run_a> outputs/<run_b> [outputs/<run_c>]
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def load_run(path: Path) -> dict[str, Any]:
    f = path / "result.json" if path.is_dir() else path
    data = json.loads(f.read_text())
    data["_dir"] = str(path)
    return data


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def section_sets(run: dict[str, Any]) -> dict[str, set[str]]:
    return {s["section_id"]: {v["id"] for v in s.get("targeted_rules", [])}
            for s in run["sections"]}


def email_wide_set(run: dict[str, Any]) -> set[str]:
    return {e["id"] for e in run.get("email_wide_rules", [])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path)
    args = parser.parse_args()
    runs = [load_run(p) for p in args.runs]
    labels = [f"{r['arch']}" for r in runs]
    if len(set(labels)) != len(labels):  # same arch twice (e.g. dc on/off) — disambiguate
        labels = [f"{r['arch']}:{Path(r['_dir']).name[-20:]}" for r in runs]
    rule_info: dict[str, Any] = {}
    for r in runs:
        rule_info.update(r.get("rules", {}))

    comparison: dict[str, Any] = {"runs": [r["_dir"] for r in runs], "sections": {}, "email_wide": {}}

    # ------------------------------------------------------------------ stats
    stats_table = Table(title="Run stats")
    for col in ("arch", "sections ok", "llm calls", "input tok", "output tok",
                "cost $", "wall s", "avg targeted", "avg email-wide"):
        stats_table.add_column(col)
    for label, r in zip(labels, runs):
        st = r["stats"]
        n = max(len(r["sections"]), 1)
        avg_t = sum(len(s.get("targeted_rules", [])) for s in r["sections"]) / n
        avg_e = sum(len(s.get("email_wide_rules", [])) for s in r["sections"]) / n
        stats_table.add_row(
            label, f"{st.get('sections_ok')}/{len(r['sections'])}",
            str(st.get("llm_calls")), str(st.get("input_tokens")), str(st.get("output_tokens")),
            f"{st.get('cost_usd', 0):.2f}", str(st.get("wall_s")),
            f"{avg_t:.1f}", f"{avg_e:.1f}",
        )
    console.print(stats_table)

    # ------------------------------------------------------------------ per-section
    all_sections = list(dict.fromkeys(
        s["section_id"] for r in runs for s in r["sections"]))
    per_run_sets = [section_sets(r) for r in runs]

    sec_table = Table(title="Per-section targeted rules")
    sec_table.add_column("section")
    for label in labels:
        sec_table.add_column(f"{label} #")
    for pair in itertools.combinations(range(len(runs)), 2):
        sec_table.add_column(f"J({labels[pair[0]]},{labels[pair[1]]})")
    for sec in all_sections:
        row = [sec] + [str(len(ps.get(sec, set()))) for ps in per_run_sets]
        for i, j in itertools.combinations(range(len(runs)), 2):
            row.append(f"{jaccard(per_run_sets[i].get(sec, set()), per_run_sets[j].get(sec, set())):.2f}")
        sec_table.add_row(*row)
        comparison["sections"][sec] = {
            labels[i]: sorted(per_run_sets[i].get(sec, set())) for i in range(len(runs))
        }
        # console detail: unique-to-arch rules
        union = set().union(*(ps.get(sec, set()) for ps in per_run_sets))
        for i, label in enumerate(labels):
            unique = per_run_sets[i].get(sec, set()) - set().union(
                *(per_run_sets[j].get(sec, set()) for j in range(len(runs)) if j != i))
            if unique:
                comparison["sections"][sec][f"unique_to_{label}"] = sorted(unique)
        comparison["sections"][sec]["agreed_by_all"] = sorted(
            set.intersection(*(per_run_sets[i].get(sec, set()) for i in range(len(runs)))))
        comparison["sections"][sec]["union_size"] = len(union)
    console.print(sec_table)

    # Unique-to-arch detail (with summaries)
    for sec in all_sections:
        printed_header = False
        for i, label in enumerate(labels):
            unique = per_run_sets[i].get(sec, set()) - set().union(
                *(per_run_sets[j].get(sec, set()) for j in range(len(runs)) if j != i))
            if not unique:
                continue
            if not printed_header:
                console.print(f"\n[bold]{sec}[/bold] — unique picks")
                printed_header = True
            console.print(f"  [cyan]{label}[/cyan]:")
            for rid in sorted(unique)[:10]:
                summary = (rule_info.get(rid) or {}).get("summary", "")
                console.print(f"    {rid}  [dim]{summary[:90]}[/dim]")
            if len(unique) > 10:
                console.print(f"    ... +{len(unique) - 10} more")

    # ------------------------------------------------------------------ email-wide
    ew_sets = [email_wide_set(r) for r in runs]
    ew_table = Table(title="Email-wide rules")
    ew_table.add_column("metric")
    for label in labels:
        ew_table.add_column(label)
    ew_table.add_row("count", *[str(len(s)) for s in ew_sets])
    agreed = set.intersection(*ew_sets) if ew_sets else set()
    ew_table.add_row("agreed by all", *[str(len(agreed))] * len(runs))
    console.print(ew_table)
    comparison["email_wide"] = {
        labels[i]: sorted(ew_sets[i]) for i in range(len(runs))
    }
    comparison["email_wide"]["agreed_by_all"] = sorted(agreed)

    out = Path(runs[0]["_dir"]) / "comparison.json"
    out.write_text(json.dumps(comparison, indent=2))
    console.print(f"\n[dim]-> {out}[/dim]")


if __name__ == "__main__":
    main()
