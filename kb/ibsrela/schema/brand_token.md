# Entity: brand_token

Design-system primitive (color, font, type_scale, spacing, radius, gradient, opacity).

- `key`: symbolic path `{type}.{tier}.{name}`, e.g. `color.primary.brand_blue`.
- `value`: `{default, variants: [{when: {surface|breakpoint}, value}]}` — token-level
  bifurcation (e.g. print font vs email fallback; desktop vs mobile size).
- `derived_from`: `{base_token_id, op: tint|opacity|mix, amount}` for derived tokens.
- `aliases`: alternate names used in source docs (same hex called "Green" and "teal").
- `tier`: primary | secondary_accent | tertiary | campaign.
- `scope`: global | campaign:{name} | partnership:{name}.
- `usage_ratio`: palette ratio 0-1 when specified (e.g. 30/30/20/15/5).
- `gated`: `{is_gated: true, gate: predicate}` for reserved tokens (e.g. teal only with
  LPGA content).
