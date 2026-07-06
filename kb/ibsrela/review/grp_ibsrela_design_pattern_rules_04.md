# Review: grp_ibsrela_design_pattern_rules_04

doc_ref: `design_pattern_rules[4]`

## Original text

````
### Alignment rule (explicit)
 
- **All text is left-aligned** — titles, headlines, subheads, body copy, and CTA button labels — regardless of background color.
- The **CTA button sits left**, flush with the left edge of the text block above it (not centered, not right-aligned). Any supporting **image or visual sits to the right** of the text block in the CTA section in a two column layout. If there is not visual, the CTA section is just left aligned stretching to the full column.
- Any supporting **image or visual sits to the right** of the text block.

````

## Extracted rules (3)

### rule_ibsrela_all_text_left_aligned
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All text is left-aligned — titles, headlines, subheads, body copy, and CTA button labels — regardless of background color.
- intent: Maintain consistent left-aligned reading rhythm across all backgrounds.

### rule_ibsrela_cta_button_left_flush
- class=cta scope=brand hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: The CTA button sits left, flush with the left edge of the text block above it — not centered, not right-aligned.
- intent: Keep CTA aligned with the content block for visual consistency.

### rule_ibsrela_cta_supporting_visual_right
- class=layout scope=brand hardness=strong_default polarity=must sections=['cta'] constraint=binding
- rule_text: Any supporting image or visual in the CTA section sits to the right of the text block, in a two-column layout. If there is no visual, the CTA section is simply left-aligned and stretches to the full column width.
- intent: Standardize CTA section composition with text left and visual right.
