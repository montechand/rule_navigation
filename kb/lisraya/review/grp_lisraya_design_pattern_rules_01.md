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

### rule_lisraya_wave_graphic_device
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Wave graphic devices are fluid wave forms available in two colorways (Sunshine/Gold and Sky Blue/Deep Blue), each in long and short variants (waves.style). Construction always uses a top wave layer at 70% transparency over the base wave (Gold over Sunshine; Sky Blue over Deep Blue) — the layered, translucent quality must always be preserved (waves.top_layer.opacity). Only approved color values may be used.
- intent: Preserve the signature translucent, layered wave look with approved colorways only.

### rule_lisraya_wave_usage_placement
- class=imagery scope=brand hardness=soft_guidance polarity=may sections=None constraint=None
- rule_text: Waves may be used alone, or overlaid on photography or gradient backgrounds, to support layout flow, frame content, or add depth. Only approved color values may be used.
- intent: Define permissible ways to deploy wave devices in layouts.

### rule_lisraya_masthead_gradient_logo_device
- class=imagery scope=brand hardness=strong_default polarity=must sections=['top_matter', 'hero'] constraint=binding
- rule_text: The masthead gradient with logo mark (Sunshine → light gold, with the logo mark placed at the lightest end) is the approved device for holding copy in masthead positions.
- intent: Establish the sanctioned copy-holding device for mastheads.
