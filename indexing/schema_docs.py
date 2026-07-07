"""Static schema documentation written into kb/{brand}/schema/*.md.

These markdown files are the agent-facing description of the v0.2 data model
(adapted from newest_email_pipeline/data_models/model_iteration_0/model_dictionary.md).
Agents read them via filesystem tools; keep them precise and compact.
"""

GLOBAL_CONVENTIONS = """# Global conventions

- Empty semantics: `null` = **unconstrained** (applies to all). `[]` = **explicitly none**.
  A rule with `selector.section_types = null` applies to EVERY section; treat those as
  candidates for email-wide/baseline rules.
- IDs: `{entity_prefix}_{brand}_{slug}`. Prefixes: `rule_` brand_rule, `tok_` brand_token,
  `ast_` design_asset, `gov_` governance, `sub_` content_sub_type (structural class),
  `tpl_` design_template (concrete instance), `tgr_` template_group, `grp_` rule_group,
  `agr_` asset_group.
- `token_ids` / `asset_ids` on a rule are derived indices of what its `effect` references.
- Only `status = active` rows are queryable.
"""

BRAND_RULE_DOC = """# Entity: brand_rule

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
"""

BRAND_TOKEN_DOC = """# Entity: brand_token

ALL possible styling properties and their values are brand tokens (color, gradient,
opacity, font, type_scale, weight, line_height, letter_spacing, case, spacing, padding,
margin, size, dimension, radius, border, shadow, ratio, breakpoint, alignment,
icon_style, image_treatment, motion, ...). The token layer is the value/IF-ELSE layer of
the KB: expect as many tokens as rules or more. Rules bind tokens; tokens carry values
and their conditional switching.

Two kinds (`kind`):
- `primitive` — a raw reusable value: a hex, an opacity stop (80%), a px step (24px), a
  radius spec, a font weight, an alignment, a casing, an image treatment.
  key grammar: `{type}.{tier_or_group}.{name}`, e.g. `color.primary.brand_blue`,
  `opacity.callout.80`, `radius.accent_shape.large`.
- `semantic` — an element-path-addressed binding: WHICH primitive applies WHERE, and
  under WHAT condition. key grammar: element-path style, e.g. `cta.button.fill`,
  `callout.fill.opacity`, `h1.color`, `body.link.color`.
  `element_paths` lists the dotted paths it binds. The value references primitives via
  `{"$ref": "tok_..."}` and conditional logic lives in `value.variants`:
  `{default: {"$ref": tok_a}, variants: [{when: {background_group: "dark"}, value: {"$ref": tok_b}}]}`
  — this is where the IF/ELSE formerly written as prose rules now lives. `when` objects
  use the closed predicate registry (see predicate_registry.md) plus surface/breakpoint.

Other attributes:
- `value`: `{default, variants: [{when: {...}, value}]}` — token-level bifurcation
  (print font vs email fallback; desktop vs mobile size; light vs dark background).
- `derived_from`: `{base_token_id, op: tint|opacity|mix, amount}` for derived tokens
  (40% tint of headline color, 70% transparency wave layer).
- `aliases`: alternate names used in source docs (same hex called "Green" and "teal").
- `tier`: primary | secondary_accent | tertiary | campaign (primitives, where stated).
- `scope`: global | campaign:{name} | partnership:{name}.
- `usage_ratio`: palette ratio 0-1 when specified (e.g. 30/30/20/15/5).
- `gated`: `{is_gated: true, gate: predicate}` for reserved tokens (teal only with LPGA
  content; Avenir Heavy reserved for boxed warning).

Navigation: `query_tokens` (facet filters), `search_tokens` (lexical), `get_entity`
(full row), `resolve_token` (flattens a semantic token's $ref chain to concrete values,
variants included — use this instead of hopping get_entity calls), `rules_for_token`
(which rules bind a token), graph edges `resolves_to` (semantic -> primitive) and
`derived_from`. token_type is a dynamic registry (extraction may register new types via
`other.<name>`). Exact duplicates are merged at build time (same type+value+scope; the
merged names live on in `aliases`); near-duplicates across scopes are kept separate
deliberately (a campaign color and a global color with the same hex carry different
gating semantics).
"""

