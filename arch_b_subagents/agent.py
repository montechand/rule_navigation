"""Architecture B — orchestrator + querying-style specialist sub-agents.

The orchestrator cannot search the KB directly; it delegates to three specialists, each an
independent tool loop restricted to one querying style:

  vector specialist  — semantic search over rule embeddings (summary/intent/text)
  graph specialist   — graph walks (section edges, token/asset links, relations)
  lexical specialist — BM25 keyword, regex grep, structured facet queries over indices

Each specialist reports candidate rule ids with evidence + confidence via its terminal
tool. The orchestrator can re-query with refined questions, inspect candidates with
get_rules, and must end with finalize_section_ruleset.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from shared import config
from shared.llm import ToolError, ToolSpec, Trace, Usage, run_tool_loop
from shared.prompts import TASK_BRIEF, render_blueprint_context, schema_primer
from shared.schemas import Blueprint, BlueprintSection, RuleVerdict, SectionResult
from shared.tool_repo import ToolRepo

ARCH_ID = "b"
ORCHESTRATOR_MAX_TURNS = 16
SPECIALIST_MAX_TURNS = 10

SPECIALISTS: dict[str, dict[str, Any]] = {
    "vector": {
        "tools": ["vector_search", "get_rules", "get_section_vocab"],
        "blurb": ("You are the SEMANTIC search specialist. Your only retrieval device is "
                  "vector search over three embedding collections (rule_summary, rule_intent, "
                  "rule_text). Issue several differently-phrased queries (design concept "
                  "wording, visual devices, copy intent, conditions) and across collections; "
                  "verify borderline hits with get_rules(view='full')."),
    },
    "graph": {
        "tools": ["rules_for_section", "rules_for_subtype", "rules_for_template",
                  "list_templates", "rules_for_token", "neighbors", "related_rules",
                  "resolve_token", "get_rules", "get_entity", "get_section_vocab"],
        "blurb": ("You are the GRAPH specialist. Navigate typed edges: section nodes "
                  "(sec_hero, sec_cta, ...), rule->token/asset/governance links, semantic "
                  "token->primitive resolves_to edges, class/template fills_section and "
                  "hosts_section edges (rules_for_subtype = class view; rules_for_template "
                  "= instance view incl. usage_conditions and pick-one group alternates), "
                  "asset pairing edges, rule-rule relations (refines/conflicts/overrides/...). "
                  "Start from the mapped section node(s) via rules_for_section (set "
                  "include_all_section_rules=true once to see the email-wide pool), then "
                  "walk neighbors of the strongest hits to find conditioned/related rules."),
    },
    "lexical": {
        "tools": ["keyword_search", "grep", "query_rules", "query_tokens", "search_tokens",
                  "rules_for_token", "resolve_token", "read_file", "list_dir", "get_rules",
                  "get_section_vocab"],
        "blurb": ("You are the LEXICAL/STRUCTURED specialist. Use BM25 keyword_search for "
                  "terminology, grep for exact strings (hex codes, px values, component and "
                  "campaign names), and query_rules for closed-facet filters (rule_class, "
                  "section_types, scope, hardness, constraint_type). The token layer is "
                  "yours too: search_tokens/query_tokens pivot from a concrete value or "
                  "element path to its token, then rules_for_token to the governing rules. "
                  "Cross-check counts: query_rules is exhaustive over the index, so use it "
                  "to enumerate pools."),
    },
}

SPECIALIST_SYSTEM = """{blurb}

You work for an orchestrator that assembles the final ruleset for one email section. Answer
ITS question about the brand-rules KB. Cast a wide net within your querying style; you are
scored on recall of applicable rules first, precision second.

