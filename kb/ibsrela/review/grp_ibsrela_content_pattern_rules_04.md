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

## Extracted rules (6)

### rule_ibsrela_email_assembly_order
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=['top_matter', 'end_matter'] constraint=ordering
- rule_text: Every SFMC email is built by stacking components in a mandatory sequence: (1) Top Matter — LOCKED, supplied; (2) Email / Primary 1 Column (optional); (3) Email / Primary 2 Column (optional); (4) Email / Secondary (optional, may be repeated); (5) End Matter — LOCKED, supplied. The two required LOCKED components bracket one or more optional content components. Top Matter and End Matter must not be built or modified.
- intent: Enforce the fixed component assembly order with locked brackets.

### rule_ibsrela_locked_top_end_matter_no_modify
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=binding
- rule_text: Top Matter and End Matter are LOCKED, supplied components — do not build or modify them.
- intent: Protect supplied locked header/footer components from designer edits.

### rule_ibsrela_template_formation_no_add_sections
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=cardinality
- rule_text: Choose one of the two pre-made template formations shown in the wireframes. Remove any unnecessary sections, but DO NOT add additional component sections. If content does not fit the pre-made templates, the content must be adjusted — not the template. Content components must follow the two reference examples; unneeded sections are removed.
- intent: Keep emails within the two approved template formations; adjust content, not structure.

### rule_ibsrela_section_element_removal_only
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Elements within a section may be removed if unneeded (e.g., omitting a button or image), but new element types may not be invented.
- intent: Allow pruning of section elements while forbidding invention of new element types.

### rule_ibsrela_dual_breakpoint_build_qa
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Both Desktop (600 px) and Mobile (375 px) layouts are provided for every component — SFMC serves the appropriate version automatically based on the recipient's device. Every content section must be built and QA'd at both breakpoints.
- intent: Guarantee every section is verified at both served breakpoints.

### rule_ibsrela_content_section_clean_edges_against_locked
- class=assembly scope=org_baseline hardness=strong_default polarity=must sections=['top_matter', 'end_matter'] constraint=binding
- rule_text: [INHERITED] The first content section must open cleanly against the bottom edge of the locked Top Matter (white/theme background, optional wave edge at its own top); the last content section must close cleanly against the locked End Matter, whose wave-edge ISI panel sits directly below it.
- intent: Ensure content sections seam cleanly against the locked Top/End Matter brackets.
