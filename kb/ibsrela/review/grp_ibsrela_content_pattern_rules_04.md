# Review: grp_ibsrela_content_pattern_rules_04

doc_ref: `content_pattern_rules[4]`

## Original text

````
### Email content structure (explicit — Email Component Library)
Every SFMC email is built by stacking components **in sequence**. The two required components bracket one or more optional content components.
 
**Standard assembly order (mandatory):**
1. **Top Matter — LOCKED, supplied** ★ (do not build or modify)
2. Email / Primary 1 Column — optional ← *section designer scope*
3. Email / Primary 2 Column — optional ← *section designer scope*
4. Email / Secondary — optional, may be repeated ← *section designer scope*
5. **End Matter — LOCKED, supplied** ★ (do not build or modify)


Rules:
- Choose **one of the 2 pre-made template formations** shown in the wireframes. Remove any unnecessary sections, but **DO NOT add additional component sections**. If content does not fit the pre-made templates, the content must be adjusted — not the template.
- Content components must follow the two reference examples; unneeded sections are removed. Elements within a section may be removed if unneeded (e.g., omitting a button or image), but new element types may not be invented.
- Both Desktop (600 px) and Mobile (375 px) layouts are provided for every component — SFMC serves the appropriate version automatically based on the recipient's device. Every content section must be built and QA'd at **both** breakpoints.
- **[INHERITED]** The first content section must open cleanly against the bottom edge of the locked Top Matter (white/theme background, optional wave edge at its own top); the last content section must close cleanly against the locked End Matter, whose wave-edge ISI panel sits directly below it.
````

## Extracted rules (4)

### rule_ibsrela_email_assembly_order
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=['top_matter', 'end_matter'] constraint=ordering
- rule_text: Every SFMC email is built by stacking components in sequence. Mandatory assembly order: (1) Top Matter — LOCKED, supplied (do not build or modify); (2) Email / Primary 1 Column — optional; (3) Email / Primary 2 Column — optional; (4) Email / Secondary — optional, may be repeated; (5) End Matter — LOCKED, supplied (do not build or modify). The two required components (Top Matter and End Matter) bracket one or more optional content components.
- intent: Enforce the fixed component stacking order with locked top/end matter bracketing optional content.

### rule_ibsrela_no_added_sections_beyond_templates
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Choose one of the 2 pre-made template formations shown in the wireframes. Remove any unnecessary sections, but DO NOT add additional component sections. If content does not fit the pre-made templates, the content must be adjusted — not the template. Content components must follow the two reference examples; unneeded sections are removed. Elements within a section may be removed if unneeded (e.g., omitting a button or image), but new element types may not be invented.
- intent: Constrain builders to pre-made templates: subtract-only, never add sections or invent element types.

### rule_ibsrela_dual_breakpoint_build_qa
- class=layout scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Both Desktop (600 px) and Mobile (375 px) layouts are provided for every component — SFMC serves the appropriate version automatically based on the recipient's device. Every content section must be built and QA'd at both breakpoints.
- intent: Guarantee both device layouts are built and verified since SFMC auto-serves by device.

### rule_ibsrela_content_edges_against_locked_matter
- class=assembly scope=brand hardness=strong_default polarity=must sections=['top_matter', 'end_matter'] constraint=None
- rule_text: [INHERITED] The first content section must open cleanly against the bottom edge of the locked Top Matter (white/theme background, optional wave edge at its own top); the last content section must close cleanly against the locked End Matter, whose wave-edge ISI panel sits directly below it.
- intent: Ensure content sections mate cleanly with the locked Top and End Matter edges.
