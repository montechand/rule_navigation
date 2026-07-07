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

### rule_ibsrela_primary_gradients_definition_and_usage
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Two brand gradients are defined: the Dark Blue → Purple gradient (section.gradient.primary; stops #262262 at 0, midpoint at 40, #92278F at 100) is the primary background/color-block gradient, and the Silver → White gradient (section.gradient.light; #CFDCE3 → #FFFFFF) is the light background/panel gradient. The ideal gradient angle is 45° (section.gradient.angle), but rotation is permitted as needed.
- intent: Standardize the brand's two-color gradients and their default angle.

### rule_ibsrela_gradient_on_headlines_callouts_sparingly
- class=color_application scope=brand hardness=soft_guidance polarity=should sections=['callout'] constraint=None
- rule_text: The Dark Blue → Purple gradient may be applied to headlines and callouts, but only sparingly — e.g., a two-tone headline where the back half of the phrase shifts to Purple.
- intent: Allow occasional expressive gradient text while preventing overuse.

### rule_ibsrela_email_gradient_background_only_no_gradient_text
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: [BASELINE for email] Gradients may only be used as section background images or CSS with a solid #92278F/#262262 fallback for Outlook. Never use gradient body text in email — use the two-color split headline technique instead (navy phrase + purple phrase).
- intent: Ensure Outlook-safe rendering and legible email text by forbidding gradient text.
