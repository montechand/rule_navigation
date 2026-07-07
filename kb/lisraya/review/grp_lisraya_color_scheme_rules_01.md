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

## Extracted rules (8)

### rule_lisraya_palette_usage_ratio
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Apply the palette in the primary > secondary > tertiary ratio: blues and golds dominate; tertiary colors are accents and surfaces.
- intent: Preserve brand color balance with primary hues dominant.

### rule_lisraya_headline_body_color_application
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines/headings use Brand Blue (or White on dark/gradient backgrounds). Body text uses Graphite #212121 on light backgrounds; White on dark backgrounds with increased line height. Background-driven variants are carried on the semantic tokens.
- intent: Ensure legible, on-brand text color per background.

### rule_lisraya_chart_color_application
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: In charts, Brand Blue + Sky Blue are the dominant series colors; Sunshine/Gold is strictly reserved for emphasizing key figures; gray is used for placebo.
- intent: Keep emphasis color meaningful and consistent in data viz.

### rule_lisraya_chart_emphasis_color_reserved
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: Sunshine/Gold is strictly reserved for emphasizing key figures in charts and must not be used for general chart series.
- intent: Preserve the signal value of the emphasis color.

### rule_lisraya_callout_surface_tints
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Callout surfaces: Light Blue at 70% tint for data callouts; Golden Sand at 30% tint for text-heavy callouts.
- intent: Differentiate callout types via consistent surface tints.

### rule_lisraya_coral_restricted_accent
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Coral is a sparing tertiary accent only — never for primary CTAs, headlines, or data. [GENERAL] Avoid Coral in email sections unless the brief calls for it.
- intent: Restrict Coral to occasional accent use.

### rule_lisraya_link_color_and_decoration
- class=color_application scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Links: Brand Blue #00529b, underlined, on light backgrounds; White underlined on dark backgrounds. Background variants carried on the semantic tokens.
- intent: Keep links recognizable and accessible on all backgrounds.

### rule_lisraya_logo_gold_opacity_maintained
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The logo icon's 70% transparency of Pantone 7548 C / #ffc60a must be maintained in all instances (logo, and when the mark is used as a pattern/graphic).
- intent: Protect the fixed logo mark treatment.
