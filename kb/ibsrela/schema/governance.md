# Entity: governance

Regulatory/legal/MLR adjudication of claims and required language.

- `gov_type`: regulatory | legal | mlr_claim | disclosure | trademark.
- `subject`: the claim/topic being adjudicated.
- `match`: `{method: semantic|lexical|exact, threshold?}` — how generated text triggers it.
- `verdict`: allowed | forbidden | allowed_with_disclosure | requires_qualifier | verbatim_only.
- `preferred_form`: the verbatim string (disclosure text, qualifier, approved claim wording).
- `severity`: info (prompt context) | warn (QA flag) | block (generation guard).
- Rules referencing a governance row carry it in `governance_ids`.
