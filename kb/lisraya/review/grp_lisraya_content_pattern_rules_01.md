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

## Extracted rules (15)

### rule_lisraya_print_headline_font_agenda
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: In print materials, headlines and headers must be set in Agenda (Adobe font).
- intent: Maintain consistent headline typography in print.

### rule_lisraya_digital_headline_font_nunito_sans
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: In digital/email, headlines and headers must be set in Nunito Sans (Google font), using bolder weights and Title Case.
- intent: Consistent digital headline typography.

### rule_lisraya_agenda_live_text_campaign_headline_only
- class=typography scope=campaign hardness=strong_default polarity=may sections=None constraint=exclusivity
- rule_text: Agenda may be used as live text in digital for the campaign headline only.
- intent: Restrict Agenda live text in digital to the campaign headline.

### rule_lisraya_body_copy_font_nunito_sans
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy, footers, and fine print must be set in Nunito Sans across print and digital/email.
- intent: Consistent body typography.

### rule_lisraya_word_ppt_fallback_font_aptos
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: In Word / PPT / Excel, use Aptos as the fallback font for headlines, headers, body copy, footers, and fine print.
- intent: Office document fallback typography.

### rule_lisraya_email_font_stack_css
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Email CSS font stack must be `'Nunito Sans', Verdana, Helvetica, Arial, sans-serif`. Nunito Sans must be loaded via @font-face / Google Fonts link where the client supports it; the stack guarantees graceful fallback in Outlook and other clients that strip webfonts.
- intent: Guarantee graceful font fallback in email clients.

### rule_lisraya_email_type_scale
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Email type scale (px / line-height): H1 (section hero headline) 28px/36px (≈130%) Nunito Sans ExtraBold or Bold; H2 (section heading) 22px/30px (≈136%) Nunito Sans Bold; H3 (subhead) 18px/26px (≈144%) Nunito Sans Bold or SemiBold; Body 16px/24px (150%) Nunito Sans Regular; Secondary/supporting body 14px/21px (150%) Nunito Sans Regular; Footnote/reference text 12px/18px (150%).
- intent: Define the email typographic scale.

### rule_lisraya_body_copy_min_16px_2
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: 16px is the brand-mandated minimum for body copy ("bigger is better").
- intent: Ensure legible body copy size.

### rule_lisraya_secondary_body_sparingly
- class=typography scope=brand hardness=strong_default polarity=must_not sections=None constraint=None
- rule_text: Secondary/supporting body (14px/21px) must be used sparingly and never for primary content.
- intent: Reserve smaller body size for supporting text only.

### rule_lisraya_footnote_noticeably_smaller_separated
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Footnote/reference text within a section (12px/18px) must be "noticeably smaller" than primary data and clearly separated from it.
- intent: Distinguish footnotes from primary data.

### rule_lisraya_never_running_text_below_12px
- class=typography scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Never set running text below 12px. (ISI sizing is owned by the locked component.)
- intent: Maintain minimum legible text size.

### rule_lisraya_line_height_min_150_2
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Line height must be a minimum of 150% for all body copy (brand accessibility rule).
- intent: Ensure readable line spacing.

### rule_lisraya_line_height_light_on_dark_160
- class=typography scope=org_baseline hardness=strong_default polarity=must sections=None constraint=None
- rule_text: For light text on dark backgrounds, increase line height further — use 160% (e.g., 16px/26px).
- intent: Improve legibility of light text on dark backgrounds.

### rule_lisraya_clear_type_scale_hierarchy
- class=typography scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Use a clear type scale / visual hierarchy so the reader knows what to read first, next, and last.
- intent: Guide reader attention through clear hierarchy.

### rule_lisraya_no_adjacent_same_size_weight_blocks
- class=typography scope=brand hardness=strong_default polarity=must_not sections=None constraint=None
- rule_text: Never use two adjacent text blocks at the same size+weight to signal different hierarchy levels.
- intent: Prevent ambiguous hierarchy signaling.
