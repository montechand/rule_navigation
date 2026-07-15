"""Offline LLM fake for KB Extraction v2 tests.

Serves canned JSON from ``fixtures/minibible/llm/{prompt_name}/{cache_key_or_seq}.json``,
records every call, and accounts token usage deterministically. No network clients.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from shared.llm import Usage

MINIBIBLE_BRAND = "minibible"
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "minibible"
LLM_FIXTURE_ROOT = FIXTURE_ROOT / "llm"

# Deterministic per-call token accounting (runner may scale).
_DEFAULT_INPUT_TOKENS = 120
_DEFAULT_OUTPUT_TOKENS = 80


class UnexpectedLLMCallError(AssertionError):
    """Raised when FakeLLM receives a call with no matching fixture."""


@dataclass
class LLMCallRecord:
    prompt_name: str
    rendered_hash: str
    cache_key: Optional[str]
    seq: int
    model: str
    system: str
    user: str


@dataclass
class FakeLLM:
    """Fixture-backed stand-in for the forthcoming runner ``LLMClient`` protocol."""

    fixture_root: Path = field(default_factory=lambda: LLM_FIXTURE_ROOT)
    brand: str = MINIBIBLE_BRAND
    default_model: str = "fake-model"
    input_tokens: int = _DEFAULT_INPUT_TOKENS
    output_tokens: int = _DEFAULT_OUTPUT_TOKENS
    _call_log: list[LLMCallRecord] = field(default_factory=list, init=False, repr=False)
    _seq_counters: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    @staticmethod
    def rendered_hash(system: str, user: str) -> str:
        payload = f"{system}\n---\n{user}"
        return hashlib.sha1(payload.encode()).hexdigest()[:16]

    def calls(self) -> list[LLMCallRecord]:
        return list(self._call_log)

    def reset(self) -> None:
        self._call_log.clear()
        self._seq_counters.clear()

    def _next_seq(self, prompt_name: str) -> int:
        seq = self._seq_counters.get(prompt_name, 0) + 1
        self._seq_counters[prompt_name] = seq
        return seq

    def _resolve_path(self, prompt_name: str, cache_key: Optional[str], seq: int) -> Path:
        base = self.fixture_root / prompt_name
        if cache_key is not None:
            keyed = base / f"{cache_key}.json"
            if keyed.is_file():
                return keyed
        sequential = base / f"{seq:03d}.json"
        if sequential.is_file():
            return sequential
        prefixed = sorted(base.glob(f"*_{seq:03d}.json"))
        if prefixed:
            return prefixed[0]
        # ponytail: fall back to sorted fixture order when names are run-prefixed (r0_001…).
        ordered = sorted(base.glob("*.json"))
        if 0 < seq <= len(ordered):
            return ordered[seq - 1]
        raise UnexpectedLLMCallError(
            f"No fixture for prompt_name={prompt_name!r} cache_key={cache_key!r} seq={seq}"
        )

    def _record(
        self,
        *,
        prompt_name: str,
        cache_key: Optional[str],
        model: str,
        system: str,
        user: str,
    ) -> Path:
        rh = self.rendered_hash(system, user)
        seq = self._next_seq(prompt_name)
        path = self._resolve_path(prompt_name, cache_key, seq)
        self._call_log.append(
            LLMCallRecord(
                prompt_name=prompt_name,
                rendered_hash=rh,
                cache_key=cache_key,
                seq=seq,
                model=model,
                system=system,
                user=user,
            )
        )
        return path

    def _load_fixture(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def _filter_classifier_fixture(self, data: Any, user: str, path: Path) -> Any:
        target_ids = re.findall(
            r"^\[([^\]]+)\]\s+\([^)]*\)\s+TARGET\b",
            user,
            flags=re.MULTILINE,
        )
        if not target_ids:
            return data
        rows = data.get("units") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise UnexpectedLLMCallError(
                f"Classifier fixture {path.name} has no units list"
            )
        targets = set(target_ids)
        available = {
            row.get("unit_id")
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("unit_id"), str)
        }
        missing = sorted(targets - available)
        if missing:
            raise UnexpectedLLMCallError(
                f"Classifier fixture {path.name} missing TARGET unit {missing[0]!r}"
            )
        return {
            **data,
            "units": [row for row in rows if row.get("unit_id") in targets],
        }

    def _account(self, usage: Optional[Usage], model: str) -> None:
        if usage is not None:
            usage.add(model, self.input_tokens, self.output_tokens)

    async def complete_json(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 16_000,
        usage: Optional[Usage] = None,
        *,
        prompt_name: str,
        cache_key: Optional[str] = None,
    ) -> Any:
        path = self._record(
            prompt_name=prompt_name,
            cache_key=cache_key,
            model=model,
            system=system,
            user=user,
        )
        self._account(usage, model)
        data = self._load_fixture(path)
        if prompt_name == "unit_classifier":
            data = self._filter_classifier_fixture(data, user, path)
        return data

    async def chat(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        *,
        prompt_name: str,
        cache_key: Optional[str] = None,
        usage: Optional[Usage] = None,
        max_tokens: int = 16_000,
        **_: Any,
    ) -> dict[str, Any]:
        user = "\n".join(
            m.get("content", "") for m in messages if m.get("role") == "user"
        )
        data = await self.complete_json(
            model,
            system,
            user,
            max_tokens=max_tokens,
            usage=usage,
            prompt_name=prompt_name,
            cache_key=cache_key,
        )
        return {"role": "assistant", "content": json.dumps(data)}

    def load_fixture(self, prompt_name: str, cache_key_or_seq: str) -> Any:
        """Direct fixture access for tests that assert on canned payloads."""
        path = self.fixture_root / prompt_name / f"{cache_key_or_seq}.json"
        if not path.is_file():
            raise FileNotFoundError(path)
        return self._load_fixture(path)
