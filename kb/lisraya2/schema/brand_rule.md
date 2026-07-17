# Entity: brand_rule

A coherent, independently-injectable CLUSTER of brand knowledge about one topic/device
(e.g. "CTA button coloring", "callout opacity system", "chart container geometry").

Token-first convention: every concrete value (hex, px, %, radius, weight, alignment,
casing) and every conditional value switch (IF light background ELSE dark...) lives in
the brand_token layer — rules do NOT restate values. A rule covers the normative
statements about its topic, binds the relevant tokens via `effect`/`token_ids`, and
carries only the cross-element / cross-token logic that cannot live on a single token
(cardinality, ordering, pairing, exclusivity, verbatim content, prose obligations).
To resolve a rule to concrete values, follow its `token_ids` (see brand_token.md).

Key attributes:
- `rule_class` (primary facet): one of typography, color_application, cta, layout, spacing,
  imagery, iconography, copy_editorial, voice_tone, accessibility, assembly.
- `tags`: secondary facets, same vocabulary (cross-cutting rules carry extra classes here).
- `audience`: dtp_patient | hcp | caregiver | null (null = all audiences).
- `content_types`: [email, banner, social, print, web, ppt] | null = all surfaces.
- `content_sub_type_ids`: FK[] -> content_sub_type CLASSES (sub_ ids only); null = all
  sub-types. Rules never scope to template instances (tpl_) — instances inherit through
  instance_of and fills_section.
- `scope`: org_baseline | brand | campaign. org_baseline = general production baseline
  (marked [BASELINE]/[GENERAL] in source docs), brand = from the brand guide,
  campaign = tied to a named campaign.
- `selector`: `{section_types: [...] | null, element_path: "cta.button.fill" | null}` —
  WHERE the rule attaches. Section vocabulary: hero, intro, efficacy, safety,
  patient_story, affordability, symptom_trio, cta, callout, chart, top_matter, end_matter.
  `section_types = null` means the rule applies to all sections.
- `applies_when`: predicate[] (closed registry, see predicate_registry.md); null = always.
- `evaluation_scope`: element | sentence | section | email — where the constraint is CHECKED.
  evaluation_scope=email rules (e.g. "max 3 CTAs per email") are email-wide by nature.
- `constraint_type` + `effect`: machine-readable payload, discriminated union:
  - binding: `[{element_path, token_id}]`
  - cardinality: `{target, min?, max?, per}`
  - ordering: `{sequence: [...], strict}`
  - pairing: `{a, b, relation: requires|forbids}`
  - exclusivity: `{subject, reserved_for}`
  - verbatim_content: `{content, trigger}`
  May be null when the source statement resists structuring; `rule_text` is then authoritative.
- `polarity`: must | must_not | should | should_not | may.
- `hardness`: hard_constraint (compiled validator) | strong_default (prompt rule) |
  soft_guidance (prompt context).
- `precedence`: int, tie-break among rules matching the same query after selector specificity.
- `rule_text` (WHAT, human-readable, faithful to source), `intent` (WHY, one line),
  `summary` (one-line compressed), `snippets` (illustrative MJML/SVG if any).
- `governance`: compliance facet — set on rules that adjudicate claims, required language,
  disclosures, or trademark use: `{gov_type: regulatory|legal|mlr_claim|disclosure|
  trademark, verdict: allowed|forbidden|allowed_with_disclosure|requires_qualifier|
  verbatim_only, preferred_form?: <exact verbatim string>, match?: {method}, severity:
  info|warn|block}`. Governance is a FACET of a rule, not a separate entity — such rules
  are almost always hard_constraint and surface in every normal rule query; filter them
  explicitly with query_rules(has_governance/gov_type/verdict). severity meaning:
  info -> prompt context, warn -> QA flag, block -> generation guard.
- Provenance: `source`, `doc_ref`, `group_id` (the original blob it was atomized from).
