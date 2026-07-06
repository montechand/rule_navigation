"""Thin async LLM layer: provider routing (Anthropic/OpenAI), a unified tool-call
loop with chat history, JSON helpers, usage/cost counters, and JSONL tracing.

Neutral message format used internally:
  {"role": "user"|"assistant", "content": str, "tool_calls": [{id,name,args}]}
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

_anthropic_client: Optional[AsyncAnthropic] = None
_openai_client: Optional[AsyncOpenAI] = None


def _anthropic() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic()
    return _anthropic_client


def _openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI()
    return _openai_client


def is_anthropic_model(model: str) -> bool:
    return model.startswith("claude")


# Adaptive-thinking effort levels (Anthropic only). "none" disables thinking. The API decides
# the actual thinking token spend per request; effort is soft guidance, not a hard budget.
THINKING_EFFORTS = ("low", "medium", "high", "xhigh", "max")


# USD per 1M tokens (input, output); rough, for run comparison only.
_PRICES = {
    "claude-opus": (15.0, 75.0),
    "claude-sonnet": (3.0, 15.0),
    "claude-haiku": (0.8, 4.0),
    "gpt-5": (1.25, 10.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "gpt-4.1": (2.0, 8.0),
    "text-embedding-3-large": (0.13, 0.0),
}


def _price_for(model: str) -> tuple[float, float]:
    for prefix, p in sorted(_PRICES.items(), key=lambda kv: -len(kv[0])):
        if model.startswith(prefix):
            return p
    return (0.0, 0.0)


class Usage:
    """Mutable aggregate of token usage + cost across calls."""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.llm_calls = 0
        self.cost_usd = 0.0

    def add(self, model: str, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.llm_calls += 1
        pin, pout = _price_for(model)
        self.cost_usd += (input_tokens * pin + output_tokens * pout) / 1e6

    def merge(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.llm_calls += other.llm_calls
        self.cost_usd += other.cost_usd

    def as_dict(self) -> dict[str, Any]:
        return {
            "llm_calls": self.llm_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost_usd, 4),
        }


class Trace:
    """Append-only event log; one Trace per section run, dumped as JSONL."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self._t0 = time.time()

    def log(self, kind: str, agent: str, **data: Any) -> None:
        self.events.append({"t": round(time.time() - self._t0, 3), "kind": kind, "agent": agent, **data})

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for e in self.events:
                f.write(json.dumps(e, default=str) + "\n")


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass
class AssistantTurn:
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str
    # Raw Anthropic thinking/redacted_thinking blocks (empty for OpenAI or when
    # thinking is disabled). Must be replayed verbatim in the next request's history —
    # Anthropic requires the thinking blocks that preceded a tool_use to come back
    # unmodified alongside the tool_result for the model to keep reasoning coherently.
    thinking_blocks: list[dict[str, Any]] = field(default_factory=list)


class ToolError(Exception):
    """Raised by tool handlers; message is fed back to the model as the tool result."""


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the arguments object
    handler: Callable[[dict[str, Any]], Awaitable[Any]]
    terminal: bool = False  # a successful call of a terminal tool ends the loop


async def _call_with_retry(fn: Callable[[], Awaitable[Any]], attempts: int = 5) -> Any:
    delay = 2.0
    for attempt in range(attempts):
        try:
            return await fn()
        except Exception as e:  # noqa: BLE001 — re-raised on final attempt below
            transient = any(
                s in type(e).__name__.lower() or s in str(e).lower()
                for s in ("ratelimit", "overloaded", "timeout", "529", "503", "connection")
            )
            if attempt == attempts - 1 or not transient:
                raise
            await asyncio.sleep(delay)
            delay *= 2


async def chat(
    model: str,
    system: str,
    messages: list[dict[str, Any]],
    tools: Optional[list[ToolSpec]] = None,
    max_tokens: int = 8192,
    usage: Optional[Usage] = None,
    thinking_effort: Optional[str] = None,
) -> AssistantTurn:
    """One model call in the neutral format, routed by provider.

    thinking_effort: one of THINKING_EFFORTS ("low"/"medium"/"high"/"xhigh"/"max") to enable
    Anthropic adaptive thinking guided by that effort level, or None/"none" to disable.
    Ignored for non-Anthropic models (no equivalent wired up here).
    """
    if is_anthropic_model(model):
        return await _chat_anthropic(model, system, messages, tools, max_tokens, usage, thinking_effort)
    return await _chat_openai(model, system, messages, tools, max_tokens, usage)


