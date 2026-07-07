# Review: grp_lisraya_color_scheme_rules_03

doc_ref: `color_scheme_rules[3]`

## Original text

````
### Gradient Specifications (approved set — never invent gradients)
| Gradient | Stops | Usage |
|---|---|---|
| Brand Blue → Dark Navy | `#00529b` → `#011E45` | Dark backgrounds, blue masthead/waves |
| Sky Blue → Deep Blue | `#358CCB` → `#003D74` | Blue backgrounds, waves |
| Sunshine → 75% Gold | `#faa31b` → Gold @75% | Warm backgrounds |
| Golden Sand → White → Light Blue | `#FEF1C8` → `#ffffff` → `#E6F0F9` | Soft light backgrounds |
| Golden Sand → 75% Gold → Sunshine | `#FEF1C8` → Gold @75% → `#faa31b` | Warm light-to-saturated backgrounds |
| Sunshine → 0C,10M,78Y,0K (≈`#ffe05c` light gold) | `#faa31b` → light gold | **Masthead gradient — the gradient to use with the logo mark for contrast; mark sits at the lightest end** |
- Gradients run horizontally in masthead/banner applications (dark/saturated → light, left → right as shown).
- Used as backgrounds, in combination with the wave graphic, and with the LISRAYA logo mark. Approved values only.
````

## Extracted rules (4)

### rule_lisraya_approved_gradient_set_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Use only the approved gradient set — never invent gradients. Approved gradients: Brand Blue → Dark Navy (#00529b → #011E45) for dark backgrounds and blue masthead/waves; Sky Blue → Deep Blue (#358CCB → #003D74) for blue backgrounds/waves; Sunshine → 75% Gold (#faa31b → Gold @75%) for warm backgrounds; Golden Sand → White → Light Blue (#FEF1C8 → #ffffff → #E6F0F9) for soft light backgrounds; Golden Sand → 75% Gold → Sunshine (#FEF1C8 → Gold @75% → #faa31b) for warm light-to-saturated backgrounds. Approved values only. Concrete stops and usage-specific switching are carried by the gradient tokens.
- intent: Preserve brand color integrity by locking the gradient palette to a fixed approved set.

### rule_lisraya_masthead_gradient_logo_mark_contrast
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: The Masthead gradient (Sunshine → light gold ≈#ffe05c) is the gradient to use with the logo mark for contrast; the logo mark sits at the lightest end of the gradient.
- intent: Ensure the logo mark reads clearly against its masthead background.

### rule_lisraya_gradient_horizontal_direction_masthead_banner
- class=color_application scope=brand hardness=strong_default polarity=must sections=['top_matter'] constraint=ordering
- rule_text: In masthead/banner applications, gradients run horizontally, transitioning dark/saturated → light (left → right as shown).
- intent: Maintain consistent directional flow of brand gradients across mastheads and banners.

### rule_lisraya_gradient_usage_contexts
- class=color_application scope=brand hardness=soft_guidance polarity=may sections=None constraint=None
- rule_text: Approved gradients are used as backgrounds, in combination with the wave graphic, and with the LISRAYA logo mark.
- intent: Clarify the sanctioned application contexts for brand gradients.
