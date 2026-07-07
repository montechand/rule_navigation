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

## Extracted rules (3)

### rule_lisraya_approved_gradient_set_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Never invent gradients. Only the approved gradient set may be used: Brand Blue → Dark Navy (tok_lisraya_gradient_brand_blue_dark_navy), Sky Blue → Deep Blue (tok_lisraya_gradient_sky_blue_deep_blue), Sunshine → 75% Gold (tok_lisraya_gradient_sunshine_gold75), Golden Sand → White → Light Blue (tok_lisraya_gradient_goldensand_white_lightblue), Golden Sand → 75% Gold → Sunshine (tok_lisraya_gradient_goldensand_gold75_sunshine), and the Masthead Sunshine → light gold gradient (tok_lisraya_gradient_masthead_sunshine_lightgold). Approved values only; gradients are used as backgrounds, in combination with the wave graphic, and with the LISRAYA logo mark.
- intent: Restrict gradient usage to the approved palette-derived set to preserve brand consistency.

### rule_lisraya_masthead_gradient_with_logo_mark
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: The Masthead gradient (Sunshine → light gold, tok_lisraya_masthead_gradient) is the gradient to use with the LISRAYA logo mark for contrast; the logo mark sits at the lightest end of the gradient.
- intent: Ensure the logo mark reads clearly by pairing it with the designated masthead gradient at its lightest end.

### rule_lisraya_gradient_horizontal_direction
- class=color_application scope=brand hardness=strong_default polarity=must sections=['top_matter'] constraint=binding
- rule_text: In masthead/banner applications, gradients run horizontally: dark/saturated → light, left → right (tok_lisraya_gradient_angle_horizontal).
- intent: Standardize gradient direction across masthead and banner applications.
