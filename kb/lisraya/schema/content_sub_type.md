# Entity: content_sub_type

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
