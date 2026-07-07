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
- rule_text: The parent-brand typography hierarchy is set in Avenir: Headline (H1) — Black, Title Case, Dark Blue or Purple; Subhead (H2) — Black, Sentence case, Dark Blue or Purple; Body copy and ISI body — Roman, Sentence case, Black; ISI subheads ('INDICATION', 'IMPORTANT SAFETY INFORMATION') — Black, ALL CAPS, Black; Footnotes/end matter — Book, Sentence case, Black; Campaign headline ('FLIP THE SCRIPT') — Black, ALL CAPS, per campaign palette; Callouts & CTAs — Black (callouts)/per button spec, ALL CAPS. Concrete font/weight/case/color values are carried by the bound tokens.
- intent: Establish a consistent, level-by-level typographic hierarchy across brand materials.

### rule_ibsrela_avenir_heavy_reserved_isi_boxed_warning
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['safety'] constraint=exclusivity
- rule_text: Avenir Heavy weight is reserved exclusively for ISI boxed warning text and must not be used for any other type level.
- intent: Preserve the boxed warning's distinct emphasis and prevent weight overuse.

### rule_ibsrela_email_ppt_avenir_arial_substitution
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [BASELINE] In email and PowerPoint, Avenir is substituted with Arial using the stack `Arial, Helvetica, sans-serif`. Never load Avenir via webfont in email (rendering inconsistency in Outlook/SFMC). Weight mapping: Avenir Black → Arial Bold; Avenir Heavy → Arial Bold; Avenir Roman → Arial Regular; Avenir Book → Arial Regular (or reduce size 1pt for footnote distinction).
- intent: Guarantee consistent email/PPT rendering by using the sanctioned system font substitute.
