# Review: grp_ibsrela_content_pattern_rules_07

doc_ref: `content_pattern_rules[7]`

## Original text

````
### CTA label conventions (DTP emails)
- Approved DTP CTA labels are short verb phrases, sentence case (not ALL CAPS), 1–3 words: "Explore IBSRELA", "Watch Regina's story", "Watch video", "Learn more about how IBSRELA is different", "Yes, I have".
- A poll/segmentation question (e.g., "Have you started taking IBSRELA?") may use a single solid-fill response button ("Yes, I have") styled like a primary CTA.
- DTP CTAs do not use the HCP library default "Get connected"; that label is HCP-scope. Per-section CTAs must match the section's topic (story → "Watch [name]'s story"; product overview → "Explore IBSRELA" or "Learn more about how IBSRELA is different").
````

## Extracted rules (3)

### rule_ibsrela_dtp_cta_label_conventions
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=['cta'] constraint=binding
- rule_text: Approved DTP CTA labels are short verb phrases in sentence case (not ALL CAPS), 1–3 words — e.g. "Explore IBSRELA", "Watch Regina's story", "Watch video", "Learn more about how IBSRELA is different", "Yes, I have". (DTP audience drives the sentence-case variant of cta.button.label.case, which otherwise defaults to all-caps.)
- intent: Keep DTP CTAs conversational, short, and in sentence case rather than the branded all-caps style.

### rule_ibsrela_dtp_poll_response_button
- class=cta scope=brand hardness=soft_guidance polarity=may sections=['cta'] constraint=None
- rule_text: A poll/segmentation question (e.g., "Have you started taking IBSRELA?") may use a single solid-fill response button ("Yes, I have") styled like a primary CTA.
- intent: Allow segmentation polls to present a response as a primary-styled CTA button.

### rule_ibsrela_dtp_cta_label_scope_and_topic_match
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=['cta'] constraint=None
- rule_text: DTP CTAs must not use the HCP library default "Get connected" (that label is HCP-scope). Each per-section CTA must match the section's topic — e.g. patient story → "Watch [name]'s story"; product overview → "Explore IBSRELA" or "Learn more about how IBSRELA is different".
- intent: Prevent HCP-only labels in DTP and keep CTA copy relevant to the section it sits in.
