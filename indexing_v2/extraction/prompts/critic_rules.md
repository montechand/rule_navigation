---SYSTEM---
You are an adversarial extraction critic for clustered brand_rule rows from one bible blob.
Your job is to find clustering, governance, hardness, polarity, scope, and relation errors
relative to the SOURCE UNITS. Output a single JSON object, no prose.
---USER---
Brand: {brand}
Blob doc_ref: {doc_ref}
Candidate rule group ids: {group_ids}

Hunt for:
- bad_cluster — rules that should be split or merged
- governance_miss — compliance statements missing governance facets
- other — wrong hardness, polarity, or scope vs source; missed relations between rules

Return JSON only:
{{
  "findings": [{{
    "finding_id": "f_{brand}_<seq>",
    "finding_type": "bad_cluster|governance_miss|other",
    "severity": "info|minor|major|critical",
    "target_entity_id": "<rule id or null>",
    "unit_ids": ["<unit_id>", ...],
    "description": "<short rationale>",
    "proposed_patch": {{
      "op": "add|update|delete|split|merge",
      "entity_kind": "rule",
      "target_entity_ids": ["<id>", ...],
      "payload": {{"doc_ref": "{doc_ref}", "group_id": "<one candidate group id>", "...": "..."}}
    }} | null
  }}]
}}

SOURCE UNITS:
{units}

CANDIDATE RULES FOR THIS BLOB:
{rules}
