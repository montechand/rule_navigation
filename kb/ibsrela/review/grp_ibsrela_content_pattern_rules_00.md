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

### rule_ibsrela_typography_hierarchy_parent_system
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Typography hierarchy follows the parent brand system: Headline (H1) is Avenir Black, Title Case, Dark Blue or Purple; Subhead (H2) is Avenir Black, sentence case, Dark Blue or Purple; Body copy and ISI body are Avenir Roman, sentence case, Black; ISI subheads (e.g. 'INDICATION', 'IMPORTANT SAFETY INFORMATION') are Avenir Black, ALL CAPS, Black; Footnotes/end matter are Avenir Book, sentence case, Black; campaign headlines are Avenir Black, ALL CAPS per campaign palette; callouts are Avenir Black, ALL CAPS. Concrete font, weight, case, and color values are carried by their tokens.
- intent: Establish the single brand type hierarchy across all levels.

### rule_ibsrela_isi_heavy_weight_reserved
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=exclusivity
- rule_text: Avenir Heavy weight is reserved exclusively for ISI boxed-warning text and must not be used for any other content.
- intent: Reserve Heavy weight so it uniquely signals the boxed warning.

### rule_ibsrela_email_ppt_font_substitution
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: In email and PowerPoint, Arial is the sanctioned Avenir substitute and must be used: email font stack is 'Arial, Helvetica, sans-serif'. Never load Avenir via webfont in email (Outlook/SFMC rendering inconsistency). Weight mapping: Avenir Black → Arial Bold; Avenir Heavy → Arial Bold; Avenir Roman → Arial Regular; Avenir Book → Arial Regular (or reduce size 1pt for footnote distinction).
- intent: Guarantee consistent rendering in email/PPT where Avenir is unavailable.
