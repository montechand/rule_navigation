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

### rule_lisraya_chart_infographic_headline_casing_and_fonts
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Chart and infographic headlines are ALL CAPS (chart.headline.case = all_caps), set in Agenda for print (font.headline.agenda = Agenda) and Nunito Sans Bold or heavier for email fallback (font.body.nunito_sans = Nunito Sans; weight.bold = Bold).
- intent: Keep chart and infographic headline treatment consistent across print and email.

### rule_lisraya_general_casing_hierarchy
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines and headings use initial caps/title case (case.headline.title_case = title_case), and body copy uses sentence case (case.body.sentence_case = sentence_case). Do not use ALL CAPS for body copy, buttons, or subheads, except for the specifically approved campaign and chart/infographic headline cases.
- intent: Maintain an approved, readable capitalization hierarchy while reserving ALL CAPS for approved emphasis devices.

### rule_lisraya_you_deserve_more_campaign_all_caps
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The "YOU DESERVE MORE" campaign headline is always ALL CAPS (campaign.headline.case = all_caps).
- intent: Preserve the locked campaign headline treatment.
