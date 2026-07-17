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

## Extracted rules (2)

### rule_lisraya_email_code_compatibility_conventions
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: For email-client compatibility, code all colors as HEX and all sizing in px, use inline CSS only, and duplicate background colors in `bgcolor` attributes for Outlook.
- intent: Maintain consistent rendering across email clients, including Outlook.

### rule_lisraya_modular_section_assembly_and_metadata
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Email sections are self-contained table-based blocks using the email canvas width (size.canvas.email_width = 600px) and section vertical padding (padding.section.vertical = 32px). Sections have no external margins and are assembled by direct stacking. Section metadata must declare its background color, whether it establishes dermatomyositis (DM), consumed footnote symbols, and CTA presence. Footnotes are superscripted and assigned in order of appearance at assembly time; sections use placeholder tokens rather than hard-coded daggers when multiple referenced claims occur. Core-team locked header, footer, and ISI components are inserted separately, so adjacent sections must not contain decorative elements visually dependent on those locked components. Assemblers must not place dark-background sections next to other dark-background sections.
- intent: Enable safe modular email assembly, collision-free footnotes, and reliable component adjacency.
