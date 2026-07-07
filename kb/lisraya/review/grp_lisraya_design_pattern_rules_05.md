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

### rule_lisraya_icon_minimal_line_style
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Icons use minimal line illustration (icon.style) for clarity and quick recall. New icons are permitted but must match this stylistic approach: consistent stroke weight, rounded line caps, single-color line work. Default Brand Blue strokes (icon.stroke.color) on light backgrounds.
- intent: Keep iconography visually consistent and instantly recognizable.

### rule_lisraya_icon_color_within_palette
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Icon colors and backgrounds are adjustable only within the brand palette.
- intent: Prevent off-brand icon coloring.

### rule_lisraya_icon_min_render_low_vision
- class=iconography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Consider scale and contrast for low-vision audiences. [GENERAL] Minimum render size 32×32px in email (icon.min_render_size).
- intent: Ensure icons remain legible for low-vision users.
