# Entity: content_sub_type

Format or structural component of a surface (kind: dimension_format | platform_format |
email_component). For email: the component library (Top Matter, Primary 1 Column,
Primary 2 Column, Secondary, End Matter, ...) PLUS concrete approved templates ingested
from the brand's template library (ids like `sub_{brand}_tpl_*`, `template_ref` = library
id, `template_file` = kb-relative path to the stored MJML body). For banners, dimension
formats (kind=dimension_format with `size`) play the same role.

- `slots`: editable fields of the component (hero image, H1, body, CTA label, ...).
- `reference_dims`: `{desktop: {w,h}, mobile: {w,h}}` reference proportions.
- `assembly`: `{position: first|last|any, repeatable: bool, locked: bool}` — assembly-order
  constraints. Locked components are supplied by the core team, never built or modified.
- `covers_section_types`: which section vocabulary entries the component/template covers
  (a header-with-hero template covers [top_matter, hero]) — graph edge `covers_section`.
- `best_for`: retrieval hint describing when to use the component.
- `notes` are non-normative; constraints were promoted to brand_rule rows scoped here.

Rule scoping: `brand_rule.content_sub_type_ids` — null means the rule applies to ALL
sub-types of its content_types; ids scope it to specific components/templates/formats.
Use the `rules_for_subtype` tool to surface everything applying to one template:
directly-scoped rules + rules targeting its covered sections + the all-subtype baseline.
