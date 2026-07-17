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

### rule_lisraya_brand_name_and_trademark_usage
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content governance=trademark/verbatim_only
- rule_text: Always write LISRAYA in ALL CAPS (case.campaign.all_caps = "all_caps") in patient marketing materials, superseding standard title-case guides. The registered trademark symbol ® must only be applied on the first or most prominent mention in external-facing documents, and only when paired with the generic name formatted in lowercase parentheses: LISRAYA® (brepocitinib). Subsequent mentions must omit the ® symbol.
- intent: Maintain strict, regulatory-compliant trademark presentation for LISRAYA.

### rule_lisraya_parent_company_footer_lock
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['end_matter'] constraint=exclusivity governance=legal/verbatim_only
- rule_text: The parent company sign-off 'Priovant Therapeutics, Inc.' is locked to the footer. Do not add this mention in normal content sections of the email.
- intent: Prevent duplicate parent company sign-offs outside of designated legal areas.
