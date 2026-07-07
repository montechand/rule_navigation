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
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Clinical claims require footnote markers (†), with the footnote text clearly separated and rendered noticeably smaller (per footnote type scale) (§1.2).
- intent: Ensure clinical claims are properly qualified and visually distinguished from body copy.

### rule_lisraya_patient_quote_attribution_style
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['patient_story'] constraint=verbatim_content
- rule_text: Patient quotes must be attributed as `- [Name], LISRAYA patient`, presented in italic or otherwise distinguished styling (per patient_story.quote.style), and paired with warm lifestyle imagery.
- intent: Standardize authentic patient testimonial attribution and presentation.

### rule_lisraya_locked_legal_elements_confined_to_header_footer
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=exclusivity
- rule_text: The Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI all live in the locked header/footer components — never reproduce them in content sections.
- intent: Keep mandatory legal/regulatory elements confined to locked, approved components.
