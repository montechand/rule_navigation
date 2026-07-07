# Review: grp_lisraya_design_pattern_rules_01

doc_ref: `design_pattern_rules[1]`

## Original text

````
### Graphic Elements — Waves
- Fluid wave forms in **two colorways**: **Sunshine/Gold** and **Sky Blue/Deep Blue**; each in **long and short** variants.
- Construction: top wave layer at **70% transparency** over the base wave (Gold over Sunshine; Sky Blue over Deep Blue) — always preserve the layered, translucent quality.
- Usage: alone, or overlaid on photography or gradient backgrounds; to support layout flow, frame content, or add depth. Approved color values only.
- **Masthead gradient with logo mark** (Sunshine → 0C,10M,78Y,0K, logo mark placed at the lightest end) is the approved device for holding copy in masthead positions.
````

## Extracted rules (3)

### rule_lisraya_wave_graphic_device_construction
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Wave forms exist in two colorways — Sunshine/Gold (agr_lisraya_wave_gold) and Sky Blue/Deep Blue (agr_lisraya_wave_blue) — each in long and short variants. Construct every wave as a top wave layer at 70% transparency (wave.top_layer.opacity) over the base wave: Gold over Sunshine, Sky Blue over Deep Blue. Always preserve the layered, translucent quality and use approved color values only.
- intent: Preserve the signature layered, translucent wave look with approved colorways only.

### rule_lisraya_wave_graphic_device_usage
- class=imagery scope=brand hardness=soft_guidance polarity=may sections=None constraint=None
- rule_text: Waves may be used alone or overlaid on photography or gradient backgrounds to support layout flow, frame content, or add depth. Only approved color values may be used.
- intent: Define the permitted placement and purpose of the wave graphic device.

### rule_lisraya_masthead_gradient_logo_mark_device
- class=layout scope=brand hardness=strong_default polarity=must sections=['top_matter'] constraint=binding
- rule_text: The masthead gradient (Sunshine → light gold 0C,10M,78Y,0K) with the LISRAYA logo mark placed at the lightest end (ast_lisraya_masthead_logo_mark) is the approved device for holding copy in masthead positions.
- intent: Standardize the approved masthead copy-holding device.
