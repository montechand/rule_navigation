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

## Extracted rules (6)

### rule_ibsrela_min_contrast_ratios
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding governance=regulatory/requires_qualifier
- rule_text: Maintain minimum contrast of 4.5:1 for body text and 3:1 for ≥18 px bold headlines. White on #92278F / #262262 / #01A47E passes. Never use silver text on white and never periwinkle text on white.
- intent: Ensure text remains legible for low-vision users.

### rule_ibsrela_images_require_alt_text_livetext_isi
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding governance=disclosure/requires_qualifier
- rule_text: All images require alt text. The email must communicate indication + safety even with images off — ISI must be live text, never image-based.
- intent: Guarantee safety information and indication remain accessible when images fail to load or are disabled.

### rule_ibsrela_min_text_sizes_and_tap_targets
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Minimum live-text size is 10 px (footnotes); body text never below 12 px; tap targets ≥ 44 px; use logical heading order with exactly one H1 per email.
- intent: Preserve legibility and touch usability and provide a coherent document outline.

### rule_ibsrela_single_h1_per_email
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Use logical heading order with exactly one H1 per email.
- intent: Provide a correct, single-rooted document heading structure for assistive technology.

### rule_ibsrela_underline_links_not_color_alone
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Underline links; do not rely on color alone to indicate links.
- intent: Make links perceivable independent of color perception.

### rule_ibsrela_semantic_presentation_table_markup
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Use semantic <table role="presentation"> markup for layout tables.
- intent: Prevent screen readers from announcing layout tables as data tables.
