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

### rule_ibsrela_bold_reserved_usage
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: Bold (Arial Bold) is reserved for: headlines, subheads, card titles, CTA labels, ISI subheads, boxed-warning text, and key claim phrases — the last only when the claim is MLR-approved with that emphasis. Bold must not substitute for hierarchy: if a passage needs prominence, promote it to a subhead or approved callout style instead.
- intent: Keep bold as a controlled emphasis device tied to approved hierarchy, not ad-hoc prominence.

### rule_ibsrela_bold_prohibited_targets
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Do not bold: whole body paragraphs, footnotes, references, links (links are underlined, not bolded), or more than ~10 words consecutively inside body copy.
- intent: Prevent overuse of bold that dilutes emphasis and mis-styles links/legal text.

### rule_ibsrela_no_bold_italic_combo_italic_reserved
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Do not combine bold + italic in email body. Italic (Arial Italic) is only for journal titles in references or where the approved copy deck specifies it.
- intent: Restrict italic to reference styling and forbid stacked bold+italic emphasis in body.
