# Review: grp_lisraya_content_pattern_rules_09

doc_ref: `content_pattern_rules[9]`

## Original text

````
### Required Elements Within Sections
- Clinical claims require footnote markers (†) with footnote text clearly separated and noticeably smaller (§1.2).
- Patient quotes: attributed as `- [Name], LISRAYA patient`, italic or distinguished styling, paired with warm lifestyle imagery.
- Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI all live in the **locked header/footer components — never reproduce in sections.**
````

## Extracted rules (3)

### rule_lisraya_clinical_claim_footnote_markers
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Clinical claims require footnote markers (†), with footnote text clearly separated from the claim and set noticeably smaller (per §1.2 footnote type scale).
- intent: Ensure clinical claims are properly qualified and substantiated with visible footnote markers.

### rule_lisraya_patient_quote_attribution_styling
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=['patient_story'] constraint=verbatim_content
- rule_text: Patient quotes must be attributed in the format `- [Name], LISRAYA patient`, set in italic or otherwise distinguished styling, and paired with warm lifestyle imagery (see patient_story.quote.style token).
- intent: Keep patient testimonials consistently attributed, styled and visually anchored in real-patient imagery.

### rule_lisraya_locked_legal_elements_never_in_sections
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=exclusivity
- rule_text: The Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI all live in the locked header/footer components and must never be reproduced within content sections.
- intent: Prevent duplication or alteration of legally locked elements outside their governed components.
