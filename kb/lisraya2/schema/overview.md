# Knowledge base overview — brand: lisraya

This KB is the structured form of the LISRAYA design bible, atomized into the
v0.2 brand-rules data model.

Contents: 59 brand_rules (topic clusters; 18
carry the governance/compliance facet), 82 brand_tokens
(71 primitive / 11 semantic),
3 design_assets, 4 content_sub_type
classes, 2 design_templates in 0
template_groups, 28 rule_groups,
0 asset_groups.

## Layout

- `schema/` — this documentation (entities, section vocab, predicate registry)
- `rules/_index.json` — compact row per rule (id, rule_class, tags, sections, scope,
  hardness, polarity, constraint_type, applies_when, one-line summary)
- `rules/{rule_id}.json` — full rule rows
- `tokens/ assets/ subtypes/` — side entities, each with `_index.json`
- `templates/` — concrete approved artifacts: bodies as `{id}.mjml`, metadata in
  `_meta/{id}.json`, index in `_index.json`
- `groups/rule_groups.json` — original pre-atomization text blobs (provenance)
- `groups/asset_groups.json`, `groups/template_groups.json`, `groups/relations.json`
- `graph/graph.json` — nodes + typed edges (rule->section, rule->token, rule->asset,
  rule->group, class/template->section, template->class/group, asset->token,
  asset->asset_group, rule->rule)

Governance/compliance is a RULE FACET, not an entity: disclosures, required qualifiers,
verbatim messaging, and trademark adjudications are brand_rules with `governance` set
(the exact required strings live in governance.preferred_form). They surface in every
normal rule query; filter with query_rules(has_governance / gov_type / verdict).

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
