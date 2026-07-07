# rule_navigation — Brand Rule Navigation Pipelines (3 agentic architectures)

Standalone experiment suite answering: **can an LLM agent navigate a structured brand-rule
knowledge graph precisely enough to assign the right ruleset to each email-blueprint
section?** (Benchmarked later against humans doing the same task; FNR-first.)

> **Branch `token-first-kb`**: token-first KB variant. Extraction runs token-level first
> and exhaustively — every concrete styling value is a `primitive` token; every
> element-path binding (which value applies where, under what condition) is a `semantic`
> token whose `value.variants[].when` carries the IF/ELSE formerly written as prose rules.
> Rules become coherent topic CLUSTERS that bind tokens instead of restating values;
> expect token counts >= rule counts. New tools: `query_tokens`, `search_tokens`;
> new graph edges: `resolves_to` (semantic -> primitive). `main` holds the atomic-rule
> baseline.

Inputs: a structured brand-rules KB (migrated from the design bibles) + an email blueprint
(`content_blueprint[]`, with or without per-section `design_concept`).
Output per section: `targeted_rules` (precisely scoped to that section) and
`email_wide_rules` (baseline, union-deduped across sections with vote provenance).

## Setup

```bash
cd rule_navigation
python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt
# API keys are read from ../newest_email_pipeline/.env (OPENAI_API_KEY, ANTHROPIC_API_KEY)
```

## Pipeline

```bash
# 0. Migrate design bibles -> structured KB (one-time; LLM outputs cached in indexing/_cache)
.venv/bin/python -m indexing.build_kb --brand lisraya ibsrela

# 1. Rule summaries + embeddings (3 Chroma collections per brand: summary/intent/text)
.venv/bin/python -m indexing.summarize_embed

# 2. Run architectures over a blueprint
.venv/bin/python -m runner.run_blueprint --arch all --brand ibsrela \
    --blueprint examples/ibsrela_blueprint.json

# 3. Compare runs
.venv/bin/python -m runner.compare outputs/<run_a> outputs/<run_b> outputs/<run_c>
```

Useful flags on `run_blueprint`: `--design-concept off` (blueprint-only navigation),
`--sections hero cta` (subset), `--model` (any claude-*/gpt-* chat model),
`--section-concurrency`.

## The three architectures

| | style | mechanics |
|---|---|---|
| `arch_a_orchestrator` | generalist orchestrator | one loop, full chat history, ALL tools, terminal `finalize_section_ruleset` |
| `arch_b_subagents` | querying-style specialists | orchestrator can only delegate (`ask_vector/graph/lexical_specialist`), each specialist is a scoped loop reporting candidates+evidence; orchestrator merges, iterates, finalizes |
| `arch_c_schema_network` | schema-sharded network | fixed parallel fan-out of 4 shard agents (color+typography / imagery+assets / layout+assembly+cta / copy+governance), composer agent merges and finalizes |

All three share the same task brief, section rendering, finalize contract (validated ids,
targeted/email-wide disjoint), tool repository, and tracing — so differences in output are
architectural, not prompt-shaped.

## Knowledge base (`kb/{brand}/`)

- `schema/*.md` — agent-facing data-model docs (entities, section vocab, predicate registry)
- `rules/*.json` + `rules/_index.json` — atomic `brand_rule` rows (v0.2 dictionary:
  closed-vocab `rule_class`, `selector.section_types`, `applies_when` predicates,
  `constraint_type`+typed `effect`, `scope`, `hardness`, derived `token_ids`/`asset_ids`)
- `tokens/ assets/ subtypes/ governance/` — side entities with indices
- `groups/` — `rule_groups.json` (original pre-atomization blobs), `asset_groups.json`,
  `relations.json`
- `graph/graph.json` — typed nodes+edges (rule→section/token/asset/governance/group, asset
  pairings, rule↔rule relations)
- `review/` — per-blob original-vs-extracted files + build warnings (human spot-checking)
- `vectors/chroma/` — persistent local vector store

## Tool repository (`shared/tool_repo`)

filesystem (`list_dir`, `read_file`, `grep`) · schema (`describe_entity`,
`get_section_vocab`, `get_predicate_registry`) · lookup (`get_rules` short/full,
`get_entity`) · structured (`query_rules` facet filters) · tokens (`query_tokens` facet
filters, `search_tokens` BM25 over keys/aliases/paths/values) · keyword (BM25) · vector
(3 collections, metadata filters) · graph (`rules_for_section`, `rules_for_token`,
`neighbors`, `related_rules`) · terminal `finalize_section_ruleset` factory.

## Outputs (`outputs/{run_id}/`)

- `result.json` — sections with targeted rules (+why), aggregated email-wide rules
  (+voted_by), hydrated rule payloads, usage/cost/latency stats
- `traces/{order}_{section}.jsonl` — every LLM turn and tool call (args, result sizes,
  previews) per section; the artifact for judging navigation behavior and for the
  benchmark harness later
- `comparison.json` (from `runner.compare`) — per-section rule sets, Jaccard overlap,
  unique-to-arch picks, email-wide agreement

## Layout

```
shared/      config, pydantic schemas, LLM tool-loop client, KB access, tool repo, prompts
indexing/    build_kb.py (migration), summarize_embed.py, static schema docs, _cache/
kb/          generated KB per brand (checked in, human-reviewable)
arch_a_orchestrator/  arch_b_subagents/  arch_c_schema_network/
runner/      run_blueprint.py, compare.py
examples/    lisraya_blueprint.json (from rob_in_the_loop_v1), ibsrela_blueprint.json
outputs/     run results + traces (gitignored-ish; safe to delete)
```