# ---------------------------------------------------------------------------
# Anthropic adapter
# ---------------------------------------------------------------------------

def _to_anthropic_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        if m["role"] == "assistant":
            blocks: list[dict[str, Any]] = []
            # Thinking blocks must lead the content array, exactly as returned, when
            # replaying an assistant turn that used extended thinking.
            blocks.extend(m.get("thinking_blocks", []))
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for tc in m.get("tool_calls", []):
                blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["args"]})
            out.append({"role": "assistant", "content": blocks or [{"type": "text", "text": ""}]})
        elif m["role"] == "tool":
            block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
            if m.get("is_error"):
                block["is_error"] = True
            # Consecutive tool results must merge into one user message.
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list) \
                    and out[-1]["content"] and out[-1]["content"][0].get("type") == "tool_result":
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        else:
            out.append({"role": "user", "content": m["content"]})
    return out


async def _chat_anthropic(model, system, messages, tools, max_tokens, usage,
                           thinking_effort: Optional[str] = None) -> AssistantTurn:
    kwargs: dict[str, Any] = {
        "model": model,
        "system": system,
        "messages": _to_anthropic_messages(messages),
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = [
            {"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools
        ]
    if thinking_effort and thinking_effort != "none":
        if thinking_effort not in THINKING_EFFORTS:
            raise ValueError(f"unknown thinking_effort {thinking_effort!r}; "
                             f"expected one of {THINKING_EFFORTS} or 'none'")
        # Adaptive thinking: the model itself decides whether/how much to think per
        # request; effort is soft guidance passed via output_config, not a token budget.
        # (Manual thinking.enabled + budget_tokens is deprecated on current models.)
        kwargs["thinking"] = {"type": "adaptive"}
        kwargs["output_config"] = {"effort": thinking_effort}

    async def _do() -> Any:
        # Stream + accumulate: required by the SDK for large max_tokens requests.
        async with _anthropic().messages.stream(**kwargs) as stream:
            return await stream.get_final_message()

    resp = await _call_with_retry(_do)
    text_parts, tool_calls, thinking_blocks = [], [], []
    for block in resp.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append(ToolCall(id=block.id, name=block.name, args=dict(block.input or {})))
        elif block.type == "thinking":
            thinking_blocks.append({"type": "thinking", "thinking": block.thinking, "signature": block.signature})
        elif block.type == "redacted_thinking":
            thinking_blocks.append({"type": "redacted_thinking", "data": block.data})
    if usage is not None:
        usage.add(model, resp.usage.input_tokens, resp.usage.output_tokens)
    return AssistantTurn(text="\n".join(text_parts), tool_calls=tool_calls, stop_reason=resp.stop_reason or "",
                         thinking_blocks=thinking_blocks)


# ---------------------------------------------------------------------------
# OpenAI adapter
# ---------------------------------------------------------------------------

def _to_openai_messages(system: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for m in messages:
        if m["role"] == "assistant":
            entry: dict[str, Any] = {"role": "assistant", "content": m.get("content") or None}
            if m.get("tool_calls"):
                entry["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])},
                    }
                    for tc in m["tool_calls"]
                ]
            out.append(entry)
        elif m["role"] == "tool":
            out.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
        else:
            out.append({"role": "user", "content": m["content"]})
    return out


async def _chat_openai(model, system, messages, tools, max_tokens, usage) -> AssistantTurn:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": _to_openai_messages(system, messages),
    }
    if tools:
        kwargs["tools"] = [
            {
                "type": "function",
                "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
            }
            for t in tools
        ]
    resp = await _call_with_retry(lambda: _openai().chat.completions.create(**kwargs))
    choice = resp.choices[0]
    tool_calls = []
    for tc in choice.message.tool_calls or []:
        try:
            args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {"_malformed_arguments": tc.function.arguments}
        tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, args=args))
    if usage is not None and resp.usage:
        usage.add(model, resp.usage.prompt_tokens, resp.usage.completion_tokens)
    return AssistantTurn(
        text=choice.message.content or "", tool_calls=tool_calls, stop_reason=choice.finish_reason or ""
    )


# ---------------------------------------------------------------------------
# Tolerant JSON completion (used by migration / summaries / composer)
# ---------------------------------------------------------------------------

