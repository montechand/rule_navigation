# Review: grp_lisraya_color_scheme_rules_01

doc_ref: `color_scheme_rules[1]`

## Original text

````
### Hierarchy & Application
- Apply the palette in the **primary > secondary > tertiary ratio** shown in the guide: blues and golds dominate; tertiary colors are accents and surfaces.
- **Headlines/headings:** Brand Blue (or White on dark/gradient backgrounds).
- **Body text:** Graphite #212121 on light backgrounds; White on dark backgrounds (with increased line height, §1.2).
- **Charts/about:blank** Brand Blue + Sky Blue dominant; **Sunshine/Gold strictly reserved for emphasizing key figures**; gray for placebo.
- **Callout surfaces:** Light Blue at 70% tint (data callouts); Golden Sand at 30% tint (text-heavy callouts).
- **Coral:** sparing tertiary accent only — never for primary CTAs, headlines, or data. **[GENERAL]:** avoid Coral in email sections unless the brief calls for it.
- **Links [GENERAL]:** Brand Blue #00529b, underlined, on light backgrounds; White underlined on dark.
- The logo icon's **70% transparency of Pantone 7548 C / #ffc60a must be maintained in all instances** (logo, and when the mark is used as a pattern/graphic).
````

## Extracted rules (7)

### rule_lisraya_palette_usage_hierarchy_2
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Apply the palette in the primary > secondary > tertiary usage ratio (palette.usage_ratio): blues and golds dominate; tertiary colors are used as accents and surfaces only.
- intent: Preserve brand color balance so primary blues/golds lead and tertiary colors stay as accents.

### rule_lisraya_headline_body_text_colors
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Headlines/headings use Brand Blue (or White on dark/gradient backgrounds) via headline.color; body text uses Graphite on light backgrounds and White on dark backgrounds via body.color, with increased line height on dark backgrounds (body.line_height). Light/dark switching is carried by the token variants.
- intent: Ensure legible, on-brand text colors across light and dark backgrounds.

### rule_lisraya_chart_color_roles
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: In charts, Brand Blue + Sky Blue are the dominant series colors (chart.series.color) and gray is used for placebo (chart.placebo.color). Sunshine/Gold is strictly reserved for emphasizing key figures (chart.emphasis.color) and must not be used for non-emphasis series.
- intent: Keep chart color coding consistent so emphasis gold reads as significance, not decoration.

### rule_lisraya_callout_surface_tints
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Callout surfaces use Light Blue at 70% tint for data callouts (callout.data.fill / opacity) and Golden Sand at 30% tint for text-heavy callouts (callout.text_heavy.fill / opacity).
- intent: Distinguish data vs text-heavy callouts with consistent branded surface tints.

### rule_lisraya_coral_sparing_accent_only
- class=color_application scope=brand hardness=strong_default polarity=must_not sections=None constraint=exclusivity
- rule_text: Coral is a sparing tertiary accent only — never use it for primary CTAs, headlines, or data. [GENERAL] Avoid Coral in email sections unless the brief calls for it.
- intent: Prevent overuse or misapplication of Coral outside its accent role.

### rule_lisraya_link_styling
- class=color_application scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Links are Brand Blue #00529b, underlined, on light backgrounds; White underlined on dark backgrounds. Color switching is carried by the body.link.color token variants; underline decoration is bound via body.link.decoration.
- intent: Ensure links are consistently identifiable and legible on any background.

### rule_lisraya_logo_mark_gold_opacity_locked
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding governance=trademark/verbatim_only
- rule_text: The logo icon's 70% transparency of Pantone 7548 C / #ffc60a (logo.mark.gold_opacity) must be maintained in all instances — for the logo and when the mark is used as a pattern/graphic.
- intent: Protect the trademarked logo mark treatment across all uses.
