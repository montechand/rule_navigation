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

### rule_ibsrela_email_width_desktop_mobile
- class=layout scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Desktop email width is 600 px and mobile email width is 375 px. Both layouts must exist for every component; SFMC serves the correct one automatically.
- intent: Ensure every component renders correctly across desktop and mobile via responsive serving.

### rule_ibsrela_component_heights_are_proportions
- class=layout scope=brand hardness=soft_guidance polarity=should sections=None constraint=None
- rule_text: Treat component reference heights from the library as proportions, not hard limits: Primary 1-Col 600×1138 / 375×788; Primary 2-Col 600×1088 / 375×1538; Secondary 600×458 desktop row.
- intent: Allow content-driven height while keeping proportions consistent with the library.

### rule_ibsrela_baseline_600px_fluid_hybrid_build
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: [BASELINE] Build emails on a 600 px fixed-width table; handle mobile via fluid/hybrid technique collapsing to a 375 px design width (100% fluid below 480 px).
- intent: Standardize the responsive build technique for reliable cross-client rendering.
