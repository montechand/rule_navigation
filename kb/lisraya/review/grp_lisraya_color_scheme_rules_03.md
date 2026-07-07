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

## Extracted rules (2)

### rule_lisraya_approved_gradients_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Never invent gradients. Only the approved gradient set may be used: Brand Blue → Dark Navy (background.dark.gradient), Sky Blue → Deep Blue (wave.blue.gradient), Sunshine → 75% Gold (wave.gold.gradient), Golden Sand → White → Light Blue (background.soft_light.gradient), Golden Sand → 75% Gold → Sunshine (background.warm.gradient), and the Masthead gradient. Approved values only — each gradient's stops are fixed per its token.
- intent: Prevent off-palette gradients and enforce the sanctioned gradient inventory.

### rule_lisraya_gradient_usage_and_orientation
- class=color_application scope=brand hardness=strong_default polarity=must sections=['top_matter'] constraint=binding
- rule_text: In masthead/banner applications gradients run horizontally, transitioning from the dark/saturated end to the light end (left → right as shown). Gradients are used as backgrounds, in combination with the wave graphic, and with the LISRAYA logo mark. The Masthead gradient (Sunshine → light gold, ≈#ffe05c) is the gradient to use with the logo mark for contrast, with the mark sitting at the lightest end.
- intent: Ensure gradient orientation and the correct masthead gradient for logo-mark contrast.
