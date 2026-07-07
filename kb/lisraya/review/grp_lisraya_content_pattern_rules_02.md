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
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines and headings use initial caps (title case): capitalize nouns, pronouns, adjectives, verbs, and adverbs; lowercase articles, conjunctions, and prepositions. Example: 'LISRAYA Targets the Root Cause of Dermatomyositis'.
- intent: Consistent, readable headline capitalization across the brand.

### rule_lisraya_body_sentence_case
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Body copy is set in sentence case.
- intent: Approachable, readable body copy.

### rule_lisraya_campaign_headline_all_caps
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The campaign headline 'YOU DESERVE MORE' is always set in ALL CAPS (see 1.6).
- intent: Preserve the fixed visual treatment of the campaign headline.

### rule_lisraya_chart_headline_all_caps
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Chart and infographic headlines are set in ALL CAPS, using Agenda (print) or Nunito Sans Bold+ (email fallback).
- intent: Distinguish and standardize chart/infographic headers.

### rule_lisraya_no_all_caps_body_buttons_subheads
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: [GENERAL] Do not use ALL CAPS for body copy, buttons, or subheads other than the sanctioned cases (campaign headline 'YOU DESERVE MORE', chart/infographic headlines).
- intent: Reserve ALL CAPS for approved uses only, keeping emphasis meaningful.
