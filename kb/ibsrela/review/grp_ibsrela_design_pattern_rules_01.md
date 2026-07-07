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
- rule_text: All spacing values must be multiples of 8px (8-pt system). Never introduce odd one-off values; if a layout needs adjustment, move in 8px steps.
- intent: Keep spacing rhythm consistent so independently-built sections align.

### rule_ibsrela_spacing_section_padding_gutters
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Inside every section: outer/container side padding (24px desktop, 16px mobile, left & right), section vertical padding (32px top and bottom desktop, 24px mobile), two-column gutter (24px desktop; columns stack with 24px vertical gap on mobile), card internal padding (16px all sides), and image-to-text gap (16px). Breakpoint variants ride on the tokens.
- intent: Standardize intra-section spacing so sections read consistently across breakpoints.

### rule_ibsrela_spacing_no_margin_between_sections
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Adjacent sections rely on their own padding — no margin between stacked section tables. Sections must be edge-to-edge so backgrounds and wave shapes meet flush.
- intent: Let independently-built sections butt together cleanly with backgrounds/wave shapes meeting flush.

### rule_ibsrela_spacing_grid_content_area
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Use a 12-column mental grid over the 552px content area (600 − 2×24); half-width column = 264px content + 24px gutter.
- intent: Provide a consistent column framework for layout within the email content area.
