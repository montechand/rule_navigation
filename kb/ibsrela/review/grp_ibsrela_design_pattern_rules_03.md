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

### rule_ibsrela_symptom_trio_icon_style_and_order
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=['symptom_trio'] constraint=binding
- rule_text: When referencing the three IBS-C symptoms together, use the approved icon trio: Constipation, Belly Pain, Bloating displayed left-to-right in that order (symptom_trio.icon.order). Each symptom is a circular green-tinted icon (symptom_trio.icon.style) with the symptom label beneath it in navy #262262 (symptom_trio.label.color).
- intent: Enforce the standardized, approved presentation of the three IBS-C symptoms.

### rule_ibsrela_symptom_trio_completeness_and_no_substitution
- class=iconography scope=brand hardness=hard_constraint polarity=must_not sections=['symptom_trio'] constraint=cardinality
- rule_text: All three symptom icons must appear together; do not show one or two in isolation, do not reorder them, and do not substitute alternate icon styles.
- intent: Prevent partial, reordered, or off-brand rendering of the symptom trio.

### rule_ibsrela_symptom_trio_placement_and_following_content
- class=layout scope=brand hardness=strong_default polarity=should sections=['symptom_trio'] constraint=ordering
- rule_text: The symptom-icon trio sits on a green/teal panel (or on white directly above one) and is followed by a headline (e.g. "Different matters: Because one size does not fit all") with supporting body copy and a CTA.
- intent: Define the surrounding layout context for the symptom trio row.
