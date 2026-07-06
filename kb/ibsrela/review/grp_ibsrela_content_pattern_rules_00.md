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

## Extracted rules (11)

### rule_ibsrela_h1_headline_typography
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headline (H1) must be set in Avenir, Black weight, Title Case, colored either Dark Blue #262262 or Purple #92278F.
- intent: Enforce consistent headline typographic identity.

### rule_ibsrela_h2_subhead_typography
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Subhead (H2) must be set in Avenir, Black weight, Sentence case, colored either Dark Blue #262262 or Purple #92278F.
- intent: Enforce consistent subhead typographic identity.

### rule_ibsrela_body_copy_typography
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy must be set in Avenir, Roman weight, Sentence case, colored Black #000000.
- intent: Consistent body typography and legibility.

### rule_ibsrela_isi_body_typography
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: ISI body must be set in Avenir, Roman weight, Sentence case, colored Black #000000.
- intent: Consistent ISI body typography.

### rule_ibsrela_isi_boxed_warning_heavy_reserved
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=exclusivity
- rule_text: ISI boxed warning text uses Avenir Heavy weight, which is reserved exclusively for this use; case per approved ISI, color Black #000000.
- intent: Reserve the Heavy weight to visually signal boxed warning severity.

### rule_ibsrela_isi_subheads_typography
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: ISI subheads (e.g. "INDICATION", "IMPORTANT SAFETY INFORMATION") must be set in Avenir, Black weight, ALL CAPS, colored Black #000000.
- intent: Consistent ISI subhead treatment.

### rule_ibsrela_footnotes_end_matter_typography
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: Footnotes / end matter must be set in Avenir, Book weight, Sentence case, colored Black #000000.
- intent: Consistent footnote typography.

### rule_ibsrela_campaign_headline_typography
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Campaign headlines (e.g. "FLIP THE SCRIPT") must be set in Avenir, Black weight, ALL CAPS, colored per the campaign palette.
- intent: Consistent campaign headline treatment.

### rule_ibsrela_callouts_ctas_typography
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['callout', 'cta'] constraint=None
- rule_text: Callouts and CTAs must be set in Avenir, ALL CAPS; weight is Black for callouts and per button spec for CTAs; color per callout/button spec.
- intent: Consistent callout and CTA typographic treatment.

### rule_ibsrela_avenir_to_arial_substitution_map
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The system font replacement for Avenir is Arial, which must be used when designing emails and PowerPoint presentations. Map weights: Avenir Black → Arial Bold; Avenir Heavy → Arial Bold; Avenir Roman → Arial Regular; Avenir Book → Arial Regular (or reduce size 1pt for footnote distinction).
- intent: Ensure reliable rendering where Avenir is unavailable.

### rule_ibsrela_email_font_stack_no_avenir_webfont
- class=typography scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: [BASELINE] Email font stack is `Arial, Helvetica, sans-serif`. Never load Avenir via webfont in email (rendering inconsistency in Outlook/SFMC); Arial is the brand-sanctioned substitute.
- intent: Avoid webfont rendering failures in email clients.
