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

## Extracted rules (5)

### rule_ibsrela_min_contrast_ratios
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Maintain minimum contrast of 4.5:1 for body text and 3:1 for bold headlines ≥18 px. White on #92278F/#262262/#01A47E passes. Never set silver text on white, and never set periwinkle text on white.
- intent: Ensure text remains legible for all readers.

### rule_ibsrela_images_alt_text_and_image_off_resilience
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All images require alt text. The email must communicate indication and safety even with images off — ISI must be live text, never image-based.
- intent: Guarantee critical regulatory content is accessible without images.

### rule_ibsrela_min_text_size_and_tap_targets
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Minimum live-text size is 10 px (footnotes); body text never below 12 px; tap targets must be ≥44 px. Maintain logical heading order with exactly one H1 per email.
- intent: Preserve legibility and predictable navigation structure.

### rule_ibsrela_one_h1_per_email
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Maintain a logical heading order with exactly one H1 per email.
- intent: Provide a coherent document outline for assistive technology.

### rule_ibsrela_underline_links_and_semantic_markup
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Underline links; don't rely on color alone to indicate them. Use semantic <table role="presentation"> markup.
- intent: Ensure links and layout tables are perceivable and correctly interpreted.
