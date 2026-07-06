# Review: grp_lisraya_color_scheme_rules_04

doc_ref: `color_scheme_rules[4]`

## Original text

````
### Contrast
- **Test contrast levels** (webaim.com or equivalent) for every text/background pair. [GENERAL minimums: WCAG AA — 4.5:1 body text, 3:1 large text ≥24px or 19px bold.]
- Known-safe pairs: Brand Blue, Deep Blue, Dark Navy, Graphite on White/Light Blue/Golden Sand; White on Brand Blue/Deep Blue/Dark Navy. **Avoid:** Gold or Sunshine text on White (fails contrast) — golds are for surfaces, rules, and large display emphasis only.
- **Don't rely on color alone** to convey meaning — pair with icons, depth, clear copy, or visual feedback.
````

## Extracted rules (4)

### rule_lisraya_test_contrast_every_text_bg_pair
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Test contrast levels (webaim.com or equivalent) for every text/background pair. General minimums are WCAG AA — 4.5:1 for body text, and 3:1 for large text (≥24px, or 19px bold).
- intent: Ensure all text meets WCAG AA legibility requirements.

### rule_lisraya_known_safe_dark_text_on_light_surfaces
- class=color_application scope=org_baseline hardness=strong_default polarity=should sections=None constraint=pairing
- rule_text: Known-safe text/background pairs: Brand Blue (#00529b), Deep Blue (#003D74), Dark Navy (#011E45), and Graphite (#212121) on White (#ffffff), Light Blue (#E6F0F9), or Golden Sand (#FEF1C8); and White on Brand Blue, Deep Blue, or Dark Navy.
- intent: Provide vetted, contrast-safe color combinations for text.

### rule_lisraya_no_gold_sunshine_text_on_white
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Avoid Gold (#ffc60a) or Sunshine (#faa31b) text on White (#ffffff) — it fails contrast. Golds are for surfaces, rules, and large display emphasis only, not body text.
- intent: Prevent illegible low-contrast gold text.

### rule_lisraya_dont_rely_on_color_alone
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Don't rely on color alone to convey meaning — pair color with icons, depth, clear copy, or visual feedback.
- intent: Ensure meaning is perceivable regardless of color perception.
