# Brand sheets — lisraya

## Brand Accent Shape (core container device) (component_spec)

| item | value |
|---|---|
| Approved radius pairs (print) | **1.25" & 0.0625"** (large containers/photos), **0.5" & 0.0625"** (banners), **0.4375" & 0.0625"** (small callout boxes). |
| [GENERAL] Email px conversions (at 96dpi) | ** large: 120px & 6px; banner: 48px & 6px; callout: 42px & 6px. Apply the large radius to one diagonal pair (e.g., top-left + bottom-right), the 6px radius to the other pair. Be consistent within an email: same diagonal orientation across all sections (default: large radius top-left & bottom-right). |
| Exception | charts and tables use uniform rounded corners on all four corners** (not the asymmetric accent shape). [GENERAL: 12px uniform radius.] |

## Callout Formatting (three approved styles — use judiciously; never two of the same style competing on one screen/section) (color_palette)

| item | value |
|---|---|
| Main callout (key point) | ** Bold **Brand Blue (#00529b)** text with **Gold (#ffc60a)** horizontal rules above and below. Centered text. [GENERAL: rule weight 2px, rule width ≈ 60–100% of text block, 16px padding between rule and text.] |
| Secondary/data callout | ** **Light Blue (#E6F0F9) box at 70% tint** with **Bold Brand Blue** text; may include one line icon (e.g., 1x pill icon). [GENERAL: 20px internal padding, corner radius per accent-shape rules §2.5.] |
| Text-heavy callout (lists/descriptions) | ** **Golden Sand (#FEF1C8) box at 30% tint**, **Bold Brand Blue headline**, line icons, **Bold Sky Blue (#358CCB) subheads**, **Regular Graphite (#212121) body text**. [GENERAL: 24px internal padding; two-column icon+text layout collapses to single column on mobile.] |

## Complete Palette (color_palette)

| Name | HEX | RGB | CMYK | Pantone |
|---|---|---|---|---|
| Brand Blue | `#00529b` | 0, 82, 155 | 100, 76, 6, 1 | 2145 C |
| Sunshine | `#faa31b` | 250, 163, 27 | 0, 42, 100, 0 | 137 C |
| Gold | `#ffc60a` | 255, 198, 10 | 0, 23, 100, 0 | 7548 C |

Bound by `rule_lisraya_complete_palette_table_binding`.

## Complete Palette (color_palette)

| Name | HEX | RGB | CMYK |
|---|---|---|---|
| Sky Blue | `#358CCB` | 53, 140, 203 | 75, 35, 0, 0 |
| Deep Blue | `#003D74` | 0, 61, 116 | 100, 83, 29, 14 |
| Dark Navy | `#011E45` | 1, 30, 69 | 100, 89, 40, 49 |

## Complete Palette (color_palette)

| Name | HEX | RGB | CMYK |
|---|---|---|---|
| Coral | `#F26A38` | 242, 106, 56 | 0, 73, 87, 0 |
| Light Blue | `#E6F0F9` | 230, 240, 249 | 8, 2, 0, 0 |
| Golden Sand | `#FEF1C8` | 254, 241, 200 | 0, 3, 24, 0 |
| Graphite | `#212121` | 33, 33, 33 | 0, 0, 0, 88 |
| White | `#ffffff` | 255, 255, 255 | 0, 0, 0, 0 |

Bound by `rule_lisraya_complete_palette_table_binding_3`.

## Editorial / Style Rules (component_spec)

| item | value |
|---|---|
| Numbers | ** spell out zero–nine; numerals for 10+. **Exceptions — always numerals: percentages, ages, ratios.** Percentages use the % sign (e.g., 74%). |
| Data tone | ** when citing clinical data, avoid negative or fear-based language; use an empathetic, supportive, trust-building tone without oversimplifying. Example pattern: "Participants in the VALOR study taking LISRAYA had nearly 50% more improvement in their DM symptoms after one year compared to placebo." |
| Punctuation | ** Oxford/serial comma always in series of 3+. |

## Email Canvas & Grid **[GENERAL — not specified in guide; Solstice email baseline]** (canvas_spec)

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

Bound by `rule_lisraya_email_canvas_grid_table_binding`.

## [IMPORTANT] Gradient Callout CTA Section Rule (gradient_set)

| item | value |
|---|---|
| Background | the gradient PNG, applied as the section background, sized `cover`, `no-repeat`, centered, spanning the full content width (600px). Always set a solid `background-color` of Sunshine `#faa31b` as fallback, since clients like Outlook drop background images. |
| Headline | Brand Blue `#00529b`, centered, sitting in the **top third**, Nunito Sans weight 800, ~28px, one line. |
| Button | centered, in the **lower-middle** below the headline. Fill Deep Blue `#003D74`, white label (Nunito Sans 800, 18px), with a Gold `#FFC20E` arrow `›` (24px) after two non-breaking spaces. Size 248 × 64px. **Background image:** asset is `https://solstice-public-forever.s3.us-east-1.amazonaws.com/design_library/12912e15-c371-4bf0-a5b9-08a7f8c57d20/7772aba5-1ff5-4985-80bf-c15b782111a4/Gradient_callout.png` — do not re-host or recolor. The background may be skipped **only in very, very rare cases** (plain-text/AMP fallback, a client that strips all images, a hard size budget). When skipped, the section still renders on a solid Sunshine `#faa31b` fill and every other rule stays identical. |

## Gradient Specifications (approved set — never invent gradients) (gradient_set)

| Gradient | Stops | Usage |
|---|---|---|
| Brand Blue → Dark Navy | `#00529b` → `#011E45` | Dark backgrounds, blue masthead/waves |
| Sky Blue → Deep Blue | `#358CCB` → `#003D74` | Blue backgrounds, waves |
| Sunshine → 75% Gold | `#faa31b` → Gold @75% | Warm backgrounds |
| Golden Sand → White → Light Blue | `#FEF1C8` → `#ffffff` → `#E6F0F9` | Soft light backgrounds |
| Golden Sand → 75% Gold → Sunshine | `#FEF1C8` → Gold @75% → `#faa31b` | Warm light-to-saturated backgrounds |
| Sunshine → 0C,10M,78Y,0K (≈`#ffe05c` light gold) | `#faa31b` → light gold | **Masthead gradient — the gradient to use with the logo mark for contrast; mark sits at the lightest end** |

## Hierarchy & Application (color_palette)

| item | value |
|---|---|
| Body text | ** Graphite #212121 on light backgrounds; White on dark backgrounds (with increased line height, §1.2). |
| Callout surfaces | ** Light Blue at 70% tint (data callouts); Golden Sand at 30% tint (text-heavy callouts). |
| Links [GENERAL] | ** Brand Blue #00529b, underlined, on light backgrounds; White underlined on dark. |

Bound by `rule_lisraya_hierarchy_application_table_binding`.

## Palette reference (color_palette)

| Token | HEX | Use here |
|---|---|---|
| Brand Blue | `#00529b` | Headline text + icon stroke |
| Light Blue | `#E6F0F9` | Box fill |
| White | `#ffffff` | Icon badge fill |
| Dark Navy | `#011E45` | Drop-shadow color (low opacity) |

Bound by `rule_lisraya_palette_reference_table_binding`.

## Tint Rules (component_spec)

| item | value |
|---|---|
| Campaign headline "D" and "M" | **≈40% tint** of the headline color (Gold or Brand Blue colorway). |
| Light Blue callout box | **70% tint**. |
| Golden Sand callout box | **30% tint**. |
| Wave top layers | **70% transparency**. |

Bound by `rule_lisraya_tint_rules_table_binding`.

## Typography Hierarchy (fonts, weights, cases) (typography_scale)

| Level | Print | Digital / Email | Word / PPT / Excel fallback |
|---|---|---|---|
| Headlines & headers | **Agenda** (Adobe font) | **Nunito Sans** (Google font), bolder weights, Title Case; *Agenda may be used as live text in digital for the campaign headline only* | **Aptos** |
| Body copy | **Nunito Sans** | **Nunito Sans** | **Aptos** |
| Footers, fine print | Nunito Sans | Nunito Sans | Aptos |

## Typography Hierarchy (fonts, weights, cases) (typography_scale)

| item | value |
|---|---|
| H1 (section hero headline) | 28px / 36px (≈130%), Nunito Sans ExtraBold or Bold |
| H2 (section heading) | 22px / 30px (≈136%), Nunito Sans Bold |
| H3 (subhead) | 18px / 26px (≈144%), Nunito Sans Bold or SemiBold |
| Body | 16px / 24px (150%), Nunito Sans Regular — **16px is the brand-mandated minimum for body copy ("bigger is better")** |
| Secondary/supporting body | 14px / 21px (150%), Nunito Sans Regular — use sparingly, never for primary content |
| Footnote/reference text within a section | 12px / 18px (150%) — must be "noticeably smaller" than primary data and clearly separated from it |
| Line height | minimum 150% for all body copy** (brand accessibility rule). **For light text on dark backgrounds, increase further** — [GENERAL] use 160% (e.g., 16px/26px). |
