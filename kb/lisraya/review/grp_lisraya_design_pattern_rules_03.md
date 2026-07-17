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

## Extracted rules (1)

### rule_lisraya_brand_accent_shape_core_container_device_table_b
- class=assembly scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: The Brand Accent Shape (core container device) table is a closed, brand-approved set; every row binds its listed values exactly as specified. Do not invent or alter rows.

| item | value |
|---|---|
| Approved radius pairs (print) | **1.25" & 0.0625"** (large containers/photos), **0.5" & 0.0625"** (banners), **0.4375" & 0.0625"** (small callout boxes). |
| [GENERAL] Email px conversions (at 96dpi) | ** large: 120px & 6px; banner: 48px & 6px; callout: 42px & 6px. Apply the large radius to one diagonal pair (e.g., top-left + bottom-right), the 6px radius to the other pair. Be consistent within an email: same diagonal orientation across all sections (default: large radius top-left & bottom-right). |
| Exception | charts and tables use uniform rounded corners on all four corners** (not the asymmetric accent shape). [GENERAL: 12px uniform radius.] |
- intent: Bind the Brand Accent Shape (core container device) table values verbatim.
