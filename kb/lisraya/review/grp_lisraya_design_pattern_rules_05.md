# Review: grp_lisraya_design_pattern_rules_05

doc_ref: `design_pattern_rules[5]`

## Original text

````
### Iconography
- Style: **minimal line illustration** for clarity and quick recall. New icons are permitted but **must match this stylistic approach** (consistent stroke weight, rounded line caps, single-color line work).
- Icon colors and backgrounds adjustable **only within the brand palette**.
- Consider scale and contrast for low-vision audiences. [GENERAL: minimum render size 32×32px in email; default Brand Blue strokes on light backgrounds.]
````

## Extracted rules (2)

### rule_lisraya_icon_line_style_and_palette
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Icons use minimal line illustration for clarity and quick recall. New icons must match this approach with consistent stroke weight, rounded line caps, and single-color line work; icon colors and backgrounds may be adjusted only within the brand palette.
- intent: Maintain a recognizable, clear icon system while preventing off-brand color treatments.

### rule_lisraya_icon_low_vision_size_and_light_background_stroke
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: For low-vision audiences in email, icons must render at a minimum 32×32px; on light backgrounds, use default Brand Blue (#00529b) strokes.
- intent: Preserve icon visibility and legibility for low-vision audiences.
