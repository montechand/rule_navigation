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

## Dynamic registries + templates (this branch)

- `shared/registries.json` (committed = permanent) holds DYNAMIC vocabularies:
  `section_types` (curated core + brand-discovered devices, e.g. ibsrela's
  `symptom_trio`), `relations` (enriched with overrides / mutually_exclusive /
  depends_on), `token_types`. Extraction proposes novel entries as `other.<name>`;
  the build registers real discoveries permanently, bare unknown values are dropped.
- Concrete approved templates (`config.TEMPLATE_LIBRARIES`, e.g. the ibsrela email
  header/footer library) are ingested as `content_sub_type` rows with
  `covers_section_types` (a header-with-hero template covers `[top_matter, hero]`),
  `template_ref`/`template_file` (bodies stored under `kb/{brand}/templates/`), and
  `covers_section` graph edges. Rules scope to templates/components via
  `content_sub_type_ids` (null = all email sub-types) — same mechanism dimension
  formats use for banner-size-specific rules. New tool: `rules_for_subtype`.
- Token hygiene: exact duplicates (same kind+type+value+scope) are auto-merged at build
  time (merged names survive as aliases; `$ref`s remapped); near-duplicates across
  scopes are reported to `review/token_near_duplicates.md`, not merged. Query-time
  multi-level composition is handled by the `resolve_token` tool (flattens `$ref`
  chains to concrete values with variants).
- Asset vocabulary: `wave` generalized to `graphic_device` (brand-look motifs: waves,
  swooshes, accent shapes, patterns).

## v0.3 class/template split (this branch)

- `content_sub_type` = structural CLASSES only (source-defined component library, locked
  matter, dimension formats). Role-echo pseudo-components are gone — recurring section
  patterns stay rules + selector + tokens.
- New `design_template` entity (`tpl_`): concrete approved artifacts from template
  libraries AND approved MJML blocks embedded verbatim in the bibles. Templates fill
  section roles (`fills_section_types`), may realize a class (`instance_of`), sit in
  pick-one `template_group`s (`tgr_`, e.g. approved email headers), and carry their own
  `usage_conditions` (selection gates like `requires_content_tags: [lpga]`, inferred
  automatically when a template's body references a gated asset).
- `covers_section_types` split into `fills_section_types` (IS the role; feeds rule
  surfacing) vs `hosts_section_types` (CAN CARRY the role; affordance hint only).
- Rules scope to classes only; `tpl_`/`tgr_` ids in `content_sub_type_ids` are rejected
  at validation. New tools: `list_templates`, `rules_for_template` (instance view:
  rules via class + via filled sections + own usage_conditions + group alternates).

## Governance as a rule facet (this branch)

The standalone `governance` entity is retired. Compliance statements (required
disclosures, mandated qualifiers, verbatim-only messaging, trademark adjudications) are
ordinary `brand_rule` rows carrying a `governance` facet:
`{gov_type, verdict, preferred_form?, match?, severity}` — the exact required strings
live in `governance.preferred_form`, and such rules land as `hard_constraint`. They
surface in every normal rule query (no separate corner for the agent to forget) and are
filterable via `query_rules(has_governance / gov_type / verdict)`; `keyword_search`
indexes the verbatim strings. MLR-specific bookkeeping (`evidence`, `effective_from`,
`expires_at`) was dropped for now.

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
