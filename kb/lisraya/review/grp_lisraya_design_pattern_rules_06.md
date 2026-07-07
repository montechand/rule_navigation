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

## Extracted rules (4)

### rule_lisraya_limit_focal_points_per_section
- class=layout scope=brand hardness=strong_default polarity=must sections=None constraint=cardinality
- rule_text: Maintain generous white space; keep sections clean, never cluttered. Limit focal points per section — use contrast to direct attention to the single most important element.
- intent: Direct attention to one key element per section and avoid clutter.

### rule_lisraya_show_dont_tell_break_text_walls
- class=layout scope=brand hardness=soft_guidance polarity=should sections=None constraint=None
- rule_text: "Show, don't tell": break up text walls with imagery and icons.
- intent: Improve readability and engagement by balancing text with visuals.

### rule_lisraya_alternate_section_backgrounds_no_adjacent_match
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: Color blocks delineate topics (My Compass webpage pattern) — alternate White / Light Blue / Golden Sand / gradient section backgrounds so adjacent assembled sections don't visually merge. [GENERAL]: section designers must declare their section's background color in the component metadata so assemblers can sequence without two identical adjacent backgrounds.
- intent: Prevent adjacent sections from visually merging by declaring and alternating background colors.

### rule_lisraya_canonical_content_block_pattern
- class=layout scope=brand hardness=strong_default polarity=should sections=['hero', 'patient_story'] constraint=ordering
- rule_text: Bold headline + simple benefit statements + patient quote is the canonical content block pattern (per patient brochure, which is the reference template for visuals, messaging, and overall tone of ALL LISRAYA materials).
- intent: Establish the reusable canonical content block anchored to the reference patient brochure.
