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

## Extracted rules (6)

### rule_ibsrela_branded_palette_usage_ratio
- class=color_application scope=brand hardness=strong_default polarity=should sections=None constraint=binding
- rule_text: The branded palette follows a 30/30/20/15/5 usage ratio (Purple 30%, Dark Blue 30%, White 20%, Silver 15% incl. Dark Gray, Green 5%). The three primary colors (Purple, Dark Blue, White) embody 'creative reliability'; all branded pieces lean into these with a slight preference for Purple. Silver, Dark Gray, and Green are accents only.
- intent: Preserve brand color balance and primary-color dominance.

### rule_ibsrela_accent_color_reservations
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=exclusivity
- rule_text: [BASELINE] Never set body copy in Purple or Green; reserve Green for CTA fills and small accents; Dark Gray for charts/secondary UI only; never use Silver for text.
- intent: Constrain accent colors to their reserved roles.

### rule_ibsrela_text_color_assignments
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Explicit text color assignments: Titles → Purple (#92278F); Headlines & subheads → Dark Blue (#262262); Body copy & ISI → black (#000000; the guide's '#00000' is a 5-digit typo, use #000000).
- intent: Bind each text role to its mandated color.

### rule_ibsrela_title_purple_only
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['hero'] constraint=exclusivity
- rule_text: The title is how the email starts and should always be purple; the first line in the email should always be purple. No other text in the email may be purple colored.
- intent: Reserve purple text exclusively for the opening title line.

### rule_ibsrela_white_section_highlight_black_bold
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: If something needs to be highlighted on a white section in the body (not headings, sub-headings or titles), it must be black colored and bold; blue or purple color cannot be used in the body section of a paragraph.
- intent: Emphasize body text with black bold, never colored, on white sections.

### rule_ibsrela_one_color_per_sentence
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: There should be no instance of mixing two colors within the same sentence. Each sentence, whether a heading or body, must have only one color.
- intent: Enforce single-color sentences for visual consistency.
