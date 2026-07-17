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

## Extracted rules (2)

### rule_lisraya_email_canvas_grid_table_binding
- class=assembly scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: The Email Canvas & Grid **[GENERAL — not specified in guide; Solstice email baseline]** table is a closed, brand-approved set; every row binds its listed values exactly as specified. Do not invent or alter rows.

| item | value |
|---|---|
| Email body width | **600px** fixed, centered; sections must render edge-to-edge at exactly 600px so assembled sections butt cleanly. |
| Mobile breakpoint | **480px**; all multi-column layouts collapse to single column. |
| Internal section grid | 12-column mental model; practical layouts are 1-col, 2-col (50/50), or image/text split (≈40/60). |
| Section side padding | 24px** left/right (consistent across ALL sections — this is what makes assembly seamless). Full-bleed imagery/gradient backgrounds may run to 600px, but text within them still respects 24px insets. |
| Vertical rhythm | 8px base unit.** All padding/margins are multiples of 8. |
| Section top/bottom internal padding | **32px** (each section owns its own top AND bottom padding; no external margins between sections — assembly is zero-gap stacking). |
| Heading → body gap | 16px. Paragraph → paragraph: 16px. Body → callout/CTA: 24px. Image → caption: 8px. |
| Buttons/CTA **[GENERAL, contrast-checked to palette] | ** Brand Blue #00529b background, White #ffffff text, Nunito Sans Bold 16px, padding 14px 32px, **min touch target 48px height** (brand accessibility rule: ≥48px clickable areas), corner radius 24px (fully rounded pill, echoing the rounded brand aesthetic). Secondary CTA: White background, 2px Brand Blue border, Brand Blue text, same metrics. One primary CTA per section maximum. |
- intent: Bind the Email Canvas & Grid **[GENERAL — not specified in guide; Solstice email baseline]** table values verbatim.

### rule_lisraya_one_primary_cta_per_section
- class=cta scope=org_baseline hardness=hard_constraint polarity=must sections=['cta'] constraint=cardinality
- rule_text: Use no more than one primary CTA in each section.
- intent: Keep section hierarchy focused and avoid competing primary actions.
