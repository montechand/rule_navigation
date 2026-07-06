# Review: grp_ibsrela_content_pattern_rules_01

doc_ref: `content_pattern_rules[1]`

## Original text

````
## Type scale

| Element | Desktop (600 px) | Mobile (375 px) | Line height | Weight | Notes |
|---|---|---|---|---|---|
| **H1 — main section headline** | **24 px** | 22 px | 1.25 | Bold | e.g. "Prepare for your next appointment…", "If You Are Bothered By Your IBS-C Symptoms…", "Ask your healthcare provider…" |
| **H2 — secondary headline / two-column card headline** | 16 px | 16 px | 1.5 | Bold | secondary bold lead-in lines (e.g. "Download this guide so you can prepare…") |
| **Body copy** | **16 px** | 16 px | 1.5 | Regular | all editorial body copy |
| CTA button label | 14 px | 14 px | 1.2 (single line) | Bold | white pill, teal (#01A47E) label |
| ISI subheads | 14 px | 14 px | 1.4 | Bold | **locked footer build** |
| ISI "IMPORTANT RISK INFORMATION" | 15 px | 15 px | 1.4 | Bold | **locked footer build** |
| ISI body | 13 px | 13 px | 1.4 | Regular | **locked footer build** |
| Footnotes / abbreviations / references | 11 px | 11 px | 1.4 | Regular | **locked footer build** |
| Footer / legal / unsubscribe | 11 px | 11 px | 1.4 | Regular | **locked footer build** |

## Spacing (baseline)

### Paragraph rhythm (within a section)

- Letter-spacing/kerning: `0` for body; ALL-CAPS callouts and CTAs at `+0.5 px`. Never use negative tracking in email.
- Headline → subhead: **8 px**
- Subhead → body: **12 px**
- Headline → body (when there is no subhead): **12 px**
- Between body paragraphs: **12 px**
- Body → CTA button: **16 px**

### Section padding (defaults — how independently built sections stack)

Sections are built one at a time by different designers, so spacing is owned by the
section, not the boundary. **Every section owns half of every gap**: pick the section
*type* below and apply its fixed padding verbatim. Do not hand-tune these values — adjust
"air" by choosing the section type, never by editing padding.

| Section type | Padding (T R B L) | Use for |
|---|---|---|
| **Editorial** (default) | **12 px 24 px 12 px 24 px** | all white content sections (intro, copy, options, callbacks) |
| **Dark feature** | **24 px 24 px 24 px 24 px** | navy `#262262` / purple `#92278F` blocks: CTA, partnership, closing |
| **Inset card / callout** | host = Editorial; card = radius **12 px**, internal padding **24 px** all sides | boxed highlight inside a white section (`border-collapse: separate`; squares off in Outlook) |

Side gutters are always **24 px** on both edges, every section, no exceptions.

Because the tokens are fixed, every boundary resolves to one predictable gap:

| Boundary | Resulting gap |
|---|---|
| Editorial → Editorial | 24 px |
| Editorial ↔ Dark feature | 36 px |
| Dark feature → Dark feature | 48 px |
| Full-bleed hero/swirl (0) → first/last section | 12 px |

Two hard rules:

1. **Never override the vertical padding token.** A designer picks Editorial or Dark feature and uses it as-is.
2. **No empty spacer rows or placeholder cells** — they silently add 12–16 px and break the math.

## Locked content

The End Matter — ISI ("What is IBSRELA?", "IMPORTANT RISK INFORMATION", "Side Effects",
boxed-warning reference) and the legal footer/unsubscribe block — is a fixed system
constant and is **not** restyled by these content defaults. The ISI body sits at 13 px
in the approved build; the editorial content body at 16 px is the approved digital
content size for these emails.
````

## Extracted rules (19)

### rule_ibsrela_type_h1_main_headline
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: H1 (main section headline) is set at 24 px desktop / 22 px mobile, line height 1.25, Bold (e.g. "Prepare for your next appointment…", "If You Are Bothered By Your IBS-C Symptoms…").
- intent: Consistent main-headline typography.

### rule_ibsrela_type_h2_secondary_headline
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: H2 (secondary headline / two-column card headline, e.g. secondary bold lead-in lines) is set at 16 px desktop / 16 px mobile, line height 1.5, Bold.
- intent: Consistent secondary-headline typography.

### rule_ibsrela_type_body_copy
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: All editorial body copy is set at 16 px desktop / 16 px mobile, line height 1.5, Regular. 16 px is the approved digital content body size for these emails.
- intent: Consistent, approved body-copy size.

### rule_ibsrela_type_cta_button_label
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: CTA button label is set at 14 px desktop / 14 px mobile, line height 1.2 (single line), Bold, on a white pill with teal (#01A47E) label.
- intent: Consistent CTA button typography.

### rule_ibsrela_type_isi_subheads_locked
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: ISI subheads are set at 14 px desktop / 14 px mobile, line height 1.4, Bold, as part of the locked footer build.
- intent: ISI subhead typography is a locked system constant.

### rule_ibsrela_type_isi_iri_locked
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: The ISI "IMPORTANT RISK INFORMATION" heading is set at 15 px desktop / 15 px mobile, line height 1.4, Bold, as part of the locked footer build.
- intent: ISI IRI heading typography is a locked system constant.

### rule_ibsrela_type_isi_body_locked
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: ISI body copy is set at 13 px desktop / 13 px mobile, line height 1.4, Regular, in the approved locked footer build.
- intent: ISI body typography is a locked system constant.

### rule_ibsrela_type_footnotes_locked
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: Footnotes, abbreviations, and references are set at 11 px desktop / 11 px mobile, line height 1.4, Regular, as part of the locked footer build.
- intent: Footnote typography is a locked system constant.

### rule_ibsrela_type_footer_legal_locked
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: Footer / legal / unsubscribe copy is set at 11 px desktop / 11 px mobile, line height 1.4, Regular, as part of the locked footer build.
- intent: Footer legal typography is a locked system constant.

### rule_ibsrela_letter_spacing_body_and_caps
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Letter-spacing/kerning is 0 for body copy; ALL-CAPS callouts and CTAs use +0.5 px tracking. Never use negative tracking in email.
- intent: Consistent legible tracking; no negative kerning in email.

### rule_ibsrela_paragraph_rhythm_spacing
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Within a section, vertical rhythm is fixed: headline → subhead 8 px; subhead → body 12 px; headline → body (when there is no subhead) 12 px; between body paragraphs 12 px; body → CTA button 16 px.
- intent: Predictable intra-section vertical rhythm.

### rule_ibsrela_section_padding_editorial
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=['intro', 'callout'] constraint=binding
- rule_text: Editorial (default) sections — all white content sections (intro, copy, options, callbacks) — use fixed padding 12 px 24 px 12 px 24 px (T R B L), applied verbatim.
- intent: Section owns its air via fixed padding per type.

### rule_ibsrela_section_padding_dark_feature
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=binding
- rule_text: Dark feature sections — navy #262262 / purple #92278F blocks (CTA, partnership, closing) — use fixed padding 24 px 24 px 24 px 24 px (T R B L), applied verbatim.
- intent: Consistent air for dark feature blocks.

### rule_ibsrela_inset_card_padding_radius
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Inset card / callout: host section is Editorial; the card uses radius 12 px and internal padding 24 px on all sides. Use for a boxed highlight inside a white section (border-collapse: separate; squares off in Outlook).
- intent: Consistent callout card treatment.

### rule_ibsrela_side_gutters_fixed_24
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Side gutters are always 24 px on both edges, on every section, with no exceptions.
- intent: Uniform horizontal margins across all sections.

### rule_ibsrela_never_override_vertical_padding_token
- class=spacing scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Never override the vertical padding token. A designer picks Editorial or Dark feature and uses it as-is; adjust "air" by choosing the section type, never by editing padding values.
- intent: Preserve predictable boundary math by not hand-tuning padding.

### rule_ibsrela_no_empty_spacer_rows
- class=spacing scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: No empty spacer rows or placeholder cells — they silently add 12–16 px and break the spacing math.
- intent: Prevent hidden spacing that breaks boundary math.

### rule_ibsrela_boundary_gap_resolution
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Because padding tokens are fixed and every section owns half of every gap, each boundary resolves to a predictable gap: Editorial → Editorial = 24 px; Editorial ↔ Dark feature = 36 px; Dark feature → Dark feature = 48 px; full-bleed hero/swirl (0) → first/last section = 12 px.
- intent: Document the deterministic gaps produced by section-owned padding.

### rule_ibsrela_end_matter_isi_locked_constant
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['end_matter'] constraint=None
- rule_text: The End Matter — ISI ("What is IBSRELA?", "IMPORTANT RISK INFORMATION", "Side Effects", boxed-warning reference) and the legal footer/unsubscribe block — is a fixed system constant and is not restyled by these content defaults (ISI body sits at 13 px in the approved build; editorial content body at 16 px is the approved digital content size).
- intent: Protect the locked, approved End Matter build from content-default restyling.
