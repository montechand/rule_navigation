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
- class=layout scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Charts and infographics use a clean, scannable container consistent with the system: uniform rounded corners (chart.container.radius), a Light Blue panel fill (chart.panel.fill = #E6F0F9) with a Brand Blue rounded header bar (chart.header.fill = #00529b).
- intent: Keep data visualizations clean, scannable and on-system.

### rule_lisraya_chart_color_logic
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Chart color logic: Brand Blue (#00529b) and Sky Blue (#358CCB) are dominant for series; Sunshine (#faa31b) and Gold (#ffc60a) are reserved for emphasis on key figures/data points only. Placebo/comparator series use a neutral gray.
- intent: Reserve warm accents for emphasis so key data points stand out.

### rule_lisraya_chart_bar_icon_shape
- class=layout scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Bars and chart icons use rounded, approachable shapes (rounded bar tops).
- intent: Maintain the brand's warm, approachable visual character in data graphics.

### rule_lisraya_chart_headline_style
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart headlines are set in Agenda (print) / Nunito Sans Bold+ (email), ALL CAPS, Brand Blue, with a thin Gold rule beneath.
- intent: Give chart headings a consistent, branded, scannable treatment.

### rule_lisraya_chart_stat_callout_hierarchy
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Statistical callouts are large and bold — the % figure is the hero — with supporting copy in a lighter weight beneath.
- intent: Establish visual hierarchy that leads with the key statistic.

### rule_lisraya_chart_footnote_treatment
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart footnotes are noticeably smaller than primary data and clearly separated from it.
- intent: Distinguish supporting references from primary data without competing for attention.
