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

### rule_ibsrela_self_contained_section_flush_stacking
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Every content section is a self-contained 600 px table with its own background, top/bottom padding (§2.2), and an optional wave edge. Sections carry no outer margins, so they stack flush against each other and against the locked Top/End Matter.
- intent: Guarantee independently built sections compose without gaps or overlap.

### rule_ibsrela_adjacent_section_theme_transition
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Sections must declare their theme background at top and bottom edge so adjacent sections either match or transition via a wave edge — never a hard unstyled seam. The first section meets the header on white/theme; the last section must end on a background the locked footer's wave edge is approved against.
- intent: Prevent unstyled seams and ensure the locked footer's wave edge is honored.

### rule_ibsrela_email_wide_footnote_reference_coordination
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: Footnote symbols run per the whole email, not per section: coordinate * † ‡ § order at assembly; references are numbered continuously across sections, resolving above/within the locked End Matter per template.
- intent: Keep footnotes and references consistent and continuous across independently built sections.

### rule_ibsrela_wave_callout_cta_cardinality
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=cardinality
- rule_text: Only one Wave graphic and one key-strategic-question callout per email; one primary CTA per section, with a maximum of approximately 3 CTAs per email.
- intent: Limit repeated decorative and interactive devices to preserve focus and hierarchy.

### rule_ibsrela_no_new_styles_no_locked_copy_in_sections
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: No section may introduce fonts, colors, button shapes, or icon styles outside this document; new icons must match the existing simplified line style and line weight. No section reproduces the logo lockup or any ISI/legal copy — the locked components own these.
- intent: Keep independently built sections within the closed vocabulary and prevent duplication of locked components.

### rule_ibsrela_final_assembly_qa_checklist
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Final assembly QA: confirm body size equals the locked ISI body size (12 px / 1.4), audience matches the supplied header/footer (§4.2), all §1.8 content-section obligations are present, theme is consistent across sections, and both breakpoints render without horizontal scroll.
- intent: Enforce a pre-ship verification pass on assembled emails.
