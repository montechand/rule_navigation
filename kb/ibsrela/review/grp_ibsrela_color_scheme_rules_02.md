# Review: grp_ibsrela_color_scheme_rules_02

doc_ref: `color_scheme_rules[2]`

## Original text

````
### Gradients (explicit)
- **Dark Blue → Purple:** stops at 0 (`#262262`), 40 (midpoint marker), 100 (`#92278F`). Primary background/color-block gradient.
- **Silver → White:** stops at 0 (`#CFDCE3`), 40, 100 (`#FFFFFF`). Light background/panel gradient.
- Ideal gradient angle: **45°**, but rotation is permitted as needed.
- The Dark Blue → Purple gradient may be applied to **headlines and callouts** — **sparingly** (e.g., two-tone headline where the back half of the phrase shifts to Purple).
- [BASELINE for email: gradients only as section background images or CSS with solid `#92278F`/`#262262` fallback for Outlook; never gradient body text in email — use the two-color split headline technique (navy phrase + purple phrase) instead.]
````

## Extracted rules (2)

### rule_ibsrela_primary_gradients_definition_and_usage
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: Two primary gradients are defined: Dark Blue → Purple (gradient.primary.dark_blue_to_purple, #262262 → #92278F) is the primary background/color-block gradient; Silver → White (gradient.primary.silver_to_white, #CFDCE3 → #FFFFFF) is the light background/panel gradient. The ideal gradient angle is 45° (gradient.setting.angle_45), but rotation is permitted as needed. The Dark Blue → Purple gradient may additionally be applied to headlines and callouts, but only sparingly (e.g., a two-tone headline where the back half of the phrase shifts to Purple).
- intent: Establish the brand's two primary gradients, their default 45° angle, and permitted sparing use on headlines/callouts.

### rule_ibsrela_email_gradient_fallback_no_gradient_text
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: [BASELINE for email] In email, gradients may only be used as section background images or as CSS with a solid #92278F/#262262 fallback for Outlook. Never use gradient body text in email — instead use the two-color split headline technique (navy phrase + purple phrase).
- intent: Ensure email-client (Outlook) reliability and legibility by forbidding gradient text and requiring solid fallbacks.
