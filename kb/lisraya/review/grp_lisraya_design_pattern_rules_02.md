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

## Extracted rules (1)

### rule_lisraya_image_treatment_and_shape_masking
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding governance=regulatory/allowed_with_disclosure
- rule_text: All patient and brand photography must convey warm, realistic patient lifestyle moments and be housed within the asymmetric rounded-corner Accent Shape mask (gradient_banner.button.radius = 49.52px 1.76px 40px 1.76px). Waves and gradients may overlay photography, and every image must contain descriptive alt text for accessibility.
- intent: Maintain brand visual distinction through the asymmetric mask and enforce regulatory compliance via mandatory alt text.
