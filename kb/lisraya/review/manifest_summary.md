# Build manifest — lisraya

- schema_version: 2.0
- built_at: 2000-05-11T03:49:57Z

## Inputs

- bible_hash: `f1674fd7e5c526ba`
- template_library_hash: `(empty)`
- prompts_hash: `403260e341896d84`
- registries_hash: `af53a5e835cace9d`

## Stages

- s0: version=`1.0.0` out_hash=`0070b845cf25f67a`
- s1: version=`1.0.0` out_hash=`0b242e7595c69a2b`
- s10: version=`cascade-compile` out_hash=`f3aa6d9f3c04b068`
- s11: version=`summarize-embed-v1` out_hash=`11e150a707afe648`
- s2: version=`extraction-v2.1.1` out_hash=`42affb51bfec4dbc`
- s3: version=`1.1.4` out_hash=`40c54ebc8ec0e8a4`
- s4: version=`1.3.0` out_hash=`0e264cf5c1b93064`
- s5: version=`1.2.0` out_hash=`634a69d22f2a1416`
- s6: version=`ledger-v2.0.0` out_hash=`3f4294857cbbcd1c`
- s6b: version=`linker-v1.0.0` out_hash=`052b4d78a84a1cf5`
- s7: version=`pass-c-v3` out_hash=`cc13e0be70385fbc`
- s8: version=`write-kb-v1` out_hash=`bff04485503d9b59`
- s9: version=`pairwise+smt` out_hash=`209a428f425218ac`

## Metrics

- units: 264
- required_units: 179
### coverage

- normative: 0.9509803921568627
- rounds: 3
- value: 0.9306930693069307
- verbatim: 0.6842105263157895

### verification

- quarantine_rate: 0.0
- quarantined: 0
- value_verified_rate: 0.6618705035971223

### ensemble

- high: 97
- low: 5
- medium: 27
- runs: 3

### critic

- applied: 18
- deferred_human: 2
- findings: 105

### linker

- adjudicated_binds: 0
- auto_bound: 11
- minted_edges: 13
- needs_rule: 27
- orphans_after_transitive: 33
- orphans_before: 44
- unresolved_rule_literals: 5

### consistency

- dead_rules: 0
- equal_specificity: 0
- global_unsat: 0
- hard_hard: 0

### cascade

- contexts: 32
- distinct_sheets: 20

## Acceptance

### invariants

- determinism: pass
- no_live_contradictions: fail
- no_open_criticals: pass
- no_silent_quarantine: pass
- ref_closure: fail
- verbatim_integrity: fail

### queues

| queue | open | waived | deferred |
| --- | --- | --- | --- |
| unclaimed_unit | 12 | 0 | 0 |
| unverified_value | 4 | 0 | 0 |
| over_claimed | 1 | 0 | 0 |
| conflict | 10 | 0 | 0 |
| orphan_token | 6 | 0 | 0 |
| needs_rule | 27 | 0 | 0 |

### ratchet

skipped (--ratchet not set)
