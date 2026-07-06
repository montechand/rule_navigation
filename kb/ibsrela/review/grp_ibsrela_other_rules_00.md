# Review: grp_ibsrela_other_rules_00

doc_ref: `other_rules[0]`

## Original text

````
### Accessibility [BASELINE]
- Minimum contrast 4.5:1 for body text, 3:1 for ≥18 px bold headlines (white on `#92278F`/`#262262`/`#01A47E` passes; never silver text on white, never periwinkle text on white).
- All images require alt text; the email must communicate indication + safety even with images off (live-text ISI, never image-based ISI).
- Minimum live-text size 10 px (footnotes); body never below 12 px; tap targets ≥ 44 px; logical heading order (one H1 per email).
- Underline links (don't rely on color alone); semantic `<table role="presentation">` markup.
````

## Extracted rules (9)

### rule_ibsrela_min_contrast_ratios
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Minimum contrast must be 4.5:1 for body text and 3:1 for bold headlines ≥18 px. White text on #92278F (Purple), #262262 (Dark Blue), or #01A47E (Green) passes these requirements.
- intent: Ensure text remains legible for all users per accessibility contrast standards.

### rule_ibsrela_no_low_contrast_text_pairings
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=pairing
- rule_text: Never use silver text on white, and never use periwinkle text on white — these fail minimum contrast requirements.
- intent: Prevent illegible low-contrast text combinations.

### rule_ibsrela_all_images_require_alt_text
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All images require alt text.
- intent: Ensure image content is accessible to screen readers and when images are disabled.

### rule_ibsrela_communicate_indication_safety_images_off
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The email must communicate indication and safety even with images off; use live-text ISI, never image-based ISI.
- intent: Guarantee critical regulatory content is always readable regardless of image rendering.

### rule_ibsrela_min_live_text_sizes
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Minimum live-text size is 10 px (footnotes); body text must never be below 12 px.
- intent: Keep all text legible at accessible minimum sizes.

### rule_ibsrela_min_tap_target_size
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Tap targets must be ≥ 44 px.
- intent: Ensure interactive elements are large enough for reliable touch interaction.

### rule_ibsrela_logical_heading_order_one_h1
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Maintain logical heading order with exactly one H1 per email.
- intent: Support screen-reader navigation and document structure.

### rule_ibsrela_underline_links_not_color_alone
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Underline links; do not rely on color alone to indicate links.
- intent: Ensure links are distinguishable for users who cannot perceive color differences.

### rule_ibsrela_semantic_presentation_table_markup
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Use semantic `<table role="presentation">` markup for layout tables.
- intent: Prevent layout tables from being announced as data tables by assistive technology.
