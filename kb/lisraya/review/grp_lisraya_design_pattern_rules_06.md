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

## Extracted rules (3)

### rule_lisraya_limit_focal_points_per_section
- class=layout scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Maintain generous white space and a clean, never-cluttered layout. Limit focal points per section — use contrast to direct attention to the single most important element. Follow 'Show, don't tell': break up text walls with imagery and icons.
- intent: Direct the reader's attention to one clear focal point per section and avoid clutter.

### rule_lisraya_alternate_section_backgrounds_no_adjacent_match
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Color blocks delineate topics (My Compass webpage pattern) — alternate White / Light Blue / Golden Sand / gradient section backgrounds so adjacent assembled sections don't visually merge. [GENERAL] Section designers must declare their section's background color in the component metadata so assemblers can sequence without two identical adjacent backgrounds. The section background token carries the alternation variant keyed by adjacent-section state.
- intent: Prevent adjacent assembled sections from visually merging by alternating background colors.

### rule_lisraya_canonical_content_block_pattern
- class=assembly scope=brand hardness=strong_default polarity=should sections=['patient_story'] constraint=ordering
- rule_text: The canonical content block pattern is a bold headline + simple benefit statements + patient quote, per the patient brochure, which is the reference template for visuals, messaging, and overall tone of ALL LISRAYA materials.
- intent: Establish the patient-brochure content block as the reference pattern for all materials.
