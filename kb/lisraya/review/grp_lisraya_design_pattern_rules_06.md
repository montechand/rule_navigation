# Review: grp_lisraya_design_pattern_rules_06

doc_ref: `design_pattern_rules[6]`

## Original text

````
### Layout Principles
- Generous white space; clean, never cluttered. **Limit focal points per section** — use contrast to direct attention to the single most important element.
- "Show, don't tell": break up text walls with imagery and icons.
- Color blocks delineate topics (My Compass webpage pattern) — alternate White / Light Blue / Golden Sand / gradient section backgrounds so adjacent assembled sections don't visually merge. **[GENERAL]: section designers must declare their section's background color in the component metadata so assemblers can sequence without two identical adjacent backgrounds.**
- Bold headline + simple benefit statements + patient quote is the canonical content block pattern (per patient brochure, which is the **reference template for visuals, messaging, and overall tone of ALL LISRAYA materials**).
````

## Extracted rules (5)

### rule_lisraya_limit_focal_points_per_section
- class=layout scope=brand hardness=strong_default polarity=must sections=None constraint=cardinality
- rule_text: Maintain generous white space and keep layouts clean, never cluttered. Limit focal points per section — use contrast to direct attention to the single most important element.
- intent: Focus viewer attention on one key element per section.

### rule_lisraya_show_dont_tell_break_text_walls
- class=layout scope=brand hardness=soft_guidance polarity=should sections=None constraint=None
- rule_text: "Show, don't tell": break up text walls with imagery and icons.
- intent: Improve readability and engagement by mixing visuals with text.

### rule_lisraya_alternate_section_backgrounds
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Use color blocks to delineate topics (My Compass webpage pattern) — alternate White / Light Blue / Golden Sand / gradient section backgrounds so adjacent assembled sections don't visually merge.
- intent: Prevent adjacent sections from visually merging.

### rule_lisraya_declare_section_background_metadata
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: [GENERAL] Section designers must declare their section's background color in the component metadata so assemblers can sequence without two identical adjacent backgrounds.
- intent: Enable assemblers to avoid two identical adjacent backgrounds.

### rule_lisraya_canonical_content_block_pattern
- class=layout scope=brand hardness=strong_default polarity=should sections=['patient_story'] constraint=None
- rule_text: Bold headline + simple benefit statements + patient quote is the canonical content block pattern, per the patient brochure, which is the reference template for visuals, messaging, and overall tone of ALL LISRAYA materials.
- intent: Establish the patient brochure content block as the master reference template.
