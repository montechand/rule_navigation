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

### rule_lisraya_color_contrast_accessibility_requirements
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Test contrast levels (via webaim.com or equivalent) for every text and background pair to ensure compliance with WCAG AA standards (minimum 4.5:1 ratio for body text, 3:1 for large text >= 24px or 19px bold). Ensure readability using known-safe pairs: Brand Blue (#00529b), Deep Blue (#003D74), Dark Navy (#011E45), or Graphite (#212121) text on White (#ffffff), Light Blue (#E6F0F9), or Golden Sand (#FEF1C8) backgrounds, and White text on Brand Blue, Deep Blue, or Dark Navy backgrounds. Never use Gold (#ffc60a) or Sunshine (#faa31b) text on White background as it fails color contrast standards.
- intent: Ensure all text combinations meet standard WCAG accessibility contrast ratios.

### rule_lisraya_non_color_visual_signifiers
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Do not rely on color alone to convey meaning or hierarchical relationships; color indicators must be paired with icons, depth, clear copy, or alternate visual feedback mechanisms.
- intent: Maintain accessibility compliance for colorblind and visually impaired users.
