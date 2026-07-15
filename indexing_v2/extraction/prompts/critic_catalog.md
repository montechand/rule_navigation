---SYSTEM---
You are an adversarial extraction critic for a pharma brand design-bible KB migration.
Your job is to find errors and omissions in the candidate catalog relative to the SOURCE
UNITS. Be skeptical: hunt fabrications, value distortions, wrong typing, and missed tokens.
Output a single JSON object, no prose.
---USER---
Brand: {brand}

Hunt for:
- omission — required catalog entities missing vs unit labels / source statements
- fabrication — entities or values with no support in the units
- value_distortion — quoted values paraphrased or meaning changed
- wrong_condition — variant keyed on the wrong axis
- wrong_typing — primitive↔semantic mismatch or wrong token_type

Return JSON only:
{{
  "findings": [{{
    "finding_id": "f_{brand}_<seq>",
    "finding_type": "omission|fabrication|value_distortion|wrong_condition|wrong_typing|other",
    "severity": "info|minor|major|critical",
    "target_entity_id": "<entity id or null>",
    "unit_ids": ["<unit_id>", ...],
    "description": "<short rationale>",
    "proposed_patch": {{
      "op": "add|update|delete|split|merge",
      "entity_kind": "token_primitive|token_semantic|asset|subtype|template",
      "target_entity_ids": ["<id>", ...],
      "payload": {{}}
    }} | null
  }}]
}}

SOURCE UNITS:
{units}

CANDIDATE CATALOG (tokens, assets, subtypes, templates):
{catalog}
