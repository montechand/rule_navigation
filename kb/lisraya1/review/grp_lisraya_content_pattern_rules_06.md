# Review: grp_lisraya_content_pattern_rules_06

doc_ref: `content_pattern_rules[6]`

## Original text

````
### Callout Formatting (three approved styles — use judiciously; never two of the same style competing on one screen/section)
1. **Main callout (key point):** Bold **Brand Blue (#00529b)** text with **Gold (#ffc60a)** horizontal rules above and below. Centered text. [GENERAL: rule weight 2px, rule width ≈ 60–100% of text block, 16px padding between rule and text.]
2. **Secondary/data callout:** **Light Blue (#E6F0F9) box at 70% tint** with **Bold Brand Blue** text; may include one line icon (e.g., 1x pill icon). [GENERAL: 20px internal padding, corner radius per accent-shape rules §2.5.]
3. **Text-heavy callout (lists/descriptions):** **Golden Sand (#FEF1C8) box at 30% tint**, **Bold Brand Blue headline**, line icons, **Bold Sky Blue (#358CCB) subheads**, **Regular Graphite (#212121) body text**. [GENERAL: 24px internal padding; two-column icon+text layout collapses to single column on mobile.]
````

## Extracted rules (1)

### rule_lisraya_callout_style_exclusivity
- class=layout scope=brand hardness=strong_default polarity=must_not sections=['callout'] constraint=exclusivity
- rule_text: There are three approved callout styles; use them judiciously and never place two of the same style competing on one screen/section.
- intent: Prevent visual repetition and preserve callout hierarchy.
