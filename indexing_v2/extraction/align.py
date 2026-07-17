"""§5.4.2 quote→span alignment and §5.4.3 witness-model verification.

Usage: call ``align_quote`` for spans or ``verify_value_path`` for path-level verification.

Verification treats cited units as the primary provenance pointer and the quote as a
witness. Deterministic unit-text containment establishes provenance first; exact or
normalized alignment then opportunistically upgrades the span to character precision.
Only non-value paths may use the anchor-and-refine fuzzy rung as a last resort after
containment misses. Concrete values are verified independently of quote alignment by
searching their canonical literal in cited unit text (with one-unit widening) and in
the quote witness. Verbatim fields retain their exact-only contract.

The fuzzy last resort uses a two-tier locate gate: a longest-common-block anchor is
the fast path, while evenly distributed sparse edits may use a local cluster of
substantial matching blocks. Both feed the same bounded boundary refinement, and
acceptance remains solely ``SequenceMatcher.ratio() >= fuzzy_min_ratio``. Inputs whose
matching blocks are too scattered or sparse fail closed.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from re import Pattern
from typing import Any, Mapping, Optional, Sequence

from indexing_v2.contracts import (
    EvidenceSpan,
    MatchQuality,
    SourceUnit,
    ValueCheck,
    Verification,
)

from .normalize import normalize_value, value_patterns

STAGE_VERSION = "2.1.1"

_CURLY_MAP = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
)

_VERBATIM_FIELD_PATHS = frozenset({"governance.preferred_form", "body"})
# Minimum matching-block size counted by the multi-anchor gate.
_FUZZY_BLOCK_MIN = 3
# Maximum local block-cluster text extent relative to quote length.
_FUZZY_CLUSTER_EXTENT_FACTOR = 1.2
# Minimum quote-length coverage required to attempt final fuzzy scoring.
_FUZZY_CLUSTER_COVERAGE = 0.75
_MATCH_RANK: dict[MatchQuality, int] = {
    "exact": 5,
    "normalized": 4,
    "unit": 3,
    "fuzzy": 2,
    "failed": 1,
}


@dataclass(frozen=True, slots=True)
class AlignmentResult:
    """Alignment span plus optional disambiguation detail for verifiers."""

    span: EvidenceSpan
    detail: Optional[str] = None


def _nfc_with_index_map(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Build NFC text and one original-raw range per normalized character."""
    # ponytail: prefix normalization is O(n²); source units are short, so avoid a Unicode
    # normalization-boundary implementation until profiling shows this is material.
    previous = ""
    idx_map: list[tuple[int, int]] = []
    for raw_end in range(1, len(text) + 1):
        current = unicodedata.normalize("NFC", text[:raw_end])
        common = 0
        limit = min(len(previous), len(current))
        while common < limit and previous[common] == current[common]:
            common += 1
        changed_start = raw_end - 1
        if common < len(idx_map):
            changed_start = min(start for start, _ in idx_map[common:])
        idx_map[common:] = [(changed_start, raw_end)] * (len(current) - common)
        previous = current
    return previous, idx_map


def _normalize_with_index_map(text: str) -> tuple[str, list[tuple[int, int]]]:
    """NFC + curly-quote fix + whitespace collapse + casefold with norm→raw map."""
    nfc, nfc_map = _nfc_with_index_map(text)
    out: list[str] = []
    idx_map: list[tuple[int, int]] = []
    prev_space = False
    for ch, raw_range in zip(nfc, nfc_map):
        converted = ch.translate(_CURLY_MAP).casefold()
        for normalized_ch in converted:
            if normalized_ch.isspace():
                if prev_space:
                    start, _ = idx_map[-1]
                    idx_map[-1] = (start, raw_range[1])
                    continue
                out.append(" ")
                idx_map.append(raw_range)
                prev_space = True
                continue
            prev_space = False
            out.append(normalized_ch)
            idx_map.append(raw_range)
    return "".join(out), idx_map


