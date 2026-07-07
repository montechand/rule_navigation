# Knowledge base overview — brand: lisraya

This KB is the structured form of the LISRAYA design bible, atomized into the
v0.2 brand-rules data model.

Contents: 109 brand_rules (topic clusters),
244 brand_tokens (115 primitive /
129 semantic), 9 design_assets,
27 governance rows, 13 content_sub_types,
28 rule_groups, 1 asset_groups.

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

## Token-first layering

Concrete values and their conditional switching (IF light background ELSE dark, print vs
email, campaign gates) live in `brand_token` rows — primitives (raw values) and semantic
tokens (element-path bindings with variants). Rules are coherent topic clusters that bind
those tokens and carry cross-element logic (cardinality/ordering/pairing/exclusivity/
verbatim/prose). Resolving a rule to exact values = following its `token_ids`.

## How to find rules for an email section

1. Structured: filter `rules/_index.json` by `sections` (remember `null` = applies to ALL
   sections — those are baseline/email-wide candidates) and by rule_class facets.
2. Graph: follow `applies_to_section` edges from the section node (`sec_{name}`).
3. Semantic: vector search over rule summaries/intents/text.
4. Lexical: keyword/grep for exact terms (hex codes, component names, phrases).
5. Token pivot: a concrete detail in the design concept (a hex, an opacity, a radius, an
   alignment) -> search_tokens/query_tokens -> rules_for_token -> governing rules.

Read `schema/section_vocab.md` first to map blueprint section_ids onto the closed
section vocabulary. Rules with `evaluation_scope = email` or `selector.section_types =
null` belong in the email-wide baseline set, not the per-section set.
