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

### rule_lisraya_wave_two_colorways_only
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Fluid wave forms come in exactly two approved colorways — Sunshine/Gold and Sky Blue/Deep Blue — each available in long and short variants.
- intent: Constrain wave graphics to the approved colorway/variant family.

### rule_lisraya_wave_top_layer_70_transparency
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Waves are constructed with the top wave layer at 70% transparency over the base wave (Gold over Sunshine; Sky Blue over Deep Blue). Always preserve the layered, translucent quality.
- intent: Preserve the signature translucent, layered wave construction.

### rule_lisraya_wave_approved_color_values_only
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Waves may be used alone, or overlaid on photography or gradient backgrounds — to support layout flow, frame content, or add depth — but only using approved color values.
- intent: Allow flexible wave placement while forbidding off-brand colors.

### rule_lisraya_masthead_gradient_logo_device
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: The masthead gradient with logo mark (Sunshine → 0C,10M,78Y,0K, i.e. #faa31b → #ffe05c, with the logo mark placed at the lightest end) is the approved device for holding copy in masthead positions.
- intent: Standardize the masthead copy-holding device.
