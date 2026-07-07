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

## Extracted rules (3)

### rule_lisraya_bold_hierarchy_only
- class=copy_editorial scope=brand hardness=soft_guidance polarity=must sections=None constraint=cardinality
- rule_text: Bold is for hierarchy and key takeaways, not decoration. Per email section, bold at most: the heading(s), one key phrase or claim per paragraph, and the statistical callout figure. Always bold: callout text per the callout specs (§1.7), statistical callout numbers, and the brand name within a benefit claim when it is the focal point of the sentence (first instance per section only). Never bold entire paragraphs, footnotes/references, more than ~15% of running body text in any section, prepositional filler, or the generic name.
- intent: Reserve bold for genuine emphasis and takeaways, preventing bold overuse that flattens hierarchy.

### rule_lisraya_max_two_emphasis_devices
- class=copy_editorial scope=brand hardness=strong_default polarity=must_not sections=None constraint=exclusivity
- rule_text: Never use bold + ALL CAPS + color emphasis simultaneously on the same string, except in chart headlines and the campaign headline lockup. Pick at most two emphasis devices per element.
- intent: Prevent visually shouting text by capping stacked emphasis devices, with a narrow exception for chart/campaign headlines.

### rule_lisraya_no_underline_italic_for_emphasis
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: No underlining except real hyperlinks. No italic for emphasis in patient copy — reserve italics for study names, notes ('Note:'), and citations.
- intent: Keep underline exclusive to links and italics exclusive to references, per brand text-decoration rules.
