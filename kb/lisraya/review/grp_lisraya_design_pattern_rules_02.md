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

## Extracted rules (3)

### rule_lisraya_warm_lifestyle_photography_treatment
- class=imagery scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Photography must be warm, realistic patient lifestyle imagery — real moments of simple, everyday activity (walking the dog, beach, BBQ) — conveying returning to everyday life and 'getting back to themselves.'
- intent: Keep photographic tone warm and relatable to the patient experience.

### rule_lisraya_images_in_accent_shape_crop
- class=imagery scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Images are housed in the Accent shape (§2.5) — asymmetric rounded-corner crops, not plain rectangles or circles. Waves and gradients may overlay photography.
- intent: Enforce the branded asymmetric accent-shape crop for all photography.

### rule_lisraya_image_alt_text_required
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Every image requires descriptive alt text (brand accessibility rule).
- intent: Ensure images are accessible to assistive technology users.
