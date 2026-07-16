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

### rule_lisraya_contrast_testing_wcag_aa
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding governance=regulatory/requires_qualifier
- rule_text: Test contrast levels (webaim.com or equivalent) for every text/background pair. Meet WCAG AA minimums: 4.5:1 for body text (ratio.contrast.body = 4.5:1) and 3:1 for large text ≥24px or 19px bold (ratio.contrast.large = 3:1).
- intent: Ensure legible, accessible text/background contrast.

### rule_lisraya_no_color_alone_for_meaning
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Don't rely on color alone to convey meaning — pair with icons, depth, clear copy, or visual feedback.
- intent: Ensure meaning is perceivable without color perception.

### rule_lisraya_safe_color_pairs_and_gold_text_ban
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity governance=mlr_claim/allowed
- rule_text: Known-safe pairs: Brand Blue (#00529b), Deep Blue (#003D74), Dark Navy (#011E45), Graphite (#212121) on White/Light Blue/Golden Sand; White on Brand Blue/Deep Blue/Dark Navy. Avoid Gold or Sunshine text on White (fails contrast) — golds (color.primary.gold = #ffc60a; color.primary.sunshine = #faa31b) are reserved for surfaces, rules, and large display emphasis only.
- intent: Restrict color pairings to legible, accessible combinations and reserve golds to non-text uses.
