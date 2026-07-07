# Review: grp_ibsrela_content_pattern_rules_03

doc_ref: `content_pattern_rules[3]`

## Original text

````
### Bolding rules [BASELINE]
- Bold (Arial Bold) is reserved for: headlines, subheads, card titles, CTA labels, ISI subheads, boxed-warning text, and key claim phrases **only when the claim is MLR-approved with that emphasis**.
- Do **not** bold: whole body paragraphs, footnotes, references, links (links are underlined, not bolded), or more than ~10 words consecutively inside body copy.
- Do not combine bold + italic in email body. Italic (Arial Italic) only for journal titles in references or where the approved copy deck specifies it.
- Never use bold as a substitute for hierarchy — if a passage needs prominence, promote it to a subhead or approved callout style instead.
````

## Extracted rules (4)

### rule_ibsrela_bold_reserved_uses
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=exclusivity governance=mlr_claim/requires_qualifier
- rule_text: Bold (Arial Bold) is reserved for: headlines, subheads, card titles, CTA labels, ISI subheads, boxed-warning text, and key claim phrases — the last only when the claim is MLR-approved with that emphasis.
- intent: Restrict bold weight to structural/emphasis roles so it retains meaning and claim bolding stays MLR-controlled.

### rule_ibsrela_bold_prohibited_uses
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Do not bold whole body paragraphs, footnotes, references, or links (links are underlined, not bolded), and do not bold more than ~10 words consecutively inside body copy.
- intent: Prevent bold overuse that erodes emphasis hierarchy and misapplies weight to non-emphasis text.

### rule_ibsrela_no_bold_italic_combo_and_italic_scope
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Do not combine bold + italic in email body. Italic (Arial Italic) is only for journal titles in references or where the approved copy deck specifies it.
- intent: Keep italic scoped to journal titles/approved copy and avoid combined bold+italic styling in body.

### rule_ibsrela_no_bold_as_hierarchy_substitute
- class=typography scope=org_baseline hardness=strong_default polarity=must_not sections=None constraint=None
- rule_text: Never use bold as a substitute for hierarchy — if a passage needs prominence, promote it to a subhead or approved callout style instead.
- intent: Enforce true structural hierarchy rather than faking prominence with bold weight.
