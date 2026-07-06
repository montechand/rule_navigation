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

## Extracted rules (8)

### rule_lisraya_approved_gradients_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Never invent gradients. Only the approved gradient set may be used: Brand Blue → Dark Navy (#00529b → #011E45), Sky Blue → Deep Blue (#358CCB → #003D74), Sunshine → 75% Gold (#faa31b → Gold @75%), Golden Sand → White → Light Blue (#FEF1C8 → #ffffff → #E6F0F9), Golden Sand → 75% Gold → Sunshine (#FEF1C8 → Gold @75% → #faa31b), and the Masthead gradient Sunshine → light gold (#faa31b → ≈#ffe05c). Approved values only.
- intent: Preserve brand color integrity by preventing ad-hoc gradients.

### rule_lisraya_gradient_brand_blue_dark_navy_usage
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: The Brand Blue → Dark Navy gradient (#00529b → #011E45) is used for dark backgrounds and blue masthead/waves.
- intent: Assign the dark gradient to its approved use context.

### rule_lisraya_gradient_sky_blue_deep_blue_usage
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: The Sky Blue → Deep Blue gradient (#358CCB → #003D74) is used for blue backgrounds and waves.
- intent: Assign the blue gradient to its approved use context.

### rule_lisraya_gradient_sunshine_gold75_usage
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: The Sunshine → 75% Gold gradient (#faa31b → Gold @75%) is used for warm backgrounds.
- intent: Assign the warm gradient to its approved use context.

### rule_lisraya_gradient_golden_sand_white_light_blue_usage
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: The Golden Sand → White → Light Blue gradient (#FEF1C8 → #ffffff → #E6F0F9) is used for soft light backgrounds.
- intent: Assign the soft light gradient to its approved use context.

### rule_lisraya_gradient_golden_sand_gold75_sunshine_usage
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: The Golden Sand → 75% Gold → Sunshine gradient (#FEF1C8 → Gold @75% → #faa31b) is used for warm light-to-saturated backgrounds.
- intent: Assign the warm light-to-saturated gradient to its approved use context.

### rule_lisraya_masthead_gradient_with_logo_mark
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=pairing
- rule_text: The Masthead gradient — Sunshine → light gold (#faa31b → ≈#ffe05c, 0C,10M,78Y,0K) — is the gradient to use with the LISRAYA logo mark for contrast; the mark sits at the lightest end of the gradient.
- intent: Ensure logo mark contrast on the masthead.

### rule_lisraya_gradients_run_horizontal_masthead_banner
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: In masthead/banner applications gradients run horizontally, transitioning from dark/saturated to light (left → right as shown).
- intent: Maintain consistent gradient direction in mastheads and banners.
