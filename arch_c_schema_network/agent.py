"""Architecture C — schema-sharded agent network + composer.

A fixed parallel fan-out of four shard agents, each owning one region of the schema:

  color_typography — color_application + typography rules, token bindings/gating
  imagery_assets   — imagery + iconography rules, design_assets, pairings, asset groups
  layout_assembly  — layout/spacing/assembly/cta rules, content_sub_types, cardinality
  copy_governance  — copy_editorial/voice_tone/accessibility rules incl. governance-faceted
                     rules (disclosures/qualifiers/verbatim language)

Each shard explores only its region (scoped tools + scoped facet queries) and reports
{targeted, email_wide, evidence}. A Composer agent merges the reports, resolves
bucket conflicts, drops out-of-scope rules, and emits the final section ruleset via the
standard finalize contract.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Optional

from shared import config
from shared.llm import ToolError, ToolSpec, Trace, Usage, run_tool_loop
from shared.prompts import TASK_BRIEF, render_blueprint_context, schema_primer
from shared.schemas import Blueprint, BlueprintSection, RuleVerdict, SectionResult
from shared.tool_repo import ToolRepo

ARCH_ID = "c"
SHARD_MAX_TURNS = 12
COMPOSER_MAX_TURNS = 8

SHARDS: dict[str, dict[str, Any]] = {
    "color_typography": {
        "rule_classes": ["color_application", "typography"],
        "tools": ["query_rules", "get_rules", "keyword_search", "vector_search",
                  "query_tokens", "search_tokens", "resolve_token", "rules_for_token",
                  "get_entity", "get_section_vocab"],
        "blurb": ("You own COLOR and TYPOGRAPHY: palette application, text/heading colors, "
                  "backgrounds, gradients, tints, contrast, gated/reserved colors, fonts, "
                  "type scale, casing, line-height, bolding. The token layer carries the "
                  "values AND the conditional switching (semantic tokens like "
                  "cta.button.fill with light/dark variants): pivot from design-concept "
                  "details via search_tokens/query_tokens, then rules_for_token for the "
                  "governing rules. Check background/theme conditions (light vs dark flips "
                  "many bindings)."),
    },
    "imagery_assets": {
        "rule_classes": ["imagery", "iconography"],
        "tools": ["query_rules", "get_rules", "keyword_search", "vector_search",
                  "get_entity", "neighbors", "rules_for_token", "search_tokens",
                  "get_section_vocab"],
        "blurb": ("You own IMAGERY and ASSETS: photography treatment, icons/icon trios, "
                  "waves, lockups, approved images, alt text, asset-color pairings, "
                  "content-tag gating (e.g. LPGA), per-asset cardinality. Walk asset nodes "
                  "with neighbors() to surface pairing rules (requires_pairing_token, "
                  "member_of asset groups); image_treatment/icon_style tokens are also "
                  "in scope via search_tokens."),
    },
    "layout_assembly": {
        "rule_classes": ["layout", "spacing", "assembly", "cta"],
        "tools": ["query_rules", "get_rules", "keyword_search", "vector_search",
                  "rules_for_section", "rules_for_subtype", "rules_for_template",
                  "list_templates", "query_tokens", "search_tokens",
                  "rules_for_token", "get_entity", "get_section_vocab"],
        "blurb": ("You own LAYOUT, SPACING, ASSEMBLY and CTA structure: canvas/grid, "
                  "padding/spacing/radius/size tokens, section stacking/adjacency, the "
                  "component-class library (content_sub_types incl. locked top/end matter; "
                  "rules_for_subtype = class view) and concrete approved templates "
                  "(list_templates / rules_for_template = instance view with "
                  "usage_conditions and pick-one groups), button geometry, "
                  "CTA placement/cardinality, callout/chart container geometry. "
                  "rules_for_section gives the per-section pool; query_tokens(token_type="
                  "['spacing','padding','radius','size','dimension']) enumerates the "
                  "geometry token pool and rules_for_token links back to rules."),
    },
    "copy_governance": {
        "rule_classes": ["copy_editorial", "voice_tone", "accessibility"],
        "tools": ["query_rules", "get_rules", "keyword_search", "grep", "vector_search",
                  "get_entity", "get_section_vocab"],
        "blurb": ("You own COPY, VOICE and GOVERNANCE: editorial style, abbreviations, "
                  "capitalization in copy, inclusive language, claims/disclosures/"
                  "qualifiers, trademark usage, CTA label conventions, accessibility "
                  "copy rules (alt text, contrast reliance). Governance/compliance items "
                  "are ordinary rules carrying a `governance` facet whose preferred_form "
                  "holds the exact verbatim string — enumerate them exhaustively with "
                  "query_rules(has_governance=true) and match the section's copy outline "
                  "against them; keyword_search also indexes the verbatim strings."),
    },
}

SHARD_SYSTEM = """You are one shard agent in a network that maps brand rules to an email
section. {blurb}

Stay inside your region: other shards own the other rule classes. Within your region you
are scored on recall first — enumerate your region's rule pool with
query_rules(rule_class=[...]) (remember rules whose `tags` include your classes count too;
query_rules matches facets = rule_class OR tags), then narrow to what applies to THIS
section:
- targeted: selector matches the section's mapped type(s), or the rule governs a device
  this section clearly contains, or a conditional whose predicate the section satisfies.
- email_wide: null selector / evaluation_scope=email baseline rules from YOUR region that
  every section must obey (only email-relevant, audience-matching ones).

When done, call report_findings exactly once with per-rule one-line evidence.

