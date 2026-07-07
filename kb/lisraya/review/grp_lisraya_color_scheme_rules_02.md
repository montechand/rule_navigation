# Review: grp_lisraya_color_scheme_rules_02

doc_ref: `color_scheme_rules[2]`

## Original text

````
### Tint Rules
- Campaign headline "D" and "M": **≈40% tint** of the headline color (Gold or Brand Blue colorway).
- Light Blue callout box: **70% tint**.
- Golden Sand callout box: **30% tint**.
- Wave top layers: **70% transparency**.
- No other ad-hoc tints — use palette values or these specified tints only.

````

## Extracted rules (3)

### rule_lisraya_campaign_headline_letter_tint
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: In the 'You Deserve More' campaign, the headline letters 'D' and 'M' render at ≈40% tint of the headline color (Gold or Brand Blue colorway), per campaign_headline.letter.tint.
- intent: Distinctive campaign headline emphasis without introducing new colors.

### rule_lisraya_callout_and_wave_tint_bindings
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Tints are fixed per element: the Light Blue (data) callout box uses a 70% tint, the Golden Sand (text-heavy) callout box uses a 30% tint, and wave top layers use 70% transparency, bound via callout.data.fill.opacity, callout.text_heavy.fill.opacity, and waves.top_layer.opacity.
- intent: Keep callout and wave transparencies consistent with the approved tint values.

### rule_lisraya_no_ad_hoc_tints
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: No other ad-hoc tints are permitted — use full palette values or only the specified tints (campaign headline letter ≈40%, Light Blue callout 70%, Golden Sand callout 30%, wave top layer 70%).
- intent: Prevent arbitrary opacity values that dilute the brand palette.
