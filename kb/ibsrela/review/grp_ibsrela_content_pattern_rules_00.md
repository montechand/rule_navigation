# Review: grp_ibsrela_content_pattern_rules_00

doc_ref: `content_pattern_rules[0]`

## Original text

````
### 1.1 Typography hierarchy (parent brand system)
 
| Level | Font | Weight | Case | Color |
|---|---|---|---|---|
| Headline (H1) | Avenir | Black | **Title Case** | Dark Blue `#262262` or Purple `#92278F` |
| Subhead (H2) | Avenir | Black | Sentence case | Dark Blue `#262262` or Purple `#92278F` |
| Body copy | Avenir | Roman | Sentence case | Black `#000000` |
| ISI body | Avenir | Roman | Sentence case | Black `#000000` |
| ISI boxed warning text | Avenir | **Heavy** (reserved exclusively for this) | Per approved ISI | Black `#000000` |
| ISI subheads ("INDICATION", "IMPORTANT SAFETY INFORMATION") | Avenir | Black | ALL CAPS | Black `#000000` |
| Footnotes / end matter | Avenir | Book | Sentence case | Black `#000000` |
| Campaign headline ("FLIP THE SCRIPT") | Avenir | Black | ALL CAPS | Per campaign palette |
| Callouts & CTAs | Avenir | Black (callouts) / per button spec | ALL CAPS | Per callout/button spec |
 
- **Email/PowerPoint font substitution (explicit rule):** The system font replacement for Avenir is **Arial**. Arial must be used when designing emails and PowerPoint presentations. Map: Avenir Black → Arial Bold; Avenir Heavy → Arial Bold; Avenir Roman → Arial Regular; Avenir Book → Arial Regular (or reduce size 1pt for footnote distinction).
- **[BASELINE] Email font stack:** `Arial, Helvetica, sans-serif`. Never load Avenir via webfont in email (rendering inconsistency in Outlook/SFMC); Arial is the brand-sanctioned substitute.
````

## Extracted rules (3)

### rule_ibsrela_typography_hierarchy_parent_brand
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The parent brand typography hierarchy sets font, weight, case and color per level: Headline (H1) is Avenir Black, Title Case, in Dark Blue #262262 or Purple #92278F; Subhead (H2) is Avenir Black, sentence case, Dark Blue or Purple; Body copy and ISI body are Avenir Roman, sentence case, Black #000000; ISI subheads ('INDICATION', 'IMPORTANT SAFETY INFORMATION') are Avenir Black, ALL CAPS, Black; Footnotes/end matter are Avenir Book, sentence case, Black; Campaign headline ('FLIP THE SCRIPT') is Avenir Black, ALL CAPS, per campaign palette; Callouts are Avenir Black, ALL CAPS. Concrete values and background-driven color switching live on the referenced tokens.
- intent: Establish the single source of truth for text style across all typographic levels.

### rule_ibsrela_avenir_heavy_reserved_isi_boxed_warning
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['safety'] constraint=exclusivity
- rule_text: Avenir Heavy is reserved exclusively for ISI boxed warning text; it must not be used for any other level. The boxed warning is set in Avenir Heavy (Arial Bold in email), per approved ISI, in Black #000000.
- intent: Prevent dilution of the Heavy weight so the boxed warning remains its unique typographic signal.

### rule_ibsrela_email_ppt_avenir_arial_substitution
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [BASELINE] For email and PowerPoint, Arial is the brand-sanctioned substitute for Avenir. Use the email font stack 'Arial, Helvetica, sans-serif'. Never load Avenir via webfont in email (Outlook/SFMC rendering inconsistency). Weight mapping: Avenir Black → Arial Bold; Avenir Heavy → Arial Bold; Avenir Roman → Arial Regular; Avenir Book → Arial Regular (or reduce size 1pt for footnote distinction).
- intent: Guarantee consistent rendering in email/PPT environments where Avenir cannot be reliably embedded.
