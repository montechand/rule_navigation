# Review: grp_ibsrela_color_scheme_rules_03

doc_ref: `color_scheme_rules[3]`

## Original text

````
### Email theme system (explicit — component library)
- Theme variables style each email's frame and automatically restyle tile, button, and campaign-image colorways. Approved theme tiles shown: **White, Silver/light, Purple `#92278F`, Navy `#262262`, Green `#01A47E`** (light themes carry dark text/teal buttons; dark themes carry white text/knockout logo and light or outlined buttons).
- One theme per email; sections inherit the theme — do not theme sections independently within one send.
- [BASELINE] Contrast pairings: on Purple/Navy/Green panels → white text only; on White/Silver → navy headlines, black body, purple accents. Links on dark panels are white underlined; on light panels purple or navy underlined.

````

## Extracted rules (6)

### rule_ibsrela_one_theme_per_email
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Use exactly one theme per email; all sections inherit that theme. Do not theme sections independently within a single send. Theme variables style the email frame and automatically restyle tile, button, and campaign-image colorways.
- intent: Guarantee visual consistency across all sections of one email.

### rule_ibsrela_approved_theme_tiles
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: Approved email theme tiles are limited to: White, Silver/light, Purple #92278F, Navy #262262, and Green #01A47E. Light themes carry dark text/teal buttons; dark themes carry white text, knockout logo, and light or outlined buttons.
- intent: Restrict email theming to the sanctioned colorway set.

### rule_ibsrela_text_color_on_dark_panels
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: On Purple (#92278F), Navy (#262262), or Green (#01A47E) panels, use white text only.
- intent: Ensure legible contrast on dark theme panels.

### rule_ibsrela_text_color_on_light_panels
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: On White or Silver panels, use navy (#262262) headlines, black (#000000) body copy, and purple (#92278F) accents.
- intent: Ensure legible contrast and correct color hierarchy on light theme panels.

### rule_ibsrela_link_color_on_dark_panels
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Links on dark panels (Purple/Navy/Green) are white and underlined.
- intent: Ensure links are visible and identifiable on dark panels.

### rule_ibsrela_link_color_on_light_panels
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Links on light panels (White/Silver) are purple (#92278F) or navy (#262262) and underlined.
- intent: Ensure links are visible and identifiable on light panels.
