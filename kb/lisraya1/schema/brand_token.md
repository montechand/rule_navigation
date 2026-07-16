# Entity: brand_token

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
