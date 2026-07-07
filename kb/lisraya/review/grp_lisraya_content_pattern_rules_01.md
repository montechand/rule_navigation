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

### rule_lisraya_font_family_hierarchy
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Typography families are surface-dependent: print headlines use Agenda, digital/email headlines and all body copy use Nunito Sans (bolder weights, Title Case), and Word/PPT/Excel fallback uses Aptos. Available weights: Agenda (Light, Regular, Medium, Semibold, Bold), Nunito Sans (Light, Regular, SemiBold, Bold, ExtraBold), Aptos (Regular, Bold). Agenda may be used as live text in digital only for the campaign headline. Footers/fine print follow the same body family per surface.
- intent: Enforce consistent, surface-appropriate typeface selection across the brand.

### rule_lisraya_email_font_stack
- class=typography scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Email CSS font stack must be `'Nunito Sans', Verdana, Helvetica, Arial, sans-serif`. Nunito Sans must be loaded via @font-face/Google Fonts link where the client supports it; the stack guarantees graceful fallback in Outlook and other clients that strip webfonts.
- intent: Guarantee webfont loading with graceful fallback across email clients.

### rule_lisraya_email_type_scale
- class=typography scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Email type scale: H1 section hero headline 28px/36px Nunito Sans ExtraBold or Bold; H2 section heading 22px/30px Nunito Sans Bold; H3 subhead 18px/26px Nunito Sans Bold or SemiBold; Body 16px/24px Nunito Sans Regular; Secondary/supporting body 14px/21px Nunito Sans Regular (use sparingly, never for primary content); Footnote/reference text within a section 12px/18px, must be noticeably smaller than primary data and clearly separated from it.
- intent: Standardize the email typographic scale and weights across all sections.

### rule_lisraya_body_minimum_size_and_floor
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: 16px is the brand-mandated minimum for body copy ('bigger is better'). Secondary body (14px) is used sparingly, never for primary content. Never set running text below 12px. (ISI sizing is owned by the locked component.)
- intent: Ensure readable minimum text sizes for patients.

### rule_lisraya_body_line_height_minimum
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Line height must be a minimum of 150% for all body copy (brand accessibility rule). For light text on dark backgrounds, increase further — [GENERAL] use 160% (e.g., 16px/26px). The dark-background 160% value is carried on the body.line_height token variant.
- intent: Maintain accessible line spacing, with extra leading for light-on-dark text.

### rule_lisraya_visual_hierarchy_distinction
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Use a clear type scale / visual hierarchy so the reader knows what to read first, next, last. Never use two adjacent text blocks at the same size+weight to signal different hierarchy levels.
- intent: Preserve legible reading order through distinct typographic levels.
