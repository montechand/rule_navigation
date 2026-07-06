# Entity: content_sub_type

Format or structural component of a surface (kind: dimension_format | platform_format |
email_component). For email: the component library (Top Matter, Primary 1 Column,
Primary 2 Column, Secondary, End Matter, ...).

- `slots`: editable fields of the component (hero image, H1, body, CTA label, ...).
- `reference_dims`: `{desktop: {w,h}, mobile: {w,h}}` reference proportions.
- `assembly`: `{position: first|last|any, repeatable: bool, locked: bool}` — assembly-order
  constraints. Locked components are supplied by the core team, never built or modified.
- `best_for`: retrieval hint describing when to use the component.
- `notes` are non-normative; constraints were promoted to brand_rule rows scoped here.