DESIGN_ASSET_DOC = """# Entity: design_asset

Approved visual asset (photo, icon, logo_lockup, svg_shape, wave, background,
campaign_lockup, cta_image).

- `uri`: storage location (S3 etc). `dims`: pixel dimensions if known.
- `description` / `alt_text`: semantic description and approved accessibility string.
- `contains_token_ids`: tokens the asset embodies and must preserve (palette integrity).
- `required_pairing_token_ids`: tokens that MUST accompany the asset (e.g. golf image ->
  teal background).
- `usage_conditions`: `{requires_content_tags: [], forbidden_content_tags: [],
  max_per_email: int?}`.
- `slot_compatibility`: which slots may carry it: hero, cta_right, icon_row, background, inline.
- `group_id` + `group_order`: ordered set membership (e.g. symptom icon trio).
"""

CONTENT_SUB_TYPE_DOC = """# Entity: content_sub_type

Structural CLASS or format of a surface (kind: dimension_format | platform_format |
email_component) — only what the source itself defines as reusable: named component-
library entries (Primary 1 Column, Secondary), locked supplied components (Top Matter,
End Matter/ISI footer), dimension formats (banner "Medium Rectangle 300x250"). Concrete
approved artifacts are design_template rows (see design_template.md), never classes;
recurring section patterns / styling variants are rules + selector + tokens, not classes.

- `slots`: editable fields of the component (hero image, H1, body, CTA label, ...).
- `reference_dims`: `{desktop: {w,h}, mobile: {w,h}}` reference proportions.
- `assembly`: `{position: first|last|any, repeatable: bool, locked: bool}` — assembly-order
  constraints. Locked components are supplied by the core team, never built or modified.
- `fills_section_types`: the class IS this section role (locked header fills
  [top_matter]) — graph edge `fills_section`. Feeds rule surfacing.
- `hosts_section_types`: roles the component CAN CARRY as content (Primary 1-Col hosts
  [hero, intro, ...]) — graph edge `hosts_section`. An affordance hint, NOT used to pull
  section rules onto the class.
- `best_for`: retrieval hint describing when to use the component.
- `notes` are non-normative; constraints were promoted to brand_rule rows scoped here.

Rule scoping: `brand_rule.content_sub_type_ids` — null means the rule applies to ALL
sub-types of its content_types; sub_ ids scope it to specific classes/formats. Rules never
scope to template instances; instances inherit via instance_of/fills_section.
Tools: `rules_for_subtype` (class view), `rules_for_template` (instance view).
"""

DESIGN_TEMPLATE_DOC = """# Entity: design_template (+ template_group)

A CONCRETE approved artifact — a complete MJML/HTML block from the brand's template
library or embedded verbatim in the design bible. Instances, not classes.

- `source`: template_library | design_bible. `template_ref`: external library id.
- `file`: kb-relative path to the stored body (templates/{id}.mjml); metadata lives in
  templates/_meta/{id}.json, index in templates/_index.json.
- `instance_of`: FK -> content_sub_type when the template realizes a defined class (a
  header template realizes the locked Top Matter class). Composite templates (e.g.
  header+hero) may have no single class — their `fills_section_types` carry the roles.
- `fills_section_types`: the section role(s) this block IS (graph edge `fills_section`).
- `group_id`/`group_order`: membership in a template_group — a pick-one set of alternates
  (e.g. the brand's approved email headers; `semantics` carries the contract, like
  "assemble exactly one per email").
- `usage_conditions`: per-instance selection conditions, e.g.
  `{requires_content_tags: ["lpga"], inferred: true}` — inherited automatically when the
  template's body references gated assets/tokens. This is where "use template X only
  when ..." lives; it is NOT expressed as rules.

Rule inheritance: a template obeys (a) rules scoped to its class via content_sub_type_ids,
(b) rules targeting the section roles it fills, and (c) email-wide baseline rules. The
`rules_for_template` tool assembles exactly that view. Templates are never rule-scoped
directly.
"""

