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

### rule_lisraya_callout_surface_tints
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=binding
- rule_text: Callout surfaces use Light Blue at 70% tint (opacity.callout.light_blue_70 = 0.7) for data callouts, and Golden Sand at 30% tint (opacity.callout.golden_sand_30 = 0.3) for text-heavy callouts.
- intent: Distinguish data vs. text-heavy callout surfaces with approved tints.

### rule_lisraya_chart_color_application
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart', 'efficacy'] constraint=exclusivity
- rule_text: In charts, Brand Blue (#00529b) + Sky Blue (#358CCB) dominate; Sunshine/Gold is strictly reserved for emphasizing key figures; placebo bars use gray (chart.color.placebo).
- intent: Keep chart colors legible and reserve gold as an emphasis-only signal.

### rule_lisraya_coral_sparing_accent_only
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Coral (#F26A38) is a sparing tertiary accent only — never for primary CTAs, headlines, or data. [GENERAL] Avoid Coral in email sections unless the brief calls for it.
- intent: Constrain Coral to rare accent use and keep it out of email unless briefed.

### rule_lisraya_link_color_by_background
- class=color_application scope=org_baseline hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: [GENERAL] Links are Brand Blue (body.link.color = #00529b), underlined (body.link.decoration = underline), on light backgrounds; White underlined on dark backgrounds.
- intent: Ensure links are consistently styled and legible against their background.

### rule_lisraya_logo_gold_transparency_maintained
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding governance=trademark/requires_qualifier
- rule_text: The logo icon's 70% transparency of Pantone 7548 C / #ffc60a (gold) must be maintained in all instances — in the logo, and when the mark is used as a pattern/graphic.
- intent: Protect trademark integrity of the logo mark's gold treatment.

### rule_lisraya_palette_hierarchy_application
- class=color_application scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Apply the palette in the primary > secondary > tertiary ratio: blues and golds dominate, tertiary colors are accents/surfaces. Headlines/headings use Brand Blue (headline.color = #00529b), or White on dark/gradient backgrounds. Body text is Graphite (body.color = #212121) on light backgrounds, White on dark backgrounds (with increased line height per §1.2).
- intent: Preserve the approved brand color hierarchy across headings and body.
