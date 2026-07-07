# Review: grp_ibsrela_design_pattern_rules_03

doc_ref: `design_pattern_rules[3]`

## Original text

````
### Symptom-icon trio row (DTP)
- When referencing the three IBS-C symptoms together, use the approved **icon trio**: Constipation, Belly Pain, Bloating — displayed left-to-right in that order, each as a circular green-tinted icon with the symptom label beneath in navy `#262262`.
- All three icons must appear together; do not show one or two in isolation, do not reorder them, and do not substitute alternate icon styles.
- The trio sits on a green/teal panel (or on white directly above one) and is followed by a headline such as "Different matters: Because one size does not fit all" and supporting body copy + CTA.
````

## Extracted rules (3)

### rule_ibsrela_symptom_icon_trio_style_and_order
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=['symptom_trio'] constraint=binding
- rule_text: When referencing the three IBS-C symptoms together, use the approved icon trio: Constipation, Belly Pain, Bloating displayed left-to-right in that order (symptom_trio.icon.order). Each icon uses the approved circular green-tinted style (symptom_trio.icon.style) with the symptom label beneath in navy #262262 (symptom_trio.label.color).
- intent: Present the IBS-C symptom trio in the single approved, consistent visual form and order.

### rule_ibsrela_symptom_icon_trio_appear_together
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=['symptom_trio'] constraint=cardinality
- rule_text: All three symptom icons must appear together; do not show one or two in isolation, do not reorder them, and do not substitute alternate icon styles.
- intent: Keep the symptom trio complete and unaltered so the claim stays balanced and approved.

### rule_ibsrela_symptom_trio_placement_and_flow
- class=layout scope=brand hardness=strong_default polarity=should sections=['symptom_trio'] constraint=ordering
- rule_text: The symptom trio sits on a green/teal panel (or on white directly above one) and is followed by a headline such as "Different matters: Because one size does not fit all" and supporting body copy plus a CTA.
- intent: Establish the expected section flow around the symptom trio.
