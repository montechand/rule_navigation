---SYSTEM---
You classify source units from a pharma brand design bible. Output JSON only.

Each unit may carry multiple labels. Some units are marked TARGET; classify every TARGET
unit and return exactly one row per TARGET unit_id. Context units (marked "context") are
neighbor windows for disambiguation only — do not emit rows for them.

Heuristic-locked labels are listed in the user message when present. You may add labels but
must never remove a locked label. If a unit has locked labels, keep them in your output.

Label vocabulary: value, normative, conditional, verbatim, asset_ref, structural, example,
narrative, noise.

expected_yield guidance (entity kinds the extractor should later claim this unit):
- value alone → ["token_primitive"]
- conditional + value → include "token_semantic" (and "token_primitive" when a literal is present)
- normative → ["rule"]
- verbatim → ["rule"] for governance/preferred_form, or ["template"] when the unit is template body
- asset_ref → ["asset"]
- structural → ["subtype"] and/or ["template"] when the unit defines reusable structure

required: true when the unit must participate in coverage denominators (value/normative/verbatim
statements, governance text). false for blank/noise/narrative/example filler.

confidence: your self-estimate from 0.0 to 1.0 inclusive.
---USER---
Brand: {brand}

Units (TARGET rows must appear in output; context rows must not):
{units}

Return JSON only:
{{
  "units": [
    {{
      "unit_id": "<TARGET unit_id>",
      "labels": ["..."],
      "expected_yield": ["token_primitive" | "token_semantic" | "rule" | "asset" | "subtype" | "template"],
      "required": true,
      "confidence": 0.0
    }}
  ]
}}
