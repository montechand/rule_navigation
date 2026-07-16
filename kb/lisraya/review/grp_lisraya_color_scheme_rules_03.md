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
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Only the approved gradient set may be used — never invent gradients. Approved gradients and their usages: Brand Blue → Dark Navy (#00529b → #011E45) for dark backgrounds and blue masthead/waves; Sky Blue → Deep Blue (#358CCB → #003D74) for blue backgrounds and waves; Sunshine → 75% Gold (#faa31b → Gold @75%) for warm backgrounds; Golden Sand → White → Light Blue (#FEF1C8 → #ffffff → #E6F0F9) for soft light backgrounds; and Golden Sand → 75% Gold → Sunshine (#FEF1C8 → Gold @75% → #faa31b) for warm light-to-saturated backgrounds. Gradients are used as backgrounds, in combination with the wave graphic, and with the LISRAYA logo mark — approved values only.
- intent: Preserve brand color integrity by limiting gradients to the sanctioned palette.

### rule_lisraya_gradient_horizontal_orientation
- class=color_application scope=brand hardness=strong_default polarity=must sections=['top_matter', 'hero'] constraint=ordering
- rule_text: In masthead/banner applications gradients run horizontally, transitioning dark/saturated → light, left → right as shown.
- intent: Maintain consistent gradient direction and light-to-dark flow across banner/masthead applications.

### rule_lisraya_masthead_logo_gradient_binding
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: The masthead gradient — Sunshine → light gold (#faa31b → ≈#ffe05c / 0C,10M,78Y,0K) — is the gradient to use with the LISRAYA logo mark for contrast, with the mark sitting at the lightest end.
- intent: Ensure the logo mark reads with adequate contrast against the masthead gradient.
