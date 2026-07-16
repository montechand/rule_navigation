# Cascade schema (v2)

## contexts.json

Maps each email-level context canonical key to `{axes, sheet_hash}`.
Canonical key format: `audience=…;campaign=…;surface=…;tags=tag1+tag2|none;theme=…`.
Axes use `content_tags` in models but serialize as `tags` in sheet context.

## Sheet deduplication

Sheets are content-addressed: `sheet_hash = stable_hash(payload without context)`.
Identical resolved sheets share one `cascade/sheets/{sheet_hash}.json`.
Index `kb_hash` must match every sheet payload.

## Sheet layout

- `email`: hard_constraints, strong_defaults, soft_guidance, governance, structure buckets
- `sections/*`: per-section hard/default/guidance rule ids plus `elements` resolved properties
- `elements.{path}`: `resolved` value when top candidate residual guard is empty; `candidates` retains trace with residual guards and specificity tuples

## Resolution

Email-level axes are partial-evaluated; surviving bindings keep residual guards on section-level axes only.
Total order (higher tuple wins), evaluated left→right:
(hardness: hard=3|strong=2|soft=1,
 scope: campaign=3|brand=2|org_baseline=1,
 selector_rank,
 n_bound_axes: len(guard),
 source_kind: rule_binding=2|token_variant=1|token_default=0,
 precedence,
 source_id)               # final deterministic tiebreak — equal-through-precedence
                          # with DIFFERENT values is a Conflict, id never silently decides values

## Query defaults (`get_sheet`)

Default axes: audience=dtp_patient, surface=email, campaign=none, theme=none, tags=[].
Unknown axis keys raise `KeyError`; missing context raises `KeyError`; missing files raise `FileNotFoundError`; kb_hash or sheet hash mismatch raises `ValueError`.
