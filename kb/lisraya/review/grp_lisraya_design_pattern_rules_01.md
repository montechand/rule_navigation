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

## Extracted rules (4)

### rule_lisraya_brand_waves_colorways_and_variants
- class=imagery scope=brand hardness=strong_default polarity=must sections=None constraint=cardinality
- rule_text: Brand waves come in two approved colorways — Sunshine/Gold and Sky Blue/Deep Blue — each available in long and short variants (see agr_lisraya_waves: ast_lisraya_wave_sunshine_gold_long/short, ast_lisraya_wave_sky_deep_blue_long/short). Use approved color values only.
- intent: Constrain wave assets to the sanctioned colorways and variant set.

### rule_lisraya_brand_waves_layered_translucency
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Waves are constructed as a top wave layer at 70% transparency over the base wave (Gold over Sunshine; Sky Blue over Deep Blue). Always preserve the layered, translucent quality.
- intent: Preserve the signature layered translucent wave construction.

### rule_lisraya_brand_waves_usage_contexts
- class=imagery scope=brand hardness=soft_guidance polarity=may sections=None constraint=None
- rule_text: Waves may be used alone, or overlaid on photography or gradient backgrounds, to support layout flow, frame content, or add depth.
- intent: Define the permitted compositional uses of the wave device.

### rule_lisraya_masthead_gradient_logo_mark_device
- class=layout scope=brand hardness=strong_default polarity=must sections=['top_matter'] constraint=binding
- rule_text: The masthead gradient with logo mark (Sunshine → light gold #ffe05c, logo mark placed at the lightest end, per tok_lisraya_masthead_gradient / ast_lisraya_masthead_logo_mark) is the approved device for holding copy in masthead positions.
- intent: Establish the sanctioned masthead copy-holding device.
