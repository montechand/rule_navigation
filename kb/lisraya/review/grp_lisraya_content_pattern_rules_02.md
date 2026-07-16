# Review: grp_lisraya_content_pattern_rules_02

doc_ref: `content_pattern_rules[2]`

## Original text

````
### Capitalization & Casing
- **Headlines/headings:** Initial caps (title case) — capitalize nouns, pronouns, adjectives, verbs, adverbs; lowercase articles, conjunctions, prepositions. Example: *LISRAYA Targets the Root Cause of Dermatomyositis*.
- **Campaign headline "YOU DESERVE MORE": ALL CAPS, always** (see 1.6).
- **Chart/infographic headlines: ALL CAPS**, set in Agenda (print) / Nunito Sans Bold+ (email fallback).
- Body copy: sentence case.
- **[GENERAL]** Do not use ALL CAPS for body copy, buttons, or subheads other than the cases above.

````

## Extracted rules (3)

### rule_lisraya_body_copy_sentence_case
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy uses sentence case (body.case = sentence_case).
- intent: Consistent body capitalization.

### rule_lisraya_campaign_headline_all_caps
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The campaign headline "YOU DESERVE MORE" is set in ALL CAPS, always (campaign_headline.case = all_caps).
- intent: Locked campaign headline casing treatment.

### rule_lisraya_no_all_caps_body_buttons_subheads
- class=typography scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: [GENERAL] Do not use ALL CAPS for body copy, buttons, or subheads other than the approved cases (campaign headline "YOU DESERVE MORE" and chart/infographic headlines).
- intent: Restrict ALL CAPS to sanctioned uses only.
