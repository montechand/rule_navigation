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
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Headlines/headings use initial caps (title case): capitalize nouns, pronouns, adjectives, verbs, adverbs; lowercase articles, conjunctions, prepositions. Example: 'LISRAYA Targets the Root Cause of Dermatomyositis'. Binds headline.case (case.headline.title_case).
- intent: Consistent headline capitalization across materials.

### rule_lisraya_campaign_headline_all_caps
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The campaign headline 'YOU DESERVE MORE' is set in ALL CAPS, always (see 1.6). Binds campaign_headline.case (case.campaign_headline.all_caps).
- intent: Lock the campaign headline lockup casing.

### rule_lisraya_chart_headline_all_caps
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Chart/infographic headlines are set in ALL CAPS, in Agenda (print) / Nunito Sans Bold+ (email fallback). Binds chart.headline.case (case.chart_headline.all_caps) and chart.headline.font.
- intent: Distinguish chart headlines with consistent all-caps treatment.

### rule_lisraya_body_sentence_case
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Body copy is set in sentence case. Binds body.case (case.body.sentence_case).
- intent: Readable, conversational body copy casing.

### rule_lisraya_no_all_caps_outside_allowed
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: [GENERAL] Do not use ALL CAPS for body copy, buttons, or subheads other than the allowed cases (campaign headline 'YOU DESERVE MORE', chart/infographic headlines, brand name).
- intent: Reserve all-caps to a small set of intentional uses.
