# Review: grp_lisraya_design_pattern_rules_05

doc_ref: `design_pattern_rules[5]`

## Original text

````
### Iconography
- Style: **minimal line illustration** for clarity and quick recall. New icons are permitted but **must match this stylistic approach** (consistent stroke weight, rounded line caps, single-color line work).
- Icon colors and backgrounds adjustable **only within the brand palette**.
- Consider scale and contrast for low-vision audiences. [GENERAL: minimum render size 32×32px in email; default Brand Blue strokes on light backgrounds.]
````

## Extracted rules (3)

### rule_lisraya_iconography_minimal_line_style
- class=iconography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Iconography uses minimal line illustration for clarity and quick recall (iconography.style: consistent stroke weight, rounded line caps, single-color line work). New icons are permitted but must match this stylistic approach.
- intent: Keep icon set visually consistent and instantly recognizable.

### rule_lisraya_iconography_color_palette_only
- class=iconography scope=brand hardness=strong_default polarity=must sections=None constraint=exclusivity
- rule_text: Icon colors and backgrounds are adjustable only within the brand palette; default Brand Blue strokes on light backgrounds (iconography.color).
- intent: Confine icon coloring to approved brand colors.

### rule_lisraya_iconography_min_render_size_contrast
- class=iconography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Consider scale and contrast for low-vision audiences: minimum render size 32×32px in email (iconography.min_size).
- intent: Ensure icons remain legible for low-vision users at small sizes.
