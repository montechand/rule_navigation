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

## Extracted rules (2)

### rule_lisraya_chart_and_infographic_styling_and_hierarchy
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=None
- rule_text: Charts and infographics must use a clean, approachable style inside a Light Blue (#E6F0F9) panel with a Brand Blue (#00529b) rounded header bar. All bars and chart icons must feature rounded shapes (e.g. rounded bar tops). Structure headlines in ALL CAPS using Agenda/Nunito Sans Bold+ in Brand Blue (#00529b) with a thin Gold (#ffc60a) rule directly beneath. Statistical callouts must lead with a large, bold hero percentage figure, supported by lighter-weight copy positioned beneath. Footnotes must be noticeably smaller and clearly separated from primary data.
- intent: Maintain visual consistency, brand alignment, and hierarchy within all data-driven chart and infographic panels.

### rule_lisraya_chart_color_application_logic
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=exclusivity
- rule_text: In charts and infographics, Brand Blue (color.primary.brand_blue = #00529b) and Sky Blue (color.secondary.sky_blue = #358CCB) must be the dominant colors. Placebo or comparator data must use a neutral gray. Sunshine (color.primary.sunshine = #faa31b) and Gold (color.primary.gold = #ffc60a) are reserved exclusively for emphasizing key figures and data points.
- intent: Ensure data comparisons carry intuitive weight by restricting warm accent colors to critical data callouts.
