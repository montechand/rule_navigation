"""Phase 1: per-rule one-line summaries + embeddings into a local Chroma store.

For every brand_rule:
  - generate a one-line summary (cheap LLM call, cached by rule_text hash)
  - write `summary` back into rules/{id}.json and rules/_index.json
  - embed summary, intent, rule_text into three Chroma collections
    (rule_summary / rule_intent / rule_text), ids = rule_id (1:1 linkage),
    metadata = {rule_id, brand, rule_class, sections, scope, hardness}

Usage:
  .venv/bin/python -m indexing.summarize_embed --brand lisraya ibsrela
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

import chromadb
from openai import AsyncOpenAI
from rich.console import Console

from shared import config
from shared.llm import Usage, chat

console = Console()
CACHE_DIR = Path(__file__).parent / "_cache"

SUMMARY_SYSTEM = (
    "You compress brand design rules into one-line summaries for a retrieval index. "
    "Keep the discriminating specifics (colors, px values, section names, conditions). "
    "Max ~25 words. Output the summary line only, no quotes."
)

COLLECTIONS = ("rule_summary", "rule_intent", "rule_text")


def _summary_cache(brand: str, rule_id: str, text: str) -> Path:
    h = hashlib.sha1(f"{config.SUMMARY_MODEL}|{text}".encode()).hexdigest()[:16]
    return CACHE_DIR / brand / "summaries" / f"{rule_id}_{h}.txt"


async def summarize_rule(brand: str, rule: dict[str, Any], usage: Usage,
                         sem: asyncio.Semaphore) -> str:
    text = rule["rule_text"]
    cp = _summary_cache(brand, rule["id"], text)
    if cp.exists():
        return cp.read_text().strip()
    async with sem:
        turn = await chat(
            config.SUMMARY_MODEL, SUMMARY_SYSTEM,
            [{"role": "user", "content": f"Rule ({rule.get('rule_class')}): {text}"}],
            max_tokens=100, usage=usage,
        )
    summary = turn.text.strip().strip('"')
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(summary)
    return summary


async def embed_texts(client: AsyncOpenAI, texts: list[str], usage: Usage) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), 128):
        batch = [t[:6000] if t else " " for t in texts[i : i + 128]]
        resp = await client.embeddings.create(model=config.EMBED_MODEL, input=batch)
        out.extend(d.embedding for d in resp.data)
        if resp.usage:
            usage.add(config.EMBED_MODEL, resp.usage.prompt_tokens, 0)
    return out


def rule_metadata(brand: str, rule: dict[str, Any]) -> dict[str, Any]:
    sel = rule.get("selector") or {}
    sections = sel.get("section_types")
    return {
        "rule_id": rule["id"],
        "brand": brand,
        "rule_class": rule.get("rule_class") or "",
        # Chroma metadata must be scalar; encode list as comma-joined, "*" = all sections.
        "sections": ",".join(sections) if sections else "*",
        "scope": rule.get("scope") or "",
        "hardness": rule.get("hardness") or "",
    }


async def process_brand(brand: str, usage: Usage) -> None:
    root = config.kb_dir(brand)
    rules_dir = root / "rules"
    rule_files = [f for f in sorted(rules_dir.glob("*.json")) if not f.name.startswith("_")]
    rules = [json.loads(f.read_text()) for f in rule_files]
    console.print(f"[bold cyan]== {brand}: {len(rules)} rules ==[/bold cyan]")

    # Summaries (parallel, cached)
    sem = asyncio.Semaphore(16)
    summaries = await asyncio.gather(*(summarize_rule(brand, r, usage, sem) for r in rules))
    for rule, summary in zip(rules, summaries):
        rule["summary"] = summary
    for f, rule in zip(rule_files, rules):
        f.write_text(json.dumps(rule, indent=2))

    # Rewrite index with real summaries
    index_path = rules_dir / "_index.json"
    index = json.loads(index_path.read_text())
    by_id = {r["id"]: r for r in rules}
    for row in index:
        if row["id"] in by_id:
            row["summary"] = by_id[row["id"]].get("summary") or row["summary"]
    index_path.write_text(json.dumps(index, indent=2))
    console.print("  summaries written back to rules + index")

    # Embeddings -> Chroma (fresh collections each run)
    client = AsyncOpenAI()
    chroma = chromadb.PersistentClient(path=str(root / "vectors" / "chroma"))
    texts_by_collection = {
        "rule_summary": [r.get("summary") or r["rule_text"] for r in rules],
        "rule_intent": [r.get("intent") or r.get("summary") or r["rule_text"] for r in rules],
        "rule_text": [r["rule_text"] for r in rules],
    }
    ids = [r["id"] for r in rules]
    metadatas = [rule_metadata(brand, r) for r in rules]
    for name, texts in texts_by_collection.items():
        try:
            chroma.delete_collection(name)
        except Exception:  # noqa: BLE001 — collection may not exist yet; a fresh one is created next
            pass
        col = chroma.create_collection(name, metadata={"hnsw:space": "cosine"})
        embeddings = await embed_texts(client, texts, usage)
        col.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        console.print(f"  chroma collection [green]{name}[/green]: {col.count()} vectors")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", nargs="+", default=list(config.BRANDS), choices=list(config.BRANDS))
    args = parser.parse_args()
    config.require_keys()
    usage = Usage()
    for brand in args.brand:
        await process_brand(brand, usage)
    console.print(f"[bold]Done.[/bold] Usage: {usage.as_dict()}")


if __name__ == "__main__":
    asyncio.run(main())
