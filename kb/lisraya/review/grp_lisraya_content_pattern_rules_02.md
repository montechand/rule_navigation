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

## Extracted rules (5)

### rule_lisraya_headline_title_case
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Headlines and headings use initial caps (title case): capitalize nouns, pronouns, adjectives, verbs, and adverbs; lowercase articles, conjunctions, and prepositions. Example: 'LISRAYA Targets the Root Cause of Dermatomyositis'.
- intent: Consistent headline casing convention.

### rule_lisraya_campaign_headline_all_caps
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: The campaign headline 'YOU DESERVE MORE' is always set in ALL CAPS (see 1.6).
- intent: Preserve locked campaign headline casing.

### rule_lisraya_chart_headline_all_caps
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart/infographic headlines are set in ALL CAPS, using Agenda for print and Nunito Sans Bold or heavier for the email fallback.
- intent: Distinct, consistent chart headline treatment.

### rule_lisraya_body_copy_sentence_case
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Body copy is set in sentence case.
- intent: Readable, consistent body casing.

### rule_lisraya_no_all_caps_outside_allowed_cases
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: [GENERAL] Do not use ALL CAPS for body copy, buttons, or subheads, other than the explicitly allowed cases (the 'YOU DESERVE MORE' campaign headline and chart/infographic headlines).
- intent: Restrict ALL CAPS to the sanctioned exceptions only.