def _normalize_plain(text: str) -> str:
    """Normalize like ``_normalize_with_index_map`` without building raw offsets."""
    converted = unicodedata.normalize("NFC", text).translate(_CURLY_MAP).casefold()
    out: list[str] = []
    prev_space = False
    for ch in converted:
        if ch.isspace():
            if prev_space:
                continue
            out.append(" ")
            prev_space = True
            continue
        out.append(ch)
        prev_space = False
    return "".join(out)


def _raw_span_from_norm(
    unit: SourceUnit,
    norm_map: list[tuple[int, int]],
    norm_start: int,
    norm_end: int,
) -> tuple[int, int]:
    raw_start = unit.start + norm_map[norm_start][0]
    raw_end = unit.start + norm_map[norm_end - 1][1]
    return raw_start, raw_end


def _hull_span(
    quote: str,
    units_by_id: Mapping[str, SourceUnit],
    unit_ids: list[str],
) -> EvidenceSpan:
    cited = [units_by_id[uid] for uid in unit_ids if uid in units_by_id]
    if not cited:
        return EvidenceSpan(
            doc_ref="",
            unit_ids=[],
            start=0,
            end=0,
            quote=quote,
            match="failed",
        )
    doc_ref = cited[0].doc_ref
    same_doc = sorted(
        {u.unit_id: u for u in cited if u.doc_ref == doc_ref}.values(),
        key=lambda u: (u.ordinal, u.start, u.unit_id),
    )
    start = min(u.start for u in same_doc)
    end = max(u.end for u in same_doc)
    return EvidenceSpan(
        doc_ref=doc_ref,
        unit_ids=[u.unit_id for u in same_doc],
        start=start,
        end=end,
        quote=quote,
        match="failed",
    )


@dataclass(frozen=True, slots=True)
class _Candidate:
    units: tuple[SourceUnit, ...]
    start: int
    end: int
    quality: MatchQuality
    ratio: float
    cited: bool


def _exact_candidates(quote: str, unit: SourceUnit, cited: bool) -> list[_Candidate]:
    hits: list[_Candidate] = []
    start = 0
    while True:
        idx = unit.text.find(quote, start)
        if idx < 0:
            break
        hits.append(
            _Candidate(
                units=(unit,),
                start=unit.start + idx,
                end=unit.start + idx + len(quote),
                quality="exact",
                ratio=1.0,
                cited=cited,
            )
        )
        start = idx + 1
    return hits


def _normalized_candidates(
    quote: str,
    unit: SourceUnit,
    cited: bool,
) -> list[_Candidate]:
    quote_norm, _ = _normalize_with_index_map(quote)
    if not quote_norm:
        return []
    unit_norm, norm_map = _normalize_with_index_map(unit.text)
    hits: list[_Candidate] = []
    start = 0
    while True:
        idx = unit_norm.find(quote_norm, start)
        if idx < 0:
            break
        raw_start, raw_end = _raw_span_from_norm(unit, norm_map, idx, idx + len(quote_norm))
        hits.append(
            _Candidate(
                units=(unit,),
                start=raw_start,
                end=raw_end,
                quality="normalized",
                ratio=1.0,
                cited=cited,
            )
        )
        start = idx + 1
    return hits


