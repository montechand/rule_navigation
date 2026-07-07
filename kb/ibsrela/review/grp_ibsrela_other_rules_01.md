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

## Extracted rules (7)

### rule_ibsrela_section_self_contained_flush_stacking
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Every content section is a self-contained 600 px table with its own background and its own top/bottom padding (§2.2), plus an optional wave edge. Sections carry no outer margins, so they stack flush against each other and against the locked Top/End Matter.
- intent: Guarantee independently built sections combine seamlessly with no gaps or drift in width.

### rule_ibsrela_adjacent_section_theme_edges_transition
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Sections must declare their theme background at their top and bottom edge so adjacent sections either match or transition via a wave edge — never a hard unstyled seam. The first section must meet the header on white/theme; the last section must end on a background the locked footer's wave edge is approved against.
- intent: Prevent unstyled seams between independently authored sections and ensure clean handoff to locked header/footer.

### rule_ibsrela_footnote_reference_symbols_email_scope
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must sections=['end_matter'] constraint=ordering
- rule_text: Footnote symbols run per the whole email, not per section: coordinate the `*` `†` `‡` `§` order at assembly. References are numbered continuously across sections, resolving above or within the locked End Matter per template.
- intent: Keep footnote/reference numbering coherent across independently built sections at the email level.

### rule_ibsrela_per_email_device_cardinality_limits
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=cardinality
- rule_text: Only one Wave graphic and only one key-strategic-question callout are allowed per email. One primary CTA per section, with a maximum of ~3 CTAs per email.
- intent: Cap repeatable devices so assembled emails stay focused and on-strategy.

### rule_ibsrela_no_out_of_document_styling_tokens
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: No section may introduce fonts, colors, button shapes, or icon styles outside this document. New icons must match the existing line weight and simplified line style (explicit rule).
- intent: Enforce the closed styling vocabulary across all independently built sections.

### rule_ibsrela_locked_components_own_logo_and_isi
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=exclusivity governance=regulatory/forbidden
- rule_text: No content section reproduces the logo lockup or any ISI/legal copy; the locked components (Top/End Matter) own these.
- intent: Prevent uncontrolled duplication of trademark lockups and regulated ISI/legal copy outside the locked components.

### rule_ibsrela_final_assembly_qa_checklist
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Final assembly QA must confirm: body size equals the locked ISI body size (12 px / 1.4), audience matches the supplied header/footer (§4.2), all §1.8 content-section obligations are present, theme is consistent across sections, and both breakpoints render without horizontal scroll.
- intent: Gate the assembled email against a fixed integrity checklist before release.
