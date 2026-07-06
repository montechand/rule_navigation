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

## Extracted rules (8)

### rule_ibsrela_content_section_self_contained_600px_no_margins
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Every content section is a self-contained 600 px table with its own background, top/bottom padding (per §2.2), and optional wave edge, with no outer margins, so sections stack flush — against each other and against the locked Top/End Matter.
- intent: Ensure independently built sections stack seamlessly into a single 600px email.

### rule_ibsrela_section_theme_declared_top_bottom_no_hard_seam
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Sections must declare their theme background at top and bottom edge so adjacent sections either match or transition via a wave edge — never a hard unstyled seam. The first section meets the header on white/theme; the last section must end on a background the locked footer's wave edge is approved against.
- intent: Prevent unstyled seams and guarantee compatible transitions to locked header/footer.

### rule_ibsrela_footnote_symbols_and_references_per_email
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: Footnote symbols run per the whole email, not per section: coordinate `*` `†` `‡` `§` order at assembly; references are numbered continuously across sections, resolving above/within the locked End Matter per template.
- intent: Maintain consistent footnote/reference numbering across independently built sections.

### rule_ibsrela_max_one_wave_and_one_key_question_callout_per_em
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=['callout'] constraint=cardinality
- rule_text: Only one Wave graphic and one key-strategic-question callout are allowed per email.
- intent: Preserve visual/rhetorical impact by limiting signature elements to one per email.

### rule_ibsrela_cta_cardinality_per_section_and_email
- class=cta scope=org_baseline hardness=hard_constraint polarity=must sections=['cta'] constraint=cardinality
- rule_text: One primary CTA per section, and a maximum of approximately 3 CTAs per email.
- intent: Limit call-to-action density for focus and clarity.

### rule_ibsrela_no_section_introduces_new_brand_styles
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: No section may introduce fonts, colors, button shapes, or icon styles outside this document; new icons must match existing line weight and simplified style.
- intent: Keep all sections within the closed brand vocabulary and consistent icon styling.

### rule_ibsrela_no_section_reproduces_logo_or_isi_legal
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: No content section reproduces the logo lockup or any ISI/legal copy; the locked components (Top/End Matter) own these.
- intent: Prevent duplication of trademark logo and regulated ISI/legal copy outside locked components.

### rule_ibsrela_final_assembly_qa_checklist
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Final assembly QA must confirm: body size equals locked ISI body size (12 px / 1.4); audience matches the supplied header/footer (per §4.2); all §1.8 content-section obligations are present; theme consistency across sections; and both breakpoints render without horizontal scroll.
- intent: Gate final delivery on consistency, audience match, and cross-breakpoint rendering.
