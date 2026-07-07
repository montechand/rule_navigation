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

## Extracted rules (6)

### rule_lisraya_palette_application_hierarchy
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Apply the palette in the primary > secondary > tertiary ratio shown in the guide: blues and golds dominate; tertiary colors are accents and surfaces.
- intent: Preserve brand color balance with blues/golds dominant.

### rule_lisraya_headline_body_link_color_by_background
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Headlines/headings use Brand Blue (or White on dark/gradient backgrounds). Body text uses Graphite #212121 on light backgrounds; White on dark backgrounds (with increased line height per §1.2). Links [GENERAL] use Brand Blue #00529b, underlined, on light backgrounds; White underlined on dark. Light/dark variants are carried by the bound semantic tokens' background_group switching.
- intent: Ensure legible, on-brand text/link color across light and dark backgrounds.

### rule_lisraya_chart_color_emphasis_logic
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: In charts, Brand Blue + Sky Blue are dominant; Sunshine/Gold are strictly reserved for emphasizing key figures; gray is used for placebo. See chart.color_logic, chart.emphasis.color, chart.placebo.color.
- intent: Keep chart emphasis colors meaningful and reserved for key data.

### rule_lisraya_callout_surface_tints
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Callout surfaces: Light Blue at 70% tint for data callouts; Golden Sand at 30% tint for text-heavy callouts.
- intent: Distinguish data vs text-heavy callout surfaces via consistent tints.

### rule_lisraya_coral_accent_restriction
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Coral is a sparing tertiary accent only — never for primary CTAs, headlines, or data. [GENERAL] Avoid Coral in email sections unless the brief calls for it.
- intent: Prevent misuse of Coral outside its restricted accent role.

### rule_lisraya_logo_mark_opacity_maintained
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The logo icon's 70% transparency of Pantone 7548 C / #ffc60a must be maintained in all instances (logo, and when the mark is used as a pattern/graphic).
- intent: Preserve the signature logo mark transparency wherever it appears.
