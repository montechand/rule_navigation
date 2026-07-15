"""Prompt templates for KB extraction v2.

Markdown files may use optional YAML frontmatter (``system`` / ``user`` keys) or the
documented in-body separators ``---SYSTEM---`` and ``---USER---``. WP-08 owns the
prompt bodies; this module only loads and renders them.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent
_SYSTEM_MARKER = "---SYSTEM---"
_USER_MARKER = "---USER---"


class PromptRenderError(ValueError):
    """Raised when a template references unknown or unresolved placeholders."""

    def __init__(self, *, missing: list[str], unresolved: list[str]) -> None:
        self.missing = sorted(set(missing))
        self.unresolved = sorted(set(unresolved))
        parts: list[str] = []
        if self.missing:
            parts.append(f"missing={self.missing}")
        if self.unresolved:
            parts.append(f"unresolved={self.unresolved}")
        super().__init__("; ".join(parts) or "prompt render failed")


class RenderedPrompt(BaseModel):
    system: str
    user: str


class PromptTemplate(BaseModel):
    name: str
    system: str
    user: str
    template_hash: str = Field(description="SHA1 (first 16 hex) of raw markdown bytes")

    def placeholders(self) -> list[str]:
        found = _PLACEHOLDER_RE.findall(self.system) + _PLACEHOLDER_RE.findall(self.user)
        return sorted(set(found))

    def render(self, **variables: Any) -> RenderedPrompt:
        missing = [name for name in self.placeholders() if name not in variables]
        if missing:
            raise PromptRenderError(missing=missing, unresolved=[])
        try:
            rendered_system = self.system.format(**variables)
            rendered_user = self.user.format(**variables)
        except KeyError as exc:
            raise PromptRenderError(missing=[str(exc.args[0])], unresolved=[]) from exc
        # ponytail: do not re-scan rendered text for {placeholders}. Injected data
        # (e.g. source units containing {{fn1}}) looks like unresolved vars; missing
        # template keys are already caught above via placeholders() / KeyError.
        return RenderedPrompt(system=rendered_system, user=rendered_user)


def _template_hash(raw: str) -> str:
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---", 4)
    if end == -1:
        return {}, raw
    header = raw[4:end]
    body = raw[end + 4 :].lstrip("\n")
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []
    for line in header.splitlines():
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*:\s*\|?\s*$", line):
            if current_key is not None:
                fields[current_key] = "\n".join(current_lines).rstrip("\n")
            current_key = line.split(":", 1)[0].strip()
            current_lines = []
            continue
        if current_key is not None:
            current_lines.append(line[2:] if line.startswith("  ") else line)
    if current_key is not None:
        fields[current_key] = "\n".join(current_lines).rstrip("\n")
    return fields, body


def _split_marked_sections(raw: str) -> tuple[str, str]:
    if _SYSTEM_MARKER not in raw or _USER_MARKER not in raw:
        return "", raw
    _, after_system = raw.split(_SYSTEM_MARKER, 1)
    system_part, user_part = after_system.split(_USER_MARKER, 1)
    return system_part.strip("\n"), user_part.lstrip("\n")


def _load_markdown(path: Path) -> tuple[str, str, str]:
    raw = path.read_text(encoding="utf-8")
    frontmatter, remainder = _parse_frontmatter(raw)
    system = frontmatter.get("system", "")
    user = frontmatter.get("user", "")
    if system or user:
        if not user and remainder.strip():
            user = remainder.strip("\n")
        return system, user, raw
    system, user = _split_marked_sections(raw)
    if system or user:
        return system, user, raw
    return "", raw.strip("\n"), raw


def load_prompt(name: str, prompts_dir: Path | None = None) -> PromptTemplate:
    """Load ``{name}.md`` from ``prompts_dir`` (defaults to this package directory)."""
    root = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = root / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(path)
    system, user, raw = _load_markdown(path)
    return PromptTemplate(
        name=name,
        system=system,
        user=user,
        template_hash=_template_hash(raw),
    )
