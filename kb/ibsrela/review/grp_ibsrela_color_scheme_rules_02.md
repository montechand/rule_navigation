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

## Extracted rules (6)

### rule_ibsrela_dark_blue_purple_gradient_primary_background
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: The Dark Blue → Purple gradient (stops at 0 = #262262, 40 = midpoint marker, 100 = #92278F) is the primary background/color-block gradient.
- intent: Establish the brand's principal color-block gradient.

### rule_ibsrela_silver_white_gradient_light_panel
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: The Silver → White gradient (stops at 0 = #CFDCE3, 40 = midpoint marker, 100 = #FFFFFF) is the light background/panel gradient.
- intent: Provide the standard light-panel gradient.

### rule_ibsrela_gradient_angle_45deg
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=None
- rule_text: The ideal gradient angle is 45°, but rotation is permitted as needed.
- intent: Set the default gradient orientation while allowing flexibility.

### rule_ibsrela_dark_blue_purple_gradient_headlines_callouts_spa
- class=color_application scope=brand hardness=soft_guidance polarity=may sections=['callout'] constraint=None
- rule_text: The Dark Blue → Purple gradient may be applied to headlines and callouts, but only sparingly (e.g., a two-tone headline where the back half of the phrase shifts to Purple).
- intent: Permit limited decorative gradient use on text elements without overuse.

### rule_ibsrela_email_gradients_background_only_with_fallback
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: [BASELINE for email] In email, gradients may only be used as section background images or CSS, and must include a solid #92278F/#262262 fallback for Outlook.
- intent: Ensure email gradient rendering degrades gracefully in Outlook.

### rule_ibsrela_email_no_gradient_body_text
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: [BASELINE for email] Never use gradient body text in email; instead use the two-color split headline technique (navy phrase + purple phrase).
- intent: Avoid unreliable gradient text rendering in email clients.
