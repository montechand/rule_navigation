"""Bridge shared ToolRepo ToolSpec handlers to claude-agent-sdk in-process MCP tools."""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server

from .llm import ToolError, ToolSpec, Trace

SERVER_NAME = "kb"
# Claude Code built-ins we block so arch_d navigation is KB-tool-only.
DISALLOWED_BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebSearch",
    "WebFetch",
    "Task",
    "NotebookEdit",
    "KillShell",
    "TodoWrite",
]


def mcp_tool_name(spec_name: str, server_name: str = SERVER_NAME) -> str:
    return f"mcp__{server_name}__{spec_name}"


def mcp_allowed_tool_names(specs: list[ToolSpec], server_name: str = SERVER_NAME) -> list[str]:
    return [mcp_tool_name(s.name, server_name) for s in specs]


def _truncate(s: str, n: int = 600) -> str:
    return s if len(s) <= n else s[:n] + f"... [{len(s) - n} chars truncated]"


def tool_specs_to_mcp_server(
    specs: list[ToolSpec],
    *,
    server_name: str = SERVER_NAME,
    trace: Optional[Trace] = None,
    agent_name: str = "orchestrator_d",
    on_terminal: Optional[Callable[[Any], None]] = None,
):
    """Wrap ToolSpec handlers as an SDK MCP server config."""

    sdk_tools: list[SdkMcpTool[Any]] = []

    for spec in specs:

        async def handler(args: dict[str, Any], _spec: ToolSpec = spec) -> dict[str, Any]:
            try:
                result = await _spec.handler(args)
            except ToolError as e:
                if trace:
                    trace.log("tool_error", agent_name, tool=_spec.name, error=str(e))
                return {
                    "content": [{"type": "text", "text": f"ERROR: {e}"}],
                    "is_error": True,
                }
            except Exception as e:  # noqa: BLE001 — surfaced to the model as tool error
                if trace:
                    trace.log("tool_crash", agent_name, tool=_spec.name, error=repr(e))
                return {
                    "content": [{"type": "text", "text": f"ERROR: tool crashed: {e!r}"}],
                    "is_error": True,
                }

            if _spec.terminal:
                if trace:
                    trace.log("finalize", agent_name, tool=_spec.name)
                if on_terminal is not None:
                    on_terminal(result)

            content = result if isinstance(result, str) else json.dumps(result, default=str)
            if trace:
                trace.log(
                    "tool_call",
                    agent_name,
                    tool=_spec.name,
                    args=_truncate(json.dumps(args, default=str), 800),
                    result_chars=len(content),
                    result_preview=_truncate(content, 300),
                )
            return {"content": [{"type": "text", "text": content}]}

        sdk_tools.append(
            SdkMcpTool(
                name=spec.name,
                description=spec.description,
                input_schema=spec.parameters,
                handler=handler,
            )
        )

    return create_sdk_mcp_server(name=server_name, version="1.0.0", tools=sdk_tools)
