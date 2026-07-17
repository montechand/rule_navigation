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

## Extracted rules (3)

### rule_lisraya_chart_color_emphasis_logic
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: In charts and infographics, Brand Blue (#00529b) and Sky Blue (#358CCB) are dominant. Reserve Sunshine (#faa31b) and Gold (#ffc60a) for emphasis on key figures or data points only; render placebo/comparator data in neutral gray.
- intent: Create a disciplined data hierarchy and distinguish comparator data.

### rule_lisraya_chart_container_and_bar_geometry
- class=layout scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Charts and infographics use a clean, easy-to-scan container: a Light Blue (#E6F0F9) rounded panel with a rounded Brand Blue (#00529b) header bar. Bars and chart icons use rounded, approachable shapes, including rounded bar tops.
- intent: Keep data displays consistent, approachable, and readily scannable.

### rule_lisraya_chart_data_and_footnote_hierarchy
- class=typography scope=brand hardness=strong_default polarity=should sections=['chart'] constraint=None
- rule_text: In chart statistical callouts, make the percentage figure large and bold as the hero, with supporting copy beneath in a lighter weight. Make footnotes noticeably smaller and clearly separated from primary data.
- intent: Prioritize the key statistic while keeping supporting and reference information legible.
