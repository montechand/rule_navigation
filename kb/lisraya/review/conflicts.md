# Consistency conflicts

## Pairwise conflicts

### `30e270714117bc68`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_administration_and_convenience_messaging`, `rule_lisraya_audience_terminology_dtc`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "in", "values": ["efficacy", "intro"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_administration_and_convenience_messaging vs rule_lisraya_audience_terminology_dtc; witness={"audience": "dtp_patient", "section": "efficacy"}

### `d1cb58cb6c6bbf0b`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_administration_and_convenience_messaging`, `rule_lisraya_brand_name_and_trademark_usage`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "in", "values": ["efficacy", "intro"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_administration_and_convenience_messaging vs rule_lisraya_brand_name_and_trademark_usage; witness={"audience": "dtp_patient", "section": "efficacy"}

### `990f882e770b3471`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_administration_and_convenience_messaging`, `rule_lisraya_product_benefits_messaging`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "in", "values": ["efficacy", "intro"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_administration_and_convenience_messaging vs rule_lisraya_product_benefits_messaging; witness={"audience": "dtp_patient", "section": "efficacy"}

### `1481f477d5733e18`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_audience_terminology_dtc`, `rule_lisraya_brand_name_and_trademark_usage`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_audience_terminology_dtc vs rule_lisraya_brand_name_and_trademark_usage; witness={"audience": "dtp_patient"}

### `cd07247b50c89ac1`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_audience_terminology_dtc`, `rule_lisraya_parent_company_footer_lock`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "eq", "values": ["end_matter"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_audience_terminology_dtc vs rule_lisraya_parent_company_footer_lock; witness={"audience": "dtp_patient", "section": "end_matter"}

### `27726860db57eef8`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_audience_terminology_dtc`, `rule_lisraya_patient_support_program_naming`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "in", "values": ["affordability", "patient_story"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_audience_terminology_dtc vs rule_lisraya_patient_support_program_naming; witness={"audience": "dtp_patient", "section": "affordability"}

### `d61b096aba92b4a0`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_audience_terminology_dtc`, `rule_lisraya_product_benefits_messaging`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "in", "values": ["efficacy", "intro"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_audience_terminology_dtc vs rule_lisraya_product_benefits_messaging; witness={"audience": "dtp_patient", "section": "efficacy"}

### `e5fd9483e12cf52a`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_brand_name_and_trademark_usage`, `rule_lisraya_parent_company_footer_lock`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "eq", "values": ["end_matter"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_brand_name_and_trademark_usage vs rule_lisraya_parent_company_footer_lock; witness={"audience": "dtp_patient", "section": "end_matter"}

### `aa3ef4a788f62cf2`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_brand_name_and_trademark_usage`, `rule_lisraya_patient_support_program_naming`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "in", "values": ["affordability", "patient_story"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_brand_name_and_trademark_usage vs rule_lisraya_patient_support_program_naming; witness={"audience": "dtp_patient", "section": "affordability"}

### `901bafa2ab6c54f7`

- kind: `verbatim_clash`
- element_path: `(unspecified)`
- sources: `rule_lisraya_brand_name_and_trademark_usage`, `rule_lisraya_product_benefits_messaging`
- overlap_guard: `{"audience": {"op": "eq", "values": ["dtp_patient"]}, "section": {"op": "in", "values": ["efficacy", "intro"]}}`
- witness: `(witness unavailable — supply domains)`
- detail: verbatim clash at None: rule_lisraya_brand_name_and_trademark_usage vs rule_lisraya_product_benefits_messaging; witness={"audience": "dtp_patient", "section": "efficacy"}

## Equal-specificity precedence proposals

_None._

## Dead entries

_None._

## Global UNSAT

_None._
