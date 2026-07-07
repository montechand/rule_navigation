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

### rule_lisraya_palette_hierarchy_ratio_2
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Apply the palette in the primary > secondary > tertiary ratio: blues and golds dominate; tertiary colors are used only as accents and surfaces.
- intent: Preserve brand color dominance and visual hierarchy.

### rule_lisraya_headline_body_link_color_application
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Headlines/headings use Brand Blue (or White on dark/gradient backgrounds). Body text is Graphite #212121 on light backgrounds and White on dark backgrounds (with increased line height on dark). Links are Brand Blue #00529b underlined on light backgrounds; White underlined on dark. Background-driven light/dark switching is carried by the semantic tokens.
- intent: Ensure consistent, legible text and link colors keyed to background.

### rule_lisraya_chart_series_color_roles
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart', 'efficacy'] constraint=binding
- rule_text: In charts, Brand Blue + Sky Blue are the dominant series colors; Sunshine/Gold is strictly reserved for emphasizing key figures only; gray is used for placebo.
- intent: Reserve emphasis color so charts read consistently and truthfully.

### rule_lisraya_gold_sunshine_emphasis_exclusivity
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart', 'efficacy'] constraint=exclusivity
- rule_text: Sunshine/Gold is strictly reserved for emphasizing key figures in charts and must not be used for other chart series.
- intent: Keep emphasis color meaningful and non-decorative.

### rule_lisraya_callout_surface_tints
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Callout surfaces use Light Blue at 70% tint for data callouts and Golden Sand at 30% tint for text-heavy callouts.
- intent: Standardize callout surface fills.

### rule_lisraya_coral_sparing_restriction
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Coral is a sparing tertiary accent only — never for primary CTAs, headlines, or data. [GENERAL] Avoid Coral in email sections unless the brief calls for it.
- intent: Limit Coral to rare accents so it never competes with primary brand color.

### rule_lisraya_logo_mark_70_transparency
- class=iconography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The logo icon's 70% transparency of Pantone 7548 C / #ffc60a must be maintained in all instances (logo, and when the mark is used as a pattern/graphic).
- intent: Preserve trademarked logo mark treatment across all uses.
