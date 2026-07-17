# Review: grp_lisraya_content_pattern_rules_00

doc_ref: `content_pattern_rules[0]`

## Original text

````
### Brand Name & Trademark Usage
- Always write **LISRAYA** in ALL CAPS in all written materials (patient marketing rule; supersedes the Feb 2026 general guide's title-case rule).
- Include the **® registered trademark symbol only when the generic name is included** — i.e., LISRAYA® (brepocitinib). Apply on **first/most prominent mention only**, in **external-facing documents only**. Do not repeat ® on subsequent mentions.
- Generic name format: lowercase, in parentheses: `(brepocitinib)`.
- Parent company: Priovant Therapeutics, Inc. (sign-off lives in the locked footer — do not add it in sections).
````

## Extracted rules (2)

### rule_lisraya_external_trademark_and_generic_first_mention
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content governance=trademark/verbatim_only
- rule_text: For external-facing documents, use “LISRAYA® (brepocitinib)” only on the first or most prominent mention when the generic name is included. Format the generic name in lowercase parentheses as “(brepocitinib)”; do not repeat ® on subsequent mentions and do not use ® without the generic name.
- intent: Ensure approved trademark and generic-name treatment without repeated trademark symbols.

### rule_lisraya_parent_company_signoff_locked_footer
- class=layout scope=brand hardness=hard_constraint polarity=must_not sections=['end_matter'] constraint=exclusivity
- rule_text: The parent-company sign-off, “Priovant Therapeutics, Inc.,” is reserved for the locked footer; do not add it within sections.
- intent: Keep parent-company attribution confined to the approved footer treatment.
