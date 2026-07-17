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

### rule_lisraya_alternate_section_backgrounds_and_declare_metada
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Use color blocks to delineate topics by alternating White, Light Blue, Golden Sand, and gradient section backgrounds so adjacent assembled sections do not visually merge. [GENERAL] Section designers must declare their section background color in component metadata so assemblers can avoid two identical adjacent backgrounds.
- intent: Preserve topic separation and enable safe background sequencing during assembly.

### rule_lisraya_break_up_text_walls_with_visuals
- class=imagery scope=brand hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Apply the “Show, don't tell” principle: break up walls of text with imagery and icons.
- intent: Make content easier to scan and more visually engaging.

### rule_lisraya_canonical_patient_brochure_content_block
- class=assembly scope=brand hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Use a bold headline, simple benefit statements, and a patient quote as the canonical content-block pattern. The patient brochure is the reference template for visuals, messaging, and overall tone across all LISRAYA materials.
- intent: Maintain a consistent patient-centered content and visual approach across materials.

### rule_lisraya_single_focal_point_with_generous_whitespace
- class=layout scope=brand hardness=strong_default polarity=must sections=None constraint=cardinality
- rule_text: Sections use generous white space and remain clean rather than cluttered. Limit each section to a single focal point, using contrast to direct attention to its most important element.
- intent: Create a clear visual hierarchy without clutter.
