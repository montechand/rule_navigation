# Review: grp_ibsrela_color_scheme_rules_03

doc_ref: `color_scheme_rules[3]`

## Original text

````
### Email theme system (explicit — component library)
- Theme variables style each email's frame and automatically restyle tile, button, and campaign-image colorways. Approved theme tiles shown: **White, Silver/light, Purple `#92278F`, Navy `#262262`, Green `#01A47E`** (light themes carry dark text/teal buttons; dark themes carry white text/knockout logo and light or outlined buttons).
- One theme per email; sections inherit the theme — do not theme sections independently within one send.
- [BASELINE] Contrast pairings: on Purple/Navy/Green panels → white text only; on White/Silver → navy headlines, black body, purple accents. Links on dark panels are white underlined; on light panels purple or navy underlined.

````

## Extracted rules (2)

### rule_ibsrela_email_single_theme_inheritance
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Theme variables style each email's frame and automatically restyle tile, button, and campaign-image colorways. Use one theme per email; all sections inherit that theme — do not theme sections independently within a single send. Approved theme tiles: White, Silver/light, Purple #92278F, Navy #262262, Green #01A47E. Light themes carry dark text and teal (green) buttons; dark themes carry white text, knockout logo, and light or outlined buttons.
- intent: Ensure a consistent, single theme drives all section styling per email.

### rule_ibsrela_theme_contrast_pairings
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [BASELINE] Contrast pairings by panel: on Purple/Navy/Green panels use white text only; on White/Silver panels use navy headlines, black body, and purple accents. Links on dark panels are white and underlined; on light panels purple or navy and underlined. Concrete color-per-background switching lives on the semantic tokens (headline.color, subhead.color, body.color, body.link.color) via their background_group variants.
- intent: Guarantee legible, on-brand text/link contrast against every theme panel.
