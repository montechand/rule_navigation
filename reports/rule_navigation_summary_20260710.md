# Rule Navigation — Progress Report

**Agentic brand-rule targeting for pharma email generation · July 6–10, 2026**

Five days from research question to a benchmarked, pipeline-integrated system: design
bibles migrated to a structured knowledge graph, three agent architectures raced over
it, an FNR-first finalize contract, and the winning architecture vendored into
`newest_email_pipeline` — now measurably beating the legacy static rule pull.

| Headline | Value |
|---|---|
| Agent recall (micro, 6 ground-truth audits) | **98.7%** (legacy static pull: 94.1%) |
| Agent precision (micro, all FP counted) | **95.3%** (static pull: 85.1%) |
| Hard-constraint / governance-block misses, pooled | **2 vs 20** (agent vs static) |
| Knowledge bases built + vendored | **2** — lisraya (112 rules · 234 tokens), ibsrela (91 rules · 188 tokens) |

---

## 1. The problem

Brand rules live in prose blobs; generation needs per-section rulesets.

**Before — static pull.** The pipeline attached `applicable_brand_rules` per section by
pulling whole design-bible **markdown blobs** selected by heading-level heuristics:

- **Blob burial:** a rule inside a blob the selector never picks is unreachable — the
  brand color hierarchy hid inside a "banner" blob, the alt-text mandate inside an
  imagery blob.
- **Blob riders:** a mostly-relevant blob drags in rules for absent devices — chart
  rules with no chart, campaign lockups with no campaign.
- Include/exclude granularity is the blob, never the rule.

**Goal — precise navigation.** Can an LLM agent navigate a **structured brand-rule
knowledge graph** precisely enough to assign the right ruleset to each email-blueprint
section?

- Per section: `targeted_brand_rules` (precisely scoped) + `email_wide_brand_rules`
  (baseline, union-deduped with vote provenance).
- **FNR-first:** a missed hard constraint is a compliance defect; an extra rule is only
  prompt bloat. Optimize recall, then precision.
- Benchmarked later against humans doing the same task.

Inputs: structured brand-rules KB (migrated from the design bibles) + an email
blueprint (`content_blueprint[]`, with or without per-section design concepts).

---

## 2. Five-day arc

