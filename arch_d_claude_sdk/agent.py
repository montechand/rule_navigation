"""Architecture D — Claude Agent SDK retriever.

Uses anthropic's claude-agent-sdk with in-process MCP tools wrapping the shared
ToolRepo (same tool surface as arch A). Claude Code built-in tools are disallowed
so navigation stays KB-only. Experimental: not included in `--arch all` yet.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    query,
)

from shared import config
from shared.claude_sdk_bridge import (
    DISALLOWED_BUILTIN_TOOLS,
    mcp_allowed_tool_names,
    tool_specs_to_mcp_server,
)
from shared.llm import Trace, Usage, _truncate
from shared.prompts import TASK_BRIEF, render_blueprint_context, schema_primer
from shared.schemas import Blueprint, BlueprintSection, RuleVerdict, SectionResult
from shared.tool_repo import ToolRepo

ARCH_ID = "d"
MAX_TURNS = 24
MCP_SERVER = "kb"

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

    final_box: dict[str, Any] = {}
    kb_server = tool_specs_to_mcp_server(
        tools,
        server_name=MCP_SERVER,
        trace=trace,
        agent_name="orchestrator_d",
        on_terminal=lambda payload: final_box.update(final=payload),
    )
    allowed = mcp_allowed_tool_names(tools, MCP_SERVER)

    options = ClaudeAgentOptions(
        system_prompt=system,
        model=model,
        max_turns=MAX_TURNS,
        cwd=str(config.RULE_NAV_ROOT),
        mcp_servers={MCP_SERVER: kb_server},
        allowed_tools=allowed,
        disallowed_tools=DISALLOWED_BUILTIN_TOOLS,
        permission_mode="bypassPermissions",
    )

    tool_call_count = 0
    turns = 0
    error: Optional[str] = None

    try:
        async for message in query(prompt=user, options=options):
            if isinstance(message, AssistantMessage):
                turns += 1
                text_parts: list[str] = []
                tool_calls: list[dict[str, Any]] = []
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text_parts.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        tool_call_count += 1
                        tool_calls.append(
                            {
                                "name": block.name,
                                "args": _truncate(str(block.input), 800),
                            }
                        )
                if trace and (text_parts or tool_calls):
                    trace.log(
                        "llm_call",
                        "orchestrator_d",
                        model=model,
                        turn=turns,
                        text=_truncate("\n".join(text_parts), 400),
                        tool_calls=tool_calls,
                    )
            elif isinstance(message, ToolResultBlock):
                if trace:
                    preview = block_preview(message)
                    trace.log(
                        "sdk_tool_result",
                        "orchestrator_d",
                        tool=message.tool_use_id,
                        result_preview=_truncate(preview, 300),
                    )
            elif isinstance(message, ResultMessage):
                if message.total_cost_usd:
                    usage.cost_usd += message.total_cost_usd
                usage.llm_calls += 1
                if message.is_error:
                    error = message.result or "claude-agent-sdk run failed"
    except Exception as e:  # noqa: BLE001 — recorded on SectionResult; one section must not sink the run
        error = repr(e)

    stats = {
        "turns": turns,
        "tool_calls": tool_call_count,
        "latency_s": round(time.time() - t0, 1),
    }
    final = final_box.get("final")
    if final is None:
        return SectionResult(
            section_id=section.section_id,
            stats=stats,
            error=error or "no finalize call",
        )

    rationale = final.get("rationale", {})
    return SectionResult(
        section_id=section.section_id,
        section_types=final.get("section_type_mapping", []),
        targeted_rules=[
            RuleVerdict(id=i, why=rationale.get(i, "")) for i in final["targeted_rule_ids"]
        ],
        email_wide_rules=[
            RuleVerdict(id=i, why=rationale.get(i, "")) for i in final["email_wide_rule_ids"]
        ],
        excluded_rules=[
            RuleVerdict(id=i, why=w) for i, w in final.get("excluded", {}).items()
        ],
        stats=stats,
    )


def block_preview(message: ToolResultBlock) -> str:
    parts: list[str] = []
    for block in message.content:
        if isinstance(block, TextBlock):
            parts.append(block.text)
        elif hasattr(block, "text"):
            parts.append(str(getattr(block, "text")))
    return "\n".join(parts)
