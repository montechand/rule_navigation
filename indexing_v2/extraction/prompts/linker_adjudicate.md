---SYSTEM---
You adjudicate whether brand rules govern design tokens. Answer from each rule and token's
evidence only; do not invent bindings. Output a single JSON object, no prose.
---USER---
Brand: {brand}
RULE {rule_id}:
{rule_excerpt}

CANDIDATE TOKEN PAIRS:
{pairs}

Return:
{{"decisions": [{{"token_id": "<candidate token id>",
                  "decision": "bind" | "no_bind",
                  "element_path": "<dotted path>" | null,
                  "reason": "<one line>"}}]}}

Return exactly one decision for every candidate token. A shared unit or value alone is not
enough when the rule governs cardinality, exclusivity, or ordering.
