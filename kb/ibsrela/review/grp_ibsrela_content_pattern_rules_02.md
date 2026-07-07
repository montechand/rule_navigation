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

### rule_ibsrela_capitalization_headlines_body_callouts
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines use Title Case (h1.case); all other copy uses sentence case (body.case). Callouts and CTAs are set in ALL CAPS (callout.case).
- intent: Enforce consistent casing across headline, body, and callout/CTA text.

### rule_ibsrela_campaign_headline_all_caps
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: Campaign-specific headlines (FLIP THE SCRIPT) are set in ALL CAPS (campaign.headline.case), overriding the default Title Case for headlines.
- intent: Distinguish the Flip The Script campaign headline treatment from standard Title Case headlines.

### rule_ibsrela_campaign_name_body_capitalization
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: When the campaign name appears inside body copy, capitalize each word: 'Flip The Script' — not all caps, not 'flip the script'.
- intent: Preserve trademark-correct campaign name capitalization in running copy.

### rule_ibsrela_flip_the_script_display_lockup
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: In the 'FLIP THE SCRIPT' display lockup, the word 'THE' is flipped upside down; 'ON IBS-C' is set in Avenir Light (campaign.on_ibsc.weight) at 50% opacity (campaign.on_ibsc.opacity), with the hyphen replaced by the brand swoosh at 100% opacity (campaign.swoosh.opacity). See §2.6.
- intent: Lock the composition and treatment of the Flip The Script display lockup.
