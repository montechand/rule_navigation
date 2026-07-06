# Review: grp_ibsrela_color_scheme_rules_04

doc_ref: `color_scheme_rules[4]`

## Original text

````
### DTP section background sequencing
- DTP emails alternate section backgrounds in a fixed rhythm: **purple hero image** → **white content section** (efficacy + side-effect bullets) → **white or light photo section** (patient story / lifestyle) → **green accent panel** (`#01A47E`, used for affordability or symptom-icon trio) → **purple campaign image section** ("BECAUSE IBSRELA CAN" lockup) → locked End Matter.
- Sections butt edge-to-edge with no margin between them; transitions are achieved via background color change or full-bleed photographic hero, not via dividers or rules.
- Within one email, the green panel appears **at most once** and is reserved for either the affordability block or the symptom-icon trio — never both stacked.
````

## Extracted rules (4)

### rule_ibsrela_dtp_section_background_sequence
- class=layout scope=brand hardness=strong_default polarity=must sections=['hero', 'efficacy', 'safety', 'patient_story', 'affordability', 'symptom_trio'] constraint=ordering
- rule_text: DTP emails alternate section backgrounds in a fixed rhythm: purple hero image → white content section (efficacy + side-effect bullets) → white or light photo section (patient story / lifestyle) → green accent panel (#01A47E, used for affordability or symptom-icon trio) → purple campaign image section ('BECAUSE IBSRELA CAN' lockup) → locked End Matter.
- intent: Maintain a consistent, recognizable visual flow across DTP emails.

### rule_ibsrela_sections_butt_edge_to_edge
- class=layout scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Sections butt edge-to-edge with no margin between them; transitions are achieved via background color change or full-bleed photographic hero, not via dividers or rules.
- intent: Create seamless section transitions without visual clutter from dividers.

### rule_ibsrela_green_panel_at_most_once
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['affordability', 'symptom_trio'] constraint=cardinality
- rule_text: Within one email, the green accent panel (#01A47E) appears at most once and is reserved for either the affordability block or the symptom-icon trio — never both stacked.
- intent: Reserve the green accent for a single high-value block and avoid overuse.

### rule_ibsrela_green_panel_reserved_use
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['affordability', 'symptom_trio'] constraint=exclusivity
- rule_text: The green accent panel (#01A47E) is reserved for either the affordability block or the symptom-icon trio, and the two must never be stacked together in one green panel.
- intent: Keep the green accent semantically tied to affordability or symptom-trio content.