When done, call report_candidates exactly once:
- candidates: every plausibly applicable rule you found — rule_id, one-line evidence
  (grounded in the rule's fields), confidence 0-1
- Split notes: flag rules that look email-wide (selector null / evaluation_scope=email)
  in the note field as 'email_wide'.

{schema_primer}
"""

ORCHESTRATOR_SYSTEM = """You are the orchestrator of a team of three KB-querying specialists
for brand-rule navigation. You cannot search the knowledge base yourself; you interrogate it
through your team, then decide.

{task_brief}

## Your team (delegation tools)
- ask_vector_specialist — semantic/embedding search; best for fuzzy intent ("what rules
  govern warm lifestyle photography?"), design-concept phrasing, tone.
- ask_graph_specialist — typed graph walks; best for exhaustive per-section enumeration,
  token/asset-linked rules, related/refining rules.
- ask_lexical_specialist — keyword/regex/structured facets; best for exact terms (hex,
  component names, campaign names) and exhaustive facet pools (e.g. all assembly rules).

## Method
1. Map the target section to section vocabulary (get_section_vocab if unsure).
2. Delegate in parallel-minded fashion: ask the graph specialist for the section's rule
   pool + email-wide pool; ask the lexical specialist for facet pools and exact-term hits
   implied by the blueprint; ask the vector specialist for fuzzy/conditional matches from
   the design concept and copy.
3. Ask follow-up questions where reports disagree or leave gaps (devices in the section,
   conditions like dark background, campaign content, position in email).
4. Verify borderline candidates with get_rules(view='full') — audience, content_types,
   applies_when must actually fit.
5. Call finalize_section_ruleset exactly once. Fix and retry if it reports errors.

{schema_primer}
"""


def _specialist_spec(kind: str, repo: ToolRepo, section_context: str,
                     model: str, usage: Usage, trace: Trace) -> ToolSpec:
    meta = SPECIALISTS[kind]

    def report_candidates_spec() -> ToolSpec:
        async def handler(args: dict[str, Any]) -> Any:
            candidates = args.get("candidates") or []
            if not isinstance(candidates, list):
                raise ToolError("candidates must be an array")
            cleaned = []
            unknown = []
            for c in candidates:
                if not isinstance(c, dict) or "rule_id" not in c:
                    continue
                if c["rule_id"] not in repo.kb.rules:
                    unknown.append(c["rule_id"])
                    continue
                cleaned.append({
                    "rule_id": c["rule_id"],
                    "evidence": str(c.get("evidence", ""))[:200],
                    "confidence": float(c.get("confidence", 0.5)),
                    "note": str(c.get("note", ""))[:80],
                })
            if unknown:
                raise ToolError(f"unknown rule ids: {unknown}. Verify with get_rules and retry.")
            return {"candidates": cleaned, "notes": str(args.get("notes", ""))[:500]}

        return ToolSpec(
            name="report_candidates",
            description="FINAL ANSWER of this specialist: candidate rules with evidence.",
            parameters={
                "type": "object",
                "properties": {
                    "candidates": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "rule_id": {"type": "string"},
                            "evidence": {"type": "string"},
                            "confidence": {"type": "number"},
                            "note": {"type": "string",
                                     "description": "'email_wide' if the rule applies to every section"},
                        },
                        "required": ["rule_id", "evidence"],
                    }},
                    "notes": {"type": "string"},
                },
                "required": ["candidates"],
            },
            handler=handler,
            terminal=True,
        )

    async def delegate(args: dict[str, Any]) -> Any:
        question = args.get("question") or ""
        if not question.strip():
            raise ToolError("provide a question for the specialist")
        loop = await run_tool_loop(
            model=model,
            system=SPECIALIST_SYSTEM.format(blurb=meta["blurb"], schema_primer=schema_primer(repo.kb)),
            user_message=f"{section_context}\n\n## Orchestrator question\n{question}",
            tools=repo.specs(names=meta["tools"]) + [report_candidates_spec()],
            max_turns=SPECIALIST_MAX_TURNS,
            usage=usage,
            trace=trace,
            agent_name=f"specialist_{kind}",
        )
        if loop.final is None:
            return {"error": f"specialist failed: {loop.error}", "candidates": []}
        return loop.final

    return ToolSpec(
        name=f"ask_{kind}_specialist",
        description=f"Delegate a KB question to the {kind} specialist. {meta['blurb'][:180]}",
        parameters={
            "type": "object",
            "properties": {"question": {
                "type": "string",
                "description": "Specific, self-contained question (the specialist also sees the section context)",
            }},
            "required": ["question"],
        },
        handler=delegate,
    )


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

    delegation_tools = [
        _specialist_spec(kind, repo, section_context, model, usage, trace)
        for kind in SPECIALISTS
    ]
    inspection_tools = repo.specs(names=["get_rules", "get_section_vocab", "describe_entity"])
    tools = delegation_tools + inspection_tools + [repo.finalize_spec()]

    loop = await run_tool_loop(
        model=model,
        system=ORCHESTRATOR_SYSTEM.format(task_brief=TASK_BRIEF, schema_primer=schema_primer(repo.kb)),
        user_message=section_context,
        tools=tools,
        max_turns=ORCHESTRATOR_MAX_TURNS,
        usage=usage,
        trace=trace,
        agent_name="orchestrator_b",
    )

    stats = {"turns": loop.turns, "tool_calls": loop.tool_call_count,
             "latency_s": round(time.time() - t0, 1)}
    if loop.final is None:
        return SectionResult(section_id=section.section_id, stats=stats,
                             error=loop.error or "no finalize call")
    rationale = loop.final.get("rationale", {})
    return SectionResult(
        section_id=section.section_id,
        targeted_rules=[RuleVerdict(id=i, why=rationale.get(i, ""))
                        for i in loop.final["targeted_rule_ids"]],
        email_wide_rules=[RuleVerdict(id=i, why=rationale.get(i, ""))
                          for i in loop.final["email_wide_rule_ids"]],
        stats=stats,
    )
