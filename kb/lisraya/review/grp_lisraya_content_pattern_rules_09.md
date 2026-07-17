# Review: grp_lisraya_content_pattern_rules_09

doc_ref: `content_pattern_rules[9]`

## Original text

````
### Required Elements Within Sections
- Clinical claims require footnote markers (†) with footnote text clearly separated and noticeably smaller (§1.2).
- Patient quotes: attributed as `- [Name], LISRAYA patient`, italic or distinguished styling, paired with warm lifestyle imagery.
- Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI all live in the **locked header/footer components — never reproduce in sections.**
````

## Extracted rules (2)

### rule_lisraya_clinical_claim_footnotes
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=None governance=mlr_claim/requires_qualifier
- rule_text: Clinical claims require a footnote marker (†); the corresponding footnote text must be clearly separated and noticeably smaller than the claim text.
- intent: Ensure clinical claims carry their required supporting footnote treatment.

### rule_lisraya_legal_content_reserved_for_locked_header_footer
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=exclusivity governance=legal/forbidden
- rule_text: The Priovant logo, copyright line, ® legal line, job code [mm/yy], Indication, and ISI are reserved for locked header/footer components and must never be reproduced in sections.
- intent: Protect locked legal and product-information content from unauthorized sectional duplication.
