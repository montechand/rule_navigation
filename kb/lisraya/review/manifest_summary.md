# Build manifest — lisraya

- schema_version: 2.0
- built_at: 2000-05-11T03:49:57Z

## Inputs

- bible_hash: `f1674fd7e5c526ba`
- template_library_hash: `(empty)`
- prompts_hash: `5cf034edee1686a4`
- registries_hash: `af53a5e835cace9d`

## Stages

- s0: version=`1.0.0` out_hash=`0070b845cf25f67a`
- s1: version=`1.0.0` out_hash=`0b242e7595c69a2b`
- s10: version=`cascade-compile` out_hash=`e302602ca504edd6`
- s11: version=`summarize-embed-v1` out_hash=`326f7f2d356c7d20`
- s2: version=`extraction-v2.0.0` out_hash=`0ec5e8f8f892f538`
- s3: version=`1.1.4` out_hash=`680d19379b5ea523`
- s4: version=`1.4.0` out_hash=`2825cd8013d5c0c9`
- s5: version=`1.2.0` out_hash=`897e80370c5ef8ed`
- s6: version=`ledger-v2.0.0` out_hash=`f6f5e5a7036ee29a`
- s7: version=`pass-c-v3` out_hash=`78698c9addfef884`
- s8: version=`write-kb-v1` out_hash=`1803715ad36155f5`
- s9: version=`pairwise+smt` out_hash=`6c81b5db6b7a1a81`

## Metrics

- units: 264
- required_units: 179
### coverage

- normative: 0.9705882352941176
- rounds: 3
- value: 1.0
- verbatim: 1.0

### verification

- quarantine_rate: 0.0
- quarantined: 0
- value_verified_rate: 0.6444444444444445

### ensemble

- high: 73
- low: 26
- medium: 62
- runs: 3

### critic

- applied: 64
- deferred_human: 8
- findings: 305

### consistency

- dead_rules: 0
- equal_specificity: 0
- global_unsat: 0
- hard_hard: 0

### cascade

- contexts: 105
- distinct_sheets: 51

## Acceptance

### invariants

- determinism: pass
- no_live_contradictions: fail
- no_open_criticals: pass
- no_silent_quarantine: pass
- verbatim_integrity: fail

### queues

| queue | open | waived | deferred |
| --- | --- | --- | --- |
| unclaimed_unit | 0 | 0 | 0 |
| unverified_value | 34 | 0 | 0 |
| over_claimed | 3 | 0 | 0 |
| conflict | 8 | 0 | 0 |

### ratchet

skipped (--ratchet not set)
