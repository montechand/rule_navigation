# Review: grp_lisraya_design_pattern_rules_05

doc_ref: `design_pattern_rules[5]`

## Original text

````
### Iconography
- Style: **minimal line illustration** for clarity and quick recall. New icons are permitted but **must match this stylistic approach** (consistent stroke weight, rounded line caps, single-color line work).
- Icon colors and backgrounds adjustable **only within the brand palette**.
- Consider scale and contrast for low-vision audiences. [GENERAL: minimum render size 32×32px in email; default Brand Blue strokes on light backgrounds.]
````

## Extracted rules (4)

### rule_lisraya_icon_minimal_line_style
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Icons use a minimal line-illustration style for clarity and quick recall. New icons are permitted but must match this stylistic approach: consistent stroke weight, rounded line caps, and single-color line work.
- intent: Maintain a consistent, recognizable icon system.

### rule_lisraya_icon_colors_within_palette_only
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: Icon colors and backgrounds may be adjusted only within the brand palette.
- intent: Keep iconography on-brand and prevent ad-hoc coloring.

### rule_lisraya_icon_min_render_size_email
- class=iconography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Consider scale and contrast for low-vision audiences. Minimum icon render size is 32×32px in email.
- intent: Ensure icons remain legible for low-vision audiences.

### rule_lisraya_icon_default_brand_blue_strokes
- class=iconography scope=org_baseline hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: Default icon strokes are Brand Blue (#00529b) on light backgrounds.
- intent: Provide a consistent default icon color with adequate contrast.
