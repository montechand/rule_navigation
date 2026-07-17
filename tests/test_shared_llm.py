"""Provider-routing checks for the shared LLM adapter."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from shared import llm


@pytest.mark.asyncio
async def test_openrouter_model_uses_openrouter_client(monkeypatch: pytest.MonkeyPatch) -> None:
    create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="ok", tool_calls=[]),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        )
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr(llm, "_openrouter", lambda: client)
    monkeypatch.setattr(
        llm,
        "_openai",
        lambda: pytest.fail("openrouter-prefixed models must not use the direct OpenAI client"),
    )

    turn = await llm.chat(
        "openrouter/openai/gpt-5.6-terra",
        "system",
        [{"role": "user", "content": "hello"}],
    )

    assert turn.text == "ok"
    assert create.await_args.kwargs["model"] == "openai/gpt-5.6-terra"
    assert create.await_args.kwargs["max_tokens"] == 128_000


@pytest.mark.asyncio
async def test_native_openai_model_uses_openai_client(monkeypatch: pytest.MonkeyPatch) -> None:
    create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="ok", tool_calls=[]),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        )
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr(llm, "_openai", lambda: client)
    monkeypatch.setattr(
        llm,
        "_openrouter",
        lambda: pytest.fail("native OpenAI models must not use the OpenRouter client"),
    )

    turn = await llm.chat(
        "openai/gpt-5.6-sol",
        "system",
        [{"role": "user", "content": "hello"}],
    )

    assert turn.text == "ok"
    assert create.await_args.kwargs["model"] == "gpt-5.6-sol"
    assert "max_tokens" not in create.await_args.kwargs


@pytest.mark.asyncio
async def test_gemini_model_uses_gemini_client(monkeypatch: pytest.MonkeyPatch) -> None:
    generate = AsyncMock(
        return_value=SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[SimpleNamespace(text='{"ok": true}', function_call=None)]
                    ),
                    finish_reason="STOP",
                )
            ],
            usage_metadata=SimpleNamespace(prompt_token_count=3, candidates_token_count=5),
        )
    )
    client = SimpleNamespace(
        aio=SimpleNamespace(
            models=SimpleNamespace(generate_content=generate),
        )
    )
    monkeypatch.setattr(llm, "_gemini", lambda: client)
    monkeypatch.setattr(
        llm,
        "_openai",
        lambda: pytest.fail("gemini models must not use the OpenAI client"),
    )
    monkeypatch.setattr(
        llm,
        "_anthropic",
        lambda: pytest.fail("gemini models must not use the Anthropic client"),
    )

    turn = await llm.chat(
        "gemini-3.5-flash",
        "system",
        [{"role": "user", "content": "hello"}],
    )

    assert turn.text == '{"ok": true}'
    assert generate.await_args.kwargs["model"] == "gemini-3.5-flash"


@pytest.mark.asyncio
async def test_complete_json_requests_provider_enforced_json(monkeypatch: pytest.MonkeyPatch) -> None:
    generate = AsyncMock(
        return_value=SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[SimpleNamespace(text='{"ok": true}', function_call=None)]
                    ),
                    finish_reason="STOP",
                )
            ],
            usage_metadata=SimpleNamespace(prompt_token_count=3, candidates_token_count=5),
        )
    )
    client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate))
    )
    monkeypatch.setattr(llm, "_gemini", lambda: client)

    result = await llm.complete_json("gemini-3.5-flash", "system", "user")

    assert result == {"ok": True}
    config = generate.await_args.kwargs["config"]
    assert config.response_mime_type == "application/json"


@pytest.mark.asyncio
async def test_openai_json_mode_sets_response_format(monkeypatch: pytest.MonkeyPatch) -> None:
    create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content='{"ok": true}', tool_calls=[]),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        )
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr(llm, "_openai", lambda: client)

    result = await llm.complete_json("gpt-5", "system", "user")

    assert result == {"ok": True}
    assert create.await_args.kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_complete_json_stitches_truncated_output(monkeypatch: pytest.MonkeyPatch) -> None:
    parts = ['{"rules": [{"id": "r1"', ', "slug": "a"}]}']
    calls: list[dict] = []

    async def fake_chat(model, system, messages, tools=None, max_tokens=0,
                        usage=None, json_mode=False, **kwargs):
        calls.append({"messages": list(messages), "json_mode": json_mode})
        chunk = parts[len(calls) - 1]
        stop = "MAX_TOKENS" if len(calls) < len(parts) else "STOP"
        return llm.AssistantTurn(text=chunk, tool_calls=[], stop_reason=stop)

    monkeypatch.setattr(llm, "chat", fake_chat)

    result = await llm.complete_json("gemini-3.5-flash", "system", "user")

    assert result == {"rules": [{"id": "r1", "slug": "a"}]}
    assert len(calls) == 2
    assert calls[0]["json_mode"] is True
    # Continuations replay the partial output and must not use constrained
    # decoding (it would restart a fresh JSON document).
    assert calls[1]["json_mode"] is False
    assert calls[1]["messages"][-2]["content"] == parts[0]


@pytest.mark.asyncio
async def test_complete_json_raises_when_still_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_chat(*args, **kwargs):
        return llm.AssistantTurn(text="{", tool_calls=[], stop_reason="length")

    monkeypatch.setattr(llm, "chat", fake_chat)

    with pytest.raises(ValueError, match="still truncated"):
        await llm.complete_json("gpt-5", "system", "user", max_continuations=2)


def test_clean_continuation_strips_fences_and_overlap() -> None:
    prior = '{"rules": [{"id": "r1", "text": "abc'
    # Re-emitted overlap plus code fences must both be removed.
    chunk = '```json\n"abc def"}]}\n```'
    assert llm._clean_continuation(prior, chunk) == ' def"}]}'
    # No overlap, no fences: chunk passes through.
    assert llm._clean_continuation(prior, ' def"}]}') == ' def"}]}'


def test_parse_json_loose_repairs_missing_trailing_closers() -> None:
    # Real gemini-3.5-flash failure: FinishReason.STOP but the final "}" of the
    # document was never emitted.
    text = '{\n  "rules": [{"id": "r1"}],\n  "relations": []'
    assert llm.parse_json_loose(text) == {"rules": [{"id": "r1"}], "relations": []}


def test_parse_json_loose_repairs_open_string_and_dangling_comma() -> None:
    text = '{"rules": [{"id": "r1", "note": "cut off'
    assert llm.parse_json_loose(text) == {"rules": [{"id": "r1", "note": "cut off"}]}
    text2 = '{"rules": [{"id": "r1"},'
    assert llm.parse_json_loose(text2) == {"rules": [{"id": "r1"}]}


def test_parse_json_loose_raises_when_repair_fails() -> None:
    with pytest.raises(ValueError, match="repair failed"):
        llm.parse_json_loose('{"a" 1')


def test_required_api_keys_for_models() -> None:
    assert llm.required_api_keys_for_models("gemini-3.5-flash") == ("GOOGLE_API_KEY",)
    assert llm.required_api_keys_for_models("claude-sonnet-5", "gpt-5") == (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
    )
    assert llm.required_api_keys_for_models("openrouter/openai/gpt-5.6-terra") == (
        "OPENROUTER_API_KEY",
    )
