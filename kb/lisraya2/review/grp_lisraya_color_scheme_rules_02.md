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

### rule_lisraya_campaign_headline_character_tint
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: In campaign headlines, specific characters ("D" and "M") must be styled with an approximate 40% tint (opacity.campaign.headline_char_tint = 0.4) of the main headline color.
- intent: Maintain the specific campaign typographic branding for key headline characters.