def _refine_window(
    quote_norm: str,
    text_norm: str,
    fuzzy_min_ratio: float,
    projected_start: int,
    projected_end: int,
) -> list[tuple[int, int, float]]:
    """Refine and score one projected fuzzy window."""
    quote_len = len(quote_norm)
    budget = max(2, quote_len // 10)
    min_start = max(0, projected_start - budget)
    max_start = min(projected_end - 1, projected_start + budget)
    min_end = max(projected_start + 1, projected_end - budget)
    max_end = min(len(text_norm), projected_end + budget)
    scores: dict[tuple[int, int], float] = {}

    def score(start: int, end: int) -> float:
        key = (start, end)
        if key not in scores:
            scores[key] = SequenceMatcher(
                None,
                quote_norm,
                text_norm[start:end],
                autojunk=False,
            ).ratio()
        return scores[key]

    current_start = projected_start
    current_end = projected_end
    score(current_start, current_end)

    # Coordinate refinement keeps ratio() calls linear in the quote length while
    # allowing both boundaries to move within the fixed local neighborhood.
    for _ in range(2):
        start_scores = [
            (score(start, current_end), start)
            for start in range(min_start, min(max_start, current_end - 1) + 1)
        ]
        best_start_ratio = max(item[0] for item in start_scores)
        current_start = min(
            start
            for ratio, start in start_scores
            if ratio == best_start_ratio
        )

        end_scores = [
            (score(current_start, end), end)
            for end in range(max(min_end, current_start + 1), max_end + 1)
        ]
        best_end_ratio = max(item[0] for item in end_scores)
        current_end = min(
            end
            for ratio, end in end_scores
            if ratio == best_end_ratio
        )

    best_ratio = max(scores.values())
    if best_ratio < fuzzy_min_ratio:
        return []
    return sorted(
        (
            (start, end, ratio)
            for (start, end), ratio in scores.items()
            if ratio == best_ratio
        ),
        key=lambda item: (item[0], item[1]),
    )


def _multi_anchor_projection(
    matcher: SequenceMatcher[str],
    quote_len: int,
    text_len: int,
) -> tuple[int, int] | None:
    """Return a projected window for the best qualifying local block cluster."""
    blocks = [
        block
        for block in matcher.get_matching_blocks()
        if block.size >= _FUZZY_BLOCK_MIN
    ]
    if len(blocks) < 2:
        return None

    max_extent = _FUZZY_CLUSTER_EXTENT_FACTOR * quote_len
    left = 0
    cluster_sum = 0
    best_left = -1
    best_right = -1
    best_sum = -1
    best_first_b = -1
    best_count = -1

    for right, block in enumerate(blocks):
        cluster_sum += block.size
        while (
            left <= right
            and (block.b + block.size) - blocks[left].b > max_extent
        ):
            cluster_sum -= blocks[left].size
            left += 1
        if left > right:
            continue

        first_b = blocks[left].b
        count = right - left + 1
        if (
            cluster_sum > best_sum
            or (
                cluster_sum == best_sum
                and (
                    best_left < 0
                    or first_b < best_first_b
                    or (first_b == best_first_b and count < best_count)
                )
            )
        ):
            best_left = left
            best_right = right
            best_sum = cluster_sum
            best_first_b = first_b
            best_count = count

    if (
        best_left < 0
        or best_sum < _FUZZY_CLUSTER_COVERAGE * quote_len
    ):
        return None

    first = blocks[best_left]
    last = blocks[best_right]
    projected_start = max(0, first.b - first.a)
    projected_end = min(
        text_len,
        (last.b + last.size) + (quote_len - (last.a + last.size)),
    )
    if projected_start >= projected_end:
        return None
    return projected_start, projected_end


def _best_fuzzy_windows(
    quote_norm: str,
    text_norm: str,
    fuzzy_min_ratio: float,
) -> list[tuple[int, int, float]]:
    """Locate and score the best fuzzy windows near one qualifying anchor set."""
    if not quote_norm or not text_norm:
        return []

    matcher = SequenceMatcher(None, quote_norm, text_norm, autojunk=False)
    anchor = matcher.find_longest_match(
        0,
        len(quote_norm),
        0,
        len(text_norm),
    )
    if anchor.size < max(3, len(quote_norm) // 4):
        projection = _multi_anchor_projection(
            matcher,
            len(quote_norm),
            len(text_norm),
        )
        if projection is None:
            return []
        projected_start, projected_end = projection
    else:
        quote_len = len(quote_norm)
        projected_start = max(0, min(anchor.b - anchor.a, len(text_norm)))
        projected_end = max(
            projected_start,
            min(projected_start + quote_len, len(text_norm)),
        )
        if projected_start >= projected_end:
            return []

    return _refine_window(
        quote_norm,
        text_norm,
        fuzzy_min_ratio,
        projected_start,
        projected_end,
    )


def _fuzzy_candidates(
    quote: str,
    unit: SourceUnit,
    cited: bool,
    *,
    fuzzy_min_ratio: float,
) -> list[_Candidate]:
    quote_norm, _ = _normalize_with_index_map(quote)
    if not quote_norm:
        return []
    unit_norm, norm_map = _normalize_with_index_map(unit.text)
    if not unit_norm:
        return []

    best: list[_Candidate] = []
    for norm_start, norm_end, ratio in _best_fuzzy_windows(
        quote_norm,
        unit_norm,
        fuzzy_min_ratio,
    ):
        raw_start, raw_end = _raw_span_from_norm(
            unit,
            norm_map,
            norm_start,
            norm_end,
        )
        best.append(
            _Candidate(
                units=(unit,),
                start=raw_start,
                end=raw_end,
                quality="fuzzy",
                ratio=ratio,
                cited=cited,
            )
        )

    return best


def _consecutive_runs(units: Sequence[SourceUnit]) -> list[tuple[SourceUnit, ...]]:
    by_doc: dict[str, list[SourceUnit]] = {}
    for unit in units:
        by_doc.setdefault(unit.doc_ref, []).append(unit)

    runs: list[tuple[SourceUnit, ...]] = []
    for doc_ref in sorted(by_doc):
        ordered = sorted(
            {u.unit_id: u for u in by_doc[doc_ref]}.values(),
            key=lambda u: (u.ordinal, u.start, u.unit_id),
        )
        current: list[SourceUnit] = []
        for unit in ordered:
            if current and unit.ordinal != current[-1].ordinal + 1:
                runs.append(tuple(current))
                current = []
            current.append(unit)
        if current:
            runs.append(tuple(current))
    return runs


def _consecutive_cited_runs(units: list[SourceUnit]) -> list[tuple[SourceUnit, ...]]:
    return [run for run in _consecutive_runs(units) if len(run) > 1]


def _cross_unit_fuzzy_candidates(
    quote: str,
    cited: list[SourceUnit],
    *,
    fuzzy_min_ratio: float,
) -> list[_Candidate]:
    quote_norm, _ = _normalize_with_index_map(quote)
    if not quote_norm:
        return []

    candidates: list[_Candidate] = []
    for run in _consecutive_cited_runs(cited):
        combined = "".join(unit.text for unit in run)
        raw_offsets = [
            unit.start + offset
            for unit in run
            for offset in range(len(unit.text))
        ]
        combined_norm, norm_map = _normalize_with_index_map(combined)
        best: list[_Candidate] = []

        for norm_start, norm_end, ratio in _best_fuzzy_windows(
            quote_norm,
            combined_norm,
            fuzzy_min_ratio,
        ):
            local_start = norm_map[norm_start][0]
            local_end = norm_map[norm_end - 1][1]
            raw_start = raw_offsets[local_start]
            raw_end = raw_offsets[local_end - 1] + 1
            actual = tuple(
                unit
                for unit in run
                if unit.start < raw_end and unit.end > raw_start
            )
            if len(actual) < 2:
                continue
            best.append(
                _Candidate(
                    units=actual,
                    start=raw_start,
                    end=raw_end,
                    quality="fuzzy",
                    ratio=ratio,
                    cited=True,
                )
            )
        candidates.extend(best)
    return candidates


def _collect_candidates(
    quote: str,
    units: list[SourceUnit],
    cited_ids: set[str],
    *,
    fuzzy_min_ratio: float,
    cap_quality: Optional[MatchQuality] = None,
) -> list[_Candidate]:
    out: list[_Candidate] = []
    for unit in units:
        cited = unit.unit_id in cited_ids
        for cand in (
            *_exact_candidates(quote, unit, cited),
            *_normalized_candidates(quote, unit, cited),
            *_fuzzy_candidates(quote, unit, cited, fuzzy_min_ratio=fuzzy_min_ratio),
        ):
            quality = cand.quality
            if cap_quality is not None and _MATCH_RANK[quality] > _MATCH_RANK[cap_quality]:
                quality = cap_quality
            out.append(
                _Candidate(
                    units=cand.units,
                    start=cand.start,
                    end=cand.end,
                    quality=quality,
                    ratio=cand.ratio,
                    cited=cand.cited,
                )
            )
    return out


def _neighbor_units(
    units_by_id: Mapping[str, SourceUnit],
    cited_unit_ids: list[str],
) -> list[SourceUnit]:
    by_doc: dict[str, dict[int, SourceUnit]] = {}
    for unit in units_by_id.values():
        by_doc.setdefault(unit.doc_ref, {})[unit.ordinal] = unit

    neighbors: dict[str, SourceUnit] = {}
    for uid in cited_unit_ids:
        cited_unit = units_by_id.get(uid)
        if cited_unit is None:
            continue
        ordinal_map = by_doc.get(cited_unit.doc_ref, {})
        for ordinal in (cited_unit.ordinal - 1, cited_unit.ordinal + 1):
            neighbor = ordinal_map.get(ordinal)
            if neighbor is not None:
                neighbors[neighbor.unit_id] = neighbor
    return list(neighbors.values())


def _sorted_units(units: Sequence[SourceUnit]) -> list[SourceUnit]:
    return sorted(
        {unit.unit_id: unit for unit in units}.values(),
        key=lambda unit: (unit.doc_ref, unit.ordinal, unit.start, unit.unit_id),
    )


def _unit_hull_span(quote: str, units: Sequence[SourceUnit]) -> EvidenceSpan:
    ordered = _sorted_units(units)
    if not ordered:
        return EvidenceSpan(
            doc_ref="",
            unit_ids=[],
            start=0,
            end=0,
            quote=quote,
            match="failed",
        )
    doc_ref = ordered[0].doc_ref
    same_doc = [unit for unit in ordered if unit.doc_ref == doc_ref]
    return EvidenceSpan(
        doc_ref=doc_ref,
        unit_ids=[unit.unit_id for unit in same_doc],
        start=min(unit.start for unit in same_doc),
        end=max(unit.end for unit in same_doc),
        quote=quote,
        match="unit",
    )


def _containment_run(
    quote: str,
    units: Sequence[SourceUnit],
) -> tuple[SourceUnit, ...] | None:
    quote_norm = _normalize_plain(quote)
    if not quote_norm:
        return None
    for run in _consecutive_runs(units):
        combined_norm = _normalize_plain("".join(unit.text for unit in run))
        if quote_norm in combined_norm:
            return run
    return None


def _units_containing_patterns(
    units: Sequence[SourceUnit],
    patterns: Sequence[Pattern[str]],
) -> list[SourceUnit]:
    return [
        unit
        for unit in _sorted_units(units)
        if any(pattern.search(unit.text) for pattern in patterns)
    ]


def _pick_best(candidates: list[_Candidate]) -> tuple[Optional[_Candidate], Optional[str]]:
    if not candidates:
        return None, None

    unique: dict[tuple[object, ...], _Candidate] = {}
    for candidate in candidates:
        key = (
            tuple(unit.unit_id for unit in candidate.units),
            candidate.start,
            candidate.end,
            candidate.quality,
            candidate.ratio,
            candidate.cited,
        )
        unique.setdefault(key, candidate)
    candidates = list(unique.values())

    def quality_key(c: _Candidate) -> tuple[int, float, int]:
        return (
            _MATCH_RANK[c.quality],
            c.ratio,
            1 if c.cited else 0,
        )

    best_quality = max(quality_key(candidate) for candidate in candidates)
    top = [candidate for candidate in candidates if quality_key(candidate) == best_quality]
    best = min(
        top,
        key=lambda candidate: (
            candidate.start,
            candidate.end,
            tuple(unit.unit_id for unit in candidate.units),
        ),
    )
    detail = f"ambiguous(n={len(top)})" if len(top) > 1 else None
    return best, detail


def _exact_normalized_upgrade(
    quote: str,
    units: Sequence[SourceUnit],
) -> AlignmentResult | None:
    ordered = _sorted_units(units)
    candidates = [
        candidate
        for unit in ordered
        for candidate in _exact_candidates(quote, unit, True)
    ]
    if not candidates:
        candidates = [
            candidate
            for unit in ordered
            for candidate in _normalized_candidates(quote, unit, True)
        ]
    best, detail = _pick_best(candidates)
    if best is None:
        return None
    return AlignmentResult(
        span=EvidenceSpan(
            doc_ref=best.units[0].doc_ref,
            unit_ids=[unit.unit_id for unit in best.units],
            start=best.start,
            end=best.end,
            quote=quote,
            match=best.quality,
        ),
        detail=detail,
    )


def align_quote_with_detail(
    quote: str,
    units_by_id: Mapping[str, SourceUnit],
    cited_unit_ids: list[str],
    *,
    fuzzy_min_ratio: float = 0.92,
) -> AlignmentResult:
    """Align ``quote`` to source units; returns span and optional ambiguity detail."""
    cited = [units_by_id[uid] for uid in cited_unit_ids if uid in units_by_id]
    if not cited:
        return AlignmentResult(span=_hull_span(quote, units_by_id, cited_unit_ids))

    cited_ids = set(cited_unit_ids)

    direct = _collect_candidates(
        quote,
        cited,
        cited_ids,
        fuzzy_min_ratio=fuzzy_min_ratio,
    )
    direct.extend(
        _cross_unit_fuzzy_candidates(
            quote,
            cited,
            fuzzy_min_ratio=fuzzy_min_ratio,
        )
    )
    best, detail = _pick_best(direct)
    if best is not None:
        return AlignmentResult(
            span=EvidenceSpan(
                doc_ref=best.units[0].doc_ref,
                unit_ids=[unit.unit_id for unit in best.units],
                start=best.start,
                end=best.end,
                quote=quote,
                match=best.quality,
            ),
            detail=detail,
        )

    neighbors = _neighbor_units(units_by_id, cited_unit_ids)
    widened = _collect_candidates(
        quote,
        neighbors,
        cited_ids,
        fuzzy_min_ratio=fuzzy_min_ratio,
        cap_quality="fuzzy",
    )
    best, detail = _pick_best(widened)
    if best is not None:
        return AlignmentResult(
            span=EvidenceSpan(
                doc_ref=best.units[0].doc_ref,
                unit_ids=[unit.unit_id for unit in best.units],
                start=best.start,
                end=best.end,
                quote=quote,
                match=best.quality,
            ),
            detail=detail,
        )

    return AlignmentResult(
        span=_hull_span(quote, units_by_id, cited_unit_ids),
        detail=detail,
    )


def align_quote(
    quote: str,
    units_by_id: Mapping[str, SourceUnit],
    cited_unit_ids: list[str],
    *,
    fuzzy_min_ratio: float = 0.92,
) -> EvidenceSpan:
    """Pure quote→span alignment ladder (§5.4.2)."""
    return align_quote_with_detail(
        quote,
        units_by_id,
        cited_unit_ids,
        fuzzy_min_ratio=fuzzy_min_ratio,
    ).span


def _slice_blob(span: EvidenceSpan, units_by_id: Mapping[str, SourceUnit]) -> str:
    if not span.unit_ids:
        return ""
    units = sorted(
        (
            units_by_id[unit_id]
            for unit_id in span.unit_ids
            if unit_id in units_by_id
            and units_by_id[unit_id].doc_ref == span.doc_ref
            and units_by_id[unit_id].start < span.end
            and units_by_id[unit_id].end > span.start
        ),
        key=lambda unit: (unit.ordinal, unit.start, unit.unit_id),
    )
    return "".join(
        unit.text[
            max(span.start, unit.start) - unit.start
            : min(span.end, unit.end) - unit.start
        ]
        for unit in units
    )


def _quote_contains_value(
    token_type: str,
    raw_value: Any,
    quote: str,
    *,
    patterns: Sequence[Pattern[str]] | None = None,
) -> bool:
    if patterns is None:
        norm = normalize_value(token_type, raw_value)
        patterns = value_patterns(token_type, norm.canon)
    return any(pattern.search(quote) for pattern in patterns)


def check_value_in_span(
    token_type: str,
    raw_value: Any,
    span: EvidenceSpan,
    units_by_id: Mapping[str, SourceUnit],
) -> ValueCheck:
    """Return whether the normalized literal appears inside the aligned span."""
    if raw_value is not None and isinstance(raw_value, dict) and "$ref" in raw_value:
        return ValueCheck(status="n/a", detail="structural $ref")

    norm = normalize_value(token_type, raw_value)
    haystack = _slice_blob(span, units_by_id)
    if not haystack:
        return ValueCheck(status="fail", detail="empty span slice")

    for pattern in value_patterns(token_type, norm.canon):
        if pattern.search(haystack):
            return ValueCheck(status="pass", detail=f"matched {norm.canon!r}")
    return ValueCheck(status="fail", detail=f"normalized {norm.canon!r} not found")


def is_concrete_value_field(field_path: str) -> bool:
    """Whether ``field_path`` carries a concrete value requiring literal verification."""
    if field_path in _VERBATIM_FIELD_PATHS:
        return True
    if field_path.endswith(".value") or field_path == "value.default":
        return True
    return field_path in {"value.default", "body", "governance.preferred_form"}


def is_verbatim_exact_field(field_path: str) -> bool:
    return field_path in _VERBATIM_FIELD_PATHS or field_path == "body"


@dataclass(frozen=True, slots=True)
class ValueVerificationResult:
    """Alignment + value check + verification level for one evidence path."""

    span: EvidenceSpan
    value_check: ValueCheck
    verification: Verification
    detail: Optional[str] = None


def verify_value_path(
    *,
    field_path: str,
    token_type: str,
    raw_value: Any,
    quote: str,
    units_by_id: Mapping[str, SourceUnit],
    cited_unit_ids: list[str],
    fuzzy_min_ratio: float = 0.92,
) -> ValueVerificationResult:
    """Verify one value-bearing evidence path (§5.4.3)."""
    if isinstance(raw_value, dict) and "$ref" in raw_value:
        alignment = align_quote_with_detail(
            quote,
            units_by_id,
            cited_unit_ids,
            fuzzy_min_ratio=fuzzy_min_ratio,
        )
        return ValueVerificationResult(
            span=alignment.span,
            value_check=ValueCheck(status="n/a", detail="structural $ref"),
            verification="unverified",
            detail=alignment.detail,
        )

    verbatim_exact = is_verbatim_exact_field(field_path)
    if verbatim_exact:
        alignment = align_quote_with_detail(
            quote,
            units_by_id,
            cited_unit_ids,
            fuzzy_min_ratio=fuzzy_min_ratio,
        )
        expected = normalize_value("preferred_form" if "preferred_form" in field_path else "body", raw_value)
        actual = normalize_value("preferred_form" if "preferred_form" in field_path else "body", quote)
        if alignment.span.match != "exact" or expected.canon != actual.canon:
            return ValueVerificationResult(
                span=alignment.span,
                value_check=ValueCheck(
                    status="fail",
                    detail="verbatim field requires exact NFC-trimmed match",
                ),
                verification="unverified",
                detail=alignment.detail,
            )
        return ValueVerificationResult(
            span=alignment.span,
            value_check=ValueCheck(status="pass", detail="verbatim exact match"),
            verification="value_verified",
            detail=alignment.detail,
        )

    cited = _sorted_units(
        [units_by_id[unit_id] for unit_id in cited_unit_ids if unit_id in units_by_id]
    )

    # Composite values (e.g. {"base": {"$ref": ...}, "top": {"$ref": ...}} under
    # a scalar token_type) cannot be literal-matched against prose; their
    # members verify through the $ref targets' own records. Route them down the
    # span-only path instead of letting normalize_value raise on the mapping.
    # Gradient dicts stay concrete: their normalizer handles mappings.
    composite_value = isinstance(raw_value, (dict, list)) and not (
        isinstance(raw_value, dict) and token_type.casefold() == "gradient"
    )
    norm = None
    if is_concrete_value_field(field_path) and not composite_value:
        try:
            norm = normalize_value(token_type, raw_value)
        except (TypeError, ValueError):
            # Value doesn't fit the declared type's scalar shape (e.g. a
            # gradient described as free text). No canonical literal exists to
            # match, so degrade to span-only verification with value_check
            # "n/a" — same treatment as composites — rather than crash.
            norm = None
    if norm is None:
        run = _containment_run(quote, cited)
        containment_detail: str | None = None
        if run is None:
            neighbors = _neighbor_units(units_by_id, cited_unit_ids)
            run = _containment_run(quote, [*cited, *neighbors])
            if run is not None:
                containment_detail = "widened"

        if run is not None:
            span = _unit_hull_span(quote, run)
            upgrade = _exact_normalized_upgrade(quote, run)
            if upgrade is not None:
                span = upgrade.span
                if containment_detail is None:
                    containment_detail = upgrade.detail
            return ValueVerificationResult(
                span=span,
                value_check=ValueCheck(status="n/a"),
                verification="span_verified",
                detail=containment_detail,
            )

        alignment = align_quote_with_detail(
            quote,
            units_by_id,
            cited_unit_ids,
            fuzzy_min_ratio=fuzzy_min_ratio,
        )
        verification: Verification = (
            "unverified" if alignment.span.match == "failed" else "span_verified"
        )
        return ValueVerificationResult(
            span=alignment.span,
            value_check=ValueCheck(status="n/a"),
            verification=verification,
            detail=alignment.detail,
        )

    patterns = value_patterns(token_type, norm.canon)
    hit_units = _units_containing_patterns(cited, patterns)
    containment_detail = None
    if not hit_units:
        neighbors = _neighbor_units(units_by_id, cited_unit_ids)
        hit_units = _units_containing_patterns(neighbors, patterns)
        if hit_units:
            containment_detail = "widened"

    if not hit_units:
        return ValueVerificationResult(
            span=_hull_span(quote, units_by_id, cited_unit_ids),
            value_check=ValueCheck(
                status="fail",
                detail=f"normalized {norm.canon!r} not found in cited units or neighbors",
            ),
            verification="unverified",
        )

    span = _unit_hull_span(quote, hit_units)
    if not _quote_contains_value(
        token_type,
        raw_value,
        quote,
        patterns=patterns,
    ):
        return ValueVerificationResult(
            span=span,
            value_check=ValueCheck(
                status="fail",
                detail="quote missing normalized value literal",
            ),
            verification="unverified",
            detail=containment_detail,
        )

    upgrade = _exact_normalized_upgrade(quote, hit_units)
    if upgrade is not None:
        span = upgrade.span
        if containment_detail is None:
            containment_detail = upgrade.detail
    return ValueVerificationResult(
        span=span,
        value_check=ValueCheck(status="pass", detail=f"matched {norm.canon!r}"),
        verification="value_verified",
        detail=containment_detail,
    )
