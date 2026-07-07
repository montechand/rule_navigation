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

## Extracted rules (3)

### rule_lisraya_brand_name_all_caps
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Always write LISRAYA in ALL CAPS in all written materials. This patient-marketing rule supersedes the Feb 2026 general guide's title-case rule.
- intent: Consistent, protected brand-name presentation across all materials.

### rule_lisraya_registered_trademark_first_mention
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Include the ® registered trademark symbol only when the generic name is included — i.e., LISRAYA® (brepocitinib). Apply on first/most prominent mention only, in external-facing documents only. Do not repeat ® on subsequent mentions. Generic name format is lowercase in parentheses: (brepocitinib).
- intent: Correct trademark qualification and generic-name pairing per legal rules.

### rule_lisraya_parent_company_sign_off_footer_only
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must_not sections=['end_matter'] constraint=verbatim_content
- rule_text: Parent company is Priovant Therapeutics, Inc. The sign-off lives in the locked footer — do not add it in sections.
- intent: Keep parent-company sign-off confined to the locked footer.
