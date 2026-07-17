# Review: grp_lisraya_content_pattern_rules_03

doc_ref: `content_pattern_rules[3]`

## Original text

````
### Bolding Rules **[GENERAL — calibrated to the guide's callout/chart patterns]**
- Bold is for **hierarchy and key takeaways, not decoration**. Per email section, bold at most: the heading(s), one key phrase or claim per paragraph, and the statistical callout figure.
- Always bold: callout text per the callout specs (§1.7), statistical callout numbers, brand name within a benefit claim when it is the focal point of the sentence (first instance per section only).
- Never bold: entire paragraphs, footnotes/references, more than ~15% of running body text in any section, prepositional filler, the generic name.
- Never use bold + ALL CAPS + color emphasis simultaneously on the same string except in chart headlines and the campaign headline lockup. Pick at most two emphasis devices per element.
- No underlining except real hyperlinks. No italic for emphasis in patient copy — reserve italics for study names, notes ("Note:"), and citations.

````

## Extracted rules (4)

### rule_lisraya_bold_hierarchy_and_takeaway_limits
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Use Bold styling (weight.bold = Bold) for hierarchy and key takeaways, not decoration. In each email section, bold only headings, no more than one key phrase or claim per paragraph, and the statistical callout figure. Always bold callout text specified by the callout specs and statistical callout numbers; bold the focal brand name in a benefit claim only on its first instance in that section. Never bold entire paragraphs, footnotes or references, more than approximately 15% of running body text in a section, prepositional filler, or the generic name.
- intent: Preserve emphasis hierarchy while preventing overuse of bold styling.

### rule_lisraya_limit_combined_text_emphasis_devices
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Do not combine Bold, ALL CAPS, and color emphasis on the same string, except in chart headlines and the campaign headline lockup. Use no more than two emphasis devices per element.
- intent: Avoid visually excessive text treatment while preserving approved chart and campaign exceptions.

### rule_lisraya_patient_copy_italic_reservations
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Do not use italics for emphasis in patient copy. Reserve italics for study names, notes introduced as "Note:", and citations.
- intent: Prevent italic styling from becoming a patient-facing emphasis device.

### rule_lisraya_underline_only_real_hyperlinks
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Reserve underlining for real hyperlinks only; hyperlinks use underline decoration (body.link.text_decoration = underline).
- intent: Keep underlining as a reliable hyperlink cue.
