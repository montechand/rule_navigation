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
- class=color_application scope=campaign hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: In Flip The Script campaign pieces, the three campaign colors (Periwinkle #7B7BED, Purple #92278F, Green #01A47E) are balanced at a 33% / 33% / 33% usage ratio (campaign variant of palette.usage_ratio). In campaign-specific pieces these colors act as accents to the branded palette, not replacements.
- intent: Keep campaign colors balanced and subordinate to the core branded palette.

### rule_ibsrela_flip_script_scene_color_pairings_fixed
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=['callout'] constraint=pairing
- rule_text: Flip The Script scene-color pairings are fixed and may not be used interchangeably: Periwinkle → Office, Purple → Cafe, Green → Soccer. The scene-banner color (callout.scene_banner.color) must match the paired scene.
- intent: Preserve fixed campaign color-to-scene associations.

### rule_ibsrela_flip_script_callout_opacity_pairings
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Callout opacity pairings over white are fixed: Periwinkle 80% / Purple 60% / Green 40% (callout.scene_banner.opacity variants); white banner over imagery is set at 80% (callout.white_banner.opacity).
- intent: Lock campaign callout transparency levels for legibility and consistency over imagery.
