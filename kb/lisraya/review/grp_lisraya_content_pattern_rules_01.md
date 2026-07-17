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

## Extracted rules (4)

### rule_lisraya_cross_surface_typeface_hierarchy
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Apply the typeface hierarchy by surface: headlines and headers use Agenda in print, Nunito Sans in digital/email, and Aptos in Word/PPT/Excel; body copy and footer/fine print use Nunito Sans in print and digital/email and Aptos in Word/PPT/Excel. Digital/email headlines use bolder weights and Title Case.
- intent: Maintain a consistent, surface-appropriate typographic hierarchy.

### rule_lisraya_digital_agenda_campaign_headline_exception
- class=typography scope=brand hardness=hard_constraint polarity=may sections=None constraint=exclusivity
- rule_text: Agenda may be used as live text in digital only for the campaign headline; it is reserved from other digital live-text uses.
- intent: Preserve the explicit digital exception without broadening Agenda usage.

### rule_lisraya_distinct_text_hierarchy_levels
- class=typography scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Use a clear type scale and visual hierarchy so readers know what to read first, next, and last. Never use two adjacent text blocks at the same size and weight to signal different hierarchy levels.
- intent: Make content order and hierarchy immediately legible.

### rule_lisraya_email_type_scale_and_legibility
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: For email, use the Nunito Sans, Verdana, Helvetica, Arial, sans-serif stack and load Nunito Sans through @font-face or a Google Fonts link where supported. Use the approved H1, H2, H3, body, secondary-body, and footnote scales; body copy is at least 16px, running text is never below 12px, and body line height is at least 150% (160% for light text on dark backgrounds). Use 14px secondary/supporting body sparingly and never for primary content; keep 12px footnotes noticeably smaller than primary data and clearly separated from it.
- intent: Ensure reliable email rendering, readable hierarchy, and accessible text sizing.
