"""§5.1 S0 Markdown segmenter — gap-free SourceUnit coverage over brand bibles.

Usage: ``segment_bible(brand, bible["website"])`` returns deterministic source units.
"""

from __future__ import annotations

import re
from pathlib import Path

from indexing_v2.contracts import (
    SCHEMA_VERSION,
    SourceUnit,
    UnitKind,
    atomic_write_json,
    slugify,
    write_jsonl,
)

STAGE_VERSION = "1.0.0"

_ATX_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:[ \t]*)$")
_LIST_MARKER_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+")
_ABBREV_ENDINGS = frozenset(
    {
        "i.e",
        "e.g",
        "vs",
        "etc",
        "dr",
        "fig",
        "mr",
        "mrs",
        "ms",
        "prof",
        "sr",
        "jr",
        "no",
        "al",
        "st",
    }
)


def normalize_line_endings(text: str) -> str:
    """Normalize CRLF and lone CR to LF before offset math."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def segment_bible(brand: str, bible: dict[str, list[str]]) -> list[SourceUnit]:
    units: list[SourceUnit] = []
    for category in sorted(bible):
        blobs = bible[category]
        for index, raw in enumerate(blobs):
            doc_ref = f"{category}[{index}]"
            units.extend(_segment_blob(brand, doc_ref, normalize_line_endings(raw)))
    return units


def run_segmenter(brand: str, bible: dict[str, list[str]], work_dir: Path) -> list[SourceUnit]:
    units = segment_bible(brand, bible)
    blobs = {
        f"{category}[{index}]": normalize_line_endings(raw)
        for category in sorted(bible)
        for index, raw in enumerate(bible[category])
    }
    work_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(work_dir / "units.jsonl", units)
    atomic_write_json(work_dir / "blobs.json", blobs)
    return units


def _segment_blob(brand: str, doc_ref: str, blob: str) -> list[SourceUnit]:
    units: list[SourceUnit] = []
    heading_stack: list[str] = []
    ordinal = 0
    pos = 0
    slug = slugify(doc_ref)

    def emit(start: int, end: int, kind: UnitKind, heading_path: list[str]) -> None:
        nonlocal ordinal
        units.append(
            SourceUnit(
                schema_version=SCHEMA_VERSION,
                unit_id=f"u_{slug}_{ordinal:04d}",
                brand_id=brand,
                doc_ref=doc_ref,
                ordinal=ordinal,
                start=start,
                end=end,
                kind=kind,
                text=blob[start:end],
                heading_path=list(heading_path),
            )
        )
        ordinal += 1

    while pos < len(blob):
        line_end = blob.find("\n", pos)
        if line_end == -1:
            line_end = len(blob)
        line = blob[pos:line_end]
        line_nl_end = line_end + 1 if line_end < len(blob) else line_end

        blank_end = _blank_run_end(blob, pos)
        if blank_end is not None:
            emit(pos, blank_end, "blank", heading_stack)
            pos = blank_end
            continue

        if _is_fence_line(line):
            end = _code_block_end(blob, pos)
            emit(pos, end, "code_block", heading_stack)
            pos = end
            continue

        heading = _parse_atx_heading(line)
        if heading is not None:
            level, title = heading
            emit(pos, line_nl_end, "heading", heading_stack[: level - 1])
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            pos = line_nl_end
            continue

        if _is_table_row(line):
            row_end = line_nl_end
            emit(pos, row_end, "table_row", heading_stack)
            pos = row_end
            continue

        list_match = _LIST_MARKER_RE.match(line)
        if list_match is not None:
            item_end = _list_item_end(blob, pos)
            emit(pos, item_end, "list_item", heading_stack)
            pos = item_end
            continue

        paragraph_end = _paragraph_end(blob, pos)
        for sent_start, sent_end in _split_sentences(blob[pos:paragraph_end]):
            emit(pos + sent_start, pos + sent_end, "sentence", heading_stack)
        pos = paragraph_end

    return units


def _blank_run_end(blob: str, pos: int) -> int | None:
    if pos >= len(blob):
        return None
    start = pos
    cursor = pos
    while cursor < len(blob):
        line_end = blob.find("\n", cursor)
        if line_end == -1:
            line_end = len(blob)
        line = blob[cursor:line_end]
        if line.strip():
            break
        cursor = line_end + 1 if line_end < len(blob) else line_end
    if cursor == start:
        return None
    return cursor


def _is_fence_line(line: str) -> bool:
    return line.lstrip().startswith("```")


def _code_block_end(blob: str, pos: int) -> int:
    line_end = blob.find("\n", pos)
    if line_end == -1:
        return len(blob)
    cursor = line_end + 1
    while cursor < len(blob):
        next_end = blob.find("\n", cursor)
        if next_end == -1:
            next_end = len(blob)
        line = blob[cursor:next_end]
        if _is_fence_line(line):
            return next_end + 1 if next_end < len(blob) else next_end
        cursor = next_end + 1 if next_end < len(blob) else next_end
    return len(blob)


def _parse_atx_heading(line: str) -> tuple[int, str] | None:
    match = _ATX_HEADING_RE.match(line)
    if match is None:
        return None
    return len(match.group(1)), match.group(2).strip()


def _is_table_row(line: str) -> bool:
    stripped = line.rstrip("\n")
    if not stripped.startswith("|"):
        return False
    idx = 0
    while idx < len(stripped):
        char = stripped[idx]
        if char == "\\" and idx + 1 < len(stripped):
            idx += 2
            continue
        idx += 1
    return stripped.rstrip().endswith("|")


def _list_item_end(blob: str, pos: int) -> int:
    cursor = pos
    while cursor < len(blob):
        line_end = blob.find("\n", cursor)
        if line_end == -1:
            line_end = len(blob)
        line = blob[cursor:line_end]
        line_nl_end = line_end + 1 if line_end < len(blob) else line_end

        if cursor != pos:
            if _blank_run_end(blob, cursor) is not None:
                break
            if _is_fence_line(line) or _parse_atx_heading(line) is not None or _is_table_row(line):
                break
            if _LIST_MARKER_RE.match(line) is not None:
                break
        cursor = line_nl_end
    return cursor


def _paragraph_end(blob: str, pos: int) -> int:
    cursor = pos
    while cursor < len(blob):
        line_end = blob.find("\n", cursor)
        if line_end == -1:
            line_end = len(blob)
        line = blob[cursor:line_end]
        line_nl_end = line_end + 1 if line_end < len(blob) else line_end

        if cursor != pos and _blank_run_end(blob, cursor) is not None:
            break
        if _is_fence_line(line) or _parse_atx_heading(line) is not None or _is_table_row(line):
            break
        if _LIST_MARKER_RE.match(line) is not None:
            break
        cursor = line_nl_end
    return cursor


def _split_sentences(paragraph: str) -> list[tuple[int, int]]:
    if not paragraph:
        return []

    spans: list[tuple[int, int]] = []
    start = 0
    idx = 0
    length = len(paragraph)

    while idx < length:
        char = paragraph[idx]
        if char not in ".?!":
            idx += 1
            continue
        if _inside_delimiters(paragraph, idx):
            idx += 1
            continue
        punct_end = idx + 1
        while punct_end < length and paragraph[punct_end] in ".?!":
            punct_end += 1
        if _is_abbreviation_boundary(paragraph, idx):
            idx = punct_end
            continue
        if _is_decimal_boundary(paragraph, idx):
            idx = punct_end
            continue
        ws_match = re.match(r"\s+", paragraph[punct_end:])
        if ws_match is None:
            idx = punct_end
            continue
        after_ws = punct_end + ws_match.end()
        if after_ws >= length or not _sentence_lookahead(paragraph[after_ws]):
            idx = punct_end
            continue
        spans.append((start, after_ws))
        start = after_ws
        idx = after_ws

    spans.append((start, length))
    return spans


def _inside_delimiters(text: str, idx: int) -> bool:
    parens = 0
    quote: str | None = None
    backticks = 0
    pos = 0
    while pos < idx:
        char = text[pos]
        if quote is not None:
            if char == "\\" and pos + 1 < idx:
                pos += 2
                continue
            if char == quote and not (
                quote == "'" and _is_intra_word_apostrophe(text, pos)
            ):
                quote = None
            pos += 1
            continue
        if backticks > 0:
            if char == "`":
                run = 1
                while pos + run < idx and text[pos + run] == "`":
                    run += 1
                if run == backticks:
                    backticks = 0
                    pos += run
                    continue
            pos += 1
            continue
        if char == '"' or (char == "'" and not _is_word_apostrophe(text, pos)):
            quote = char
        elif char == "(":
            parens += 1
        elif char == ")" and parens > 0:
            parens -= 1
        elif char == "`":
            run = 1
            while pos + run < idx and text[pos + run] == "`":
                run += 1
            backticks = run
            pos += run
            continue
        pos += 1
    return parens > 0 or quote is not None or backticks > 0


def _is_word_apostrophe(text: str, pos: int) -> bool:
    """Treat contractions and possessives as apostrophes, not quote delimiters."""
    return pos > 0 and text[pos - 1].isalnum()


def _is_intra_word_apostrophe(text: str, pos: int) -> bool:
    return _is_word_apostrophe(text, pos) and pos + 1 < len(text) and text[pos + 1].isalnum()


def _is_abbreviation_boundary(text: str, dot_idx: int) -> bool:
    prefix = text[:dot_idx]
    word_match = re.search(r"([A-Za-z]+)$", prefix)
    if word_match is not None:
        word = word_match.group(1).casefold()
        if word in _ABBREV_ENDINGS:
            return True
    if re.search(r"(?:Fig|No|Sec|Eq|Ch)\.\s*\d+$", prefix, re.IGNORECASE):
        return True
    initial_match = re.search(r"(?:^|[\s(])((?:[A-Z]\.)+)$", prefix)
    if initial_match is not None:
        return True
    if dot_idx > 0 and prefix[-1].isupper() and (dot_idx + 1 >= len(text) or text[dot_idx + 1].isspace()):
        tail = text[dot_idx + 1 :].lstrip()
        if tail and (tail[0].islower() or (len(tail) > 1 and tail[0].isupper() and tail[1] == ".")):
            return True
    return False


def _is_decimal_boundary(text: str, dot_idx: int) -> bool:
    return dot_idx > 0 and dot_idx + 1 < len(text) and text[dot_idx - 1].isdigit() and text[dot_idx + 1].isdigit()


def _sentence_lookahead(char: str) -> bool:
    return char.isupper() or char.isdigit() or char in "\"'“‘([{"
