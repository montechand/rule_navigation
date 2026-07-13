"""Architecture D — Claude Agent SDK filesystem retriever.

The agent runs on the local server filesystem (Docker today): Claude Code built-ins
(Read / Bash / Glob / Grep) navigate `kb/{brand}/` directly. Two experimental arms:

  tool_mode="fs"   — built-ins only (+ terminal finalize MCP, held constant for output
                     contract). Prompt teaches KB layout + FS navigation.
  tool_mode="full" — built-ins + full ToolRepo MCP tools (+ finalize). Prompt teaches
                     both FS and structured tools.

Compare the two arms over the same blueprints. Experimental: not in `--arch all`.
"""

from __future__ import annotations

import time
from typing import Any, Literal, Optional

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
from shared.prompts import TASK_BRIEF, render_blueprint_context, schema_primer
from shared.schemas import Blueprint, BlueprintSection, RuleVerdict, SectionResult
from shared.tool_repo import ToolRepo

ARCH_ID = "d"
# FS navigation is turn-hungry (many small Bash reads). Empirically at max_turns=24,
# successes finalized on attempt 2 around turn ~40 of the SDK counter; failures never
# called finalize at all — they burned the budget exploring. Cap raised; prompts below
# also force an early first finalize so coverage-check iteration fits.
DEFAULT_MAX_TURNS = 48
MCP_SERVER = "kb"
ToolMode = Literal["fs", "full"]

# ---------------------------------------------------------------------------
# Prompt A — filesystem only (no structured KB tools)
# ---------------------------------------------------------------------------

SYSTEM_FS = """You are a brand-rule navigation agent for pharma email generation.
Your working directory IS this brand's knowledge base on the local filesystem. Navigate
it with Claude Code tools: Read, Glob, Grep, Bash (and Write if you need scratch notes).
There are NO structured query tools — you must find rules by reading and searching files.

{task_brief}

## KB layout (cwd = brand KB root)
- `schema/` — start here: `overview.md`, `section_vocab.md`, …
- `rules/_index.json` — compact catalog of every rule (id, sections, scope, hardness,
  summary). Prefer ONE python/jq dump over many tiny Bash calls.
- `rules/{{rule_id}}.json` — full rule payloads (read only uncertain candidates)
- `tokens/`, `assets/`, `subtypes/`, `templates/` — side entities (each with `_index.json`)
- `graph/graph.json` — typed edges (optional; do NOT deep-walk before first finalize)

## Turn budget (critical)
You have a hard turn cap. DO NOT spend the whole budget exploring.
1. Turns 1–8: gather candidates with LARGE batched reads (see script below). Map section
   types. Skim `_index.json` summaries — do not cat every rule file.
2. By ~turn 10–15: call finalize_section_ruleset with your BEST CURRENT answer. Put every
   coverage candidate you are unsure about into `excluded` with a one-line reason (or
   include it). A coverage-check error listing missing ids is EXPECTED and cheap to fix —
   that is the intended iteration loop.
3. Turns after first finalize: only resolve the ids finalize complained about (Read those
   few JSON files), then finalize again. Stop once finalize succeeds.
Do NOT graph-walk, token-walk, or open templates before the first finalize attempt.

## Preferred first Bash (adapt section types)
```bash
python3 - <<'PY'
import json
TYPES = {{"hero", "intro"}}  # <-- your mapped section types
idx = json.load(open("rules/_index.json"))
targeted = [r for r in idx if r.get("sections") and set(r["sections"]) & TYPES]
email_wide = [r for r in idx if r.get("sections") is None]
print("TARGETED", len(targeted))
for r in targeted:
    print(r["id"], r.get("hardness"), r.get("applies_when"), "|", r["summary"][:100])
print("EMAIL_WIDE", len(email_wide))
for r in email_wide:
    print(r["id"], r.get("hardness"), r.get("applies_when"), "|", r["summary"][:100])
PY
```
Then Read full JSON only for rules whose summary / applies_when is unclear. Prefer Grep
over dozens of `cat` calls when searching tokens/ or rule text.

{schema_primer}
"""

