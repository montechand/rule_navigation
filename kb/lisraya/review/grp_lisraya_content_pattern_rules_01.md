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

## Extracted rules (3)

### rule_lisraya_rule_lisraya_email_type_scale_hierarchy
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Email designs must enforce the standard typographic hierarchy. Use the email font stack (font.stack.email = 'Nunito Sans', Verdana, Helvetica, Arial, sans-serif) with the defined type scale: H1 is 28px/36px (type_scale.h1), H2 is 22px/30px (type_scale.h2), H3 is 18px/26px (type_scale.h3), Body is 16px/24px (type_scale.body), Secondary Body is 14px/21px (type_scale.secondary_body), and Footnote is 12px/18px (type_scale.footnote). Avoid using adjacent text blocks with matching size and weight to construct different visual tiers.
- intent: Maintain structured typographic scale across email elements to establish a clear hierarchy of information.

### rule_lisraya_rule_lisraya_line_height_accessibility
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Line height must be set to a minimum of 150% for all running body copy (body.line_height = 150%). For light text rendered on dark backgrounds, increase the line height further to 160% (e.g., 16px/26px) to enhance readability.
- intent: Enhance text readability and support brand accessibility requirements.

### rule_lisraya_rule_lisraya_minimum_running_text_size
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=cardinality governance=regulatory/allowed_with_disclosure
- rule_text: Never render running body copy or footnote text below 12px. Sizing for standard Important Safety Information (ISI) copy is managed independently by locked components.
- intent: Enforce minimum font readability standard to remain regulatory compliant and accessible.
