# Build manifest — lisraya

- schema_version: 2.0
- built_at: 2000-05-11T03:49:57Z

## Inputs

- bible_hash: `f1674fd7e5c526ba`
- template_library_hash: `(empty)`
- prompts_hash: `80418ab6e106d4f5`
- registries_hash: `af53a5e835cace9d`

## Stages

- s0: version=`1.0.0` out_hash=`0070b845cf25f67a`
- s1: version=`1.0.0` out_hash=`d9997aac99cf08fd`
- s10: version=`cascade-compile` out_hash=`7205308a852e3f5e`
- s11: version=`summarize-embed-v1` out_hash=`a5459a4ea1577a65`
- s2: version=`extraction-v2.1.1` out_hash=`0fe053fe72f3c9b3`
- s3: version=`1.1.4` out_hash=`428e39ab1da4f2c3`
- s4: version=`1.4.1` out_hash=`ef3495c8857531f9`
- s5: version=`1.2.0` out_hash=`db082a20899a30ae`
- s6: version=`ledger-v2.0.0` out_hash=`b8635e22e32b7576`
- s6b: version=`linker-v1.0.0` out_hash=`46143003bfcc4915`
- s7: version=`pass-c-v3` out_hash=`f244524c52545ef5`
- s8: version=`write-kb-v1` out_hash=`c347409f1ab44d6a`
- s9: version=`pairwise+smt` out_hash=`cc2574df63d9ae70`

## Metrics

- units: 264
- required_units: 182
### coverage

- normative: 1.0
- rounds: 0
- value: 1.0
- verbatim: 1.0

### verification

- quarantine_rate: 0.0
- quarantined: 0
- value_verified_rate: 0.7632211538461539

### ensemble

- high: 259
- low: 8
- medium: 47
- runs: 3

### critic

- applied: 20
- deferred_human: 0
- findings: 203

### linker

- adjudicated_binds: 1
- auto_bound: 0
- minted_edges: 1
- needs_rule: 10
- orphans_after_transitive: 15
- orphans_before: 16
- unresolved_rule_literals: 3

### consistency

- dead_rules: 1
- equal_specificity: 24
- global_unsat: 0
- hard_hard: 2

### cascade

- contexts: 120
- distinct_sheets: 40

## Acceptance

### invariants

- determinism: pass
- no_live_contradictions: fail
- no_open_criticals: pass
- no_silent_quarantine: pass
- ref_closure: pass
- verbatim_integrity: pass

### queues

| queue | open | waived | deferred |
| --- | --- | --- | --- |
| unclaimed_unit | 0 | 0 | 0 |
| unverified_value | 26 | 0 | 0 |
| over_claimed | 0 | 0 | 0 |
| conflict | 29 | 0 | 0 |
| orphan_token | 6 | 0 | 0 |
| needs_rule | 10 | 0 | 0 |

### ratchet

skipped (--ratchet not set)
