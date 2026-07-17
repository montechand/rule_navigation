"""Thin async LLM layer: provider routing (Anthropic/OpenAI/Gemini), a unified tool-call
loop with chat history, JSON helpers, usage/cost counters, and JSONL tracing.

Neutral message format used internally:
  {"role": "user"|"assistant", "content": str, "tool_calls": [{id,name,args}]}
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

_anthropic_client: Optional[AsyncAnthropic] = None
_openai_client: Optional[AsyncOpenAI] = None
_openrouter_client: Optional[AsyncOpenAI] = None
_gemini_client: Any = None


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


def _openrouter() -> AsyncOpenAI:
    global _openrouter_client
    if _openrouter_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENROUTER_API_KEY")
        _openrouter_client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _openrouter_client


def _gemini() -> Any:
    global _gemini_client
    if _gemini_client is None:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai SDK is required for Gemini models. "
                "Install via: pip install google-genai"
            ) from exc
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GOOGLE_API_KEY (or GEMINI_API_KEY)")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def is_anthropic_model(model: str) -> bool:
    return model.startswith("claude")


def is_gemini_model(model: str) -> bool:
    return model.startswith("gemini")


def is_openrouter_model(model: str) -> bool:
    return model.startswith("openrouter/")


def openrouter_model_id(model: str) -> str:
    """Strip ``openrouter/`` and pass the remainder to the OpenRouter API."""
    if not is_openrouter_model(model):
        raise ValueError(f"not an OpenRouter model id: {model!r}")
    return model[len("openrouter/") :]


def native_openai_model_id(model: str) -> str:
    """Model id for the direct OpenAI API (strip optional ``openai/`` vendor prefix)."""
    if model.startswith("openai/"):
        return model[len("openai/") :]
    return model


def required_api_keys_for_models(*models: str) -> tuple[str, ...]:
    """Return sorted API-key env var names required for the given model ids."""
    keys: set[str] = set()
    for model in models:
        if is_openrouter_model(model):
            keys.add("OPENROUTER_API_KEY")
        elif is_anthropic_model(model):
            keys.add("ANTHROPIC_API_KEY")
        elif is_gemini_model(model):
            keys.add("GOOGLE_API_KEY")
        else:
            keys.add("OPENAI_API_KEY")
    return tuple(sorted(keys))


# Adaptive-thinking effort levels (Anthropic only). "none" disables thinking. The API decides
# the actual thinking token spend per request; effort is soft guidance, not a hard budget.
THINKING_EFFORTS = ("low", "medium", "high", "xhigh", "max")


# USD per 1M tokens (input, output); rough, for run comparison only.
_PRICES = {
    "openai/gpt-5.6-sol": (5.0, 30.0),
    "claude-opus": (15.0, 75.0),
    "claude-sonnet": (3.0, 15.0),
    "claude-haiku": (0.8, 4.0),
    "gpt-5": (1.25, 10.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "gpt-4.1": (2.0, 8.0),
    "gemini-3.5-flash": (0.15, 0.6),
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
    max_tokens: int = 128_000,
    usage: Optional[Usage] = None,
    thinking_effort: Optional[str] = None,
    json_mode: bool = False,
) -> AssistantTurn:
    """One model call in the neutral format, routed by provider.

    thinking_effort: one of THINKING_EFFORTS ("low"/"medium"/"high"/"xhigh"/"max") to enable
    Anthropic adaptive thinking guided by that effort level, or None/"none" to disable.
    Ignored for non-Anthropic models (no equivalent wired up here).

    json_mode: ask the provider to enforce syntactically valid JSON output
    (Gemini response_mime_type / OpenAI response_format). Ignored for Anthropic,
    which has no equivalent constraint.
    """
    if is_anthropic_model(model):
        return await _chat_anthropic(model, system, messages, tools, max_tokens, usage, thinking_effort)
    if is_gemini_model(model):
        return await _chat_gemini(model, system, messages, tools, max_tokens, usage, json_mode=json_mode)
    return await _chat_openai(model, system, messages, tools, max_tokens, usage, json_mode=json_mode)


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
# Gemini adapter
# ---------------------------------------------------------------------------

def _to_gemini_contents(messages: list[dict[str, Any]]) -> list[Any]:
    from google.genai import types

    contents: list[Any] = []
    pending_tool_parts: list[Any] = []

    def _flush_tool_parts() -> None:
        nonlocal pending_tool_parts
        if pending_tool_parts:
            contents.append(types.Content(role="user", parts=pending_tool_parts))
            pending_tool_parts = []

    for m in messages:
        if m["role"] == "user":
            _flush_tool_parts()
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=m["content"])])
            )
        elif m["role"] == "assistant":
            _flush_tool_parts()
            parts: list[Any] = []
            if m.get("content"):
                parts.append(types.Part.from_text(text=m["content"]))
            for tc in m.get("tool_calls", []):
                fc_kwargs: dict[str, Any] = {"name": tc["name"], "args": tc["args"]}
                if tc.get("id"):
                    fc_kwargs["id"] = tc["id"]
                parts.append(types.Part(function_call=types.FunctionCall(**fc_kwargs)))
            contents.append(
                types.Content(role="model", parts=parts or [types.Part.from_text(text="")])
            )
        elif m["role"] == "tool":
            response: dict[str, Any] = {"content": m["content"]}
            if m.get("is_error"):
                response["error"] = m["content"]
            pending_tool_parts.append(
                types.Part.from_function_response(name=m["name"], response=response)
            )
    _flush_tool_parts()
    return contents


async def _chat_gemini(model, system, messages, tools, max_tokens, usage,
                       json_mode: bool = False) -> AssistantTurn:
    from google.genai import types

    config_kwargs: dict[str, Any] = {
        "system_instruction": system,
        "max_output_tokens": max_tokens,
        "thinking_config": types.ThinkingConfig(thinking_level="minimal"),
    }
    if json_mode and not tools:
        # Constrained decoding: the API guarantees syntactically valid JSON.
        # Not combinable with function calling, hence the tools guard.
        config_kwargs["response_mime_type"] = "application/json"
    if tools:
        config_kwargs["tools"] = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=t.name,
                        description=t.description,
                        parameters=t.parameters,
                    )
                    for t in tools
                ]
            )
        ]

    async def _do() -> Any:
        return await _gemini().aio.models.generate_content(
            model=model,
            contents=_to_gemini_contents(messages),
            config=types.GenerateContentConfig(**config_kwargs),
        )

    resp = await _call_with_retry(_do)
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    for cand in getattr(resp, "candidates", None) or []:
        content = getattr(cand, "content", None)
        if content is None:
            continue
        for part in getattr(content, "parts", None) or []:
            if getattr(part, "text", None):
                text_parts.append(part.text)
            fc = getattr(part, "function_call", None)
            if fc is not None and getattr(fc, "name", None):
                args = getattr(fc, "args", None) or {}
                call_id = getattr(fc, "id", None) or f"call_{fc.name}_{len(tool_calls)}"
                tool_calls.append(ToolCall(id=call_id, name=fc.name, args=dict(args)))

    meta = getattr(resp, "usage_metadata", None)
    if usage is not None and meta is not None:
        usage.add(
            model,
            getattr(meta, "prompt_token_count", 0) or 0,
            getattr(meta, "candidates_token_count", 0) or 0,
        )
    stop_reason = ""
    if getattr(resp, "candidates", None):
        stop_reason = getattr(resp.candidates[0], "finish_reason", "") or ""
    return AssistantTurn(
        text="\n".join(text_parts),
        tool_calls=tool_calls,
        stop_reason=str(stop_reason),
    )


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


async def _chat_openai(model, system, messages, tools, max_tokens, usage,
                       json_mode: bool = False) -> AssistantTurn:
    via_openrouter = is_openrouter_model(model)
    api_model = openrouter_model_id(model) if via_openrouter else native_openai_model_id(model)
    kwargs: dict[str, Any] = {
        "model": api_model,
        "messages": _to_openai_messages(system, messages),
    }
    if via_openrouter:
        kwargs["max_tokens"] = max_tokens
    if json_mode and not tools:
        kwargs["response_format"] = {"type": "json_object"}
    if tools:
        kwargs["tools"] = [
            {
                "type": "function",
                "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
            }
            for t in tools
        ]
    client = _openrouter() if via_openrouter else _openai()
    resp = await _call_with_retry(lambda: client.chat.completions.create(**kwargs))
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
    stack: list[str] = []
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
        elif c in "{[":
            stack.append("}" if c == "{" else "]")
        elif c in "}]":
            if stack:
                stack.pop()
            if not stack:
                return json.loads(text[start : i + 1])
    # The document never closed. Models (Gemini flash in particular) sometimes
    # report a normal stop while dropping the trailing closers; salvage by
    # closing any open string, trimming a dangling comma, and appending the
    # missing brackets in stack order. json.loads still arbitrates validity.
    tail = text[start:].rstrip()
    if in_str:
        tail += '"'
    tail = tail.rstrip()
    if tail.endswith(","):
        tail = tail[:-1]
    repaired = tail + "".join(reversed(stack))
    try:
        return json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Unbalanced JSON in model output (repair failed: {exc})") from exc


def _is_truncated(stop_reason: str) -> bool:
    reason = (stop_reason or "").lower()
    return reason == "length" or "max_token" in reason


_CONTINUE_PROMPT = (
    "Your previous response was cut off mid-output. Continue EXACTLY from the "
    "character where it stopped, emitting only the remaining part of the JSON "
    "document. Do not repeat anything already emitted, do not add code fences, "
    "and do not add commentary."
)


async def complete_json(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 128_000,
    usage: Optional[Usage] = None,
    max_continuations: int = 3,
) -> Any:
    messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
    turn = await chat(model, system, messages, tools=None,
                      max_tokens=max_tokens, usage=usage, json_mode=True)
    text = turn.text
    # Provider JSON modes guarantee syntax only for completed responses; an
    # output that hits the token ceiling is cut mid-document. Stitch it back
    # together by asking the model to resume from the cut, without json_mode
    # (constrained decoding would restart a fresh JSON document).
    for _ in range(max_continuations):
        if not _is_truncated(turn.stop_reason):
            break
        messages.append({"role": "assistant", "content": turn.text})
        messages.append({"role": "user", "content": _CONTINUE_PROMPT})
        turn = await chat(model, system, messages, tools=None,
                          max_tokens=max_tokens, usage=usage, json_mode=False)
        text += _clean_continuation(text, turn.text)
    if _is_truncated(turn.stop_reason):
        raise ValueError(
            f"model output still truncated after {max_continuations} continuation(s) "
            f"(stop_reason={turn.stop_reason!r}, chars={len(text)})"
        )
    try:
        return parse_json_loose(text)
    except (ValueError, json.JSONDecodeError) as exc:
        debug_path = _dump_parse_failure(model, turn.stop_reason, text)
        raise ValueError(
            f"{exc} (model={model}, stop_reason={turn.stop_reason!r}, "
            f"chars={len(text)}, raw_dump={debug_path})"
        ) from exc


def _clean_continuation(prior: str, chunk: str) -> str:
    """Normalize a mid-document continuation before splicing it onto ``prior``.

    Models often wrap the resumed output in code fences or re-emit a trailing
    slice of what they already produced; both would corrupt the spliced JSON.
    """
    stripped = chunk.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence:
        chunk = fence.group(1).strip()
    elif stripped.startswith("```"):
        # Unterminated fence (continuation itself may be truncated later).
        chunk = stripped.split("\n", 1)[1] if "\n" in stripped else ""
    # Otherwise leave chunk untouched: the cut can land inside a JSON string,
    # where leading whitespace is significant.
    # Drop the longest suffix of prior that the chunk re-emitted as its prefix.
    max_overlap = min(len(prior), len(chunk), 2000)
    for size in range(max_overlap, 0, -1):
        if prior.endswith(chunk[:size]):
            return chunk[size:]
    return chunk


def _dump_parse_failure(model: str, stop_reason: str, text: str) -> Path:
    """Persist unparseable model output for offline diagnosis."""
    out_dir = Path(os.getenv("RULE_NAV_LLM_DEBUG_DIR", "/tmp/rule_nav_llm_failures"))
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = out_dir / f"{stamp}_{model.replace('/', '_')}_{os.getpid()}_{len(text)}.txt"
    path.write_text(f"model: {model}\nstop_reason: {stop_reason}\n---\n{text}", encoding="utf-8")
    return path


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
    max_tokens: int = 128_000,
    thinking_effort: Optional[str] = None,
    api: str = "chat_completions",
) -> LoopResult:
    """Run an agent loop: model <-> tools with full chat history, until a terminal
    tool succeeds or max_turns is hit. Tool handler exceptions (ToolError) are fed
    back to the model as error results so it can self-correct.

    api selects the OpenAI transport:
      - "chat_completions" (default): the neutral chat() path used by all providers.
      - "responses": the OpenAI Responses API, which supports function tools together
        with reasoning (reasoning={"effort": ...}). Chat Completions rejects the
        tools + non-none reasoning combination for some reasoning models (e.g.
        gpt-5.6-luna), so reasoning-plus-tools OpenAI runs must use "responses".
        Only valid for OpenAI models.
    """
    if api == "responses":
        if is_anthropic_model(model) or is_gemini_model(model):
            raise ValueError("api='responses' is only supported for OpenAI models")
        return await _run_tool_loop_responses(
            model=model,
            system=system,
            user_message=user_message,
            tools=tools,
            max_turns=max_turns,
            usage=usage,
            trace=trace,
            agent_name=agent_name,
            max_tokens=max_tokens,
            thinking_effort=thinking_effort,
        )
    if api != "chat_completions":
        raise ValueError(f"unknown api {api!r}; expected 'chat_completions' or 'responses'")

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


# ---------------------------------------------------------------------------
# OpenAI Responses API tool loop
# ---------------------------------------------------------------------------
# Chat Completions rejects function tools combined with non-none reasoning effort
# for some OpenAI reasoning models. The Responses API supports that combination and
# configures reasoning via reasoning={"effort": ...}. This loop mirrors run_tool_loop's
# behavior (terminal tool ends the loop, tool errors are fed back for self-repair) but
# maintains Responses `input` history instead of the neutral chat format. Reasoning and
# function-call items from each response are appended back verbatim so the model keeps
# its reasoning state across tool calls.


def _to_responses_tool(spec: ToolSpec) -> dict[str, Any]:
    # Responses uses a flat function-tool definition (not nested under "function").
    # strict=False because these schemas allow optional properties and do not set
    # additionalProperties: false, which strict mode requires.
    return {
        "type": "function",
        "name": spec.name,
        "description": spec.description,
        "parameters": spec.parameters,
        "strict": False,
    }


async def _run_tool_loop_responses(
    *,
    model: str,
    system: str,
    user_message: str,
    tools: list[ToolSpec],
    max_turns: int,
    usage: Optional[Usage],
    trace: Optional[Trace],
    agent_name: str,
    max_tokens: int,
    thinking_effort: Optional[str],
) -> LoopResult:
    by_name = {t.name: t for t in tools}
    api_tools = [_to_responses_tool(t) for t in tools]

    # This list is the full Responses input history; SDK output items are appended
    # back verbatim (reasoning + function_call) so reasoning state is preserved.
    input_items: list[Any] = [{"role": "user", "content": user_message}]
    tool_call_count = 0
    nudged = False

    for turn_i in range(max_turns):
        via_openrouter = is_openrouter_model(model)
        api_model = openrouter_model_id(model) if via_openrouter else native_openai_model_id(model)
        request: dict[str, Any] = {
            "model": api_model,
            "instructions": system,
            "input": input_items,
            "tools": api_tools,
            "max_output_tokens": max_tokens,
            # Deterministic terminal-tool handling: one tool call per turn.
            "parallel_tool_calls": False,
        }
        if thinking_effort and thinking_effort != "none":
            request["reasoning"] = {"effort": thinking_effort}

        client = _openrouter() if via_openrouter else _openai()
        resp = await _call_with_retry(lambda: client.responses.create(**request))

        if usage is not None and resp.usage is not None:
            usage.add(model, resp.usage.input_tokens or 0, resp.usage.output_tokens or 0)

        # Preserve reasoning and function-call items for the next request.
        input_items.extend(resp.output)

        calls = [item for item in resp.output if item.type == "function_call"]
        text = resp.output_text or ""

        if trace:
            trace.log(
                "llm_call", agent_name, model=model, turn=turn_i,
                text=_truncate(text, 400),
                tool_calls=[{"name": c.name, "args": _truncate(c.arguments or "", 800)} for c in calls],
                stop_reason=resp.status or "",
            )

        if not calls:
            # Model stopped without calling a tool: nudge once, then give up.
            if nudged:
                return LoopResult(final=None, messages=input_items, turns=turn_i + 1,
                                  tool_call_count=tool_call_count,
                                  error="model ended without calling the terminal tool"
                                        + (f": {text[:500]}" if text else ""))
            nudged = True
            terminal_names = [t.name for t in tools if t.terminal]
            input_items.append({
                "role": "user",
                "content": f"You must finish by calling {terminal_names or ['the terminal tool']}. "
                           "Call it now with your best answer.",
            })
            continue

        for call in calls:
            tool_call_count += 1
            spec = by_name.get(call.name)
            if spec is None:
                input_items.append({
                    "type": "function_call_output", "call_id": call.call_id,
                    "output": json.dumps({"error": f"unknown tool: {call.name}"}),
                })
                continue
            try:
                args = json.loads(call.arguments or "{}")
            except json.JSONDecodeError as e:
                input_items.append({
                    "type": "function_call_output", "call_id": call.call_id,
                    "output": json.dumps({"error": f"invalid JSON arguments: {e}"}),
                })
                continue

            try:
                result = await spec.handler(args)
            except ToolError as e:
                if trace:
                    trace.log("tool_error", agent_name, tool=call.name, error=str(e))
                input_items.append({
                    "type": "function_call_output", "call_id": call.call_id,
                    "output": json.dumps({"error": f"ERROR: {e}"}),
                })
                continue
            except Exception as e:  # noqa: BLE001 — surfaced to the model, loop continues; run fails via max_turns if persistent
                if trace:
                    trace.log("tool_crash", agent_name, tool=call.name, error=repr(e))
                input_items.append({
                    "type": "function_call_output", "call_id": call.call_id,
                    "output": json.dumps({"error": f"ERROR: tool crashed: {e!r}"}),
                })
                continue

            if spec.terminal:
                if trace:
                    trace.log("finalize", agent_name, tool=call.name)
                return LoopResult(final=result, messages=input_items, turns=turn_i + 1,
                                  tool_call_count=tool_call_count)

            content = result if isinstance(result, str) else json.dumps(result, default=str)
            if trace:
                trace.log("tool_call", agent_name, tool=call.name,
                          args=_truncate(json.dumps(args, default=str), 800),
                          result_chars=len(content), result_preview=_truncate(content, 300))
            input_items.append({
                "type": "function_call_output", "call_id": call.call_id, "output": content,
            })

    return LoopResult(final=None, messages=input_items, turns=max_turns,
                      tool_call_count=tool_call_count, error=f"max_turns ({max_turns}) exceeded")
