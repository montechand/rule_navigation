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

### rule_lisraya_accent_shape_asymmetric_corners
- class=layout scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The Brand Accent Shape is a rectangle with selectively enlarged opposite corner radii while the other two corners keep a slight radius; it houses callout text and photography. Approved radius pairs (print): 1.25" & 0.0625" for large containers/photos, 0.5" & 0.0625" for banners, and 0.4375" & 0.0625" for small callout boxes. Email px conversions at 96dpi: large 120px & 6px, banner 48px & 6px, callout 42px & 6px. Apply the large radius to one diagonal pair (e.g., top-left + bottom-right) and the 6px radius to the other pair.
- intent: Preserve the signature accent-shape container device with locked radius specs.

### rule_lisraya_accent_shape_consistent_orientation
- class=layout scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Be consistent within an email: use the same diagonal orientation of the accent shape across all sections. Default: large radius on top-left & bottom-right, 6px radius on the other pair.
- intent: Keep accent-shape orientation consistent across an email for visual coherence.

### rule_lisraya_charts_tables_uniform_radius
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Exception to the asymmetric accent shape: charts and tables use uniform rounded corners on all four corners (12px uniform radius), not the asymmetric accent shape.
- intent: Ensure charts/tables read as data containers with uniform corners.
