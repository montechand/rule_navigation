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

## Extracted rules (4)

### rule_lisraya_email_compatibility_coding_standards
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: All CSS styling must be inline. All background colors must use the 'bgcolor' attribute duplicated directly on table elements for Outlook support. All colors must be written in HEX code and all sizing/dimensions defined in px.
- intent: Guarantee robust, pixel-perfect rendering across legacy and modern email clients.

### rule_lisraya_locked_components_isolation
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Sections adjacent to locked components (header, footer, ISI) must not include decorative or graphic elements that rely on continuous flow or visually depend on the adjacent locked component's design.
- intent: Maintain modularity and visual safety across arbitrary modular arrangements.

### rule_lisraya_modular_section_layout
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Each section is a self-contained layout block fixed at 600px (dimension.canvas.width = "600px") with its own top/bottom 32px padding (padding.section.vertical = "32px"). No margins are permitted outside the section block to ensure clean, direct stacking.
- intent: Maintain robust structure and consistent vertical rhythm across standard stacked email sections.

### rule_lisraya_section_metadata_declaration
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Section metadata must declare: background color, whether the section establishes 'dermatomyositis (DM)', footnote symbols consumed, and whether it contains a CTA. Standardized placeholder tokens (e.g., '{{fn1}}') must be used rather than hard-coded symbols to avoid collisions upon assembly.
- intent: Enable dynamic, conflict-free dynamic footnote mapping and correct layout validation.
