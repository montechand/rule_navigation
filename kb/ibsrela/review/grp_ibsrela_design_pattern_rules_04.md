# Review: grp_ibsrela_design_pattern_rules_04

doc_ref: `design_pattern_rules[4]`

## Original text

````
### Alignment rule (explicit)
 
- **All text is left-aligned** — titles, headlines, subheads, body copy, and CTA button labels — regardless of background color.
- The **CTA button sits left**, flush with the left edge of the text block above it (not centered, not right-aligned). Any supporting **image or visual sits to the right** of the text block in the CTA section in a two column layout. If there is not visual, the CTA section is just left aligned stretching to the full column.
- Any supporting **image or visual sits to the right** of the text block.

````

## Extracted rules (2)

### rule_ibsrela_global_left_alignment
- class=layout scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All text is left-aligned — titles, headlines, subheads, body copy, and CTA button labels — regardless of background color. The CTA button sits left, flush with the left edge of the text block above it (not centered, not right-aligned).
- intent: Maintain consistent left-aligned typographic rhythm across all backgrounds.

### rule_ibsrela_cta_image_right_placement
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: Any supporting image or visual sits to the right of the text block in the CTA section in a two-column layout. If there is no visual, the CTA section is just left-aligned, stretching to the full column.
- intent: Enforce the two-column CTA structure with image on the right and text on the left.
