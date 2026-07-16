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

### rule_lisraya_tint_values_closed_set
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout', 'hero'] constraint=exclusivity
- rule_text: Only the specified tints are permitted; no other ad-hoc tints — use palette values or these specified tints only. Permitted tints are: campaign headline decorative "D" and "M" letters at ≈40% tint of the headline color (Gold or Brand Blue colorway) (opacity.campaign_headline.40 = 0.4); Light Blue callout box at 70% tint (opacity.callout.light_blue_70 = 0.7); Golden Sand callout box at 30% tint (opacity.callout.golden_sand_30 = 0.3); Wave top layers at 70% transparency.
- intent: Restrict tinting to an approved closed set for palette consistency.
