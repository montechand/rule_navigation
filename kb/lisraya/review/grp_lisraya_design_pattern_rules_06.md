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

### rule_lisraya_adjacent_section_background_alternation
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: Adjacent assembled sections must not share identical backgrounds (White, Light Blue, Golden Sand, or gradients). Designers must declare the section background color in the component metadata so assemblers can alternate colors and prevent visual merging.
- intent: Ensure distinct visual separation between subsequent sections in modular emails.

### rule_lisraya_canonical_content_block_pattern
- class=assembly scope=brand hardness=strong_default polarity=should sections=['patient_story'] constraint=ordering
- rule_text: Follow the canonical content block pattern (Bold headline + simple benefit statements + patient quote) as modeled by the reference patient brochure for visuals, messaging, and overall tone.
- intent: Align layouts with the approved structure of the core brand reference materials.

### rule_lisraya_layout_principles_and_clutter_prevention
- class=layout scope=brand hardness=strong_default polarity=must sections=None constraint=cardinality
- rule_text: Apply generous white space to maintain a clean layout. Limit focal points to a single primary element per section, directing attention through contrast. Break up text walls by incorporating supporting imagery and icons.
- intent: Maintain clean, uncluttered layouts with a single dominant visual focal point per section.
