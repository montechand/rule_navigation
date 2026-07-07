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

### rule_ibsrela_capitalization_by_element
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines use Title Case; all other copy is sentence case. Callouts and CTAs are set in ALL CAPS. Case is governed per element by the headline.case, subhead.case, body.case, callout.case, and cta.button.label.case tokens.
- intent: Enforce consistent casing conventions by element type.

### rule_ibsrela_campaign_headline_all_caps
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Campaign-specific headlines (FLIP THE SCRIPT) are set in ALL CAPS, per the campaign.headline.case token.
- intent: FLIP THE SCRIPT campaign headlines override default title-case headlines with all caps.

### rule_ibsrela_campaign_name_body_capitalization
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: When the campaign name appears inside body copy, capitalize each word: 'Flip The Script' (not all caps, not 'flip the script'). Governed by campaign.body_name.case (title case).
- intent: Preserve verbatim campaign-name capitalization in running body copy.

### rule_ibsrela_flip_the_script_display_lockup
- class=imagery scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: In the 'FLIP THE SCRIPT' display lockup, the word 'THE' is flipped upside down; 'ON IBS-C' is set in Avenir Light at 50% opacity, with the hyphen replaced by the brand swoosh at 100% opacity. Weight/opacity governed by campaign.lockup.on_ibsc.weight, campaign.lockup.on_ibsc.opacity, and campaign.lockup.swoosh.opacity tokens.
- intent: Lock the specific typographic construction of the FLIP THE SCRIPT display lockup.
