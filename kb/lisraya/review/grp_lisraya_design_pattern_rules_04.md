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

## Extracted rules (8)

### rule_lisraya_chart_container_style
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Chart and infographic containers use uniform rounded corners (12px), a Light Blue (#E6F0F9) panel, and a Brand Blue (#00529b) rounded header bar.
- intent: Keep charts clean, scannable, and consistent with the visual system.

### rule_lisraya_chart_color_logic_dominant_blues
- class=color_application scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: In charts, Brand Blue (#00529b) and Sky Blue (#358CCB) are dominant for data.
- intent: Maintain palette hierarchy in data visualization.

### rule_lisraya_chart_warm_colors_reserved_for_emphasis
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: In charts, Sunshine (#faa31b) and Gold (#ffc60a) are reserved for emphasis on key figures/data points only.
- intent: Preserve warm accents as emphasis signals, not general fills.

### rule_lisraya_chart_placebo_comparator_gray
- class=color_application scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Placebo/comparator data in charts uses a neutral gray.
- intent: Visually subordinate comparator data.

### rule_lisraya_chart_rounded_bars_and_icons
- class=iconography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=None
- rule_text: Chart bars and chart icons use rounded, approachable shapes (rounded bar tops).
- intent: Reinforce the brand's warm, approachable visual character.

### rule_lisraya_chart_headline_style
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Chart headlines use Agenda (print) / Nunito Sans Bold or heavier (email), set in ALL CAPS, Brand Blue (#00529b), with a thin Gold rule beneath.
- intent: Consistent, on-brand chart titling.

### rule_lisraya_chart_statistical_callout_hierarchy
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=None
- rule_text: Statistical callouts are large and bold with the % figure as the hero; supporting copy is set in a lighter weight beneath.
- intent: Make the key data point the focal point.

### rule_lisraya_chart_footnote_style
- class=typography scope=brand hardness=strong_default polarity=must sections=['chart'] constraint=binding
- rule_text: Chart footnotes are noticeably smaller and clearly separated from the primary data.
- intent: Keep footnotes legible but subordinate and separated per disclosure practice.
