"""Architecture E — Claude Agent SDK over original design bibles.

One SDK session per blueprint (not per section). The agent reads
`simple_kb/{brand}/` (verbatim design_bible.json + _index.json) with Claude Code
built-ins and terminates via `finalize_blueprint_ruleset`, assigning passage refs
like `website.color_scheme_rules[3]` to sections and email-wide.

Experimental: opt-in via `--arch e` (not in `--arch all`). Does not use the
structured `kb/{brand}/` atomization or ToolRepo query tools.
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
    ALLOWED_BUILTIN_TOOLS,
    DISALLOWED_BUILTIN_TOOLS,
    mcp_allowed_tool_names,
    tool_specs_to_mcp_server,
)
from shared.llm import Trace, Usage, _truncate
from shared.prompts import TASK_BRIEF_SIMPLE, render_full_blueprint_context
from shared.schemas import Blueprint, BlueprintSection, EmailWideRule, RuleVerdict, SectionResult
from shared.simple_kb import SimpleBible, finalize_blueprint_spec

ARCH_ID = "e"
DEFAULT_MAX_TURNS = 32
MCP_SERVER = "simple_kb"

SYSTEM_PROMPT = """You are a brand-rule navigation agent for pharma email generation.
Your working directory IS this brand's ORIGINAL design bible folder on the local
filesystem. Navigate it with Claude Code tools: Read, Glob, Grep, Bash (and Write for
scratch notes). There are NO structured KB query tools — only the original bible.

{task_brief}

## Layout (cwd = simple_kb/{{brand}})
- `design_bible.json` — original bible. Top-level `website` keys are categories
  (`other_rules`, `color_scheme_rules`, `design_pattern_rules`, `content_pattern_rules`,
  optionally `internal_banner_rules`). Each array entry is ONE selectable passage.
- `_index.json` — compact catalog: ref, category, index, title, preview, chars.
  Prefer reading `_index.json` first, then Read / Grep specific passages from
  `design_bible.json` only when the preview is insufficient.
- Passage refs MUST be exact `_index.json` `ref` values, e.g.
  `website.color_scheme_rules[5]` or `website.content_pattern_rules[0]`.

## Turn budget
You have a hard turn cap. Do not burn it exploring:
1. Turns 1–6: Read `_index.json`, skim titles/previews, Grep design_bible.json for
   devices named in the blueprint (CTA, callout, accent shape, typography, palette…).
2. By ~turn 8–12: call finalize_blueprint_ruleset with your best current assignment for
   EVERY section_id plus email_wide_rule_ids. Coverage / unknown-ref errors are the
   intended iteration loop — fix only what finalize lists, then finalize again.
3. Stop once finalize succeeds.

## Finalize shape reminder
```json
{{
  "sections": [
    {{"section_id": "intro", "targeted_rule_ids": ["website...."]}},
    {{"section_id": "cta", "targeted_rule_ids": ["website...."]}}
  ],
  "email_wide_rule_ids": ["website.other_rules[0]", "..."],
  "rationale": {{"website....": "one-line why"}}
}}
```
"""


async def run_blueprint(
    bible: SimpleBible,
    blueprint: Blueprint,
    sections: list[BlueprintSection],
    *,
    model: Optional[str] = None,
    include_design_concept: bool = True,
    trace: Trace,
    usage: Usage,
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = 128_000,  # runner parity; SDK manages its own budgets
    thinking_effort: Optional[str] = "medium",  # runner parity; unused here
) -> tuple[list[SectionResult], list[EmailWideRule], dict[str, Any]]:
    """Run one whole-blueprint Claude SDK session.

    Returns (section_results, email_wide_rules, stats).
    """
    del max_tokens, thinking_effort
    model = model or config.AGENT_MODEL
    t0 = time.time()
    cwd = str(bible.root)
    expected_ids = [s.section_id for s in sections]
    system = SYSTEM_PROMPT.format(task_brief=TASK_BRIEF_SIMPLE)
    user = render_full_blueprint_context(blueprint, sections, include_design_concept)

    finalize = finalize_blueprint_spec(bible, expected_section_ids=expected_ids)
    final_box: dict[str, Any] = {}
    server = tool_specs_to_mcp_server(
        [finalize],
        server_name=MCP_SERVER,
        trace=trace,
        agent_name="orchestrator_e",
        on_terminal=lambda payload: final_box.update(final=payload),
    )
    allowed = list(ALLOWED_BUILTIN_TOOLS) + mcp_allowed_tool_names([finalize], MCP_SERVER)

    options = ClaudeAgentOptions(
        system_prompt=system,
        model=model,
        max_turns=max_turns,
        cwd=cwd,
        mcp_servers={MCP_SERVER: server},
        allowed_tools=allowed,
        disallowed_tools=DISALLOWED_BUILTIN_TOOLS,
        permission_mode="bypassPermissions",
    )

    tool_call_count = 0
    turns = 0
    error: Optional[str] = None
    agent_name = "orchestrator_e"

    if trace:
        trace.log(
            "arch_e_config",
            agent_name,
            cwd=cwd,
            max_turns=max_turns,
            passage_count=len(bible.refs),
            sections=expected_ids,
            allowed_tools=allowed,
        )

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
                        agent_name,
                        model=model,
                        turn=turns,
                        text=_truncate("\n".join(text_parts), 400),
                        tool_calls=tool_calls,
                    )
            elif isinstance(message, ToolResultBlock):
                if trace:
                    trace.log(
                        "sdk_tool_result",
                        agent_name,
                        tool=message.tool_use_id,
                        result_preview=_truncate(block_preview(message), 300),
                    )
            elif isinstance(message, ResultMessage):
                if message.total_cost_usd:
                    usage.cost_usd += message.total_cost_usd
                usage.llm_calls += 1
                if message.is_error:
                    error = message.result or "claude-agent-sdk run failed"
    except Exception as e:  # noqa: BLE001 — recorded on results; must not raise past runner
        error = repr(e)

    stats = {
        "turns": turns,
        "tool_calls": tool_call_count,
        "latency_s": round(time.time() - t0, 1),
        "passage_count": len(bible.refs),
    }

    final = final_box.get("final")
    if final is None:
        err = error or "no finalize call"
        return (
            [
                SectionResult(section_id=s.section_id, stats=stats, error=err)
                for s in sections
            ],
            [],
            stats,
        )

    rationale = final.get("rationale", {})
    by_id = {row["section_id"]: row for row in final["sections"]}
    section_results: list[SectionResult] = []
    for s in sections:
        row = by_id[s.section_id]
        section_results.append(
            SectionResult(
                section_id=s.section_id,
                targeted_rules=[
                    RuleVerdict(id=ref, why=rationale.get(ref, ""))
                    for ref in row["targeted_rule_ids"]
                ],
                email_wide_rules=[],  # email-wide is blueprint-level for arch e
                stats=stats,
            )
        )

    email_wide = [
        EmailWideRule(
            id=ref,
            voted_by=[s.section_id for s in sections],
            why=rationale.get(ref, ""),
        )
        for ref in final["email_wide_rule_ids"]
    ]
    return section_results, email_wide, stats


def block_preview(message: ToolResultBlock) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if not content:
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, TextBlock):
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
        elif hasattr(block, "text"):
            parts.append(str(getattr(block, "text")))
    return "\n".join(parts)
