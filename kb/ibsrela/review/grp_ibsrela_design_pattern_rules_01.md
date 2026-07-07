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

### rule_ibsrela_spacing_8pt_system_baseline
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All spacing values must be multiples of the 8 px base unit (8-pt system). Never introduce odd one-off values; if a layout needs adjustment, move in 8 px steps.
- intent: Keep a consistent spatial rhythm so independently-built sections align.

### rule_ibsrela_spacing_container_and_section_padding
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Every section carries its own outer/container side padding (24 px desktop, 16 px mobile, left & right) and section vertical padding (32 px desktop, 24 px mobile top and bottom). Card internal padding is 16 px on all sides and the image-to-text gap is 16 px. Concrete values and breakpoint switching live on the referenced tokens.
- intent: Give each independently-built section self-contained padding so sections butt together cleanly.

### rule_ibsrela_spacing_no_margin_between_sections
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Adjacent sections rely on their own padding — there must be no margin between stacked section tables. Sections must be edge-to-edge so backgrounds and wave shapes meet flush.
- intent: Ensure backgrounds and wave shapes meet flush when sections are stacked.

### rule_ibsrela_spacing_two_column_gutter_and_grid
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Two-column layouts use a 24 px gutter on desktop; columns stack with a 24 px vertical gap on mobile. Layout follows a 12-column mental grid over the 552 px content area (600 − 2×24), where a half-width column is 264 px content plus 24 px gutter. Values live on the referenced tokens.
- intent: Standardize column structure and content width for consistent multi-column layouts.
