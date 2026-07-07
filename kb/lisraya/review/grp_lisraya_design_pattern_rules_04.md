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

## Extracted rules (6)

### rule_lisraya_chart_container_style
- class=imagery scope=brand hardness=strong_default polarity=must sections=['chart', 'efficacy'] constraint=binding
- rule_text: Charts and infographics must be clean, easy to scan, and consistent with the system. The container uses uniform rounded corners with a Light Blue (#E6F0F9) panel fill and a Brand Blue rounded header bar (chart.container.radius, chart.panel.fill, chart.header.fill).
- intent: Keep chart containers visually consistent and legible across the system.

### rule_lisraya_chart_color_logic
- class=color_application scope=brand hardness=strong_default polarity=must sections=['chart', 'efficacy'] constraint=binding
- rule_text: Chart color logic: Brand Blue (#00529b) and Sky Blue (#358CCB) are dominant; Sunshine (#faa31b) and Gold (#ffc60a) are reserved for emphasis on key figures/data points only (chart.series.dominant_color / emphasis_color). Placebo/comparator series use neutral gray (chart.series.placebo_color).
- intent: Reserve warm accent colors for genuine data emphasis so hierarchy reads clearly.

### rule_lisraya_chart_bar_icon_shape
- class=imagery scope=brand hardness=strong_default polarity=must sections=['chart', 'efficacy'] constraint=binding
- rule_text: Bars and chart icons use rounded, approachable shapes (rounded bar tops) per chart.bar.style.
- intent: Maintain the approachable, rounded brand feel in data visuals.

### rule_lisraya_chart_headline_style
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart', 'efficacy'] constraint=binding
- rule_text: Chart headlines are set in Agenda (print) / Nunito Sans Bold+ (email), ALL CAPS, Brand Blue, with a thin Gold rule beneath (chart.header.font, chart.header.case, chart.header.color, chart.header.rule_color).
- intent: Give charts a consistent, branded heading treatment.

### rule_lisraya_chart_statistical_callout_hierarchy
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart', 'efficacy'] constraint=binding
- rule_text: Statistical callouts must be large and bold — the % figure is the hero — with supporting copy set in a lighter weight beneath (chart.stat_callout.weight).
- intent: Make the headline statistic the visual focal point of the chart.

### rule_lisraya_chart_footnote_separation
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart', 'efficacy'] constraint=binding
- rule_text: Footnotes in charts must be noticeably smaller and clearly separated from the primary data (footnote.type_scale).
- intent: Keep supporting/reference text subordinate to and distinct from headline data.
