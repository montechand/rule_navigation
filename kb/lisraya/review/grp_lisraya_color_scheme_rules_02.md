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

## Extracted rules (5)

### rule_lisraya_campaign_headline_dm_letter_tint
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The campaign headline letters "D" and "M" must be rendered at approximately a 40% tint of the headline color (Gold or Brand Blue colorway).
- intent: Ensure consistent campaign headline lockup styling.

### rule_lisraya_light_blue_callout_tint_70
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Light Blue callout boxes must use a 70% tint of Light Blue (#E6F0F9).
- intent: Standardize callout box background tinting.

### rule_lisraya_golden_sand_callout_tint_30
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Golden Sand callout boxes must use a 30% tint of Golden Sand (#FEF1C8).
- intent: Standardize callout box background tinting.

### rule_lisraya_wave_top_layer_transparency_70
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Wave top layers must be set to 70% transparency.
- intent: Maintain the consistent layered look of wave assets.

### rule_lisraya_no_ad_hoc_tints
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: No other ad-hoc tints are allowed — use palette values or only the specified tints (campaign headline letters ≈40%, Light Blue callout 70%, Golden Sand callout 30%, wave top layers 70% transparency).
- intent: Prevent invented tints that dilute the palette system.