{schema_primer}
"""

COMPOSER_SYSTEM = """You are the composer of a schema-sharded agent network. Four shard
agents (color_typography, imagery_assets, layout_assembly, copy_governance) each explored
their region of the brand-rules KB for the same target email section and reported findings
(hydrated with each rule's compact view below).

{task_brief}

## Your job
1. Merge and dedupe the shard reports into the final two buckets.
2. Resolve bucket conflicts: a rule reported in both buckets goes to email_wide only if its
   selector is null (applies everywhere) or evaluation_scope=email; otherwise targeted.
3. Drop out-of-scope entries: wrong audience, non-email content_types, sections the rule
   explicitly does not cover, locked components this section doesn't touch.
4. Shards can miss cross-region devices; you may verify individual rules with
   get_rules(view='full') if evidence looks weak or conflicting — but do not re-open
   broad exploration.
5. Call finalize_section_ruleset exactly once; per-rule rationale = the best shard evidence.
"""


def _report_findings_spec(repo: ToolRepo) -> ToolSpec:
    async def handler(args: dict[str, Any]) -> Any:
        def clean(entries: Any, bucket: str) -> list[dict[str, Any]]:
            if not isinstance(entries, list):
                raise ToolError(f"{bucket} must be an array")
            out = []
            unknown = []
            for e in entries:
                if not isinstance(e, dict) or "rule_id" not in e:
                    continue
                if e["rule_id"] not in repo.kb.rules:
                    unknown.append(e["rule_id"])
                    continue
                out.append({"rule_id": e["rule_id"], "evidence": str(e.get("evidence", ""))[:200]})
            if unknown:
                raise ToolError(f"unknown rule ids in {bucket}: {unknown}. Verify and retry.")
            return out

        return {
            "targeted": clean(args.get("targeted") or [], "targeted"),
            "email_wide": clean(args.get("email_wide") or [], "email_wide"),
            "notes": str(args.get("notes", ""))[:500],
        }

    entry_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"rule_id": {"type": "string"}, "evidence": {"type": "string"}},
            "required": ["rule_id", "evidence"],
        },
    }
    return ToolSpec(
        name="report_findings",
        description="FINAL ANSWER of this shard: applicable rules from your schema region.",
        parameters={
            "type": "object",
            "properties": {"targeted": entry_schema, "email_wide": entry_schema,
                           "notes": {"type": "string"}},
            "required": ["targeted", "email_wide"],
        },
        handler=handler,
        terminal=True,
    )


async def _run_shard(name: str, repo: ToolRepo, section_context: str, model: str,
                     usage: Usage, trace: Trace) -> dict[str, Any]:
    meta = SHARDS[name]
    user = (f"{section_context}\n\n## Your region\nrule classes: {meta['rule_classes']} "
            f"(as rule_class OR tags)")
    loop = await run_tool_loop(
        model=model,
        system=SHARD_SYSTEM.format(blurb=meta["blurb"], schema_primer=schema_primer(repo.kb)),
        user_message=user,
        tools=repo.specs(names=meta["tools"]) + [_report_findings_spec(repo)],
        max_turns=SHARD_MAX_TURNS,
        usage=usage,
        trace=trace,
        agent_name=f"shard_{name}",
    )
    if loop.final is None:
        return {"shard": name, "error": loop.error, "targeted": [], "email_wide": [], "notes": ""}
    return {"shard": name, **loop.final}


def _hydrate(repo: ToolRepo, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for e in entries:
        rule = repo.kb.rules.get(e["rule_id"])
        if rule is None:
            continue
        out.append({**e, "rule": repo.kb.short_rule(rule)})
    return out


async def run_section(
    repo: ToolRepo,
    blueprint: Blueprint,
    section: BlueprintSection,
    *,
    model: Optional[str] = None,
    include_design_concept: bool = True,
    trace: Trace,
    usage: Usage,
) -> SectionResult:
    model = model or config.AGENT_MODEL
    t0 = time.time()
    section_context = render_blueprint_context(blueprint, section, include_design_concept)

    # Fan-out: all shards in parallel.
    reports = await asyncio.gather(*(
        _run_shard(name, repo, section_context, model, usage, trace) for name in SHARDS
    ))
    trace.log("shard_reports", "network_c",
              sizes={r["shard"]: {"targeted": len(r.get("targeted", [])),
                                  "email_wide": len(r.get("email_wide", []))} for r in reports})

    # Compose.
    hydrated = [
        {"shard": r["shard"],
         "error": r.get("error"),
         "notes": r.get("notes", ""),
         "targeted": _hydrate(repo, r.get("targeted", [])),
         "email_wide": _hydrate(repo, r.get("email_wide", []))}
        for r in reports
    ]
    composer_user = (
        f"{section_context}\n\n## Shard reports\n"
        f"{json.dumps(hydrated, indent=1)}"
    )
    composer_tools = repo.specs(names=["get_rules"]) + [repo.finalize_spec()]
    loop = await run_tool_loop(
        model=model,
        system=COMPOSER_SYSTEM.format(task_brief=TASK_BRIEF),
        user_message=composer_user,
        tools=composer_tools,
        max_turns=COMPOSER_MAX_TURNS,
        usage=usage,
        trace=trace,
        agent_name="composer_c",
    )

    stats = {"turns": loop.turns, "tool_calls": loop.tool_call_count,
             "latency_s": round(time.time() - t0, 1),
             "shard_errors": [r["shard"] for r in reports if r.get("error")]}
    if loop.final is None:
        return SectionResult(section_id=section.section_id, stats=stats,
                             error=loop.error or "composer did not finalize")
    rationale = loop.final.get("rationale", {})
    return SectionResult(
        section_id=section.section_id,
        targeted_rules=[RuleVerdict(id=i, why=rationale.get(i, ""))
                        for i in loop.final["targeted_rule_ids"]],
        email_wide_rules=[RuleVerdict(id=i, why=rationale.get(i, ""))
                          for i in loop.final["email_wide_rule_ids"]],
        stats=stats,
    )
