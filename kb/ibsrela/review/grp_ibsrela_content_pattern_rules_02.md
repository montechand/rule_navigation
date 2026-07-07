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

### rule_ibsrela_headline_body_case_defaults
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines are set in Title Case (h1.case); all other copy is sentence case (body.case / h2.case).
- intent: Establish the baseline casing system across headline vs. body copy.

### rule_ibsrela_campaign_headline_all_caps
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Campaign-specific headlines (FLIP THE SCRIPT) are set in ALL CAPS (campaign.headline.case), overriding the default headline Title Case.
- intent: Give the FLIP THE SCRIPT campaign its distinct all-caps headline treatment.

### rule_ibsrela_callout_cta_all_caps
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['callout', 'cta'] constraint=binding
- rule_text: All caps is also required for callouts (callout.case) and CTAs (cta.button.label.case).
- intent: Ensure callout and CTA labels use the emphatic all-caps treatment.

### rule_ibsrela_flip_the_script_body_capitalization
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: When the campaign name appears inside body copy, capitalize each word: 'Flip The Script' (not all caps, not 'flip the script').
- intent: Preserve correct trademark capitalization of the campaign name in running copy.

### rule_ibsrela_flip_the_script_display_lockup
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: In the 'FLIP THE SCRIPT' display lockup, the word 'THE' is flipped upside down; 'ON IBS-C' is set in Avenir Light (campaign.lockup.on_ibsc.weight) at 50% opacity (campaign.lockup.on_ibsc.opacity), with the hyphen replaced by the brand swoosh at 100% opacity (campaign.lockup.swoosh). See §2.6.
- intent: Lock the exact construction of the campaign display lockup.
