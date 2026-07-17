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

### rule_lisraya_bolding_and_emphasis_hierarchy
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Bold text must be used strictly for hierarchy and key takeaways, not decoration. Per section, bold at most the heading(s), one key phrase or claim per paragraph, and the statistical callout figure. Never bold entire paragraphs, footnotes/references, prepositional filler, or the generic name. Do not exceed more than ~15% of running body text in bold within any section.
- intent: Maintain typographic hierarchy and readability by restricting the overuse of bolding in running copy.

### rule_lisraya_bolding_mandatory_triggers
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=pairing
- rule_text: Always bold: callout text per the callout specs (§1.7), statistical callout numbers, and the brand name within a benefit claim when it is the focal point of the sentence (restricted to the first instance per section only).
- intent: Standardize formatting of high-importance numbers, callouts, and brand claims.

### rule_lisraya_emphasis_device_combinations
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Never use bold + ALL CAPS + color emphasis simultaneously on the same string except in chart headlines and the campaign headline lockup. Pick at most two emphasis devices per element.
- intent: Prevent visual over-emphasis and maintain aesthetic restraint in typography.

### rule_lisraya_underline_and_italic_restrictions
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=pairing
- rule_text: Do not underline text unless it functions as a real hyperlink. Never use italics for emphasis in patient copy; reserve italics strictly for study names, notes (such as 'Note:'), and citations.
- intent: Maintain visual clarity and web standards compliance by restricting underlines to hyperlinks and structuring italic use.
