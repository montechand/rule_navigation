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

### rule_ibsrela_symptom_trio_icon_composition
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=['symptom_trio'] constraint=binding
- rule_text: When referencing the three IBS-C symptoms together, use the approved icon trio: Constipation, Belly Pain, Bloating displayed left-to-right in that order, each as a circular green-tinted icon (symptom_trio.icon.style) with the symptom label beneath in navy #262262 (symptom_trio.label.color). Icon order is fixed per symptom_trio.icon.order.
- intent: Preserve the approved, MLR-locked symptom representation so the three symptoms read consistently.

### rule_ibsrela_symptom_trio_integrity_all_three
- class=iconography scope=brand hardness=hard_constraint polarity=must_not sections=['symptom_trio'] constraint=cardinality
- rule_text: All three symptom icons must appear together; do not show one or two in isolation, do not reorder them, and do not substitute alternate icon styles.
- intent: Prevent partial or altered symptom representation that would misstate the claim.

### rule_ibsrela_symptom_trio_placement_layout
- class=layout scope=brand hardness=strong_default polarity=should sections=['symptom_trio'] constraint=ordering
- rule_text: The trio sits on a green/teal panel (or on white directly above one) and is followed by a headline such as "Different matters: Because one size does not fit all" plus supporting body copy and a CTA.
- intent: Give the symptom trio its expected surrounding layout: green panel, then headline, body, and CTA.
