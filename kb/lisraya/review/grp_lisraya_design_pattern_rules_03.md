# Review: grp_lisraya_design_pattern_rules_03

doc_ref: `design_pattern_rules[3]`

## Original text

````
### Brand Accent Shape (core container device)
- A rectangle with **selectively enlarged opposite corner radii**; the other two corners keep a slight radius. Used to house callout text and photography. Reads modern and optimistic.
- Approved radius pairs (print): **1.25" & 0.0625"** (large containers/photos), **0.5" & 0.0625"** (banners), **0.4375" & 0.0625"** (small callout boxes).
- **[GENERAL] Email px conversions (at 96dpi):** large: 120px & 6px; banner: 48px & 6px; callout: 42px & 6px. Apply the large radius to one diagonal pair (e.g., top-left + bottom-right), the 6px radius to the other pair. Be consistent within an email: same diagonal orientation across all sections (default: large radius top-left & bottom-right).
- **Exception: charts and tables use uniform rounded corners on all four corners** (not the asymmetric accent shape). [GENERAL: 12px uniform radius.]
````

## Extracted rules (3)

### rule_lisraya_accent_shape_asymmetric_radius
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The Brand Accent Shape is a rectangle with selectively enlarged opposite corner radii (the large radius on one diagonal pair, a slight ~6px radius on the other), used to house callout text and photography. Use only the approved radius pairs: print large 1.25" & 0.0625" (large containers/photos), banner 0.5" & 0.0625", small callout 0.4375" & 0.0625"; email px conversions at 96dpi are large 120px & 6px, banner 48px & 6px, callout 42px & 6px. Apply the large radius to one diagonal pair (e.g. top-left + bottom-right) and the 6px radius to the other pair.
- intent: Preserve the signature asymmetric accent-shape container device that reads modern and optimistic.

### rule_lisraya_accent_shape_consistent_orientation
- class=imagery scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Be consistent within an email: use the same diagonal orientation for the accent-shape radius across all sections. Default: large radius on top-left & bottom-right.
- intent: Ensure visual coherence of the accent shape across a single email.

### rule_lisraya_chart_table_uniform_radius_exception
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Exception: charts and tables use uniform rounded corners on all four corners (12px uniform radius), not the asymmetric accent shape.
- intent: Distinguish data containers from the branded accent-shape device for legibility.
