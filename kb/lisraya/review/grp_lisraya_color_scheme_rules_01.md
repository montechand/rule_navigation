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

## Extracted rules (3)

### rule_lisraya_chart_palette_and_key_figure_emphasis
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: In charts, Brand Blue (#00529b) and Sky Blue (#358ccb) are dominant; Sunshine (#faa31b) and Gold (#ffc60a) are strictly reserved for emphasizing key figures, and gray represents placebo.
- intent: Keep data visualizations consistent and reserve warm colors for meaningful emphasis.

### rule_lisraya_hierarchy_application_table_binding
- class=assembly scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: The Hierarchy & Application table is a closed, brand-approved set; every row binds its listed values exactly as specified. Do not invent or alter rows.

| item | value |
|---|---|
| Body text | ** Graphite #212121 on light backgrounds; White on dark backgrounds (with increased line height, §1.2). |
| Callout surfaces | ** Light Blue at 70% tint (data callouts); Golden Sand at 30% tint (text-heavy callouts). |
| Links [GENERAL] | ** Brand Blue #00529b, underlined, on light backgrounds; White underlined on dark. |
- intent: Bind the Hierarchy & Application table values verbatim.

### rule_lisraya_palette_hierarchy_application
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Apply the palette in the primary > secondary > tertiary ratio shown in the guide: blues and golds dominate, while tertiary colors serve as accents and surfaces.
- intent: Maintain the intended visual hierarchy of the brand palette.
