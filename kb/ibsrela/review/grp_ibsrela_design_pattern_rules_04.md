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
- rule_text: All text is left-aligned — titles, headlines, subheads, body copy, and CTA button labels — regardless of background color.
- intent: Enforce consistent left alignment across all text elements independent of background.

### rule_ibsrela_cta_button_left_flush_layout
- class=cta scope=brand hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: The CTA button sits left, flush with the left edge of the text block above it (not centered, not right-aligned). Any supporting image or visual sits to the right of the text block in the CTA section in a two-column layout. If there is no visual, the CTA section is just left aligned, stretching to the full column.
- intent: Anchor the CTA button to the left edge and place any supporting visual to the right.