GOVERNANCE_DOC = """# Entity: governance

Regulatory/legal/MLR adjudication of claims and required language.

- `gov_type`: regulatory | legal | mlr_claim | disclosure | trademark.
- `subject`: the claim/topic being adjudicated.
- `match`: `{method: semantic|lexical|exact, threshold?}` — how generated text triggers it.
- `verdict`: allowed | forbidden | allowed_with_disclosure | requires_qualifier | verbatim_only.
- `preferred_form`: the verbatim string (disclosure text, qualifier, approved claim wording).
- `severity`: info (prompt context) | warn (QA flag) | block (generation guard).
- Rules referencing a governance row carry it in `governance_ids`.
"""

def support_entities_doc() -> str:
    from shared.registries import get_registries

    relations = get_registries().relations()
    return f"""# Support entities

## rule_relation
Directed edge between rules: `{{src_rule_id, dst_rule_id, relation, note}}`.
relation vocabulary (dynamic registry; extraction proposes genuinely new kinds via
`other.<name>`, which get registered permanently): {" | ".join(relations)}.

## rule_group
Provenance blob a rule was atomized from: `{{id, source, doc_ref, original_text}}`.
Use it to read the original un-atomized text around a rule.

## asset_group
Named ordered set of assets (e.g. symptom_icon_trio): `{{id, name, semantics}}`.
Set contract like "all members appear together"; ordering enforced by a brand_rule
with constraint_type=ordering targeting the group.
"""


_CORE_SECTION_GLOSSARY = {
    "hero": "lead visual + headline block opening the email body",
    "intro": "opening copy establishing context/empathy",
    "efficacy": "clinical results, data claims, charts of outcomes",
    "safety": "safety info, side effects (content sections; full ISI lives in end_matter)",
    "patient_story": "testimonial/lifestyle narrative modules",
    "affordability": "pricing/copay/support-program content",
    "cta": "call-to-action section (button, optional right-side image)",
    "callout": "highlighted panel/box devices inside content",
    "chart": "data visualization blocks",
    "top_matter": "locked header component (logo, safety links)",
    "end_matter": "locked footer component (ISI, legal, unsubscribe)",
}


def section_vocab_doc(brand: str) -> str:
    """Brand-specific section vocabulary: curated core + registry-discovered devices."""
    from shared.registries import get_registries

    reg = get_registries()
    lines = ["# Section vocabulary (selector.section_types)", "",
             "This vocabulary is DYNAMIC: a curated core plus brand-discovered section",
             "devices (extraction proposes `other.<name>`; novel entries are registered",
             "permanently in shared/registries.json).", "", "## Core"]
    for name in reg.data["section_types"]["core"]:
        gloss = _CORE_SECTION_GLOSSARY.get(name, "")
        lines.append(f"{name} — {gloss}" if gloss else name)
    discovered = [(n, meta) for n, meta in reg.discovered("section_types").items()
                  if brand in (meta.get("brands") or [])]
    if discovered:
        lines += ["", f"## Discovered for {brand}"]
        for name, meta in discovered:
            note = meta.get("note", "")
            lines.append(f"{name} — {note}" if note else name)
    lines += ["",
              "A blueprint's free-form `section_id` values (e.g. \"what_it_means\") must be",
              "mapped to the closest vocabulary entries by the querying agent; a section may",
              "match several (e.g. a benefits panel = intro + callout).", "",
              "Component classes (content_sub_type) and concrete templates (design_template)",
              "attach to roles via `fills_section_types` (IS that role; feeds rule surfacing)",
              "and classes additionally via `hosts_section_types` (CAN CARRY those roles;",
              "affordance only) — graph edges fills_section / hosts_section. E.g. a",
              "header-with-hero template fills [top_matter, hero], bundling locked-header",
              "obligations with hero design rules."]
    return "\n".join(lines)

