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

### rule_ibsrela_dtp_cta_label_conventions
- class=cta scope=brand hardness=strong_default polarity=must sections=['cta'] constraint=binding
- rule_text: Approved DTP CTA labels are short verb phrases in sentence case (not ALL CAPS), 1–3 words — e.g. "Explore IBSRELA", "Watch Regina's story", "Watch video", "Learn more about how IBSRELA is different", "Yes, I have". The DTP label case follows cta.button.label.case (sentence_case for dtp_patient audience).
- intent: Keep DTP CTA labels short, action-oriented, and in sentence case per patient-facing voice.

### rule_ibsrela_dtp_poll_response_button
- class=cta scope=brand hardness=soft_guidance polarity=may sections=['cta'] constraint=None
- rule_text: A poll/segmentation question (e.g. "Have you started taking IBSRELA?") may use a single solid-fill response button ("Yes, I have") styled like a primary CTA.
- intent: Allow poll responses to be presented as a primary-styled CTA button.

### rule_ibsrela_dtp_no_hcp_get_connected_label
- class=cta scope=brand hardness=strong_default polarity=must_not sections=['cta'] constraint=exclusivity
- rule_text: DTP CTAs do not use the HCP library default "Get connected"; that label is HCP-scope only.
- intent: Prevent HCP-scope CTA labels from leaking into patient-facing DTP emails.

### rule_ibsrela_dtp_cta_label_matches_section_topic
- class=cta scope=brand hardness=strong_default polarity=must sections=['cta'] constraint=None
- rule_text: Per-section CTAs must match the section's topic: story → "Watch [name]'s story"; product overview → "Explore IBSRELA" or "Learn more about how IBSRELA is different".
- intent: Ensure each CTA's label is relevant to the content of its section.
