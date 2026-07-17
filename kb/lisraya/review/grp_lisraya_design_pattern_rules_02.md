# Review: grp_lisraya_design_pattern_rules_02

doc_ref: `design_pattern_rules[2]`

## Original text

````
### Image Treatment
- Photography: **warm, realistic patient lifestyle imagery** — real moments of simple, everyday activity (walking the dog, beach, BBQ). Conveys returning to everyday life and "getting back to themselves."
- Images are housed in the **Accent shape** (§2.5) — asymmetric rounded-corner crops, not plain rectangles or circles.
- Waves and gradients may overlay photography.
- Every image requires **descriptive alt text** (brand accessibility rule).
````

## Extracted rules (2)

### rule_lisraya_descriptive_image_alt_text
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=cardinality governance=regulatory/requires_qualifier
- rule_text: Every image requires descriptive alt text.
- intent: Ensure image content is accessible to people using assistive technology.

### rule_lisraya_photography_wave_gradient_overlays
- class=imagery scope=brand hardness=soft_guidance polarity=may sections=None constraint=None
- rule_text: Waves and gradients may overlay photography.
- intent: Allow brand graphic depth over photographic imagery.
