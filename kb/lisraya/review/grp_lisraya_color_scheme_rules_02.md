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

## Extracted rules (2)

### rule_lisraya_approved_tints_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: No other ad-hoc tints are permitted — use palette values or these specified tints only: campaign headline 'D'/'M' letters at ≈40% tint of the headline color (Gold or Brand Blue colorway) via campaign_headline.dm_letters.tint; Light Blue callout box at 70% tint (data_callout.box.opacity); Golden Sand callout box at 30% tint (text_callout.box.opacity); wave top layers at 70% transparency (wave.top_layer.opacity).
- intent: Prevent unauthorized tint values that dilute brand color consistency.

### rule_lisraya_specified_tint_bindings
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Approved tints: campaign headline 'D' and 'M' letters use ≈40% tint of the headline color (Gold or Brand Blue colorway); the Light Blue callout box uses a 70% tint; the Golden Sand callout box uses a 30% tint; wave top layers use 70% transparency.
- intent: Bind each specified tint to its canonical token value.
