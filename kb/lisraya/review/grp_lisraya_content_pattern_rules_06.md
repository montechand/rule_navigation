# Review: grp_lisraya_content_pattern_rules_06

doc_ref: `content_pattern_rules[6]`

## Original text

````
### Callout Formatting (three approved styles — use judiciously; never two of the same style competing on one screen/section)
1. **Main callout (key point):** Bold **Brand Blue (#00529b)** text with **Gold (#ffc60a)** horizontal rules above and below. Centered text. [GENERAL: rule weight 2px, rule width ≈ 60–100% of text block, 16px padding between rule and text.]
2. **Secondary/data callout:** **Light Blue (#E6F0F9) box at 70% tint** with **Bold Brand Blue** text; may include one line icon (e.g., 1x pill icon). [GENERAL: 20px internal padding, corner radius per accent-shape rules §2.5.]
3. **Text-heavy callout (lists/descriptions):** **Golden Sand (#FEF1C8) box at 30% tint**, **Bold Brand Blue headline**, line icons, **Bold Sky Blue (#358CCB) subheads**, **Regular Graphite (#212121) body text**. [GENERAL: 24px internal padding; two-column icon+text layout collapses to single column on mobile.]
````

## Extracted rules (8)

### rule_lisraya_callout_no_duplicate_style_per_section
- class=layout scope=brand hardness=hard_constraint polarity=must_not sections=['callout'] constraint=exclusivity
- rule_text: There are three approved callout styles; use them judiciously. Never place two callouts of the same style competing on one screen/section.
- intent: Preserve visual hierarchy and prevent redundant callout treatments.

### rule_lisraya_callout_main_key_point
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Main callout (key point): Bold Brand Blue (#00529b) centered text with Gold (#ffc60a) horizontal rules above and below the text.
- intent: Standardize the key-point callout treatment.

### rule_lisraya_callout_main_rule_spec
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=['callout'] constraint=None
- rule_text: [GENERAL] For the main callout, horizontal rules are 2px weight, width ≈ 60–100% of the text block, with 16px padding between the rule and the text.
- intent: Lock the geometry of the main callout rules.

### rule_lisraya_callout_secondary_data
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Secondary/data callout: Light Blue (#E6F0F9) box at 70% tint with Bold Brand Blue text; may include one line icon (e.g., 1x pill icon).
- intent: Standardize the data callout treatment.

### rule_lisraya_callout_secondary_one_icon_max
- class=iconography scope=brand hardness=strong_default polarity=may sections=['callout'] constraint=cardinality
- rule_text: The secondary/data callout may include at most one line icon (e.g., 1x pill icon).
- intent: Limit icon density in data callouts.

### rule_lisraya_callout_secondary_spacing
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=['callout'] constraint=None
- rule_text: [GENERAL] The secondary/data callout box has 20px internal padding, with corner radius per accent-shape rules (§2.5).
- intent: Lock spacing and radius for the data callout box.

### rule_lisraya_callout_text_heavy
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Text-heavy callout (lists/descriptions): Golden Sand (#FEF1C8) box at 30% tint, with Bold Brand Blue (#00529b) headline, line icons, Bold Sky Blue (#358CCB) subheads, and Regular Graphite (#212121) body text.
- intent: Standardize the text-heavy/list callout treatment.

### rule_lisraya_callout_text_heavy_layout
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=['callout'] constraint=None
- rule_text: [GENERAL] The text-heavy callout has 24px internal padding and uses a two-column icon+text layout that collapses to a single column on mobile.
- intent: Lock spacing and responsive layout for the text-heavy callout.
