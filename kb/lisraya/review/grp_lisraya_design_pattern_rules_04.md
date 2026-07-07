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

### rule_lisraya_chart_container_structure
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Charts and infographics must be clean, easy to scan, and consistent with the system. Container uses uniform rounded corners (chart.container.radius) with a Light Blue panel fill (chart.panel.fill) and a Brand Blue rounded header bar (chart.header.fill).
- intent: Keep data visualizations visually consistent and legible within the brand system.

### rule_lisraya_chart_color_logic
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: Chart color logic: Brand Blue and Sky Blue are dominant series colors (chart.series.dominant_color); Sunshine and Gold (chart.emphasis.color) are reserved for emphasis on key figures/data points only. Placebo/comparator series use neutral gray (chart.placebo.color).
- intent: Direct viewer attention to key data using reserved emphasis colors while keeping dominant/comparator series neutral.

### rule_lisraya_chart_bars_style
- class=layout scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Bars and chart icons must use rounded, approachable shapes (rounded bar tops), per chart.bars.style.
- intent: Reinforce the warm, approachable brand tone in data visuals.

### rule_lisraya_chart_headline_treatment
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Chart headline uses Agenda (print) / Nunito Sans Bold+ (email) per chart.header.font, set ALL CAPS (chart.header.case), in Brand Blue (chart.header.color), with a thin Gold rule beneath (chart.header.rule_color).
- intent: Standardize chart headers so they read as branded, scannable labels.

### rule_lisraya_chart_stat_callout_style
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Statistical callouts are large and bold with the % figure as the hero; supporting copy sits beneath in a lighter weight (chart.stat_callout.style).
- intent: Make key statistics the visual focal point of a chart.

### rule_lisraya_chart_footnote_treatment
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart footnotes are noticeably smaller (chart.footnote.size) and clearly separated from the primary data.
- intent: Keep footnotes legible but visually subordinate and distinct from core data.
