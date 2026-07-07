# Review: grp_ibsrela_design_pattern_rules_00

doc_ref: `design_pattern_rules[0]`

## Original text

````
### Canvas & breakpoints (explicit)
- **Desktop email width: 600 px. Mobile email width: 375 px.** Both layouts must exist for every component; SFMC serves the correct one automatically.
- Component reference heights (from library; treat as proportions, not hard limits): Primary 1-Col 600×1138 / 375×788; Primary 2-Col 600×1088 / 375×1538; Secondary 600×458 desktop row.
- [BASELINE] Build emails on a 600 px fixed-width table; mobile via fluid/hybrid technique collapsing to 375 px design width (100% fluid below 480 px).
````

## Extracted rules (2)

### rule_ibsrela_email_dual_layout_widths
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Desktop email width is 600px and mobile email width is 375px; both layouts must exist for every component, and SFMC serves the correct one automatically. Build emails on a 600px fixed-width table with mobile via fluid/hybrid technique collapsing to 375px design width (100% fluid below 480px).
- intent: Guarantee responsive email rendering across desktop and mobile.

### rule_ibsrela_component_reference_dimensions
- class=layout scope=org_baseline hardness=soft_guidance polarity=should sections=None constraint=binding
- rule_text: Component reference heights from the library (Primary 1-Col 600×1138 / 375×788; Primary 2-Col 600×1088 / 375×1538; Secondary 600×458 desktop row) are treated as proportions, not hard limits.
- intent: Provide proportional guidance for component sizing without imposing hard height limits.
