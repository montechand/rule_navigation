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

### rule_lisraya_approved_gradients_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Never invent gradients. Only the approved gradient set may be used: Brand Blue → Dark Navy (tok_lisraya_gradient_brand_blue_dark_navy), Sky Blue → Deep Blue (tok_lisraya_gradient_sky_blue_deep_blue), Sunshine → 75% Gold (tok_lisraya_gradient_sunshine_gold75), Golden Sand → White → Light Blue (tok_lisraya_gradient_goldensand_white_lightblue), Golden Sand → 75% Gold → Sunshine (tok_lisraya_gradient_goldensand_gold75_sunshine), and the Masthead Sunshine → light gold (tok_lisraya_gradient_masthead_sunshine_lightgold). Approved values only.
- intent: Keep gradient usage on-brand and prevent ad-hoc color blends.

### rule_lisraya_gradient_usage_contexts
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: Approved gradients are used as backgrounds, in combination with the wave graphic, and with the LISRAYA logo mark. Match gradient to context: Brand Blue → Dark Navy for dark backgrounds and blue masthead/waves; Sky Blue → Deep Blue for blue backgrounds and waves; Sunshine → 75% Gold for warm backgrounds; Golden Sand → White → Light Blue for soft light backgrounds; Golden Sand → 75% Gold → Sunshine for warm light-to-saturated backgrounds.
- intent: Guide selection of the correct approved gradient per surface context.

### rule_lisraya_gradient_horizontal_direction
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: In masthead/banner applications, gradients run horizontally: dark/saturated → light, left → right (tok_lisraya_gradient_angle_horizontal).
- intent: Ensure consistent gradient direction in masthead and banner layouts.

### rule_lisraya_masthead_gradient_logo_mark_contrast
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: The Masthead gradient (Sunshine → light gold ≈#ffe05c, tok_lisraya_gradient_masthead_sunshine_lightgold) is the gradient to use with the logo mark for contrast; the logo mark sits at the lightest end of the gradient.
- intent: Guarantee logo-mark legibility against the masthead gradient.
