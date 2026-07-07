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

### rule_ibsrela_flip_script_campaign_palette_ratio
- class=color_application scope=campaign hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: In Flip The Script campaign pieces the three campaign colors (Periwinkle, Purple, Green) are distributed evenly at a 33% / 33% / 33% ratio (ratio.palette.campaign_usage). In campaign-specific pieces these colors act as accents to the branded palette, not replacements for it.
- intent: Keep campaign palette balanced and subordinate to the core brand palette.

### rule_ibsrela_flip_script_scene_color_pairings_fixed
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=None constraint=pairing
- rule_text: Scene-color pairings are fixed and may not be used interchangeably: Periwinkle→Office, Purple→Cafe, Green→Soccer. White (Safe White) has no paired scene.
- intent: Preserve the intended color-to-scene mapping across campaign creative.

### rule_ibsrela_flip_script_callout_opacity_pairings
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Callout opacity pairings over white are fixed: Periwinkle at 80% (opacity.callout.80), Purple at 60% (opacity.callout.60), Green at 40% (opacity.callout.40). White banner over imagery sits at 80% (opacity.white_banner.80).
- intent: Ensure consistent legibility and layering of campaign callouts.
