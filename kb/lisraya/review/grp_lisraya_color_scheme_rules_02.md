# Review: grp_lisraya_color_scheme_rules_02

doc_ref: `color_scheme_rules[2]`

## Original text

````
### Tint Rules
- Campaign headline "D" and "M": **≈40% tint** of the headline color (Gold or Brand Blue colorway).
- Light Blue callout box: **70% tint**.
- Golden Sand callout box: **30% tint**.
- Wave top layers: **70% transparency**.
- No other ad-hoc tints — use palette values or these specified tints only.

````

## Extracted rules (2)

### rule_lisraya_no_ad_hoc_tints
- class=color_application scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity
- rule_text: Do not use any ad-hoc tints; use palette values or only the specified tint treatments.
- intent: Prevent unapproved tonal variations outside the defined palette and tint system.

### rule_lisraya_tint_rules_table_binding
- class=assembly scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: The Tint Rules table is a closed, brand-approved set; every row binds its listed values exactly as specified. Do not invent or alter rows.

| item | value |
|---|---|
| Campaign headline "D" and "M" | **≈40% tint** of the headline color (Gold or Brand Blue colorway). |
| Light Blue callout box | **70% tint**. |
| Golden Sand callout box | **30% tint**. |
| Wave top layers | **70% transparency**. |
- intent: Bind the Tint Rules table values verbatim.
