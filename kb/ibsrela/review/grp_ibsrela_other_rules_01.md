# Review: grp_ibsrela_other_rules_01

doc_ref: `other_rules[1]`

## Original text

````
### Section-designer assembly rules [BASELINE] — for combining independently built sections
1. Every content section is a self-contained 600 px table with its own background, top/bottom padding (§2.2), and optional wave edge; **no outer margins**, so sections stack flush — against each other and against the locked Top/End Matter.
2. Sections must declare their theme background at top and bottom edge so adjacent sections either match or transition via a wave edge — never a hard unstyled seam. The first section meets the header on white/theme; the last section must end on a background the locked footer's wave edge is approved against.
3. Footnote symbols run per the whole email, not per section: coordinate `*` `†` `‡` `§` order at assembly; references are numbered continuously across sections, resolving above/within the locked End Matter per template.
4. Only one Wave graphic and one key-strategic-question callout per email; one primary CTA per section, max ~3 CTAs per email.
5. No section may introduce fonts, colors, button shapes, or icon styles outside this document; new icons must match existing line weight and simplified style (explicit rule). No section reproduces the logo lockup or any ISI/legal copy (locked components own these).
6. Final assembly QA: confirm body size = locked ISI body size (12 px / 1.4), audience match with the supplied header/footer (§4.2), all §1.8 content-section obligations present, theme consistency across sections, and both breakpoints render without horizontal scroll.

````

## Extracted rules (6)

### rule_ibsrela_section_self_contained_flush_stack
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Every content section is a self-contained 600px table with its own background and its own top/bottom padding (§2.2), plus an optional wave edge. Sections carry no outer margins, so they stack flush — against each other and against the locked Top/End Matter.
- intent: Independently built sections must tile seamlessly into one email without margin gaps.

### rule_ibsrela_section_edge_theme_declaration
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Sections must declare their theme background at both top and bottom edges so adjacent sections either match or transition via a wave edge — never a hard unstyled seam. The first section meets the header on white/theme; the last section must end on a background the locked footer's wave edge is approved against.
- intent: Prevent unstyled seams between independently built sections and the locked header/footer.

### rule_ibsrela_footnote_symbols_per_email
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: Footnote symbols run per the whole email, not per section: coordinate `*` `†` `‡` `§` order at assembly, and number references continuously across sections, resolving above/within the locked End Matter per template.
- intent: Keep footnote references consistent and continuous across independently authored sections.

### rule_ibsrela_email_component_cardinality
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Only one Wave graphic and one key-strategic-question callout per email; one primary CTA per section, with a maximum of about 3 CTAs per email.
- intent: Cap repeated emphasis elements so the email stays focused.

### rule_ibsrela_no_out_of_document_styles_or_locked_copy
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: No section may introduce fonts, colors, button shapes, or icon styles outside this document; any new icons must match the existing line weight and simplified line style. No section reproduces the logo lockup or any ISI/legal copy — the locked components own these.
- intent: Confine every section to the sanctioned design system and to locked-component ownership of logo/ISI/legal.

### rule_ibsrela_final_assembly_qa_checklist
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Final assembly QA must confirm: body size equals the locked ISI body size (12px / 1.4 line-height); audience matches the supplied header/footer (§4.2); all §1.8 content-section obligations are present; theme consistency across sections; and both breakpoints render without horizontal scroll.
- intent: Verify cross-section consistency, audience match, and responsive integrity before release.
