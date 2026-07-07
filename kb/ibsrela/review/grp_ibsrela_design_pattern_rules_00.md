# Review: grp_ibsrela_design_pattern_rules_00

doc_ref: `design_pattern_rules[0]`

## Original text

````
### Canvas & breakpoints (explicit)
- **Desktop email width: 600 px. Mobile email width: 375 px.** Both layouts must exist for every component; SFMC serves the correct one automatically.
- Component reference heights (from library; treat as proportions, not hard limits): Primary 1-Col 600×1138 / 375×788; Primary 2-Col 600×1088 / 375×1538; Secondary 600×458 desktop row.
- [BASELINE] Build emails on a 600 px fixed-width table; mobile via fluid/hybrid technique collapsing to 375 px design width (100% fluid below 480 px).
````

## Extracted rules (3)

### rule_ibsrela_email_dual_layout_widths
- class=layout scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Desktop email width is 600 px and mobile email width is 375 px (email.width). Both desktop and mobile layouts must exist for every component; SFMC serves the correct one automatically.
- intent: Guarantee responsive delivery across the two supported email widths.

### rule_ibsrela_email_fixed_width_fluid_collapse
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [BASELINE] Build emails on a 600 px fixed-width table; handle mobile via fluid/hybrid technique that collapses to a 375 px design width, going 100% fluid below the 480 px breakpoint.
- intent: Standardize the fixed-width + fluid-hybrid build technique for all emails.

### rule_ibsrela_component_reference_heights_proportional
- class=layout scope=brand hardness=soft_guidance polarity=should sections=None constraint=binding
- rule_text: Component reference heights from the library (Primary 1-Col 600×1138 / 375×788; Primary 2-Col 600×1088 / 375×1538; Secondary 600×458 desktop row) should be treated as proportions, not hard limits.
- intent: Provide sizing guidance without imposing rigid height caps.