PREDICATE_REGISTRY_DOC = """# applies_when predicate registry (closed)

- background_group: {group: light|dark} — rule fires only on that background family
- background_token: {token_id} — fires only on a specific background token
- theme: {theme} — email theme (one theme per email systems)
- content_tag: {tag} — presence of tagged content, e.g. "lpga"
- campaign: {name} — active campaign, e.g. "flip_the_script", "you_deserve_more"
- breakpoint: {breakpoint: desktop|mobile}
- adjacent_section_state: {state} — e.g. "section_above_populated", adjacent background group
- position_in_email: {position: first|last}
- first_mention: {term} — first occurrence of a term, e.g. "dermatomyositis"

Predicates are evaluable by the generator at decision time. Extraction classifies
conditions into this registry and never invents new predicate kinds.
"""


def entity_docs() -> dict[str, str]:
    """filename-stem -> markdown content. section_vocab.md is written separately per
    brand via section_vocab_doc()."""
    return {
        "conventions": GLOBAL_CONVENTIONS,
        "brand_rule": BRAND_RULE_DOC,
        "brand_token": BRAND_TOKEN_DOC,
        "design_asset": DESIGN_ASSET_DOC,
        "content_sub_type": CONTENT_SUB_TYPE_DOC,
        "design_template": DESIGN_TEMPLATE_DOC,
        "governance": GOVERNANCE_DOC,
        "support_entities": support_entities_doc(),
        "predicate_registry": PREDICATE_REGISTRY_DOC,
    }


def overview_doc(brand: str, counts: dict[str, int]) -> str:
    return f"""# Knowledge base overview — brand: {brand}

This KB is the structured form of the {brand.upper()} design bible, atomized into the
v0.2 brand-rules data model.

Contents: {counts.get('rules', 0)} brand_rules (topic clusters),
{counts.get('tokens', 0)} brand_tokens ({counts.get('tokens_primitive', 0)} primitive /
{counts.get('tokens_semantic', 0)} semantic), {counts.get('assets', 0)} design_assets,
{counts.get('governance', 0)} governance rows, {counts.get('subtypes', 0)} content_sub_type
classes, {counts.get('templates', 0)} design_templates in {counts.get('template_groups', 0)}
template_groups, {counts.get('rule_groups', 0)} rule_groups,
{counts.get('asset_groups', 0)} asset_groups.

## Layout

- `schema/` — this documentation (entities, section vocab, predicate registry)
- `rules/_index.json` — compact row per rule (id, rule_class, tags, sections, scope,
  hardness, polarity, constraint_type, applies_when, one-line summary)
- `rules/{{rule_id}}.json` — full rule rows
- `tokens/ assets/ subtypes/ governance/` — side entities, each with `_index.json`
- `templates/` — concrete approved artifacts: bodies as `{{id}}.mjml`, metadata in
  `_meta/{{id}}.json`, index in `_index.json`
- `groups/rule_groups.json` — original pre-atomization text blobs (provenance)
- `groups/asset_groups.json`, `groups/template_groups.json`, `groups/relations.json`
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
2. Graph: follow `applies_to_section` edges from the section node (`sec_{{name}}`).
3. Semantic: vector search over rule summaries/intents/text.
4. Lexical: keyword/grep for exact terms (hex codes, component names, phrases).
5. Token pivot: a concrete detail in the design concept (a hex, an opacity, a radius, an
   alignment) -> search_tokens/query_tokens -> rules_for_token -> governing rules.

Read `schema/section_vocab.md` first to map blueprint section_ids onto the closed
section vocabulary. Rules with `evaluation_scope = email` or `selector.section_types =
null` belong in the email-wide baseline set, not the per-section set.
"""
