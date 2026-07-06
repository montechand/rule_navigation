# Review: grp_lisraya_content_pattern_rules_09

doc_ref: `content_pattern_rules[9]`

## Original text

````
### Required Elements Within Sections
- Clinical claims require footnote markers (†) with footnote text clearly separated and noticeably smaller (§1.2).
- Patient quotes: attributed as `- [Name], LISRAYA patient`, italic or distinguished styling, paired with warm lifestyle imagery.
- Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI all live in the **locked header/footer components — never reproduce in sections.**
````

## Extracted rules (4)

### rule_lisraya_clinical_claim_footnote_markers
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Clinical claims require footnote markers (†) with the footnote text clearly separated and noticeably smaller than body copy (§1.2).
- intent: Ensure clinical claims are properly substantiated and disclosed.

### rule_lisraya_patient_quote_attribution_format
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['patient_story'] constraint=verbatim_content
- rule_text: Patient quotes must be attributed in the format `- [Name], LISRAYA patient`, set in italic or otherwise distinguished styling, and paired with warm lifestyle imagery.
- intent: Standardize patient quote attribution and pair with authentic imagery.

### rule_lisraya_patient_quote_pair_lifestyle_imagery
- class=imagery scope=brand hardness=strong_default polarity=must sections=['patient_story'] constraint=pairing
- rule_text: Patient quotes must be paired with warm lifestyle imagery.
- intent: Reinforce authenticity of patient stories through imagery pairing.

### rule_lisraya_locked_legal_elements_header_footer_only
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=exclusivity
- rule_text: The Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI all live in the locked header/footer components and must never be reproduced within modular sections.
- intent: Keep regulated legal elements confined to locked, controlled components.
