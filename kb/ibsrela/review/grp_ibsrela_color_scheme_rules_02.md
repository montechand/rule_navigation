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

## Extracted rules (3)

### rule_ibsrela_primary_gradient_definition_and_angle
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: Two brand gradients are defined: the primary Dark Blue → Purple gradient (background.primary.gradient — stops at #262262, midpoint marker, #92278F) used as the primary background/color-block gradient, and the light Silver → White gradient (background.light.gradient — #CFDCE3 to #FFFFFF) for light backgrounds/panels. Ideal gradient angle is 45°, but rotation is permitted as needed.
- intent: Establish the two brand gradients and their default angle.

### rule_ibsrela_primary_gradient_on_headlines_callouts
- class=color_application scope=brand hardness=soft_guidance polarity=may sections=['callout'] constraint=binding
- rule_text: The Dark Blue → Purple gradient may be applied to headlines and callouts, but only sparingly (e.g., a two-tone headline where the back half of the phrase shifts to Purple).
- intent: Permit but limit decorative gradient use on headlines/callouts.

### rule_ibsrela_email_gradient_background_only_solid_fallback
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: [BASELINE for email] Gradients may only be used as section background images or CSS with a solid #92278F/#262262 fallback for Outlook. Never use gradient body text in email — instead use the two-color split headline technique (navy phrase + purple phrase).
- intent: Ensure email gradient rendering degrades gracefully in Outlook and avoids gradient text.
