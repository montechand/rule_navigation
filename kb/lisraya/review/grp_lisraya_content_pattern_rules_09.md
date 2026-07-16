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
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['efficacy', 'safety'] constraint=pairing governance=mlr_claim/requires_qualifier
- rule_text: Clinical claims require footnote markers (†), with the associated footnote text clearly separated from the claim and rendered noticeably smaller (per §1.2 footnote type scale, e.g. footnote.type_scale = 12px/18px).
- intent: Ensure clinical claims are properly qualified with visible, referenced footnotes for MLR compliance.

### rule_lisraya_locked_header_footer_legal_elements
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=exclusivity governance=regulatory/forbidden
- rule_text: Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI all live in the locked header/footer components and must never be reproduced within content sections.
- intent: Prevent duplication or drift of mandated legal/regulatory elements outside their locked components.

### rule_lisraya_patient_quote_attribution_style
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['patient_story'] constraint=verbatim_content governance=trademark/verbatim_only
- rule_text: Patient quotes must be attributed in the form `- [Name], LISRAYA patient`, set in italic or otherwise distinguished styling (patient_story.quote.style = italic), and paired with warm lifestyle imagery (image.treatment = warm_realistic_patient_lifestyle).
- intent: Maintain consistent, authentic patient-quote presentation and attribution.
