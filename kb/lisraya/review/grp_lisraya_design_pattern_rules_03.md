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

### rule_lisraya_brand_accent_shape_container_device
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: The core brand accent shape is a rectangle with selectively enlarged opposite corner radii (large radius on one diagonal pair, slight radius on the other), used to house callout text and photography, reading modern and optimistic. Approved radius pairs are cataloged per surface (print large 1.25"&0.0625", banner 0.5"&0.0625", callout 0.4375"&0.0625"; email large 120px&6px, banner 48px&6px, callout 42px&6px). Apply the large radius to one diagonal pair (e.g. top-left + bottom-right) and the 6px/slight radius to the other pair.
- intent: Establish the signature asymmetric accent-shape container as the brand's core housing device.

### rule_lisraya_accent_shape_diagonal_consistency
- class=imagery scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Be consistent within an email: use the same diagonal orientation of the accent-shape corner radii across all sections. Default: large radius on top-left & bottom-right.
- intent: Keep accent-shape orientation uniform across an email for visual coherence.

### rule_lisraya_chart_table_uniform_corner_radius_exception
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Exception: charts and tables use uniform rounded corners on all four corners (12px uniform radius), not the asymmetric accent shape.
- intent: Charts/tables use a uniform radius container instead of the asymmetric accent device.
