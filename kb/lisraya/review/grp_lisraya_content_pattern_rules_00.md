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

## Extracted rules (4)

### rule_lisraya_brand_name_allcaps
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Always write LISRAYA in ALL CAPS in all written materials. This patient-marketing rule supersedes the Feb 2026 general guide's title-case rule for the brand name.
- intent: Enforce consistent, trademark-correct brand name presentation.

### rule_lisraya_registered_trademark_first_mention
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Include the ® registered trademark symbol only when the generic name is included — i.e., LISRAYA® (brepocitinib). Apply on first/most prominent mention only, in external-facing documents only. Do not repeat ® on subsequent mentions.
- intent: Correct, non-redundant trademark symbol placement per legal requirements.

### rule_lisraya_generic_name_format
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Generic name format: lowercase, in parentheses: (brepocitinib).
- intent: Standardize generic name presentation.

### rule_lisraya_parent_company_signoff_footer_only
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must_not sections=['end_matter'] constraint=verbatim_content
- rule_text: Parent company sign-off (Priovant Therapeutics, Inc.) lives in the locked footer — do not add it in content sections.
- intent: Keep legal sign-off in the locked footer and out of body sections.
