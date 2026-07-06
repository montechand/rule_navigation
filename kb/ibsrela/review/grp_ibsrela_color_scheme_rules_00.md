# Review: grp_ibsrela_color_scheme_rules_00

doc_ref: `color_scheme_rules[0]`

## Original text

````
### Branded palette (explicit — complete values)
 
| Color | HEX | RGB | CMYK | PMS | Usage ratio |
|---|---|---|---|---|---|
| **Purple** (primary) | `#92278F` | 146 / 39 / 143 | 50 / 100 / 0 / 0 | 2592 | 30% |
| **Dark Blue** (primary) | `#262262` | 38 / 34 / 98 | 100 / 100 / 25 / 25 | 2756 | 30% |
| **White** (primary) | `#FFFFFF` | 255 / 255 / 255 | 0 / 0 / 0 / 0 | Pantone Safe White | 20% |
| **Silver** (accent) | `#CFDCE3` | 207 / 220 / 227 | 18 / 7 / 7 / 0 | — | 15% |
| **Dark Gray** (accent) | `#567483` | 86 / 116 / 131 | 70 / 46 / 38 / 9 | — | within 15% band |
| **Green** (accent) | `#01A47E` | 1 / 164 / 126 | 81 / 10 / 66 / 0 | — | 5% |
 
- The three primary colors (Purple, Dark Blue, White) embody "creative reliability." **All branded pieces lean into these, with a slight preference for Purple.** Silver, Dark Gray, and Green are accents only.
- **Text color assignments (explicit):**Titles** → `#92278F`.** Headlines & subheads → `#262262`. Body copy & ISI → black (`#000000`; the guide prints "#00000" — a 5-digit typo; use `#000000`).
- [BASELINE] Never set body copy in Purple or Green; reserve Green for CTA fills and small accents; Dark Gray for charts/secondary UI only; never use Silver for text.
- Title is how the email starts. It should always be purple. The first line in the email should always be purple. No other text in the email can be purple colored. 
- If something needs to be highlighted on a white section in the body (not headings, sub-headings or titles), they need to be black colored and bold, you cannot use blue or purple color in the body section of a paragraph.
- There should be no instance of mixing two colors within the same sentence. Each sentence, be it a heading or body, needs to have only one color. 
````

## Extracted rules (11)

### rule_ibsrela_primary_color_ratios_purple_preference
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=cardinality
- rule_text: All branded pieces should lean into the three primary colors — Purple (#92278F, ~30%), Dark Blue (#262262, ~30%), and White (#FFFFFF, ~20%) — which embody 'creative reliability,' with a slight preference for Purple. Silver (#CFDCE3, ~15%), Dark Gray (#567483, within the 15% band), and Green (#01A47E, ~5%) are accents only.
- intent: Maintain brand color balance dominated by primary palette.

### rule_ibsrela_title_color_purple
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Titles must be set in Purple (#92278F). The title is how the email starts; the first line in the email should always be purple.
- intent: Anchor the brand color at the top of every email.

### rule_ibsrela_headlines_subheads_dark_blue
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines and subheads must be set in Dark Blue (#262262).
- intent: Consistent hierarchy color for secondary headings.

### rule_ibsrela_body_copy_isi_black
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy and ISI must be set in black (#000000). (The guide prints '#00000' — a 5-digit typo; use #000000.)
- intent: Ensure legible, correct body/ISI text color.

### rule_ibsrela_never_body_purple_or_green
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: [BASELINE] Never set body copy in Purple (#92278F) or Green (#01A47E).
- intent: Reserve accent/primary hues away from body text.

### rule_ibsrela_green_reserved_cta_accents
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: [BASELINE] Reserve Green (#01A47E) for CTA fills and small accents only.
- intent: Constrain Green to CTA/accent usage.

### rule_ibsrela_dark_gray_reserved_charts_ui
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: [BASELINE] Use Dark Gray (#567483) for charts and secondary UI only.
- intent: Constrain Dark Gray to chart/UI usage.

### rule_ibsrela_never_silver_for_text
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: [BASELINE] Never use Silver (#CFDCE3) for text.
- intent: Prevent low-contrast/illegible text.

### rule_ibsrela_purple_only_first_line
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: No text other than the title/first line may be colored Purple (#92278F). Purple text is reserved exclusively for the title.
- intent: Keep Purple exclusive to the opening title line.

### rule_ibsrela_white_section_highlight_black_bold
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: To highlight something within body paragraph copy on a white section (not headings, subheadings, or titles), it must be black (#000000) and bold; blue or purple may not be used to highlight within the body section of a paragraph.
- intent: Standardize in-body emphasis to black bold on white.

### rule_ibsrela_one_color_per_sentence
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: There must be no instance of mixing two colors within the same sentence. Each sentence, whether a heading or body, must use only one color.
- intent: Prevent multi-color text within a single sentence.
