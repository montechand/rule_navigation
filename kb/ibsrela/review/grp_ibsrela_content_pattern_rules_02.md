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

## Extracted rules (4)

### rule_ibsrela_capitalization_case_by_element
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Headlines are set in Title Case; all other copy is sentence case. Callouts and CTAs are set in ALL CAPS. (Casing values carried by h1.case=title_case, body.case=sentence_case, callout.case=all_caps, cta.button.label.case=all_caps.)
- intent: Establish the standard casing hierarchy across element types.

### rule_ibsrela_campaign_headline_all_caps
- class=typography scope=campaign hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Campaign-specific headlines (FLIP THE SCRIPT) are set in ALL CAPS, overriding the default Title Case headline casing.
- intent: Give the Flip The Script campaign its distinctive all-caps headline treatment.

### rule_ibsrela_campaign_name_in_body_title_case
- class=copy_editorial scope=campaign hardness=strong_default polarity=must sections=None constraint=verbatim_content
- rule_text: When the campaign name appears inside body copy, capitalize each word: 'Flip The Script' (not all caps, not 'flip the script'). Bound to campaign.body.case=title_case.
- intent: Ensure the campaign name reads as a Title-Cased proper name in running text, distinct from its display lockup.

### rule_ibsrela_flip_the_script_display_lockup
- class=imagery scope=campaign hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: The 'FLIP THE SCRIPT' display lockup sets the word 'THE' flipped upside down; 'ON IBS-C' is set in Avenir Light at 50% opacity, with the hyphen replaced by the brand swoosh at 100% opacity (see §2.6). Uses asset ast_ibsrela_flip_the_script_lockup with the swoosh device ast_ibsrela_brand_swoosh.
- intent: Lock the exact construction of the Flip The Script display lockup.
