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

## Extracted rules (10)

### rule_lisraya_email_body_width_600px
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Email body width is 600px fixed, centered. Sections must render edge-to-edge at exactly 600px so assembled sections butt cleanly.
- intent: Ensure seamless section assembly with a fixed canvas width.

### rule_lisraya_mobile_breakpoint_480px_single_column
- class=layout scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Mobile breakpoint is 480px; all multi-column layouts collapse to single column at this breakpoint.
- intent: Guarantee readable single-column layout on mobile.

### rule_lisraya_section_grid_column_options
- class=layout scope=org_baseline hardness=soft_guidance polarity=should sections=None constraint=None
- rule_text: Internal section grid uses a 12-column mental model; practical layouts are 1-col, 2-col (50/50), or image/text split (~40/60).
- intent: Constrain layouts to a small set of predictable grids.

### rule_lisraya_section_side_padding_24px
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Section side padding is 24px left/right, consistent across ALL sections (this is what makes assembly seamless). Full-bleed imagery/gradient backgrounds may run to 600px, but text within them still respects the 24px insets.
- intent: Consistent side padding enables seamless section stacking and text alignment.

### rule_lisraya_vertical_rhythm_8px_base
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Vertical rhythm uses an 8px base unit; all padding and margins are multiples of 8. Heading → body gap: 16px. Paragraph → paragraph: 16px. Body → callout/CTA: 24px. Image → caption: 8px.
- intent: Maintain consistent vertical rhythm across all spacing.

### rule_lisraya_section_top_bottom_padding_zero_gap
- class=spacing scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Section top/bottom internal padding is 32px; each section owns its own top AND bottom padding. There are no external margins between sections — assembly is zero-gap stacking.
- intent: Zero-gap stacking requires each section to own its own top and bottom padding.

### rule_lisraya_primary_cta_style
- class=cta scope=org_baseline hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: Primary CTA button: Brand Blue #00529b background, White #ffffff text, Nunito Sans Bold 16px, padding 14px 32px, corner radius 24px (fully rounded pill echoing the rounded brand aesthetic).
- intent: Standardize the primary CTA appearance to the palette and brand aesthetic.

### rule_lisraya_cta_min_touch_target_48px
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: Buttons/CTAs must have a minimum touch target of 48px height; the brand accessibility rule requires ≥48px clickable areas.
- intent: Meet accessibility minimum for tappable/clickable targets.

### rule_lisraya_secondary_cta_style
- class=cta scope=org_baseline hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: Secondary CTA: White background, 2px Brand Blue #00529b border, Brand Blue text, using the same metrics as the primary CTA (Nunito Sans Bold 16px, padding 14px 32px, radius 24px, ≥48px touch target).
- intent: Provide a visually subordinate but consistent secondary CTA style.

### rule_lisraya_one_primary_cta_per_section
- class=cta scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: One primary CTA per section maximum.
- intent: Avoid competing calls to action within a single section.
