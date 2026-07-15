# Consistency conflicts

## Pairwise conflicts

### `c35190c18e82c65f`

- kind: `equal_specificity`
- element_path: `cta.button.fill`
- sources: `tok_d`, `tok_c`
- overlap_guard: `{"background_group": {"op": "in", "values": ["dark", "light"]}}`
- witness: `{"background_group": "dark"}`
- detail: equal specificity at cta.button.fill

### `d4c339f1922031a2`

- kind: `hard_hard`
- element_path: `cta.button.fill`
- sources: `tok_b`, `tok_a`
- overlap_guard: `{"background_group": {"op": "eq", "values": ["dark"]}}`
- witness: `{"background_group": "dark"}`
- detail: value conflict at cta.button.fill

## Equal-specificity precedence proposals

- `rule_later` precedence `5`: propose precedence 5 for rule_later over rule_earlier

## Dead entries

- `rule_dead` (rule, empty_selector_sections): rule rule_dead selector.section_types is empty

## Global UNSAT

### `audience=dtp_patient;campaign=none;surface=email;tags=none;theme=none`

- core: `["rule_max_cta", "rule_min_cta"]`
- detail: global_unsat in audience=dtp_patient;campaign=none;surface=email;tags=none;theme=none: core=["rule_max_cta", "rule_min_cta"]
