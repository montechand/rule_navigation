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

## Extracted rules (5)

### rule_ibsrela_email_assembly_order
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: Every SFMC email is built by stacking components in a mandatory sequence: (1) Top Matter — LOCKED, supplied; (2) Email / Primary 1 Column — optional; (3) Email / Primary 2 Column — optional; (4) Email / Secondary — optional, may be repeated; (5) End Matter — LOCKED, supplied. The two required LOCKED components bracket one or more optional content components. The Secondary component may be repeated.
- intent: Guarantee a consistent, compliant email skeleton with locked top/end matter bracketing optional content.

### rule_ibsrela_locked_matter_no_modify
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=['top_matter', 'end_matter'] constraint=binding
- rule_text: Top Matter and End Matter are LOCKED and supplied — do not build or modify them.
- intent: Preserve compliance-controlled header/footer/ISI content that designers must never alter.

### rule_ibsrela_template_no_added_components
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=cardinality
- rule_text: Choose one of the 2 pre-made template formations shown in the wireframes. Remove any unnecessary sections, but DO NOT add additional component sections. If content does not fit the pre-made templates, the content must be adjusted — not the template. Content components must follow the two reference examples. Elements within a section may be removed if unneeded (e.g., omitting a button or image), but new element types may not be invented.
- intent: Constrain design to two approved template formations; allow removal but never invention of sections or element types.

### rule_ibsrela_dual_breakpoint_build_qa
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Both Desktop (600px) and Mobile (375px) layouts are provided for every component; SFMC serves the appropriate version automatically based on the recipient's device. Every content section must be built and QA'd at both breakpoints.
- intent: Ensure every section renders and is verified at both supported email breakpoints.

### rule_ibsrela_content_edges_against_locked_matter
- class=assembly scope=org_baseline hardness=strong_default polarity=must sections=['top_matter', 'end_matter'] constraint=binding
- rule_text: [INHERITED] The first content section must open cleanly against the bottom edge of the locked Top Matter (white/theme background, optional wave edge at its own top); the last content section must close cleanly against the locked End Matter, whose wave-edge ISI panel sits directly below it.
- intent: Ensure clean visual joins between optional content and the locked top/end matter panels.
