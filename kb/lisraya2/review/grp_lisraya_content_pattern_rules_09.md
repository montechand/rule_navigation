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

### rule_lisraya_clinical_claims_footnotes
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=pairing governance=regulatory/requires_qualifier
- rule_text: Clinical claims must be paired with footnote markers (†) and their corresponding footnote text, which must be clearly separated and noticeably smaller.
- intent: Maintain medical accuracy and clear distinction between clinical claims and supporting footnotes.

### rule_lisraya_locked_header_footer_isolation
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=exclusivity governance=legal/forbidden
- rule_text: Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI must only live in the locked header/footer components and must never be reproduced in content sections.
- intent: Protect regulatory boilerplate and corporate branding structures from fragmentation or repetition in the body.

### rule_lisraya_patient_quotes_pairing
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=['patient_story'] constraint=pairing
- rule_text: Patient quotes must be formatted as `- [Name], LISRAYA patient` (in italic or otherwise distinguished styling) and paired alongside warm lifestyle imagery.
- intent: Ensure consistent attribution format and layout pairing for real-world patient testimonials.
