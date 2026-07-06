# Entity: brand_rule

The atomic, independently-injectable unit of brand knowledge. One rule = one normative
statement (a MUST/SHOULD/NEVER about typography, color, layout, copy, ...).

Key attributes:
- `rule_class` (primary facet): one of typography, color_application, cta, layout, spacing,
  imagery, iconography, copy_editorial, voice_tone, accessibility, assembly.
- `tags`: secondary facets, same vocabulary (cross-cutting rules carry extra classes here).
- `audience`: dtp_patient | hcp | caregiver | null (null = all audiences).
- `content_types`: [email, banner, social, print, web, ppt] | null = all surfaces.
- `content_sub_type_ids`: FK[] -> content_sub_type; null = all sub-types.
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
  - verbatim_content: `{content | governance_id, trigger}`
  May be null when the source statement resists structuring; `rule_text` is then authoritative.
- `polarity`: must | must_not | should | should_not | may.
- `hardness`: hard_constraint (compiled validator) | strong_default (prompt rule) |
  soft_guidance (prompt context).
- `precedence`: int, tie-break among rules matching the same query after selector specificity.
- `rule_text` (WHAT, human-readable, faithful to source), `intent` (WHY, one line),
  `summary` (one-line compressed), `snippets` (illustrative MJML/SVG if any).
- `governance_ids`: claims/disclosures gating this rule.
- Provenance: `source`, `doc_ref`, `group_id` (the original blob it was atomized from).
