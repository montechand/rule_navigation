# Entity: design_template (+ template_group)

A CONCRETE approved artifact — a complete MJML/HTML block from the brand's template
library or embedded verbatim in the design bible. Instances, not classes.

- `source`: template_library | design_bible. `template_ref`: external library id.
- `file`: kb-relative path to the stored body (templates/{id}.mjml); metadata lives in
  templates/_meta/{id}.json, index in templates/_index.json.
- `instance_of`: FK -> content_sub_type when the template realizes a defined class (a
  header template realizes the locked Top Matter class). Composite templates (e.g.
  header+hero) may have no single class — their `fills_section_types` carry the roles.
- `fills_section_types`: the section role(s) this block IS (graph edge `fills_section`).
- `group_id`/`group_order`: membership in a template_group — a pick-one set of alternates
  (e.g. the brand's approved email headers; `semantics` carries the contract, like
  "assemble exactly one per email").
- `usage_conditions`: per-instance selection conditions, e.g.
  `{requires_content_tags: ["lpga"], inferred: true}` — inherited automatically when the
  template's body references gated assets/tokens. This is where "use template X only
  when ..." lives; it is NOT expressed as rules.

Rule inheritance: a template obeys (a) rules scoped to its class via content_sub_type_ids,
(b) rules targeting the section roles it fills, and (c) email-wide baseline rules. The
`rules_for_template` tool assembles exactly that view. Templates are never rule-scoped
directly.