| Date | What happened |
|---|---|
| **Jul 6** | **Experiment suite stood up** (standalone repo, 11 commits total): KB migration from design bibles, 3 agent architectures (A/B/C), shared tool repo + tracing; first ibsrela/lisraya runs. Evening: **token-first KB** branch — exhaustive token layer, cluster-level rules. |
| **Jul 7** | **Schema maturity:** dynamic registries, template ingestion + `resolve_token`; **v0.3 class/template split** (`design_template` + `template_group`); governance retired as an entity, reborn as a **rule facet**. Blueprint sweep runs (lisraya 1–4). |
| **Jul 8** | **FNR-first finalize contract:** coverage check + excluded-with-reason + section-type mapping; **non-excludable mandatory baseline** (unconditional hard/block rules auto-include). Full 4-blueprint re-sweep. Vendoring into the pipeline begins (`Agentic_Workflows/rule_navigation`). |
| **Jul 9** | **Boundary resolution** (token bindings flattened into hydrated payloads), extraction-hygiene rules staged for the next KB rebuild (#5), `_tmp_boundary_polish` compensating in-pipeline. **7 enrichment runs** dumped; **6 FN/FP ground-truth audits** written (4 lisraya + 2 ibsrela). |
| **Jul 10** | **PRE-art-director targeting hook** (curated rules can now shape design concepts, not just constrain the designer), cache schema v3; 5 more enrichment runs incl. cache-hit and PRE-mode exercises. **This report + FNR collection.** |

Standalone repo: ~29 experiment runs (`outputs/` + `outputs1/`) across 6 example
blueprints. Pipeline: 12 enrichment runs dumped so far.

---

## 3. The knowledge base: design bibles → typed, queryable rule graph

- **Atomic rules** (`brand_rule`): closed-vocab `rule_class`, section-type selectors,
  `applies_when` predicates, typed effects, hardness, governance facet.
- **Token-first layer:** every concrete styling value is a *primitive* token; every
  element-path binding is a *semantic* token whose `when`-variants carry the IF/ELSE
  formerly written as prose. Rules become topic clusters that **bind tokens instead of
  restating values** (`resolves_to` edges).
- **v0.3 split:** `content_sub_type` = structural classes; `design_template` (`tpl_`) =
  concrete approved artifacts filling section roles, grouped in pick-one
  `template_group`s with their own usage gates.
- **Governance as a facet:** required disclosures / verbatim messaging are ordinary
  rules carrying `{gov_type, verdict, preferred_form, severity}` — they surface in
  every normal query, no forgotten corner.
- **Hygiene:** build-time exact-duplicate token merge, near-duplicate review reports,
  human-reviewable `review/` per-blob original-vs-extracted files.

### Vendored KB stats

| | lisraya | ibsrela |
|---|---|---|
| atomic rules | **112** | **91** |
| tokens | 234 | 188 |
| assets | 12 | 11 |
| subtypes / templates | 3 / 3 | 5 / 6 |
| graph nodes | 376 | 318 |
| graph edges | 596 | 521 |

Plus rule-group provenance (`groups/`), schema docs the agent reads, and 3 Chroma
vector collections per brand (summary / intent / text) in the standalone repo.

---

## 4. Three architectures, one harness

| Arch | Style | Mechanics |
|---|---|---|
| **A — generalist orchestrator** (chosen) | one agent loop | full chat history, the **entire tool repository**; explores freely, must end with the terminal `finalize_section_ruleset` call. Won on results-per-dollar and simplicity → vendored into the pipeline. |
| **B — querying-style specialists** | delegation only | orchestrator can only call `ask_vector/graph/lexical_specialist`; each specialist is a scoped loop reporting candidates + evidence; orchestrator merges, iterates, finalizes. |
| **C — schema-sharded network** | fixed fan-out | 4 parallel shard agents (color+typography / imagery+assets / layout+cta / copy+governance); a composer agent merges and finalizes. |

**Shared tool repository** (identical across archs): filesystem (`list_dir` ·
`read_file` · `grep`) · schema docs · lookup (`get_rules` · `get_entity`) · structured
facet queries (`query_rules`, paginated) · tokens (`query_tokens` · `search_tokens` ·
`resolve_token`) · BM25 keyword · vector (3 collections, metadata filters) · graph
walks (`rules_for_section/token` · `related_rules` · `rules_for_template`) · terminal
finalize.

Same task brief, section rendering, validation, and JSONL tracing — so output
differences are architectural, not prompt-shaped.

---

## 5. The FNR-first finalize contract: silent drops are structurally impossible

- **Coverage check.** The `finalize_section_ruleset` payload must declare the agent's
  `section_type_mapping`, and **every mechanically-derivable candidate** — selector
  matches for that mapping plus all null-selector (all-sections) rules — must appear in
  `targeted`, `email_wide`, or an `excluded` map with a one-line disqualifier. The call
  **fails listing anything unaccounted**. The dominant false-negative mode observed in
  early vetting — the quiet omission — cannot happen.
- **Mandatory baseline.** Unconditional hard-constraint / governance-block rules are
  **auto-included and non-excludable** — the agent cannot talk itself out of an
  accessibility mandate or a verbatim-messaging requirement that applies everywhere.
- Exclusions and the section-type mapping persist to `result.json`, so every "why was
  this rule left out" question has a recorded answer.

Result artifacts per run: `result.json` (targeted + email-wide + excluded +
usage/cost/latency) and `traces/*.jsonl` (every LLM turn and tool call — the substrate
for the later human-benchmark harness).

---

## 6. Pipeline integration (vendored into `newest_email_pipeline`)

Flow: blueprint arrives (`enrich_blueprint_design_flow`, brand resolved to a vendored
KB slug) → **PRE targeting** (opt-in, before the art director so concepts are composed
against curated rules) → art director → **POST targeting** (default; re-targets with
design concepts in the fingerprint) → designer node serves curated rules as XML
IF/THEN/WHY blocks marked SUPREME (falls back to the full bible).

What the integration does:

- One arch_a agent per section, parallel (concurrency 3); every rule id **hydrated to a
  full payload** — rule text, intent, hardness, severity, `preferred_form`, resolved
  token bindings — so downstream needs *zero KB access*.
- **File cache** keyed by brand + agent-visible section content (schema v3): a run
  costs ~$10 / ~15 min per blueprint; the cache makes repeated local docker spin-ups
  free. Partial runs are never cached.
- **Never raises:** any failure logs and returns False; the designer falls back to the
  legacy full-ruleset path.
- `_tmp_boundary_polish` (disposable, documented): 4 boundary-side fixes for pre-#5 KB
  defects — prose-token binding recovery, tok-id → literal rewrite, redundant-SET
  suppression, cross-blob duplicate collapse. Dropped after the KB rebuild.

### Env gates (all greppable)

| Variable | Purpose |
|---|---|
| `RULE_TARGETING_ENABLED` | master gate |
| `RULE_TARGETING_USE_IN_ART_DIRECTOR` | PRE run (default off) |
| `RULE_TARGETING_POST_DESIGN_CONCEPT` | POST run (default on) |
| `RULE_TARGETING_USE_IN_DESIGNER` | curated vs full-bible A/B lever |
| `RULE_TARGETING_DUMP_ENRICHMENT` | run-wise before/after dumps |
| `RULE_NAV_AGENT_MODEL` / `_PROVIDER` | agent model config |

Consumers: designer context (`designer_tools/brand_rules.py`), art-director prompt
(`query_agent_v3/tools/blueprint.py`), message-generator state plumbing. Tests:
`tests/test_targeting.py`.

---

## 7. FN/FP benchmark: agent vs legacy static pull, same atomic rule space

- **Ground truth.** For each audited enrichment run: a manual per-rule judgment of the
  brand's **entire atomic-rule universe** (112 lisraya / 91 ibsrela) against that run's
  blueprint — applicable / not applicable / borderline (borderline excluded from both
  FN and FP counting). Blueprint families share audits where content is identical.
- **Two approaches, one artifact.** Both scored from the same
  `03_rule_attachments.json`:
  - **query_agent** — per-section `targeted_brand_rules` + `email_wide_brand_rules`.
  - **static_pull** — legacy `applicable_brand_rules` blobs, mapped blob → rule_group →
    member atomic rules (every blob matched; 0 unmatched in all runs) so both live in
    the same atomic space.
- FP split: *structural* (wrong device/surface) vs *defensive-verbatim* (untriggered
  conditional hedges the generator re-checks — cheap).

### Per-run results (6 audits: 4 lisraya + 2 ibsrela)

| Run · blueprint | Approach | TP | FN | FN hard/block | FP struct | FP defens. | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| 153557 · lisraya bp4 (intro/benefits/callout/cta) | **query_agent** | 83 | **0** | 0 | 1 | 3 | 95.4% | **100%** |
| | static_pull | 81 | 2 | 2 | 8 | 2 | 89.0% | 97.6% |
| 193028 · lisraya bp2 (intro/savings/enrollment/cta) | **query_agent** | 77 | 1 | **0** | 1 | 3 | 95.1% | 98.7% |
| | static_pull | 71 | 7 | 6 | 8 | 8 | 81.6% | 91.0% |
| 204535 · lisraya bp2 (intro/copay/enrollment/cta) | **query_agent** | 77 | 1 | **0** | 1 | 4 | 93.9% | 98.7% |
| | static_pull | 71 | 7 | 6 | 14 | 8 | 76.3% | 91.0% |
| 212538 · lisraya bp4 (intro/efficacy/safety/cta) | **query_agent** | 82 | 1 | **0** | **0** | 3 | 96.5% | 98.8% |
| | static_pull | 81 | 2 | 2 | 8 | 2 | 89.0% | 97.6% |
| 215930 · ibsrela (intro/causes/cta/closing) | **query_agent** | 66 | 3 | 2 | **0** | **0** | **100%** | 95.7% |
| | static_pull | 62 | 7 | 3 | 1 | 6 | 89.9% | 89.9% |
| 223059 · ibsrela (intro/guide/video/cta) | **query_agent** | 63 | **0** | 0 | **0** | 6 | 91.3% | **100%** |
| | static_pull | 61 | 2 | 1 | 3 | 7 | 85.9% | 96.8% |

Ground truths: lisraya bp4 = 83 applicable of 112; bp2 = 78 of 112; ibsrela = 69 and
63 of 91.

### Aggregate (micro-pooled over all six audits)

| | query_agent | static_pull |
|---|---|---|
| True Positives | 448 | 427 |
| False Negatives | **6** | **27** |
| — hard-constraint / gov-block | **2** | **20** |
| FP structural | 3 | 42 |
| FP defensive-verbatim | 19 | 33 |
| **Micro precision** | **95.3%** | 85.1% |
| **Micro recall** | **98.7%** | 94.1% |

The agent's only hard/block misses across all six audits are 2 of the 3
symptom-icon-trio rules in one ibsrela run. The static pull misses hard/block rules
**in every single run** — and they're the *same* rules each time, because they're
structurally unreachable.

---

## 8. Failure modes: deterministic for the static pull, incidental for the agent

**static_pull — structural, repeats every run**

- **Blob burial (FN):** lisraya's Blue>Orange>Gold color-hierarchy rule buried in a
  "banner" blob and the alt-text mandate in the imagery blob — missed in *all four*
  lisraya runs. The 5-rule Icon-Callout-Box family missed in both bp2 runs (the
  $0-copay callout is exactly that device). ibsrela's gradient pair missed in both
  runs.
- **Blob riders (FP):** all 9 chart rules dragged into a chartless email (204535);
  campaign-lockup, patient-story, masthead-gradient rules riding pulled blobs
  everywhere; the whole "Approved Campaign Messaging" blob surfacing 8 untriggered
  verbatims.

**query_agent — small, addressable**

- **Recurring structural FP** (3 of 4 lisraya runs): `cta_svg_button_shape_treatment`,
  a `content_types=['banner']` rule targeted at email CTAs — mechanically filterable on
  content type.
- **Defensive-verbatim hedges** (0–6 per run): untriggered conditional rules surfaced
  email-wide; cheap, since the generator re-checks their gates.
- **One real content miss:** the ibsrela symptom-icon trio — copy enumerating
  "constipation + belly pain + other belly symptoms" is the `content_tag` trigger, read
  as editorial. Notably the agent *did* catch the analogous LPGA-gated CTA rule in the
  same run — the trio miss is a gap in trigger salience, not capability.

---

## 9. Where everything lives

| Artifact | Path |
|---|---|
| Standalone experiment repo (git: `main` + `token-first-kb`, 11 commits) | `solstice/rule_navigation/` — `indexing/` (KB build) · `kb/{lisraya,ibsrela}/` · `arch_{a,b,c}_*/` · `runner/` (run_blueprint, compare) · `viz/` (KB graph HTML) · `outputs*/` (~29 runs) |
| Pipeline integration (vendored) | `Backend-Server/src/content_generation_new/application/Agentic_Workflows/rule_navigation/` — `targeting.py` · `arch_a.py` · `shared/` · `kb/` · `_tmp_boundary_polish/` · `tests/` |
| Run-wise enrichment dumps + FNR audits | `…/rule_navigation/outputs/enrichment/<run>/` — `01_blueprint_before` · `02_after` · `03_rule_attachments` · `04_with_section_rules` · `fnfp_comparison.md` + `_data.json` |
| Collected FNR reports (new) | `…/rule_navigation/outputs/enrichment/fnr_reports/` — `README.md` (consolidated index + aggregates) · `<run>__fnfp_comparison.md` ×6 · `fnr_collected_data.json` |
| This report (HTML deck + markdown) | `solstice/rule_navigation/reports/rule_navigation_summary_20260710.{html,md}` |

12 enrichment runs dumped to date: 6 audited (4 lisraya + 2 ibsrela), 6 pending audit
(incl. today's PRE-mode and cache-exercise runs and a fresh ibsrela run).

---

## 10. Next steps

**KB / extraction**

1. Rebuild both KBs with the staged **#5 extraction hygiene** (no raw token ids in
   prose, concrete token values, cross-blob rule dedupe) → re-vendor → **delete
   `_tmp_boundary_polish`** and bump the cache schema.
2. Mechanical trigger tables for `content_tag`-gated rule families (the symptom-trio
   lesson) — same treatment the mandatory baseline got.
3. Mechanical `content_types` filter to kill the recurring banner-rule FP.

**Evaluation / rollout**

4. Audit the 6 pending runs — especially the **PRE-art-director** runs (do rule-aware
   design concepts change downstream rule adherence?).
5. End-to-end A/B via `RULE_TARGETING_USE_IN_DESIGNER`: same enriched blueprint,
   curated vs full-bible designer context, compare rendered emails.
6. The original benchmark: humans doing the same navigation task, scored FNR-first
   against the same ground truths.

---

**Bottom line:** agentic navigation over an atomized rule graph already beats the
legacy static pull on every audited run — **98.7% recall / 95.3% precision, 2 vs 20
hard-constraint misses** — and it's wired into the pipeline behind env gates, cached,
and safe to fail.
