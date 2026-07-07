# Review: grp_lisraya_color_scheme_rules_04

doc_ref: `color_scheme_rules[4]`

## Original text

````
### Contrast
- **Test contrast levels** (webaim.com or equivalent) for every text/background pair. [GENERAL minimums: WCAG AA — 4.5:1 body text, 3:1 large text ≥24px or 19px bold.]
- Known-safe pairs: Brand Blue, Deep Blue, Dark Navy, Graphite on White/Light Blue/Golden Sand; White on Brand Blue/Deep Blue/Dark Navy. **Avoid:** Gold or Sunshine text on White (fails contrast) — golds are for surfaces, rules, and large display emphasis only.
- **Don't rely on color alone** to convey meaning — pair with icons, depth, clear copy, or visual feedback.
````

## Extracted rules (3)

### rule_lisraya_contrast_aa_minimums
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Test contrast levels (webaim.com or equivalent) for every text/background pair. Meet WCAG AA minimums: 4.5:1 for body text (contrast.body) and 3:1 for large text ≥24px or 19px bold (contrast.large).
- intent: Ensure legibility and WCAG AA compliance for all text.

### rule_lisraya_known_safe_and_gold_text_avoidance
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Known-safe pairs: Brand Blue, Deep Blue, Dark Navy, Graphite on White/Light Blue/Golden Sand; White on Brand Blue/Deep Blue/Dark Navy. Avoid Gold or Sunshine text on White (fails contrast); golds are reserved for surfaces, rules, and large display emphasis only.
- intent: Prevent low-contrast gold/sunshine text while allowing approved gold surface uses.

### rule_lisraya_no_color_alone_for_meaning
- class=accessibility scope=org_baseline hardness=strong_default polarity=must_not sections=None constraint=None
- rule_text: Don't rely on color alone to convey meaning — pair with icons, depth, clear copy, or visual feedback.
- intent: Convey meaning accessibly for color-blind and low-vision users.
