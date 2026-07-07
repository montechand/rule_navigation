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

### rule_lisraya_contrast_minimums_and_testing
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding governance=regulatory/requires_qualifier
- rule_text: Test contrast levels (webaim.com or equivalent) for every text/background pair. Meet WCAG AA minimums: 4.5:1 for body text (contrast.body) and 3:1 for large text ≥24px or 19px bold (contrast.large_text).
- intent: Ensure all text/background pairings meet accessibility contrast requirements.

### rule_lisraya_known_safe_and_avoided_text_bg_pairs
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=pairing
- rule_text: Known-safe text/background pairs: Brand Blue, Deep Blue, Dark Navy, Graphite on White/Light Blue/Golden Sand; White on Brand Blue/Deep Blue/Dark Navy. Avoid Gold or Sunshine text on White (fails contrast) — golds are reserved for surfaces, rules, and large display emphasis only.
- intent: Constrain color pairings to contrast-safe combinations and keep golds off text on white.

### rule_lisraya_no_color_alone_for_meaning
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding governance=regulatory/requires_qualifier
- rule_text: Don't rely on color alone to convey meaning — pair with icons, depth, clear copy, or visual feedback.
- intent: Guarantee meaning is perceivable without color perception.
