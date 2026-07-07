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

## Extracted rules (6)

### rule_lisraya_typography_font_families_by_surface
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Font families are assigned by surface: headlines/headers use Agenda in print and Nunito Sans (bolder weights, Title Case) in digital/email; body copy and footers/fine print use Nunito Sans across print and digital; Word/PPT/Excel fallback for all levels is Aptos. Agenda may be used as live text in digital only for the campaign headline. Available weights: Agenda (Light, Regular, Medium, Semibold, Bold); Nunito Sans (Light, Regular, SemiBold, Bold, ExtraBold); Aptos (Regular, Bold).
- intent: Consistent, correctly-loaded typeface use across every production surface.

### rule_lisraya_email_font_stack_css
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Email CSS font stack is 'Nunito Sans', Verdana, Helvetica, Arial, sans-serif. Nunito Sans must be loaded via @font-face/Google Fonts link where the client supports it; the stack guarantees graceful fallback in Outlook and other clients that strip webfonts.
- intent: Guarantee readable fallback where webfonts are stripped.

### rule_lisraya_email_type_scale_and_weights
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Email type scale: H1 hero headline 28/36 Nunito Sans ExtraBold or Bold; H2 heading 22/30 Nunito Sans Bold; H3 subhead 18/26 Nunito Sans Bold or SemiBold; Body 16/24 Nunito Sans Regular; Secondary/supporting body 14/21 Nunito Sans Regular used sparingly and never for primary content; Footnote/reference text within a section 12/18, which must be noticeably smaller than primary data and clearly separated from it. ISI sizing is owned by the locked component.
- intent: Fixed, hierarchical email type scale with weights per level.

### rule_lisraya_body_minimum_size
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: 16px is the brand-mandated minimum for body copy ("bigger is better"). Never set running text below 12px. (ISI sizing is owned by the locked component.)
- intent: Legible minimum text sizes for patient readability.

### rule_lisraya_body_line_height_minimum
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Line height is minimum 150% for all body copy (brand accessibility rule). For light text on dark backgrounds, increase further — [GENERAL] use 160% (e.g., 16px/26px). The body.line_height token carries the 150%→160% switch by background group.
- intent: Readable leading, boosted for light-on-dark contexts.

### rule_lisraya_visual_hierarchy_distinct_levels
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Use a clear type scale / visual hierarchy so the reader knows what to read first, next, last. Never use two adjacent text blocks at the same size+weight to signal different hierarchy levels.
- intent: Make reading order unambiguous through distinct type levels.
