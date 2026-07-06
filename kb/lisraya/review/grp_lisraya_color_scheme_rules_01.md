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

## Extracted rules (10)

### rule_lisraya_palette_ratio_hierarchy
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=ordering
- rule_text: Apply the palette in the primary > secondary > tertiary ratio shown in the guide: blues and golds dominate; tertiary colors are used as accents and surfaces.
- intent: Preserve palette hierarchy so brand colors dominate over accents.

### rule_lisraya_headline_color
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Headlines and headings use Brand Blue (#00529b), or White (#ffffff) on dark/gradient backgrounds.
- intent: Ensure consistent, legible headline coloring across background contexts.

### rule_lisraya_body_text_color
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Body text is Graphite #212121 on light backgrounds; White on dark backgrounds (with increased line height per §1.2).
- intent: Maintain readable body text contrast on all background types.

### rule_lisraya_chart_color_scheme
- class=color_application scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=None
- rule_text: In charts, Brand Blue (#00529b) + Sky Blue (#358CCB) are dominant; gray is used for placebo. See chart_sunshine_gold_key_figures for Sunshine/Gold restriction.
- intent: Keep chart coloring consistent and reserve warm colors for emphasis.

### rule_lisraya_chart_sunshine_gold_key_figures
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: In charts, Sunshine and Gold are strictly reserved for emphasizing key figures only.
- intent: Draw attention to key data points without diluting warm-color emphasis.

### rule_lisraya_callout_surface_tints
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Callout surfaces use Light Blue at 70% tint for data callouts, and Golden Sand at 30% tint for text-heavy callouts.
- intent: Differentiate data vs text callouts with consistent tinted surfaces.

### rule_lisraya_coral_sparing_accent_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Coral is a sparing tertiary accent only — never use it for primary CTAs, headlines, or data.
- intent: Restrict Coral to prevent overuse and off-brand emphasis.

### rule_lisraya_coral_avoid_in_email
- class=color_application scope=org_baseline hardness=strong_default polarity=should_not sections=None constraint=None
- rule_text: [GENERAL] Avoid Coral in email sections unless the brief specifically calls for it.
- intent: Keep email sections on the core blue/gold palette by default.

### rule_lisraya_link_styling
- class=color_application scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Links are Brand Blue #00529b and underlined on light backgrounds; White and underlined on dark backgrounds.
- intent: Ensure links are recognizable and legible on any background.

### rule_lisraya_logo_mark_gold_transparency
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The logo icon's 70% transparency of Pantone 7548 C / #ffc60a must be maintained in all instances (logo, and when the mark is used as a pattern/graphic).
- intent: Preserve consistent logo mark appearance everywhere it appears.
