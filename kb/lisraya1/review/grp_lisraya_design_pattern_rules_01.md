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

### rule_lisraya_masthead_gradient_logo_copy_holder
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: The Masthead gradient with logo mark (Sunshine → 0C,10M,78Y,0K, with the logo mark placed at the lightest end) is the approved device for holding copy in masthead positions.
- intent: Lock the approved masthead copy-holding device.

### rule_lisraya_wave_forms_two_colorways_layered
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Fluid wave forms (Fluid Wave Forms asset) come in two colorways — Sunshine/Gold and Sky Blue/Deep Blue — each in long and short variants. Construction layers a top wave at 70% transparency over the base wave (Gold over Sunshine; Sky Blue over Deep Blue); always preserve the layered, translucent quality using approved color values only.
- intent: Maintain consistent, on-palette translucent wave treatment.

### rule_lisraya_wave_forms_usage_contexts
- class=imagery scope=brand hardness=soft_guidance polarity=may sections=None constraint=None
- rule_text: Wave forms may be used alone, or overlaid on photography or gradient backgrounds, to support layout flow, frame content, or add depth. Only approved color values may be used.
- intent: Guide where and how waves can be applied while keeping colors on-palette.
