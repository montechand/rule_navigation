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

## Extracted rules (3)

### rule_ibsrela_bold_reserved_targets
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: Bold (Arial Bold) is reserved for: headlines, subheads, card titles, CTA labels, ISI subheads, boxed-warning text, and key claim phrases — the latter only when the claim is MLR-approved with that emphasis. Key claim phrases set in bold as highlights use body.highlight.weight (Arial Bold, 700).
- intent: Restrict bold emphasis to a defined set of approved targets so weight signals real hierarchy.

### rule_ibsrela_bold_prohibited_uses
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Do not bold whole body paragraphs, footnotes, references, or links (links are underlined, not bolded), nor more than ~10 words consecutively inside body copy. Never use bold as a substitute for hierarchy — if a passage needs prominence, promote it to a subhead or approved callout style instead.
- intent: Prevent over-bolding and misuse of weight as a stand-in for structural hierarchy.

### rule_ibsrela_no_bold_italic_combo_italic_reserved
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Do not combine bold + italic in email body. Italic (Arial Italic) is used only for journal titles in references or where the approved copy deck specifies it.
- intent: Keep italic scoped to citations and forbid stacked emphasis in body copy.
