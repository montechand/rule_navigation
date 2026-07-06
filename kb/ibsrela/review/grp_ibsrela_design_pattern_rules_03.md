# Review: grp_ibsrela_design_pattern_rules_03

doc_ref: `design_pattern_rules[3]`

## Original text

````
### Symptom-icon trio row (DTP)
- When referencing the three IBS-C symptoms together, use the approved **icon trio**: Constipation, Belly Pain, Bloating — displayed left-to-right in that order, each as a circular green-tinted icon with the symptom label beneath in navy `#262262`.
- All three icons must appear together; do not show one or two in isolation, do not reorder them, and do not substitute alternate icon styles.
- The trio sits on a green/teal panel (or on white directly above one) and is followed by a headline such as "Different matters: Because one size does not fit all" and supporting body copy + CTA.
````

## Extracted rules (4)

### rule_ibsrela_symptom_trio_use_approved_icons_ordered
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=['symptom_trio'] constraint=ordering
- rule_text: When referencing the three IBS-C symptoms together, use the approved icon trio (ast_ibsrela_symptom_icon_trio): Constipation, Belly Pain, Bloating — displayed left-to-right in that order.
- intent: Ensure consistent, approved representation and ordering of the IBS-C symptom set.

### rule_ibsrela_symptom_trio_icon_styling
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=['symptom_trio'] constraint=binding
- rule_text: Each symptom icon is a circular green-tinted icon with the symptom label beneath it set in navy #262262 (tok_ibsrela_color_dark_blue).
- intent: Lock the visual treatment of the symptom trio icons and labels.

### rule_ibsrela_symptom_trio_all_three_no_substitute
- class=iconography scope=brand hardness=hard_constraint polarity=must_not sections=['symptom_trio'] constraint=cardinality
- rule_text: All three symptom icons must appear together; do not show one or two in isolation, do not reorder them, and do not substitute alternate icon styles.
- intent: Prevent partial, reordered, or substituted symptom icon representations.

### rule_ibsrela_symptom_trio_panel_placement
- class=layout scope=brand hardness=strong_default polarity=should sections=['symptom_trio'] constraint=None
- rule_text: The symptom-icon trio sits on a green/teal panel (or on white directly above one) and is followed by a headline such as "Different matters: Because one size does not fit all" and supporting body copy plus a CTA.
- intent: Define the standard layout composition for the symptom trio row.
