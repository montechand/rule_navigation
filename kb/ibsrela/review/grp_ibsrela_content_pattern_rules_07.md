# Review: grp_ibsrela_content_pattern_rules_07

doc_ref: `content_pattern_rules[7]`

## Original text

````
### CTA label conventions (DTP emails)
- Approved DTP CTA labels are short verb phrases, sentence case (not ALL CAPS), 1–3 words: "Explore IBSRELA", "Watch Regina's story", "Watch video", "Learn more about how IBSRELA is different", "Yes, I have".
- A poll/segmentation question (e.g., "Have you started taking IBSRELA?") may use a single solid-fill response button ("Yes, I have") styled like a primary CTA.
- DTP CTAs do not use the HCP library default "Get connected"; that label is HCP-scope. Per-section CTAs must match the section's topic (story → "Watch [name]'s story"; product overview → "Explore IBSRELA" or "Learn more about how IBSRELA is different").
````

## Extracted rules (4)

### rule_ibsrela_dtp_cta_label_convention
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=['cta'] constraint=binding
- rule_text: Approved DTP CTA labels are short verb phrases in sentence case (not ALL CAPS), 1–3 words — e.g., "Explore IBSRELA", "Watch Regina's story", "Watch video", "Learn more about how IBSRELA is different", "Yes, I have". This follows the dtp.cta.label_convention token (short verb phrase, sentence case, 1–3 words).
- intent: Keep DTP CTA labels concise, action-oriented, and sentence-cased.

### rule_ibsrela_dtp_poll_response_button
- class=cta scope=brand hardness=soft_guidance polarity=may sections=['cta'] constraint=None
- rule_text: A poll/segmentation question (e.g., "Have you started taking IBSRELA?") may use a single solid-fill response button ("Yes, I have") styled like a primary CTA.
- intent: Allow poll response buttons styled as primary CTAs for segmentation questions.

### rule_ibsrela_dtp_cta_no_hcp_default_label
- class=copy_editorial scope=brand hardness=strong_default polarity=must_not sections=['cta'] constraint=exclusivity
- rule_text: DTP CTAs do not use the HCP library default "Get connected"; that label is HCP-scope only.
- intent: Prevent HCP-scope CTA label from leaking into DTP materials.

### rule_ibsrela_dtp_cta_label_matches_section_topic
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=['cta'] constraint=None
- rule_text: Per-section CTAs must match the section's topic: story sections → "Watch [name]'s story"; product overview → "Explore IBSRELA" or "Learn more about how IBSRELA is different".
- intent: Align CTA labels to the content of the section they conclude.
