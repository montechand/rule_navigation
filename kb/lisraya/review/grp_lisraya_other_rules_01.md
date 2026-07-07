# Review: grp_lisraya_other_rules_01

doc_ref: `other_rules[1]`

## Original text

````
### Audience Segmentation
- This guide governs **patient (DTC) materials**. Language rules differ by audience: "someone/people with dermatomyositis" for patient materials; "patients" acceptable in HCP materials. Confirm audience in every brief before writing.
- Patient brochure = master reference for visuals, messaging, and tone across **all** LISRAYA materials.
````

## Extracted rules (3)

### rule_lisraya_patient_dtc_material_governance
- class=voice_tone scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: This guide governs patient (DTC) materials. The audience must be confirmed in every brief before writing.
- intent: Establish that these rules apply to patient/DTC materials and require audience confirmation up front.

### rule_lisraya_patient_reference_language_by_audience
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=verbatim_content
- rule_text: Patient-reference language differs by audience: use "someone/people with dermatomyositis" for patient materials; "patients" is acceptable in HCP materials.
- intent: Use inclusive, non-clinical patient reference language appropriate to the audience.

### rule_lisraya_patient_brochure_master_reference
- class=assembly scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: The patient brochure is the master reference for visuals, messaging, and tone across all LISRAYA materials.
- intent: Anchor all materials to a single canonical source for visuals, messaging, and tone.
