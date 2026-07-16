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

### rule_lisraya_bold_hierarchy_budget
- class=copy_editorial scope=org_baseline hardness=strong_default polarity=must sections=None constraint=cardinality
- rule_text: Bold is for hierarchy and key takeaways, not decoration. Per email section, bold at most: the heading(s), one key phrase or claim per paragraph, and the statistical callout figure. Always bold: callout text per the callout specs, statistical callout numbers, and the brand name within a benefit claim when it is the focal point of the sentence (first instance per section only). Never bold: entire paragraphs, footnotes/references, more than ~15% of running body text in any section, prepositional filler, or the generic name.
- intent: Reserve bold for genuine hierarchy and key takeaways, preventing emphasis inflation.

### rule_lisraya_emphasis_device_stacking_limit
- class=typography scope=org_baseline hardness=strong_default polarity=must_not sections=None constraint=cardinality
- rule_text: Never use bold + ALL CAPS + color emphasis simultaneously on the same string, except in chart headlines and the campaign headline lockup. Pick at most two emphasis devices per element.
- intent: Prevent over-stacked emphasis so hierarchy stays legible.

### rule_lisraya_underline_and_italic_reserved_usage
- class=typography scope=org_baseline hardness=strong_default polarity=must_not sections=None constraint=exclusivity
- rule_text: No underlining except real hyperlinks. No italic for emphasis in patient copy — reserve italics for study names, notes ("Note:"), and citations.
- intent: Keep underline reserved for links and italics reserved for citations/notes to avoid ambiguous emphasis.