def parse_json_loose(text: str) -> Any:
    """Parse JSON out of model text: strips code fences, grabs outermost object/array."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start_candidates = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not start_candidates:
        raise ValueError(f"No JSON found in model output: {text[:200]!r}")
    start = min(start_candidates)
    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("Unbalanced JSON in model output")


async def complete_json(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 16000,
    usage: Optional[Usage] = None,
) -> Any:
    turn = await chat(model, system, [{"role": "user", "content": user}], tools=None,
                      max_tokens=max_tokens, usage=usage)
    return parse_json_loose(turn.text)


# ---------------------------------------------------------------------------
# The unified tool loop
# ---------------------------------------------------------------------------

@dataclass
class LoopResult:
    final: Optional[Any]  # value returned by the terminal tool handler (None if never called)
    messages: list[dict[str, Any]]
    turns: int
    tool_call_count: int = 0
    error: Optional[str] = None


def _truncate(s: str, n: int = 600) -> str:
    return s if len(s) <= n else s[:n] + f"... [{len(s) - n} chars truncated]"


async def run_tool_loop(
    *,
    model: str,
    system: str,
    user_message: str,
    tools: list[ToolSpec],
    max_turns: int = 20,
    usage: Optional[Usage] = None,
    trace: Optional[Trace] = None,
    agent_name: str = "agent",
    max_tokens: int = 8192,
    thinking_effort: Optional[str] = None,
) -> LoopResult:
    """Run an agent loop: model <-> tools with full chat history, until a terminal
    tool succeeds or max_turns is hit. Tool handler exceptions (ToolError) are fed
    back to the model as error results so it can self-correct.
    """
    by_name = {t.name: t for t in tools}
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    tool_call_count = 0
    nudged = False

    for turn_i in range(max_turns):
        turn = await chat(model, system, messages, tools=tools, usage=usage,
                          max_tokens=max_tokens, thinking_effort=thinking_effort)
        if trace:
            trace.log(
                "llm_call", agent_name, model=model, turn=turn_i,
                text=_truncate(turn.text, 400),
                tool_calls=[{"name": tc.name, "args": _truncate(json.dumps(tc.args, default=str), 800)}
                            for tc in turn.tool_calls],
                stop_reason=turn.stop_reason,
                thinking=_truncate("\n".join(b.get("thinking", "") for b in turn.thinking_blocks), 800)
                if turn.thinking_blocks else None,
            )
        messages.append({
            "role": "assistant",
            "content": turn.text,
            "tool_calls": [{"id": tc.id, "name": tc.name, "args": tc.args} for tc in turn.tool_calls],
            "thinking_blocks": turn.thinking_blocks,
        })

        if not turn.tool_calls:
            # Model stopped talking without finalizing: nudge once, then give up.
            if nudged:
                return LoopResult(final=None, messages=messages, turns=turn_i + 1,
                                  tool_call_count=tool_call_count,
                                  error="model ended without calling the terminal tool")
            nudged = True
            terminal_names = [t.name for t in tools if t.terminal]
            messages.append({
                "role": "user",
                "content": f"You must finish by calling {terminal_names or ['the terminal tool']}. "
                           "Call it now with your best answer.",
            })
            continue

        for tc in turn.tool_calls:
            tool_call_count += 1
            spec = by_name.get(tc.name)
            if spec is None:
                messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.name,
                                 "content": f"Unknown tool: {tc.name}", "is_error": True})
                continue
            try:
                result = await spec.handler(tc.args)
            except ToolError as e:
                if trace:
                    trace.log("tool_error", agent_name, tool=tc.name, error=str(e))
                messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.name,
                                 "content": f"ERROR: {e}", "is_error": True})
                continue
            except Exception as e:  # noqa: BLE001 — surfaced to the model, loop continues; run fails via max_turns if persistent
                if trace:
                    trace.log("tool_crash", agent_name, tool=tc.name, error=repr(e))
                messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.name,
                                 "content": f"ERROR: tool crashed: {e!r}", "is_error": True})
                continue

            if spec.terminal:
                if trace:
                    trace.log("finalize", agent_name, tool=tc.name)
                return LoopResult(final=result, messages=messages, turns=turn_i + 1,
                                  tool_call_count=tool_call_count)

            content = result if isinstance(result, str) else json.dumps(result, default=str)
            if trace:
                trace.log("tool_call", agent_name, tool=tc.name,
                          args=_truncate(json.dumps(tc.args, default=str), 800),
                          result_chars=len(content), result_preview=_truncate(content, 300))
            messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.name, "content": content})

    return LoopResult(final=None, messages=messages, turns=max_turns,
                      tool_call_count=tool_call_count, error=f"max_turns ({max_turns}) exceeded")
