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
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Exactly one theme is applied per email. Theme variables style the email's frame and automatically restyle tile, button, and campaign-image colorways; all sections inherit that single theme. Do not theme sections independently within one send.
- intent: Guarantee a single coherent colorway across the whole email.

### rule_ibsrela_approved_theme_tiles
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: Email themes must come from the approved theme tile set: White, Silver/light, Purple (#92278F), Navy (#262262), and Green (#01A47E). Light themes carry dark text and teal/green buttons; dark themes carry white text, knockout logo, and light or outlined buttons.
- intent: Constrain theme selection to the sanctioned colorways.

### rule_ibsrela_theme_contrast_pairings
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [BASELINE] Contrast pairings by panel: on Purple/Navy/Green panels use white text only; on White/Silver panels use navy headlines, black body, and purple accents. Links on dark panels are white underlined; on light panels purple or navy underlined. Colors resolve via the semantic text/link tokens whose background_group variants carry the light/dark switching.
- intent: Ensure legible, on-brand text/link contrast for each panel background.
