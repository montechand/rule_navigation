# Review: grp_lisraya_design_pattern_rules_00

doc_ref: `design_pattern_rules[0]`

## Original text

````
### Email Canvas & Grid **[GENERAL — not specified in guide; Solstice email baseline]**
- Email body width: **600px** fixed, centered; sections must render edge-to-edge at exactly 600px so assembled sections butt cleanly.
- Mobile breakpoint: **480px**; all multi-column layouts collapse to single column.
- Internal section grid: 12-column mental model; practical layouts are 1-col, 2-col (50/50), or image/text split (≈40/60).
- **Section side padding: 24px** left/right (consistent across ALL sections — this is what makes assembly seamless). Full-bleed imagery/gradient backgrounds may run to 600px, but text within them still respects 24px insets.
- **Vertical rhythm: 8px base unit.** All padding/margins are multiples of 8.
  - Section top/bottom internal padding: **32px** (each section owns its own top AND bottom padding; no external margins between sections — assembly is zero-gap stacking).
  - Heading → body gap: 16px. Paragraph → paragraph: 16px. Body → callout/CTA: 24px. Image → caption: 8px.
- Buttons/CTA **[GENERAL, contrast-checked to palette]:** Brand Blue #00529b background, White #ffffff text, Nunito Sans Bold 16px, padding 14px 32px, **min touch target 48px height** (brand accessibility rule: ≥48px clickable areas), corner radius 24px (fully rounded pill, echoing the rounded brand aesthetic). Secondary CTA: White background, 2px Brand Blue border, Brand Blue text, same metrics. One primary CTA per section maximum.
````

## Extracted rules (5)

### rule_lisraya_email_canvas_width_and_breakpoint
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Email body width is fixed at 600px, centered; sections must render edge-to-edge at exactly 600px so assembled sections butt cleanly. Mobile breakpoint is 480px, at which all multi-column layouts collapse to single column. Full-bleed imagery/gradient backgrounds may run to 600px, but text within them still respects the 24px side insets.
- intent: Guarantee seamless section assembly and predictable responsive collapse.

### rule_lisraya_internal_section_grid
- class=layout scope=org_baseline hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: Internal section grid uses a 12-column mental model; practical layouts are 1-col, 2-col (50/50), or image/text split (≈40/60).
- intent: Constrain layout composition to a small set of predictable grids.

### rule_lisraya_section_padding_and_vertical_rhythm
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Section side padding is 24px left/right consistently across ALL sections (this is what makes assembly seamless); text within full-bleed backgrounds still respects the 24px insets. Vertical rhythm is an 8px base unit — all padding/margins are multiples of 8. Each section owns its own 32px top AND bottom internal padding with no external margins between sections (assembly is zero-gap stacking). Heading→body gap 16px, paragraph→paragraph 16px, body→callout/CTA 24px, image→caption 8px.
- intent: Enforce a consistent spacing system enabling zero-gap section stacking.

### rule_lisraya_primary_and_secondary_cta_spec
- class=cta scope=org_baseline hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: Primary CTA buttons use Brand Blue #00529b background, White #ffffff text, Nunito Sans Bold 16px, padding 14px 32px, minimum 48px clickable touch-target height (brand accessibility rule: ≥48px clickable areas), and a fully rounded 24px pill radius echoing the rounded brand aesthetic. Secondary CTA uses a White background with a 2px Brand Blue border and Brand Blue text at the same metrics.
- intent: Standardize CTA appearance and meet the ≥48px accessible touch-target rule.

### rule_lisraya_one_primary_cta_per_section
- class=cta scope=org_baseline hardness=hard_constraint polarity=must_not sections=['cta'] constraint=cardinality
- rule_text: One primary CTA per section maximum.
- intent: Prevent competing calls-to-action within a single section.
