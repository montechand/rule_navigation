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

## Extracted rules (4)

### rule_lisraya_patient_photography_treatment
- class=imagery scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Photography uses warm, realistic patient lifestyle imagery — real moments of simple, everyday activity (walking the dog, beach, BBQ) — conveying returning to everyday life and 'getting back to themselves.'
- intent: Keep photography emotionally on-brand and true-to-life.

### rule_lisraya_image_accent_shape_crop
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Images are housed in the Accent shape (§2.5) — asymmetric rounded-corner crops, not plain rectangles or circles.
- intent: Enforce the signature accent-shape crop for imagery.

### rule_lisraya_waves_gradients_overlay_photography
- class=imagery scope=brand hardness=soft_guidance polarity=may sections=None constraint=None
- rule_text: Waves and gradients may overlay photography.
- intent: Permit brand graphic devices to layer over imagery.

### rule_lisraya_image_alt_text_required
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Every image requires descriptive alt text (brand accessibility rule).
- intent: Ensure images are accessible to assistive technology.
