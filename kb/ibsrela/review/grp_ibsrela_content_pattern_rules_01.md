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

## Extracted rules (5)

### rule_ibsrela_email_type_scale
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Email type scale is fixed per element: H1 main section headline 24px desktop / 22px mobile, line-height 1.25, bold; H2 secondary/two-column card headline 16px, line-height 1.5, bold; body copy 16px, line-height 1.5, regular; CTA button label 14px, line-height 1.2 (single line), bold; ISI subheads 14px bold; ISI 'IMPORTANT RISK INFORMATION' 15px bold; ISI body 13px regular; footnotes/abbreviations/references 11px; footer/legal/unsubscribe 11px; all ISI/footer text at line-height 1.4. ISI subhead/IRI/body/footnote/footer sizes are part of the locked footer build.
- intent: Enforce a consistent, approved typographic hierarchy across all email templates.

### rule_ibsrela_paragraph_rhythm_and_tracking
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Within a section: letter-spacing/kerning is 0 for body; ALL-CAPS callouts and CTAs use +0.5px; never use negative tracking in email. Paragraph rhythm: headline→subhead 8px, subhead→body 12px, headline→body (no subhead) 12px, between body paragraphs 12px, body→CTA button 16px.
- intent: Maintain consistent vertical rhythm and legible tracking within sections.

### rule_ibsrela_section_padding_and_boundaries
- class=spacing scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Spacing is owned by the section, not the boundary; every section owns half of every gap. Pick the section type and apply its fixed padding verbatim: Editorial (default) 12px 24px 12px 24px for all white content sections; Dark feature 24px all sides for navy #262262 / purple #92278F blocks (CTA, partnership, closing); Inset card/callout hosted in an Editorial section with radius 12px and 24px internal padding (border-collapse: separate; squares off in Outlook). Side gutters are always 24px on both edges, every section, no exceptions. Resulting boundary gaps resolve predictably: Editorial→Editorial 24px, Editorial↔Dark feature 36px, Dark feature→Dark feature 48px, full-bleed hero/swirl→first/last section 12px. Adjust 'air' only by choosing the section type.
- intent: Guarantee predictable spacing math across independently-built sections.

### rule_ibsrela_no_padding_override_or_spacers
- class=spacing scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Two hard rules: (1) Never override the vertical padding token — a designer picks Editorial or Dark feature and uses it as-is, and must not hand-tune padding values. (2) No empty spacer rows or placeholder cells — they silently add 12–16px and break the spacing math.
- intent: Protect the fixed-token spacing system from ad-hoc edits that break the math.

### rule_ibsrela_locked_isi_footer_not_restyled
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=verbatim_content
- rule_text: The End Matter — ISI ('What is IBSRELA?', 'IMPORTANT RISK INFORMATION', 'Side Effects', boxed-warning reference) and the legal footer/unsubscribe block is a fixed system constant and is NOT restyled by these content defaults. The ISI body sits at 13px in the approved locked build; the editorial content body at 16px is the approved digital content size for these emails.
- intent: Keep the regulated ISI/footer as a locked constant separate from editorial content defaults.
