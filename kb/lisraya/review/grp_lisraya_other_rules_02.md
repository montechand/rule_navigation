# Review: grp_lisraya_other_rules_02

doc_ref: `other_rules[2]`

## Original text

````
### Modular Assembly Conventions **[GENERAL — Solstice production rules]**
- Each section is a self-contained `<table>`-based block at 600px with its own top/bottom 32px padding and declared background color; **no margins outside the section** — assembly is direct stacking.
- Section metadata must declare: background color, whether the section establishes `dermatomyositis (DM)`, footnote symbols consumed (†, ‡ assigned at assembly to avoid collisions), and whether it contains a CTA.
- Footnote symbols: superscript, assigned in order of appearance at **assembly time** — sections use placeholder tokens (e.g., `{{fn1}}`) rather than hard-coded daggers when more than one referenced claim exists.
- Locked components (header, footer, ISI) are inserted by the core team; sections adjacent to them must not include decorative elements that visually depend on what's above/below (e.g., a wave that's meant to continue into the footer).
- Dark-background sections must not be placed adjacent to other dark sections (assembler responsibility, enabled by declared backgrounds).
- All colors in code as HEX; all sizing in px; inline CSS only (email client compatibility); `bgcolor` attributes duplicated for Outlook.
````

## Extracted rules (6)

### rule_lisraya_section_self_contained_block
- class=assembly scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Each section is a self-contained <table>-based block at 600px with its own top/bottom 32px padding and a declared background color. There are no margins outside the section — assembly is direct stacking.
- intent: Guarantee modular sections stack cleanly without external spacing.

### rule_lisraya_section_metadata_declaration
- class=assembly scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Section metadata must declare: background color, whether the section establishes dermatomyositis (DM), which footnote symbols (†, ‡) it consumes (assigned at assembly to avoid collisions), and whether it contains a CTA.
- intent: Provide the assembler the data needed to stack, deduplicate footnotes, and manage first-mention/CTA placement.

### rule_lisraya_footnote_symbols_assembly_assigned
- class=assembly scope=org_baseline hardness=strong_default polarity=must sections=None constraint=ordering
- rule_text: Footnote symbols are superscript and assigned in order of appearance at assembly time. Sections must use placeholder tokens (e.g., {{fn1}}) rather than hard-coded daggers when more than one referenced claim exists.
- intent: Prevent footnote symbol collisions across independently authored sections.

### rule_lisraya_locked_components_no_dependent_decoration
- class=assembly scope=org_baseline hardness=strong_default polarity=must sections=['top_matter', 'end_matter'] constraint=binding
- rule_text: Locked components (header, footer, ISI) are inserted by the core team. Sections adjacent to them must not include decorative elements that visually depend on what's above or below (e.g., a wave meant to continue into the footer).
- intent: Keep sections self-contained so locked-component insertion never breaks visual continuity.

### rule_lisraya_no_adjacent_dark_sections
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Dark-background sections must not be placed adjacent to other dark sections. This is the assembler's responsibility, enabled by the declared background colors.
- intent: Preserve visual rhythm and contrast between stacked sections.

### rule_lisraya_email_code_conventions
- class=assembly scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: All colors in code must be HEX; all sizing in px; CSS must be inline only for email client compatibility; bgcolor attributes must be duplicated for Outlook.
- intent: Ensure cross-client (especially Outlook) rendering fidelity.
