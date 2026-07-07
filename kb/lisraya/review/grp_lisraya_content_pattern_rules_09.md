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
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['efficacy'] constraint=pairing governance=mlr_claim/requires_qualifier
- rule_text: Clinical claims require footnote markers (†) with the corresponding footnote text clearly separated and rendered noticeably smaller (per §1.2).
- intent: Ensure clinical claims are properly qualified with referenced footnotes.

### rule_lisraya_patient_quote_attribution_style
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=['patient_story'] constraint=binding
- rule_text: Patient quotes must be attributed as '- [Name], LISRAYA patient' in italic or otherwise distinguished styling (per patient_story.quote.style), and paired with warm lifestyle imagery.
- intent: Give patient quotes a consistent, authentic and attributed presentation.

### rule_lisraya_legal_lockup_locked_components_only
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=exclusivity governance=disclosure/verbatim_only
- rule_text: The Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI all live exclusively in the locked header/footer components and must never be reproduced within content sections.
- intent: Keep regulated legal/disclosure copy confined to locked, approved components.
