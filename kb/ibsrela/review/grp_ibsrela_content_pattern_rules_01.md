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

## Extracted rules (8)

### rule_ibsrela_type_scale_editorial
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Editorial type scale: H1 main section headline at 24px desktop / 22px mobile, line-height 1.25, Bold; H2 secondary/two-column-card headline at 16px, line-height 1.5, Bold; body copy at 16px, line-height 1.5, Regular; CTA button label at 14px, line-height 1.2 single line, Bold (white pill, teal label). 16px editorial content body is the approved digital content size.
- intent: Lock the editorial type scale to consistent, approved sizes/weights.

### rule_ibsrela_type_scale_isi_footer_locked
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: The End Matter type scale is a fixed locked footer build and is NOT restyled by content defaults: ISI subheads 14px Bold, 'IMPORTANT RISK INFORMATION' 15px Bold, ISI body 13px Regular, footnotes/abbreviations/references 11px Regular, footer/legal/unsubscribe 11px Regular, all at line-height 1.4. The ISI body sits at 13px in the approved build.
- intent: Preserve the approved locked footer/ISI build unaffected by content styling.

### rule_ibsrela_letter_spacing_kerning
- class=typography scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Letter-spacing/kerning is 0 for body; ALL-CAPS callouts and CTAs use +0.5px. Never use negative tracking in email.
- intent: Keep tracking consistent and forbid negative kerning.

### rule_ibsrela_paragraph_rhythm
- class=spacing scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Paragraph rhythm within a section: headline→subhead 8px; subhead→body 12px; headline→body (no subhead) 12px; between body paragraphs 12px; body→CTA button 16px.
- intent: Standardize intra-section vertical rhythm.

### rule_ibsrela_section_padding_defaults
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Spacing is owned by the section, not the boundary; every section owns half of every gap. Apply fixed padding verbatim by picking the section type: Editorial (default) 12px 24px 12px 24px for all white content sections; Dark feature 24px all sides for navy #262262 / purple #92278F blocks (CTA, partnership, closing); Inset card = host Editorial with radius 12px and 24px internal padding all sides (border-collapse: separate). Side gutters are always 24px on both edges, every section, no exceptions. Adjust 'air' only by choosing the section type, never by editing padding.
- intent: Make independently-built sections stack to predictable gaps.

### rule_ibsrela_section_boundary_gaps
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Because tokens are fixed, every boundary resolves to a predictable gap: Editorial→Editorial 24px; Editorial↔Dark feature 36px; Dark feature→Dark feature 48px; Full-bleed hero/swirl (0)→first/last section 12px.
- intent: Document the resolved gaps produced by section-owned padding.

### rule_ibsrela_no_padding_overrides_no_spacers
- class=spacing scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Two hard rules: (1) Never override the vertical padding token — a designer picks Editorial or Dark feature and uses it as-is. (2) No empty spacer rows or placeholder cells — they silently add 12–16px and break the math.
- intent: Prevent ad-hoc spacing that breaks the deterministic layout math.

### rule_ibsrela_end_matter_locked_content
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=['end_matter'] constraint=verbatim_content
- rule_text: The End Matter — ISI ('What is IBSRELA?', 'IMPORTANT RISK INFORMATION', 'Side Effects', boxed-warning reference) and the legal footer/unsubscribe block — is a fixed system constant and is not restyled by these content defaults.
- intent: Treat ISI and legal footer as a locked, non-restyled system constant.
