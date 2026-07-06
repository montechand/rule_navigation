# Review: grp_lisraya_other_rules_01

doc_ref: `other_rules[1]`

## Original text

````
### Audience Segmentation
- This guide governs **patient (DTC) materials**. Language rules differ by audience: "someone/people with dermatomyositis" for patient materials; "patients" acceptable in HCP materials. Confirm audience in every brief before writing.
- Patient brochure = master reference for visuals, messaging, and tone across **all** LISRAYA materials.
````

## Extracted rules (3)

### rule_lisraya_confirm_audience_in_brief
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: This guide governs patient (DTC) materials. Confirm the audience in every brief before writing, because language rules differ by audience.
- intent: Ensure audience is established before writing so the correct language rules apply.

### rule_lisraya_patient_inclusive_language_by_audience
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: In patient materials, use 'someone/people with dermatomyositis'. The term 'patients' is acceptable only in HCP materials.
- intent: Use inclusive, non-clinical language appropriate to the patient audience.

### rule_lisraya_patient_brochure_master_reference
- class=assembly scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: The patient brochure is the master reference for visuals, messaging, and tone across all LISRAYA materials.
- intent: Anchor all materials to a single canonical reference for consistency.
