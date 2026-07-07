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

## Extracted rules (1)

### rule_lisraya_approved_tints_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: No ad-hoc tints are permitted. Only full palette values or the specified tint values may be used: the campaign headline 'D' and 'M' letters at ≈40% tint of the headline color (Gold or Brand Blue colorway) (tok_lisraya_campaign_headline_letter_tint), the Light Blue callout box at 70% tint (tok_lisraya_opacity_light_blue_callout_70), the Golden Sand callout box at 30% tint (tok_lisraya_opacity_golden_sand_callout_30), and wave top layers at 70% transparency (tok_lisraya_opacity_wave_top_70).
- intent: Prevent inconsistent, off-palette transparency by restricting tints to a fixed approved set.
