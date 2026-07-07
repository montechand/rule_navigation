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

## Extracted rules (3)

### rule_ibsrela_flip_campaign_palette_ratio
- class=color_application scope=campaign hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: For Flip The Script campaign pieces, the three campaign colors (Periwinkle, Purple, Green) are distributed evenly at a 33% / 33% / 33% ratio. In campaign-specific pieces these colors act as accents to the branded palette, not replacements.
- intent: Balance campaign accent colors while keeping them subordinate to the brand palette.

### rule_ibsrela_flip_scene_color_pairings_fixed
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=['callout'] constraint=pairing
- rule_text: Scene-color pairings are fixed and may not be used interchangeably: Periwinkle→Office, Purple→Cafe, Green→Soccer. Each campaign color is locked to its paired scene.
- intent: Preserve consistent color-to-scene associations across the campaign.

### rule_ibsrela_flip_callout_opacity_pairings
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Callout opacity pairings over white are: Periwinkle 80%, Purple 60%, Green 40%; a white banner over imagery is set at 80%.
- intent: Standardize callout transparency levels per campaign color and for white banners over imagery.
