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
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: Bold (Arial Bold) is reserved for: headlines, subheads, card titles, CTA labels, ISI subheads, boxed-warning text, and key claim phrases — but only when the claim is MLR-approved with that emphasis.
- intent: Restrict bold to defined hierarchy and approved emphasis roles.

### rule_ibsrela_no_bold_body_footnotes_links
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Do not bold: whole body paragraphs, footnotes, references, or links (links are underlined, not bolded), or more than ~10 words consecutively inside body copy.
- intent: Prevent overuse of bold that dilutes hierarchy and readability.

### rule_ibsrela_no_bold_italic_combination
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Do not combine bold + italic in email body. Italic (Arial Italic) is only for journal titles in references or where the approved copy deck specifies it.
- intent: Reserve italic for specific reference/approved use and forbid bold+italic combos.

### rule_ibsrela_no_bold_as_hierarchy_substitute
- class=typography scope=org_baseline hardness=strong_default polarity=must_not sections=None constraint=None
- rule_text: Never use bold as a substitute for hierarchy — if a passage needs prominence, promote it to a subhead or approved callout style instead.
- intent: Enforce structural hierarchy over ad hoc emphasis.
