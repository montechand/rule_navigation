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

## Extracted rules (4)

### rule_ibsrela_contrast_minimums
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Maintain minimum contrast of 4.5:1 for body text and 3:1 for bold headlines ≥18px. White on #92278F/#262262/#01A47E passes. Never set silver text on white, and never set periwinkle text on white.
- intent: Ensure text remains legible for accessibility compliance.

### rule_ibsrela_images_alt_text_and_live_isi
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: All images require alt text. The email must communicate indication + safety even with images off, meaning ISI must be live text and never image-based.
- intent: Guarantee safety information reaches users regardless of image rendering.

### rule_ibsrela_min_text_size_tap_target_heading_order
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Minimum live-text size is 10px (footnotes); body text is never below 12px; tap targets are ≥44px. Maintain logical heading order with exactly one H1 per email.
- intent: Enforce legibility, touch usability, and semantic structure.

### rule_ibsrela_link_underline_and_semantic_markup
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Underline links so meaning is not conveyed by color alone. Use semantic markup with <table role="presentation"> for layout tables.
- intent: Ensure links are perceivable without color and email markup is accessible.
