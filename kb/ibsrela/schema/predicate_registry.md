# applies_when predicate registry (closed)

- background_group: {group: light|dark} — rule fires only on that background family
- background_token: {token_id} — fires only on a specific background token
- theme: {theme} — email theme (one theme per email systems)
- content_tag: {tag} — presence of tagged content, e.g. "lpga"
- campaign: {name} — active campaign, e.g. "flip_the_script", "you_deserve_more"
- breakpoint: {breakpoint: desktop|mobile}
- adjacent_section_state: {state} — e.g. "section_above_populated", adjacent background group
- position_in_email: {position: first|last}
- first_mention: {term} — first occurrence of a term, e.g. "dermatomyositis"

Predicates are evaluable by the generator at decision time. Extraction classifies
conditions into this registry and never invents new predicate kinds.
