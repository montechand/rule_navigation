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

### rule_lisraya_generous_whitespace_single_focal_point
- class=layout scope=brand hardness=strong_default polarity=must sections=None constraint=cardinality
- rule_text: Maintain generous white space; layouts must stay clean, never cluttered. Limit focal points per section — use contrast to direct attention to the single most important element. Follow 'Show, don't tell': break up text walls with imagery and icons.
- intent: Keep sections uncluttered and guide attention to one key element.

### rule_lisraya_section_background_alternation
- class=layout scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Color blocks delineate topics (My Compass webpage pattern): alternate White / Light Blue / Golden Sand / gradient section backgrounds so adjacent assembled sections don't visually merge, per the section.background.alternation token. [GENERAL] Section designers must declare their section's background color in the component metadata so assemblers can sequence without two identical adjacent backgrounds.
- intent: Prevent adjacent sections from visually merging during assembly.

### rule_lisraya_canonical_content_block_pattern
- class=assembly scope=brand hardness=strong_default polarity=should sections=['patient_story'] constraint=ordering
- rule_text: Bold headline + simple benefit statements + patient quote is the canonical content block pattern, per the patient brochure, which is the reference template for visuals, messaging, and overall tone of ALL LISRAYA materials.
- intent: Establish the reference content structure derived from the master patient brochure.
