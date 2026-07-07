# Global conventions

- Empty semantics: `null` = **unconstrained** (applies to all). `[]` = **explicitly none**.
  A rule with `selector.section_types = null` applies to EVERY section; treat those as
  candidates for email-wide/baseline rules.
- IDs: `{entity_prefix}_{brand}_{slug}`. Prefixes: `rule_` brand_rule, `tok_` brand_token,
  `ast_` design_asset, `gov_` governance, `sub_` content_sub_type (structural class),
  `tpl_` design_template (concrete instance), `tgr_` template_group, `grp_` rule_group,
  `agr_` asset_group.
- `token_ids` / `asset_ids` on a rule are derived indices of what its `effect` references.
- Only `status = active` rows are queryable.
