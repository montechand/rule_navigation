# Consistency conflicts

## Pairwise conflicts

### `89cccd1cc6e16b9a`

- kind: `intra_token`
- element_path: `accent_shape.radius`
- sources: `tok_lisraya_accent_shape_radius`, `tok_lisraya_accent_shape_radius`
- overlap_guard: `{"surface": {"op": "eq", "values": ["print"]}, "tag:callout": {"op": "eq", "values": ["present"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: intra_token tok_lisraya_accent_shape_radius: "42px & 6px" vs "1.25\\" & 0.0625\\""; witness={"surface": "print", "tag:callout": "present"}

### `357beb2448699cda`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_administration_statement_verbatim`, `rule_lisraya_brand_name_all_caps`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_administration_statement_verbatim vs rule_lisraya_brand_name_all_caps; witness={"audience": "dtp_patient"}

### `a30268c09b8a203c`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_administration_statement_verbatim`, `rule_lisraya_doctor_discussion_cta_verbatim`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "eq", "values": ["cta"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_administration_statement_verbatim vs rule_lisraya_doctor_discussion_cta_verbatim; witness={"audience": "dtp_patient", "section": "cta"}

### `8528ffe9d0a1c43a`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_brand_name_all_caps`, `rule_lisraya_doctor_discussion_cta_verbatim`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "eq", "values": ["cta"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_brand_name_all_caps vs rule_lisraya_doctor_discussion_cta_verbatim; witness={"audience": "dtp_patient", "section": "cta"}

## Equal-specificity precedence proposals

_None._

## Dead entries

_None._

## Global UNSAT

_None._
