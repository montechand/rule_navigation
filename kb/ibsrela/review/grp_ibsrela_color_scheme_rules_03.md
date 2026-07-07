# Review: grp_ibsrela_color_scheme_rules_03

doc_ref: `color_scheme_rules[3]`

## Original text

````
### Email theme system (explicit — component library)
- Theme variables style each email's frame and automatically restyle tile, button, and campaign-image colorways. Approved theme tiles shown: **White, Silver/light, Purple `#92278F`, Navy `#262262`, Green `#01A47E`** (light themes carry dark text/teal buttons; dark themes carry white text/knockout logo and light or outlined buttons).
- One theme per email; sections inherit the theme — do not theme sections independently within one send.
- [BASELINE] Contrast pairings: on Purple/Navy/Green panels → white text only; on White/Silver → navy headlines, black body, purple accents. Links on dark panels are white underlined; on light panels purple or navy underlined.

````

## Extracted rules (3)

### rule_ibsrela_one_theme_per_email
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: One theme per email. Theme variables style each email's frame and automatically restyle tile, button, and campaign-image colorways; sections inherit the theme. Do not theme sections independently within one send.
- intent: Guarantee a single consistent colorway per send driven by the theme system.

### rule_ibsrela_approved_theme_tiles
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Approved theme tiles are White, Silver/light, Purple (#92278F), Navy (#262262), and Green (#01A47E). Light themes carry dark text with teal buttons; dark themes carry white text with knockout logo and light or outlined buttons. Tile, button, and campaign-image colorways switch per theme (see theme.tile.background variants).
- intent: Constrain the frame colorway to the approved theme set and their auto-derived treatments.

### rule_ibsrela_theme_contrast_pairings
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [BASELINE] Contrast pairings: on Purple/Navy/Green panels use white text only; on White/Silver panels use navy headlines, black body, and purple accents. Links on dark panels are white underlined; on light panels purple or navy underlined. Concrete color switching is carried by the background_group variants of the bound text/link color tokens.
- intent: Ensure legible, on-brand text and link colors across dark and light theme backgrounds.
