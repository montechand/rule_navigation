"""Offline preflight: replay the s2 token phase from the LLM response cache.

Runs ``run_token_phase`` with a client that refuses to call the network, so
every LLM response is served from ``indexing_v2/_cache``. This exercises the
exact extraction -> verification -> reconciliation path the build will take,
in seconds and at zero cost — crashes surface here instead of twenty minutes
into a paid build.

Usage:
    python -m indexing_v2.preflight --brand lisraya

Exit codes: 0 clean, 1 pipeline crash, 2 cache incomplete (build would need
new LLM calls; not a code failure).

ponytail: covers the token phase only — that is where every reconcile crash
so far has lived. Extend with the rules phase once its cache is populated.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import traceback
from typing import Any

from shared import config
from shared.llm import Usage

from indexing_v2 import settings
from indexing_v2.contracts import SourceUnit, UnitLabel, read_jsonl
from indexing_v2.extraction.runner import run_token_phase


class CacheMiss(RuntimeError):
    pass


class _CacheOnlyClient:
    """LLM client that raises instead of spending money."""

    async def complete_json(self, *args: Any, prompt_name: str = "?", **kwargs: Any) -> Any:
        raise CacheMiss(f"uncached LLM call required: prompt={prompt_name}")

    async def chat(self, *args: Any, **kwargs: Any) -> Any:
        raise CacheMiss("uncached chat call required")


# Settings that silently disable pipeline features when forced to zero/false
# by a stray RULE_NAV_* env override (the F1 incident: budget=0 skipped every
# linker adjudication with no visible signal).
_DEGENERATE_SETTINGS = (
    ("LINKER_MAX_ADJUDICATIONS", 0),
    ("REF_RETRIES", 0),
    ("MAX_CRITIC_ROUNDS", 0),
    ("MAX_GAP_ROUNDS", 0),
)


def check_degenerate_env(echo: Any = print) -> list[str]:
    """Warn when env overrides force a setting to a degenerate value."""
    import os

    warnings: list[str] = []
    for name, degenerate in _DEGENERATE_SETTINGS:
        env_key = settings._ENV_KEYS.get(name)
        if env_key is None or os.getenv(env_key) is None:
            continue
        if getattr(settings, name) == degenerate:
            warnings.append(
                f"WARNING: {env_key} overrides {name} to degenerate value "
                f"{degenerate!r} — the feature it gates is disabled"
            )
    for message in warnings:
        echo(message)
    return warnings


async def _run(brand: str) -> int:
    work_dir = config.kb_dir(brand) / "_work"
    units = read_jsonl(work_dir / "units.jsonl", SourceUnit)
    labels = read_jsonl(work_dir / "unit_labels.jsonl", UnitLabel)
    print(f"preflight {brand}: {len(units)} units, {len(settings.ENSEMBLE_RUNS)} run variants")
    check_degenerate_env()
    try:
        frozen = await run_token_phase(
            brand,
            list(settings.ENSEMBLE_RUNS),
            list(units),
            list(labels),
            Usage(),
            _CacheOnlyClient(),
            # work_dir omitted: never overwrite build artifacts from preflight.
        )
    except CacheMiss as exc:
        print(f"CACHE INCOMPLETE: {exc}")
        return 2
    except Exception:
        print("PIPELINE CRASH (this is what the build would hit):")
        traceback.print_exc()
        return 1
    print(
        f"OK: frozen catalog primitive={len(frozen.tokens_primitive)} "
        f"semantic={len(frozen.tokens_semantic)} hash={frozen.hash}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", default="lisraya")
    args = parser.parse_args(argv)
    return asyncio.run(_run(args.brand))


if __name__ == "__main__":
    sys.exit(main())
