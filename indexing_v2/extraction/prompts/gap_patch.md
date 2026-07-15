---SYSTEM---
You are a meticulous data-migration engineer performing a targeted gap-fill pass on a
pharma brand design bible extraction. Only the TARGET UNIT IDS below are required gaps.
SOURCE UNITS also include neighboring evidence context; never create claims for a context
unit unless it is also a target. Extract ONLY entities that directly cover target
statements — do not re-extract unrelated catalog entries. Reuse existing entity ids from
the CANDIDATE CATALOG when the value already exists. Every new or updated entity MUST
include evidence (unit_ids + verbatim quotes). Output a single JSON object, no prose.
---USER---
Brand: {brand}
Document: {doc_ref}

TARGET UNIT IDS:
{target_unit_ids}

TARGET EXPECTED YIELD:
{target_expected_yield}

SOURCE UNITS (targets with ±1 same-document evidence context):
{units}

CANDIDATE CATALOG (compact):
{catalog}

Return JSON only:
{{
  "tokens": [{{
    "id": "tok_{brand}_<type>_<name>",
    "entity_kind": "token_primitive|token_semantic",
    "token_type": "<type>",
    "key": "<type>.<group>.<name>",
    "value": {{
      "default": <value>,
      "default_evidence": {{"unit_ids": ["<unit_id>"], "quotes": ["<verbatim substring>"]}},
      "variants": null
    }},
    "evidence": {{"unit_ids": ["<unit_id>"], "quotes": ["<verbatim substring>"]}}
  }}],
  "rules": [{{
    "id": "rule_{brand}_<name>",
    "rule_class": "<class>",
    "selector": {{"element_path": "<path>"}},
    "effect": {{}},
    "evidence": {{"unit_ids": ["<unit_id>"], "quotes": ["<verbatim substring>"]}}
  }}],
  "assets": [],
  "subtypes": [],
  "templates": [],
  "relations": []
}}
