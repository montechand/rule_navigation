# Review: grp_ibsrela_design_pattern_rules_01

doc_ref: `design_pattern_rules[1]`

## Original text

````
### Spacing system [BASELINE]
Defined so independently-built sections butt together cleanly:
- **Outer/container side padding:** 24 px desktop, 16 px mobile (left & right) inside every section.
- **Section vertical padding:** 32 px top and bottom desktop; 24 px mobile. Adjacent sections rely on their own padding — **no margin between stacked section tables** (sections must be edge-to-edge so backgrounds and wave shapes meet flush).
- **Two-column gutter:** 24 px desktop; columns stack with 24 px vertical gap on mobile.
- **Card internal padding:** 16 px all sides.
- **Image-to-text gap:** 16 px.
- **Grid:** 12-column mental grid over the 552 px content area (600 − 2×24); half-width column = 264 px content + 24 px gutter.
- All spacing values are multiples of 8 px (8-pt system). Never introduce odd one-off values; if a layout needs adjustment, move in 8 px steps.
````

## Extracted rules (2)

### rule_ibsrela_spacing_8pt_system_baseline
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The spacing system is defined so independently-built sections butt together cleanly. Outer/container side padding is 24px desktop / 16px mobile inside every section (section.padding.sides). Section vertical padding is 32px top and bottom desktop / 24px mobile (section.padding.vertical). Two-column gutter is 24px desktop, with columns stacking at 24px vertical gap on mobile (section.two_column.gutter). Card internal padding is 16px all sides (card.padding.internal). Image-to-text gap is 16px (image.to_text.gap). A 12-column mental grid sits over the 552px content area (600 − 2×24); half-width column = 264px content + 24px gutter. All spacing values are multiples of 8px (8-pt system) — never introduce odd one-off values; if a layout needs adjustment, move in 8px steps.
- intent: Provide a consistent 8-pt spacing rhythm so modular sections align and butt cleanly.

### rule_ibsrela_sections_edge_to_edge_no_margin
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Adjacent sections rely on their own padding — there must be no margin between stacked section tables. Sections must sit edge-to-edge so backgrounds and wave shapes meet flush.
- intent: Keep independently-built sections flush so backgrounds and wave edges meet without gaps.
