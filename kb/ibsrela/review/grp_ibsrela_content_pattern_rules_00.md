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
- rule_text: Parent brand typographic hierarchy in Avenir: Headline (H1) = Avenir Black, Title Case, Dark Blue #262262 or Purple #92278F; Subhead (H2) = Avenir Black, sentence case, Dark Blue or Purple; Body copy and ISI body = Avenir Roman, sentence case, Black #000000; ISI subheads (e.g. 'INDICATION', 'IMPORTANT SAFETY INFORMATION') = Avenir Black, ALL CAPS, Black; Footnotes / end matter = Avenir Book, sentence case, Black; Campaign headline ('FLIP THE SCRIPT') = Avenir Black, ALL CAPS, per campaign palette; Callouts & CTAs = Avenir Black (callouts) / per button spec, ALL CAPS. Concrete weights, cases, colors carried by the bound tokens.
- intent: Establish the consistent brand typographic hierarchy across levels.

### rule_ibsrela_isi_boxed_warning_heavy_reserved
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['safety'] constraint=exclusivity
- rule_text: ISI boxed warning text is set in Avenir Heavy, a weight reserved exclusively for this use; case is per approved ISI, color Black #000000.
- intent: Reserve the Heavy weight so the boxed warning reads as distinct.

### rule_ibsrela_avenir_arial_substitution_email_ppt
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: In emails and PowerPoint, the system font replacement for Avenir is Arial and Arial must be used. Map: Avenir Black → Arial Bold; Avenir Heavy → Arial Bold; Avenir Roman → Arial Regular; Avenir Book → Arial Regular (or reduce size 1pt for footnote distinction). [BASELINE] Email font stack is 'Arial, Helvetica, sans-serif'. Never load Avenir via webfont in email (rendering inconsistency in Outlook/SFMC); Arial is the brand-sanctioned substitute.
- intent: Guarantee reliable rendering in email/PPT by substituting Arial for Avenir.
