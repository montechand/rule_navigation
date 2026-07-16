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

### rule_lisraya_image_descriptive_alt_text_required
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding governance=regulatory/requires_qualifier
- rule_text: Every image requires descriptive alt text (brand accessibility rule).
- intent: Ensure image accessibility for assistive technology.

### rule_lisraya_images_housed_in_accent_shape
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Images are housed in the Accent shape (§2.5) — asymmetric rounded-corner crops (accent_shape.radius default 120px & 6px), not plain rectangles or circles.
- intent: Maintain the signature asymmetric image crop treatment.

### rule_lisraya_patient_lifestyle_photography_style
- class=imagery scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Photography uses warm, realistic patient lifestyle imagery — real moments of simple, everyday activity (walking the dog, beach, BBQ) — conveying returning to everyday life and "getting back to themselves."
- intent: Keep imagery emotionally warm and true-to-life for patients.

### rule_lisraya_waves_gradients_may_overlay_photography
- class=imagery scope=brand hardness=soft_guidance polarity=may sections=None constraint=None
- rule_text: Waves and gradients may overlay photography.
- intent: Allow brand wave/gradient devices to composite over images.
