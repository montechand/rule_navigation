# Build warnings

- tok_lisraya_motion_transitions: duplicate token id (primitive/semantic collision); kept first
- gov_lisraya_inclusive_language: audience='patient' not in vocab; -> None
- tgr_lisraya_moa_statements: template_group has no members; pruned
- token dedupe: merged 11 exact duplicates
- rule_lisraya_charts_tables_uniform_corners: tags dropped invalid ['chart']
- rule_lisraya_chart_container_style: rule_class='chart' not in vocab; -> 'layout'
- rule_lisraya_chart_color_logic: tags dropped invalid ['chart']
- rule_lisraya_chart_bar_icon_shape: rule_class='chart' not in vocab; -> 'layout'
- rule_lisraya_chart_headline_style: tags dropped invalid ['chart']
- rule_lisraya_chart_stat_callout_hierarchy: tags dropped invalid ['chart']
- rule_lisraya_chart_footnote_treatment: tags dropped invalid ['chart']
- rule_lisraya_canonical_content_block_pattern: tags dropped invalid ['patient_story']