# Review: grp_ibsrela_color_scheme_rules_01

doc_ref: `color_scheme_rules[1]`

## Original text

````
### Campaign palette — Flip The Script (explicit)
 
| Color | HEX | RGB | CMYK | PMS | Paired scene |
|---|---|---|---|---|---|
| **Periwinkle** | `#7B7BED` | 123 / 123 / 237 | 59 / 55 / 0 / 0 | 2125 | Office |
| **Purple** | `#92278F` | 146 / 39 / 143 | 50 / 100 / 0 / 0 | 2592 | Cafe |
| **Green** | `#01A47E` | 1 / 164 / 126 | 81 / 10 / 66 / 0 | — | Soccer |
| **White** | `#FFFFFF` | 255 / 255 / 255 | 0 / 0 / 0 / 0 | Safe White | — |
 
- Ratio across the three campaign colors: 33% / 33% / 33%.
- **Scene-color pairings are fixed and may not be used interchangeably.** In campaign-specific pieces these colors act as accents to the branded palette, not replacements.
- Callout opacity pairings (over white): Periwinkle 80% / Purple 60% / Green 40%; white banner over imagery at 80%.
````

## Extracted rules (5)

### rule_ibsrela_ftp_campaign_color_ratio_thirds
- class=color_application scope=campaign hardness=strong_default polarity=should sections=None constraint=cardinality
- rule_text: In Flip The Script campaign pieces, the three campaign colors — Periwinkle (#7B7BED), Purple (#92278F), and Green (#01A47E) — should be balanced at a 33% / 33% / 33% ratio.
- intent: Keep the campaign palette visually balanced across the three accent colors.

### rule_ibsrela_ftp_scene_color_pairings_fixed
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=None constraint=pairing
- rule_text: Flip The Script scene-color pairings are fixed and may not be used interchangeably: Periwinkle (#7B7BED) pairs with Office, Purple (#92278F) pairs with Cafe, and Green (#01A47E) pairs with Soccer.
- intent: Preserve the fixed narrative meaning of each scene's color.

### rule_ibsrela_ftp_campaign_colors_are_accents
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: In campaign-specific pieces, the Flip The Script colors (Periwinkle #7B7BED, Purple #92278F, Green #01A47E) act as accents to the branded palette, not as replacements for it.
- intent: Prevent campaign accents from overtaking the core brand palette.

### rule_ibsrela_ftp_callout_opacity_pairings
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Callout opacity pairings over white must be: Periwinkle at 80%, Purple at 60%, and Green at 40%.
- intent: Lock the legibility/contrast of each callout color over white.

### rule_ibsrela_ftp_white_banner_over_imagery_80
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: A white banner placed over imagery must be set at 80% opacity.
- intent: Ensure consistent legibility of white banners layered over photos.
