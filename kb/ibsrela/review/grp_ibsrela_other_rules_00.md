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

### rule_ibsrela_accessibility_contrast_minimums
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Maintain minimum contrast of 4.5:1 for body text and 3:1 for bold headlines ≥18px. White text on #92278F, #262262, or #01A47E passes; never set silver text on white, and never set periwinkle text on white.
- intent: Ensure legibility and WCAG-level contrast compliance.

### rule_ibsrela_accessibility_alt_text_and_images_off
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: All images require alt text. The email must communicate indication and safety even with images off — ISI must be live text, never image-based.
- intent: Guarantee critical regulatory content survives images-off rendering and assistive tech.

### rule_ibsrela_accessibility_text_size_tap_heading_minimums
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Minimum live-text size is 10px (footnotes); body text never below 12px; tap targets ≥44px; use logical heading order with exactly one H1 per email.
- intent: Ensure readable text, tappable targets, and semantic heading structure.

### rule_ibsrela_accessibility_links_and_semantic_markup
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Underline links; do not rely on color alone to convey linkage. Use semantic table markup with role="presentation".
- intent: Ensure links are perceivable without color and email markup is accessible.
