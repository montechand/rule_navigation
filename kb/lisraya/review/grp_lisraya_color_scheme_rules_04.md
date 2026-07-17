# Review: grp_lisraya_color_scheme_rules_04

doc_ref: `color_scheme_rules[4]`

## Original text

````
### Contrast
- **Test contrast levels** (webaim.com or equivalent) for every text/background pair. [GENERAL minimums: WCAG AA — 4.5:1 body text, 3:1 large text ≥24px or 19px bold.]
- Known-safe pairs: Brand Blue, Deep Blue, Dark Navy, Graphite on White/Light Blue/Golden Sand; White on Brand Blue/Deep Blue/Dark Navy. **Avoid:** Gold or Sunshine text on White (fails contrast) — golds are for surfaces, rules, and large display emphasis only.
- **Don't rely on color alone** to convey meaning — pair with icons, depth, clear copy, or visual feedback.
````

## Extracted rules (2)

### rule_lisraya_non_color_meaning_cues
- class=accessibility scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Do not rely on color alone to convey meaning; pair color with icons, depth, clear copy, or visual feedback.
- intent: Make meaning understandable for people who cannot distinguish color cues.

### rule_lisraya_wcag_text_background_contrast
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Test every text/background pair using webaim.com or an equivalent tool. Meet WCAG AA minimum contrast: 4.5:1 for body text and 3:1 for large text (≥24px or 19px bold). Known-safe pairs are Brand Blue, Deep Blue, Dark Navy, or Graphite text on White, Light Blue, or Golden Sand; and White text on Brand Blue, Deep Blue, or Dark Navy. Avoid Gold or Sunshine text on White because it fails contrast; use golds only for surfaces, rules, and large display emphasis.
- intent: Ensure readable, WCAG-AA-compliant text treatment across approved palette combinations.
