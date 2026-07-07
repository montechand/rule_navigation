# Review: grp_lisraya_color_scheme_rules_00

doc_ref: `color_scheme_rules[0]`

## Original text

````
### Complete Palette
**PRIMARY (dominant tier):**
| Name | HEX | RGB | CMYK | Pantone |
|---|---|---|---|---|
| Brand Blue | `#00529b` | 0, 82, 155 | 100, 76, 6, 1 | 2145 C |
| Sunshine | `#faa31b` | 250, 163, 27 | 0, 42, 100, 0 | 137 C |
| Gold | `#ffc60a` | 255, 198, 10 | 0, 23, 100, 0 | 7548 C |
 
**SECONDARY:**
| Name | HEX | RGB | CMYK |
|---|---|---|---|
| Sky Blue | `#358CCB` | 53, 140, 203 | 75, 35, 0, 0 |
| Deep Blue | `#003D74` | 0, 61, 116 | 100, 83, 29, 14 |
| Dark Navy | `#011E45` | 1, 30, 69 | 100, 89, 40, 49 |
 
**TERTIARY:**
| Name | HEX | RGB | CMYK |
|---|---|---|---|
| Coral | `#F26A38` | 242, 106, 56 | 0, 73, 87, 0 |
| Light Blue | `#E6F0F9` | 230, 240, 249 | 8, 2, 0, 0 |
| Golden Sand | `#FEF1C8` | 254, 241, 200 | 0, 3, 24, 0 |
| Graphite | `#212121` | 33, 33, 33 | 0, 0, 0, 88 |
| White | `#ffffff` | 255, 255, 255 | 0, 0, 0, 0 |
````

## Extracted rules (1)

### rule_lisraya_palette_tier_hierarchy
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: The LISRAYA palette is organized into three usage tiers with a fixed dominance order (primary > secondary > tertiary). PRIMARY is the dominant tier — Brand Blue (#00529b / Pantone 2145 C), Sunshine (#faa31b / Pantone 137 C), and Gold (#ffc60a / Pantone 7548 C). SECONDARY comprises Sky Blue (#358CCB), Deep Blue (#003D74), and Dark Navy (#011E45). TERTIARY comprises Coral (#F26A38), Light Blue (#E6F0F9), Golden Sand (#FEF1C8), Graphite (#212121), and White (#ffffff). Concrete color values and cross-references (RGB/CMYK/Pantone) are carried by the individual color tokens; usage weighting follows the palette hierarchy token.
- intent: Establish the tiered brand palette and its dominance order so color usage weighting stays consistent.
