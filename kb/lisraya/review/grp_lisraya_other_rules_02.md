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

### rule_lisraya_section_self_contained_600px_block
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Each section is a self-contained <table>-based block at 600px with its own top/bottom 32px padding and a declared background color. There must be no margins outside the section — assembly is direct stacking.
- intent: Guarantee modular sections stack cleanly without external spacing dependencies.

### rule_lisraya_section_metadata_declaration
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Section metadata must declare: background color, whether the section establishes 'dermatomyositis (DM)', footnote symbols consumed (†, ‡ assigned at assembly to avoid collisions), and whether it contains a CTA.
- intent: Enable correct assembly-time collision avoidance and adjacency logic.

### rule_lisraya_footnote_symbols_assembly_time_placeholders
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Footnote symbols are superscript and assigned in order of appearance at assembly time. Sections must use placeholder tokens (e.g., {{fn1}}) rather than hard-coded daggers when more than one referenced claim exists.
- intent: Prevent footnote symbol collisions across independently authored sections.

### rule_lisraya_locked_components_no_dependent_decoration
- class=layout scope=org_baseline hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=None
- rule_text: Locked components (header, footer, ISI) are inserted by the core team. Sections adjacent to them must not include decorative elements that visually depend on what's above/below (e.g., a wave meant to continue into the footer).
- intent: Keep sections self-contained so core-team-inserted locked blocks don't break decoration.

### rule_lisraya_no_adjacent_dark_sections
- class=layout scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Dark-background sections must not be placed adjacent to other dark-background sections (assembler responsibility, enabled by declared backgrounds).
- intent: Maintain visual contrast and rhythm between stacked sections.

### rule_lisraya_code_hex_px_inline_css
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: All colors in code must be HEX; all sizing in px; inline CSS only (for email client compatibility); and bgcolor attributes must be duplicated for Outlook.
- intent: Ensure cross-client rendering compatibility, especially Outlook.