# ---------------------------------------------------------------------------
# Prompt B — filesystem + structured ToolRepo MCP tools
# ---------------------------------------------------------------------------

SYSTEM_FULL = """You are a brand-rule navigation agent for pharma email generation.
Your working directory IS this brand's knowledge base on the local filesystem. You have
TWO tool surfaces:

1. Claude Code filesystem tools — Read, Glob, Grep, Bash — for raw file navigation of
   the KB tree (schema docs, indexes, full JSON rows, graph.json).
2. Structured KB MCP tools — query_rules, get_rules, keyword_search, vector_search,
   query_tokens / search_tokens / resolve_token, rules_for_section / rules_for_token /
   neighbors, list_templates / rules_for_template, etc. Prefer these when a facet filter
   or graph walk is faster than grepping files; fall back to filesystem when you need
   the raw doc / an unindexed field / a second look.

{task_brief}

## KB layout (cwd = brand KB root) — same as filesystem-only arm
schema/ · rules/(_index.json + {{id}}.json) · tokens/ · assets/ · subtypes/ · templates/
· graph/graph.json · groups/

## Turn budget (critical)
You have a hard turn cap. Prefer structured tools (fewer round-trips than Bash).
1. Early: query_rules for mapped section types + null-selector / include_all_section_rules
   pass for the email-wide pool. Optional: keyword_search / search_tokens for devices in
   the design concept.
2. By ~turn 8–12: call finalize_section_ruleset with best current answer. Put unsure
   coverage candidates in `excluded` with reasons. Coverage-check errors are the intended
   iteration loop — fix only the listed ids, then finalize again.
3. Do not exhaust the budget exploring; stop once finalize succeeds.

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
    tool_mode: ToolMode = "fs",
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = 128_000,  # accepted for runner parity; SDK manages its own budgets
    thinking_effort: Optional[str] = "medium",  # accepted for runner parity; unused here
) -> SectionResult:
    del max_tokens, thinking_effort  # arch-d uses Claude Agent SDK defaults
    model = model or config.AGENT_MODEL
    t0 = time.time()
    kb_cwd = str(config.kb_dir(repo.kb.brand))
    primer = schema_primer(repo.kb)
    if tool_mode == "full":
        system = SYSTEM_FULL.format(task_brief=TASK_BRIEF, schema_primer=primer)
    else:
        system = SYSTEM_FS.format(task_brief=TASK_BRIEF, schema_primer=primer)
    user = render_blueprint_context(blueprint, section, include_design_concept)

    # Finalize is held constant across both arms so the FNR coverage contract stays
    # identical; the experimental variable is whether structured ToolRepo tools are
    # also available.
    finalize = repo.finalize_spec()
    mcp_specs = ([finalize] if tool_mode == "fs" else repo.specs() + [finalize])

    final_box: dict[str, Any] = {}
    kb_server = tool_specs_to_mcp_server(
        mcp_specs,
        server_name=MCP_SERVER,
        trace=trace,
        agent_name=f"orchestrator_d_{tool_mode}",
        on_terminal=lambda payload: final_box.update(final=payload),
    )
    allowed = list(ALLOWED_BUILTIN_TOOLS) + mcp_allowed_tool_names(mcp_specs, MCP_SERVER)

    options = ClaudeAgentOptions(
        system_prompt=system,
        model=model,
        max_turns=max_turns,
        cwd=kb_cwd,
        mcp_servers={MCP_SERVER: kb_server},
        allowed_tools=allowed,
        disallowed_tools=DISALLOWED_BUILTIN_TOOLS,
        permission_mode="bypassPermissions",
    )

    tool_call_count = 0
    turns = 0
    error: Optional[str] = None
    agent_name = f"orchestrator_d_{tool_mode}"

    if trace:
        trace.log("arch_d_config", agent_name, tool_mode=tool_mode, cwd=kb_cwd,
                  max_turns=max_turns, allowed_tools=allowed)

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
                    preview = block_preview(message)
                    trace.log(
                        "sdk_tool_result",
                        agent_name,
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
        "tool_mode": tool_mode,
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
