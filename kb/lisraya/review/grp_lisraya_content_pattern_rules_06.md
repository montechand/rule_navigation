# Review: grp_lisraya_content_pattern_rules_06

doc_ref: `content_pattern_rules[6]`

## Original text

````
### Callout Formatting (three approved styles — use judiciously; never two of the same style competing on one screen/section)
1. **Main callout (key point):** Bold **Brand Blue (#00529b)** text with **Gold (#ffc60a)** horizontal rules above and below. Centered text. [GENERAL: rule weight 2px, rule width ≈ 60–100% of text block, 16px padding between rule and text.]
2. **Secondary/data callout:** **Light Blue (#E6F0F9) box at 70% tint** with **Bold Brand Blue** text; may include one line icon (e.g., 1x pill icon). [GENERAL: 20px internal padding, corner radius per accent-shape rules §2.5.]
3. **Text-heavy callout (lists/descriptions):** **Golden Sand (#FEF1C8) box at 30% tint**, **Bold Brand Blue headline**, line icons, **Bold Sky Blue (#358CCB) subheads**, **Regular Graphite (#212121) body text**. [GENERAL: 24px internal padding; two-column icon+text layout collapses to single column on mobile.]
````

## Extracted rules (4)

### rule_lisraya_callout_style_exclusivity
- class=layout scope=brand hardness=strong_default polarity=must_not sections=['callout'] constraint=exclusivity
- rule_text: There are three approved callout styles (Main/key-point, Secondary/data, and Text-heavy). Use them judiciously; never let two of the same style compete on a single screen or section.
- intent: Prevent visual competition and preserve callout hierarchy.

### rule_lisraya_main_callout_key_point
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Main callout (key point): bold Brand Blue text with Gold horizontal rules above and below, centered. Rule weight 2px, rule width ≈60–100% of the text block, with 16px padding between rule and text.
- intent: Standardize the key-point callout treatment.

### rule_lisraya_secondary_data_callout
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Secondary/data callout: Light Blue box at 70% tint with bold Brand Blue text; may include one line icon (e.g., 1x pill icon). 20px internal padding; corner radius per accent-shape rules §2.5.
- intent: Standardize the data-callout box treatment.

### rule_lisraya_text_heavy_callout
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout', 'affordability'] constraint=binding
- rule_text: Text-heavy callout (lists/descriptions): Golden Sand box at 30% tint, bold Brand Blue headline, line icons, bold Sky Blue subheads, regular Graphite body text. 24px internal padding; two-column icon+text layout collapses to single column on mobile.
- intent: Standardize the text-heavy callout treatment and its responsive behavior.
