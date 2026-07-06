# Review: grp_ibsrela_content_pattern_rules_02

doc_ref: `content_pattern_rules[2]`

## Original text

````
### Capitalization & formatting rules (explicit)
- Headlines: **Title Case**. All other copy: sentence case.
- Campaign-specific headlines (FLIP THE SCRIPT): **ALL CAPS**.
- All caps also required for **callouts and CTAs**.
- When the campaign name appears inside body copy, capitalize each word: **Flip The Script** (not all caps, not "flip the script").
- "FLIP THE SCRIPT" display lockup: the word "THE" is flipped upside down; "ON IBS-C" set in Avenir Light at 50% opacity, with the hyphen replaced by the brand swoosh at 100% opacity (see §2.6).
````

## Extracted rules (5)

### rule_ibsrela_headlines_title_case_body_sentence_case
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines are set in Title Case. All other copy is set in sentence case.
- intent: Consistent editorial capitalization across headlines and body copy.

### rule_ibsrela_campaign_headlines_all_caps
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Campaign-specific headlines (FLIP THE SCRIPT) are set in ALL CAPS.
- intent: Distinguish campaign headline treatment from standard Title Case headlines.

### rule_ibsrela_callouts_ctas_all_caps
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['callout', 'cta'] constraint=binding
- rule_text: All caps is required for callouts and CTAs.
- intent: Enforce all-caps treatment on emphasis elements (callouts, CTAs).

### rule_ibsrela_flip_the_script_body_case_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: When the campaign name appears inside body copy, capitalize each word: 'Flip The Script' (not all caps, not 'flip the script').
- intent: Correct trademark casing of the campaign name in body copy.

### rule_ibsrela_flip_the_script_display_lockup_treatment
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: In the 'FLIP THE SCRIPT' display lockup, the word 'THE' is flipped upside down; 'ON IBS-C' is set in Avenir Light at 50% opacity, with the hyphen replaced by the brand swoosh at 100% opacity (see §2.6). Uses asset ast_ibsrela_flip_the_script_lockup.
- intent: Lock the exact visual construction of the Flip The Script display lockup.
