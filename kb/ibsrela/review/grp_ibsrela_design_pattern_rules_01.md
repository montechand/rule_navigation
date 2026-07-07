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

## Extracted rules (4)

### rule_ibsrela_spacing_8pt_system
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All spacing values are multiples of 8 px (8-pt system). Never introduce odd one-off values; if a layout needs adjustment, move in 8 px steps.
- intent: Keep independently-built sections dimensionally consistent on a shared rhythm.

### rule_ibsrela_section_padding_and_gutters
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Outer/container side padding is 24 px desktop / 16 px mobile inside every section; section vertical padding is 32 px top and bottom desktop / 24 px mobile; two-column gutter is 24 px desktop with columns stacking at 24 px vertical gap on mobile; card internal padding is 16 px all sides; image-to-text gap is 16 px.
- intent: Standardize internal padding and gutters so sections read as one system.

### rule_ibsrela_sections_edge_to_edge_no_margin
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Adjacent sections rely on their own padding — there must be no margin between stacked section tables. Sections must be edge-to-edge so backgrounds and wave shapes meet flush.
- intent: Ensure independently-built sections butt together cleanly with flush backgrounds/wave edges.

### rule_ibsrela_content_grid_structure
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Use a 12-column mental grid over the 552 px content area (600 − 2×24 px side padding); a half-width column is 264 px content plus 24 px gutter.
- intent: Provide a shared grid so multi-column layouts align across sections.
