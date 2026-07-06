# Knowledge base overview — brand: ibsrela

This KB is the structured form of the IBSRELA design bible, atomized into the
v0.2 brand-rules data model.

Contents: 145 brand_rules, 32 brand_tokens,
6 design_assets, 10 governance rows,
7 content_sub_types, 21 rule_groups,
2 asset_groups.

## Layout

- `schema/` — this documentation (entities, section vocab, predicate registry)
- `rules/_index.json` — compact row per rule (id, rule_class, tags, sections, scope,
  hardness, polarity, constraint_type, applies_when, one-line summary)
- `rules/{rule_id}.json` — full rule rows
- `tokens/ assets/ subtypes/ governance/` — side entities, each with `_index.json`
- `groups/rule_groups.json` — original pre-atomization text blobs (provenance)
- `groups/asset_groups.json`, `groups/relations.json`
- `graph/graph.json` — nodes + typed edges (rule->section, rule->token, rule->asset,
  rule->governance, rule->group, asset->token, asset->asset_group, rule->rule)

## How to find rules for an email section

1. Structured: filter `rules/_index.json` by `sections` (remember `null` = applies to ALL
   sections — those are baseline/email-wide candidates) and by rule_class facets.
2. Graph: follow `applies_to_section` edges from the section node (`sec_{name}`).
3. Semantic: vector search over rule summaries/intents/text.
4. Lexical: keyword/grep for exact terms (hex codes, component names, phrases).

Read `schema/section_vocab.md` first to map blueprint section_ids onto the closed
section vocabulary. Rules with `evaluation_scope = email` or `selector.section_types =
null` belong in the email-wide baseline set, not the per-section set.
