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

### rule_lisraya_contrast_minimums_wcag_aa
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Test contrast levels (webaim.com or equivalent) for every text/background pair. WCAG AA minimums apply: 4.5:1 for body text and 3:1 for large text (≥24px, or 19px bold).
- intent: Ensure all text is legible against its background per accessibility standards.

### rule_lisraya_known_safe_and_forbidden_text_pairs
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=pairing
- rule_text: Known-safe text/background pairs: Brand Blue, Deep Blue, Dark Navy, and Graphite on White/Light Blue/Golden Sand; White on Brand Blue/Deep Blue/Dark Navy. Avoid Gold or Sunshine text on White (fails contrast) — golds are reserved for surfaces, rules, and large display emphasis only.
- intent: Restrict text colors to contrast-safe combinations and keep golds off small text on white.

### rule_lisraya_no_color_alone_for_meaning
- class=accessibility scope=org_baseline hardness=strong_default polarity=must_not sections=None constraint=None
- rule_text: Don't rely on color alone to convey meaning — pair color with icons, depth, clear copy, or visual feedback.
- intent: Guarantee meaning is accessible to color-blind and low-vision users.
