"""Architecture A — generalist orchestrator.

One agent loop with full chat history and the ENTIRE tool repository (filesystem, schema,
lookup, structured, keyword, vector, graph). It explores however it likes and must end by
calling the terminal finalize_section_ruleset tool, whose validated payload is the result.
"""

from __future__ import annotations

import time
from typing import Optional

from shared import config
from shared.llm import Trace, Usage, is_anthropic_model, run_tool_loop
from shared.prompts import TASK_BRIEF, render_blueprint_context, schema_primer
from shared.schemas import Blueprint, BlueprintSection, RuleVerdict, SectionResult
from shared.tool_repo import ToolRepo

ARCH_ID = "a"
MAX_TURNS = 60

SYSTEM_TEMPLATE = """You are a brand-rule navigation agent for pharma email generation.
You have a full toolbox over a structured brand-rules knowledge base: structured facet
queries, BM25 keyword search, semantic vector search, graph walks, raw filesystem
reads/grep, and schema docs.

{task_brief}

## Strategy that works well
1. get_section_vocab / describe_entity(overview) if you need orientation — the primer
   below already covers the basics.
2. Map the target section to section type(s), then run BOTH:
   - query_rules(section_types=[...], include_all_section_rules=false) for targeted selector matches
   - query_rules with include_all_section_rules-only pass (or rules_for_section with
     include_all_section_rules=true) to enumerate the null-selector baseline pool
3. Probe for conditionals and devices the blueprint implies: vector_search / keyword_search
   for the section's design concept, colors, components (waves, callouts, icons, buttons,
   images), and copy phrases (brand name, campaign names, symptom mentions).
4. Token pivot: for concrete details in the design concept (a hex, an opacity, a radius,
   an alignment, a font), search_tokens / query_tokens finds the token, then
   rules_for_token gives its governing rules — including conditional variants you'd
   otherwise miss.
5. Inspect uncertain candidates with get_rules(view='full') — check applies_when, audience,
   content_types before including them.
6. Call finalize_section_ruleset with your final answer, including your
   section_type_mapping and an `excluded` reason for every candidate you left out. If it
   errors (unknown ids / overlap / coverage check listing unaccounted rules), resolve each
   listed rule — include it or exclude it with a reason — and call again.

{schema_primer}
"""


async def run_section(
    repo: ToolRepo,
    blueprint: Blueprint,
    section: BlueprintSection,
    *,
    model: Optional[str] = None,
    include_design_concept: bool = True,
    trace: Trace,
    usage: Usage,
    max_tokens: int = 128_000,
    thinking_effort: Optional[str] = "medium",
) -> SectionResult:
    model = model or config.AGENT_MODEL
    t0 = time.time()
    tools = repo.specs() + [repo.finalize_spec()]
    system = SYSTEM_TEMPLATE.format(task_brief=TASK_BRIEF, schema_primer=schema_primer(repo.kb))
    user = render_blueprint_context(blueprint, section, include_design_concept)

    # OpenAI reasoning models reject function tools + reasoning on Chat Completions, so
    # route them through the Responses API. This is inherently a reasoning-plus-tools
    # workflow whose coverage-repair cycle benefits from preserving reasoning between
    # calls. Anthropic models stay on the default chat path.
    api = "chat_completions" if is_anthropic_model(model) else "responses"

    loop = await run_tool_loop(
        model=model,
        system=system,
        user_message=user,
        tools=tools,
        max_turns=MAX_TURNS,
        usage=usage,
        trace=trace,
        agent_name="orchestrator_a",
        max_tokens=max_tokens,
        thinking_effort=thinking_effort,
        api=api,
    )

    stats = {"turns": loop.turns, "tool_calls": loop.tool_call_count,
             "latency_s": round(time.time() - t0, 1)}
    if loop.final is None:
        return SectionResult(section_id=section.section_id, stats=stats,
                             error=loop.error or "no finalize call")
    rationale = loop.final.get("rationale", {})
    return SectionResult(
        section_id=section.section_id,
        section_types=loop.final.get("section_type_mapping", []),
        targeted_rules=[RuleVerdict(id=i, why=rationale.get(i, ""))
                        for i in loop.final["targeted_rule_ids"]],
        email_wide_rules=[RuleVerdict(id=i, why=rationale.get(i, ""))
                          for i in loop.final["email_wide_rule_ids"]],
        excluded_rules=[RuleVerdict(id=i, why=w)
                        for i, w in loop.final.get("excluded", {}).items()],
        stats=stats,
    )
