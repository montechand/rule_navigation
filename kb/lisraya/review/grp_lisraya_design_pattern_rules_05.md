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
- class=iconography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Icons use the minimal single-color line illustration style (icon.style) for clarity and quick recall. New icons are permitted but must match this stylistic approach — consistent stroke weight, rounded line caps, single-color line work. Default strokes are Brand Blue on light backgrounds (icon.stroke_color).
- intent: Keep iconography consistent and recognizable across materials.

### rule_lisraya_icon_color_within_palette
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Icon colors and backgrounds are adjustable only within the brand palette.
- intent: Confine icon coloring to approved brand colors.

### rule_lisraya_icon_min_render_low_vision
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Consider scale and contrast for low-vision audiences. [GENERAL] Minimum render size is 32×32px in email (icon.min_render).
- intent: Ensure icons remain legible for low-vision users.
