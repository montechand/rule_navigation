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

## Extracted rules (4)

### rule_lisraya_approved_tints_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: No other ad-hoc tints are permitted — use palette values or the specified tints only: campaign headline 'D'/'M' letters at ≈40% tint of the headline color (campaign_headline.letter.tint), Light Blue callout box at 70% (callout.data.fill.opacity), Golden Sand callout box at 30% (callout.text_heavy.fill.opacity), and wave top layers at 70% transparency (waves.top_layer.opacity).
- intent: Keep tinting to a controlled, approved set to protect palette integrity.

### rule_lisraya_campaign_headline_letter_tint
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The campaign headline 'D' and 'M' letters must use a ≈40% tint of the headline color (Gold or Brand Blue colorway), per campaign_headline.letter.tint.
- intent: Consistent campaign headline lockup styling.

### rule_lisraya_callout_box_fill_tints
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: The Light Blue callout box must use a 70% tint (callout.data.fill.opacity) and the Golden Sand callout box must use a 30% tint (callout.text_heavy.fill.opacity).
- intent: Fixed tint levels for callout box fills.

### rule_lisraya_wave_top_layer_tint
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Wave top layers must be rendered at 70% transparency (waves.top_layer.opacity).
- intent: Consistent wave graphic layering.
