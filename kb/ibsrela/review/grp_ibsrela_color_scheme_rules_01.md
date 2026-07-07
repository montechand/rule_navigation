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

### rule_ibsrela_flip_the_script_campaign_palette_ratio
- class=color_application scope=campaign hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: For Flip The Script campaign pieces, the three campaign colors (Periwinkle #7B7BED, Purple #92278F, Green #01A47E) are used at an even 33% / 33% / 33% ratio (palette.usage_ratio campaign variant). In campaign-specific pieces these colors act as accents to the branded palette, not as replacements for it.
- intent: Keep campaign color usage balanced and subordinate to the core brand palette.

### rule_ibsrela_flip_the_script_scene_color_pairings_fixed
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=['callout'] constraint=pairing
- rule_text: Scene-color pairings are fixed and may not be used interchangeably: Periwinkle pairs with Office, Purple with Cafe, Green with Soccer. The scene-banner fill (callout.scene_banner.fill, content_tag variants) must follow these locked pairings.
- intent: Preserve consistent visual identity by locking each scene to its campaign color.

### rule_ibsrela_flip_the_script_callout_opacity_pairings
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Callout opacity pairings over white are locked per campaign color: Periwinkle 80% (opacity.callout.80), Purple 60% (opacity.callout.60), Green 40% (opacity.callout.40); white banner over imagery is set at 80% (opacity.white_banner.80).
- intent: Standardize campaign callout legibility over white and over imagery.
