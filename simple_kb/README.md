# simple_kb

Original (pre-atomization) design bibles for **Architecture E**.

Each brand directory contains:

- `design_bible.json` — byte-identical copy of
  `newest_email_pipeline/brand_rules/design_bible_{brand}_1.json`
- `_index.json` — catalog of every Markdown passage with a stable ref

Passage refs look like `website.color_scheme_rules[3]` and map 1:1 to the array
entry in `design_bible.json`. Architecture E assigns these refs to blueprint
sections; it does **not** use the structured `kb/{brand}/` atomization.
