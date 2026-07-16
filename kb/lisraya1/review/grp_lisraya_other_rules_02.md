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

## Extracted rules (5)

### rule_lisraya_adjacency_to_locked_components_no_dependent_deco
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter', 'safety'] constraint=binding
- rule_text: Locked components (header, footer, ISI) are inserted by the core team; sections adjacent to them must not include decorative elements that visually depend on what's above/below (e.g., a wave that's meant to continue into the footer).
- intent: Prevent broken decorative continuity against team-inserted locked blocks.

### rule_lisraya_email_code_conventions
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All colors in code must be expressed as HEX; all sizing in px; use inline CSS only for email-client compatibility; and duplicate `bgcolor` attributes for Outlook.
- intent: Ensure cross-client email rendering compatibility.

### rule_lisraya_footnote_symbols_assigned_at_assembly
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: Footnote symbols are superscript and assigned in order of appearance at assembly time; sections use placeholder tokens (e.g., `{{fn1}}`) rather than hard-coded daggers when more than one referenced claim exists.
- intent: Avoid footnote symbol collisions across independently authored sections.

### rule_lisraya_modular_section_block_structure
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Each section is a self-contained `<table>`-based block at 600px (size.email.body_width_600 = 600px) with its own top/bottom 32px padding (padding.section.vertical_32 = 32px) and a declared background color; sections carry no margins outside the block so assembly is direct stacking. Section metadata must declare: background color, whether the section establishes `dermatomyositis (DM)`, footnote symbols consumed (†, ‡ assigned at assembly to avoid collisions), and whether it contains a CTA.
- intent: Enable safe modular stacking of independent section blocks.

### rule_lisraya_no_adjacent_dark_sections
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Dark-background sections must not be placed adjacent to other dark sections (assembler responsibility, enabled by declared backgrounds).
- intent: Maintain visual rhythm and section separation.
