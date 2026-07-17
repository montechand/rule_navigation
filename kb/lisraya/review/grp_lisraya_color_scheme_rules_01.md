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

### rule_lisraya_rule_lisraya_callout_surface_tints
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=exclusivity
- rule_text: Do not use any ad-hoc tints. Use only standard brand palette values or specified design system tints.
- intent: Differentiate clinical data vs editorial content blocks using background tint styling.

### rule_lisraya_rule_lisraya_chart_statistical_callouts
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: In charts and data presentations, Brand Blue and Sky Blue must dominate. Sunshine/Gold (color.primary.sunshine = #faa31b) is strictly reserved for emphasizing key figures, while gray must be used for the placebo representation.
- intent: Maintain clean, regulatory-compliant clinical data charts with specific color cues for key statistics.

### rule_lisraya_rule_lisraya_color_hierarchy_ratio
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Apply the color palette in the primary > secondary > tertiary ratio shown in the guide, ensuring that blues and golds dominate, while tertiary colors are reserved as accents and surfaces.
- intent: Maintain the overall brand-defining color ratio across all designs.

### rule_lisraya_rule_lisraya_coral_accent_restriction
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Coral (color.tertiary.coral = #F26A38) must only be used as a sparing tertiary accent and never for primary CTAs, headlines, or clinical data. Avoid using Coral entirely in email sections unless specified by the design brief.
- intent: Prevent overuse of high-contrast accent red/orange in standard layouts.

### rule_lisraya_rule_lisraya_headline_and_body_color_binding
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Headlines and headings must use Brand Blue (headline.color = #00529b) on light backgrounds, or White (#ffffff) on dark or gradient backgrounds. Body text must use Graphite (body.color = #212121) on light backgrounds, or White (#ffffff) on dark backgrounds.
- intent: Ensure optimal readability and visual hierarchy through standardized heading and body text color rules.

### rule_lisraya_rule_lisraya_link_color_binding
- class=color_application scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Hyperlinks must be underlined. Use Brand Blue (body.link.color = #00529b) on light backgrounds, and White (#ffffff) on dark backgrounds.
- intent: Maintain accessible and cohesive interactive link styling across light and dark backgrounds.

### rule_lisraya_rule_lisraya_logo_transparency_preservation
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding governance=trademark/verbatim_only
- rule_text: The logo icon's 70% transparency level on its gold color (Pantone 7548 C / #ffc60a) must be preserved in all occurrences, including standard logos and decorative mark patterns/graphics.
- intent: Protect trademarked brand assets from alterations.
