# Support entities

## rule_relation
Directed edge between rules: `{src_rule_id, dst_rule_id, relation, note}`.
relation: refines | conflicts | cross_reference | cluster | co_applies.

## rule_group
Provenance blob a rule was atomized from: `{id, source, doc_ref, original_text}`.
Use it to read the original un-atomized text around a rule.

## asset_group
Named ordered set of assets (e.g. symptom_icon_trio): `{id, name, semantics}`.
Set contract like "all members appear together"; ordering enforced by a brand_rule
with constraint_type=ordering targeting the group.
