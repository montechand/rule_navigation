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

### rule_ibsrela_email_assembly_order_mandatory
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: Every SFMC email is built by stacking components in sequence in the mandatory standard assembly order: 1. Top Matter (LOCKED, supplied); 2. Email / Primary 1 Column (optional); 3. Email / Primary 2 Column (optional); 4. Email / Secondary (optional, may be repeated); 5. End Matter (LOCKED, supplied). The two required components (Top Matter and End Matter) bracket one or more optional content components.
- intent: Enforce a consistent, compliant email skeleton with locked bracketing components.

### rule_ibsrela_top_end_matter_locked_no_modify
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=binding
- rule_text: Top Matter and End Matter are LOCKED and supplied — do not build or modify them.
- intent: Preserve regulatory-controlled header/footer content.

### rule_ibsrela_choose_one_premade_template_no_add_sections
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=cardinality
- rule_text: Choose one of the two pre-made template formations shown in the wireframes. Remove any unnecessary sections, but DO NOT add additional component sections. If content does not fit the pre-made templates, the content must be adjusted — not the template.
- intent: Keep emails within approved template formations rather than inventing structure.

### rule_ibsrela_remove_unneeded_elements_no_new_element_types
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Content components must follow the two reference examples; unneeded sections are removed. Elements within a section may be removed if unneeded (e.g., omitting a button or image), but new element types may not be invented.
- intent: Allow subtractive editing only, never additive element invention.

### rule_ibsrela_qa_both_breakpoints
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Both Desktop (600 px) and Mobile (375 px) layouts are provided for every component; SFMC serves the appropriate version automatically based on the recipient's device. Every content section must be built and QA'd at both breakpoints.
- intent: Guarantee correct rendering across device breakpoints.

### rule_ibsrela_first_last_section_clean_edges
- class=assembly scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: [INHERITED] The first content section must open cleanly against the bottom edge of the locked Top Matter (white/theme background, optional wave edge at its own top); the last content section must close cleanly against the locked End Matter, whose wave-edge ISI panel sits directly below it.
- intent: Ensure seamless visual transitions between content and locked matter.
