# Review: grp_lisraya_design_pattern_rules_04

doc_ref: `design_pattern_rules[4]`

## Original text

````
### Charts & Infographics
- Clean, easy to scan, consistent with the system. Container: uniform rounded corners, Light Blue (#E6F0F9) panel with a Brand Blue rounded header bar.
- **Color logic: Brand Blue (#00529b) and Sky Blue (#358CCB) dominant; Sunshine (#faa31b) and Gold (#ffc60a) reserved for emphasis on key figures/data points only.** Placebo/comparator: neutral gray.
- Bars and chart icons: **rounded, approachable** shapes (rounded bar tops).
- Headline: Agenda (print) / Nunito Sans Bold+ (email), **ALL CAPS**, Brand Blue, with a thin Gold rule beneath.
- Statistical callouts: **large and bold** (the % figure is the hero), supporting copy in a **lighter weight beneath**.
- Footnotes: noticeably smaller, clearly separated from primary data.
````

## Extracted rules (5)

### rule_lisraya_chart_container_style
- class=layout scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart/infographic containers must be clean, easy to scan and consistent with the system: a Light Blue panel with uniform rounded corners and a Brand Blue rounded header bar.
- intent: Keep chart containers visually consistent and legible across the system.

### rule_lisraya_chart_color_logic
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: Chart color logic: Brand Blue and Sky Blue dominant; Sunshine and Gold reserved for emphasis on key figures/data points only; placebo/comparator uses neutral gray. Bound via chart.dominant.color, chart.emphasis.color and chart.placebo.color.
- intent: Protect the emphasis colors for the most important data and keep comparators neutral.

### rule_lisraya_chart_bar_icon_shape
- class=imagery scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=None
- rule_text: Bars and chart icons must use rounded, approachable shapes (e.g. rounded bar tops).
- intent: Reinforce the warm, approachable brand feel in data visualizations.

### rule_lisraya_chart_headline_style
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart headlines use Agenda (print) / Nunito Sans Bold+ (email), ALL CAPS, Brand Blue, with a thin Gold rule beneath.
- intent: Give chart headlines a consistent, branded treatment.

### rule_lisraya_chart_statistical_callout_hierarchy
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=None
- rule_text: Statistical callouts must be large and bold with the % figure as the hero, supporting copy in a lighter weight beneath. Footnotes must be noticeably smaller and clearly separated from primary data.
- intent: Establish a clear visual hierarchy from headline figure down to footnotes.
