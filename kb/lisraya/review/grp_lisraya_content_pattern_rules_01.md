# Review: grp_lisraya_content_pattern_rules_01

doc_ref: `content_pattern_rules[1]`

## Original text

````
### Typography Hierarchy (fonts, weights, cases)
| Level | Print | Digital / Email | Word / PPT / Excel fallback |
|---|---|---|---|
| Headlines & headers | **Agenda** (Adobe font) | **Nunito Sans** (Google font), bolder weights, Title Case; *Agenda may be used as live text in digital for the campaign headline only* | **Aptos** |
| Body copy | **Nunito Sans** | **Nunito Sans** | **Aptos** |
| Footers, fine print | Nunito Sans | Nunito Sans | Aptos |
 
- Available Agenda weights: Light, Regular, Medium, Semibold, Bold.
- Available Nunito Sans weights: Light, Regular, SemiBold, Bold, ExtraBold.
- Available Aptos weights: Regular, Bold.
- **[GENERAL] Email font stack (CSS):** `'Nunito Sans', Verdana, Helvetica, Arial, sans-serif`. Nunito Sans must be loaded via `@font-face`/Google Fonts link where the client supports it; the stack guarantees graceful fallback in Outlook and other clients that strip webfonts.
- **[GENERAL] Email type scale (px / line-height):**
  - H1 (section hero headline): 28px / 36px (≈130%), Nunito Sans ExtraBold or Bold
  - H2 (section heading): 22px / 30px (≈136%), Nunito Sans Bold
  - H3 (subhead): 18px / 26px (≈144%), Nunito Sans Bold or SemiBold
  - Body: 16px / 24px (150%), Nunito Sans Regular — **16px is the brand-mandated minimum for body copy ("bigger is better")**
  - Secondary/supporting body: 14px / 21px (150%), Nunito Sans Regular — use sparingly, never for primary content
  - Footnote/reference text within a section: 12px / 18px (150%) — must be "noticeably smaller" than primary data and clearly separated from it
  - Never set running text below 12px. (ISI sizing is owned by the locked component.)
- **Line height: minimum 150% for all body copy** (brand accessibility rule). **For light text on dark backgrounds, increase further** — [GENERAL] use 160% (e.g., 16px/26px).
- Use a clear **type scale / visual hierarchy** so the reader knows what to read first, next, last. Never use two adjacent text blocks at the same size+weight to signal different hierarchy levels.
````

## Extracted rules (5)

### rule_lisraya_typography_font_family_by_surface
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines/headers use Agenda in print, Nunito Sans (bolder weights, Title Case) in digital/email, and Aptos as the Word/PPT/Excel fallback. Body copy, footers and fine print use Nunito Sans (Aptos fallback). Available Agenda weights: Light, Regular, Medium, Semibold, Bold; Nunito Sans: Light, Regular, SemiBold, Bold, ExtraBold; Aptos: Regular, Bold. Agenda may be used as live text in digital for the campaign headline only.
- intent: Ensure consistent brand typefaces across every production surface with correct fallbacks.

### rule_lisraya_email_font_stack_fallback
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Email font stack (CSS): 'Nunito Sans', Verdana, Helvetica, Arial, sans-serif. Nunito Sans must be loaded via @font-face/Google Fonts link where the client supports it; the stack guarantees graceful fallback in Outlook and other clients that strip webfonts.
- intent: Guarantee legible fallback in email clients that strip webfonts.

### rule_lisraya_email_type_scale
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Email type scale: H1 (section hero headline) 28px/36px Nunito Sans ExtraBold or Bold; H2 (section heading) 22px/30px Bold; H3 (subhead) 18px/26px Bold or SemiBold; Body 16px/24px Regular — 16px is the brand-mandated minimum for body copy ('bigger is better'); Secondary/supporting body 14px/21px Regular — use sparingly, never for primary content; Footnote/reference text 12px/18px — must be noticeably smaller than primary data and clearly separated from it. Never set running text below 12px (ISI sizing owned by the locked component).
- intent: Lock the email type scale and enforce a 16px body minimum with a 12px hard floor.

### rule_lisraya_body_line_height_minimum
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Line height: minimum 150% for all body copy (brand accessibility rule). For light text on dark backgrounds, increase further — [GENERAL] use 160% (e.g., 16px/26px).
- intent: Ensure readable line spacing, with extra leading for light-on-dark text.

### rule_lisraya_visual_hierarchy_distinct_levels
- class=typography scope=brand hardness=strong_default polarity=must_not sections=None constraint=None
- rule_text: Use a clear type scale / visual hierarchy so the reader knows what to read first, next, last. Never use two adjacent text blocks at the same size+weight to signal different hierarchy levels.
- intent: Preserve legible reading order via distinct type levels.
