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

### rule_lisraya_chart_color_logic
- class=color_application scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=exclusivity
- rule_text: Chart color logic: Brand Blue (#00529b) and Sky Blue (#358CCB) dominant; Sunshine (#faa31b) and Gold (#ffc60a) reserved for emphasis on key figures/data points only. Placebo/comparator bars use neutral gray (chart.color.placebo = gray).
- intent: Preserve a restrained, hierarchical chart palette that spotlights key data.

### rule_lisraya_chart_container_construction
- class=color_application scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart containers are clean, easy to scan, and consistent with the system: a Light Blue (chart.container.fill = #E6F0F9) panel with uniform rounded corners (radius.chart.uniform = 12px) and a Brand Blue (chart.header.fill = #00529b) rounded header bar.
- intent: Keep charts visually consistent with the brand system.

### rule_lisraya_chart_headline_treatment
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart headlines set in Agenda (print) / Nunito Sans Bold+ (email), ALL CAPS, Brand Blue (chart.headline.color = #00529b), with a thin Gold (chart.headline.rule_color = #ffc60a) rule beneath.
- intent: Give chart headlines a consistent, recognizable brand treatment.

### rule_lisraya_chart_rounded_bar_shapes
- class=iconography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Bars and chart icons use rounded, approachable shapes with rounded bar tops (chart.bars.shape = rounded).
- intent: Convey an approachable brand feel through rounded chart geometry.

### rule_lisraya_chart_statistical_callout_hierarchy
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=None
- rule_text: Statistical callouts are large and bold — the % figure is the hero — with supporting copy in a lighter weight beneath. Footnotes are noticeably smaller and clearly separated from primary data.
- intent: Establish clear visual hierarchy that spotlights the key statistic.
