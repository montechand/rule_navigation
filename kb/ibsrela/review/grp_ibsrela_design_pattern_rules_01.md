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

## Extracted rules (8)

### rule_ibsrela_outer_side_padding_8pt
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Every section must use an outer/container side padding (left & right) of 24 px on desktop and 16 px on mobile.
- intent: Keep independently-built sections aligned at their edges.

### rule_ibsrela_section_vertical_padding_8pt
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Section vertical padding must be 32 px top and bottom on desktop and 24 px on mobile.
- intent: Consistent vertical rhythm between stacked sections.

### rule_ibsrela_no_margin_between_sections
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: There must be no margin between stacked section tables — adjacent sections rely on their own padding and must sit edge-to-edge so backgrounds and wave shapes meet flush.
- intent: Ensure backgrounds and wave shapes meet flush across section boundaries.

### rule_ibsrela_two_column_gutter_8pt
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Two-column layouts must use a 24 px gutter on desktop; columns stack with a 24 px vertical gap on mobile.
- intent: Consistent column separation across breakpoints.

### rule_ibsrela_card_internal_padding_8pt
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Card internal padding must be 16 px on all sides.
- intent: Uniform interior spacing for cards/callouts.

### rule_ibsrela_image_to_text_gap_8pt
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The gap between an image and adjacent text must be 16 px.
- intent: Consistent separation between images and text.

### rule_ibsrela_twelve_column_grid_552_content
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Lay out on a 12-column mental grid over the 552 px content area (600 − 2×24 px). A half-width column = 264 px content + 24 px gutter.
- intent: Standardize the working grid for column layouts.

### rule_ibsrela_all_spacing_multiples_of_8
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All spacing values must be multiples of 8 px (8-pt system). Never introduce odd one-off values; if a layout needs adjustment, move in 8 px steps.
- intent: Enforce a consistent 8-pt spacing system.
