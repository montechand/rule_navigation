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

### rule_lisraya_icon_style_minimal_line
- class=iconography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Icons use minimal single-color line illustration (icon.style) for clarity and quick recall — consistent stroke weight, rounded line caps, single-color line work. New icons are permitted but must match this stylistic approach. Default is Brand Blue strokes (icon.stroke.color) on light backgrounds.
- intent: Keep iconography consistent and instantly recognizable across materials.

### rule_lisraya_icon_color_palette_only
- class=iconography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Icon colors and backgrounds are adjustable only within the brand palette.
- intent: Prevent off-brand color drift in iconography.

### rule_lisraya_icon_min_render_low_vision
- class=iconography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Consider scale and contrast for low-vision audiences: minimum render size is 32×32px in email (icon.min_render_size).
- intent: Ensure icons remain legible and accessible at small sizes.
