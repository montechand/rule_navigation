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

### rule_lisraya_brand_accent_shape_asymmetric_radius
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: The brand's core container device is a rectangle with selectively enlarged opposite corner radii (a 5:1 radius ratio): apply the large radius to one diagonal pair of corners and the small (6px email) radius to the other pair, while the other two corners keep only the slight radius. It houses callout text and photography and reads modern and optimistic. Approved radius pairs are cataloged per surface — print: 1.25" & 0.0625" (large containers/photos), 0.5" & 0.0625" (banners), 0.4375" & 0.0625" (small callout boxes); email @96dpi: 120px & 6px (large), 48px & 6px (banner), 42px & 6px (callout).
- intent: Establish the signature asymmetric accent-shape container as the consistent brand device for callouts and photography.

### rule_lisraya_accent_shape_diagonal_consistency
- class=imagery scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Be consistent within an email: use the same diagonal orientation of the accent shape across all sections. Default: large radius on top-left & bottom-right, 6px radius on the other pair.
- intent: Keep accent-shape orientation uniform across an email for visual coherence.

### rule_lisraya_charts_tables_uniform_corners
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=['chart'] constraint=binding
- rule_text: Exception: charts and tables use uniform rounded corners on all four corners (12px uniform radius), NOT the asymmetric brand accent shape.
- intent: Distinguish data containers from the accent-shape device with uniform corners.
