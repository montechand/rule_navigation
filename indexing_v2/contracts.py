"""v2 contracts: models and canonical forms shared by all extraction/cascade stages."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Literal, Optional, TypeVar

from pydantic import BaseModel, Field

from shared import config
from shared.schemas import (
    PREDICATE_REGISTRY,
    BrandRule,
    BrandToken,
    ContentSubType,
    DesignAsset,
    DesignTemplate,
    Predicate,
)

SCHEMA_VERSION = "2.0"

# --- S0: source units -------------------------------------------------------

UnitKind = Literal[
    "heading",
    "list_item",
    "table_row",
    "sentence",
    "code_block",
    "blank",
    "other",
]


class SourceUnit(BaseModel):
    schema_version: str = SCHEMA_VERSION
    unit_id: str
    brand_id: str
    doc_ref: str
    ordinal: int
    start: int
    end: int
    kind: UnitKind
    text: str
    heading_path: list[str] = Field(default_factory=list)


# --- S1: unit labels --------------------------------------------------------

UnitLabelName = Literal[
    "value",
    "normative",
    "conditional",
    "verbatim",
    "asset_ref",
    "structural",
    "example",
    "narrative",
    "noise",
]
EntityKind = Literal[
    "token_primitive",
    "token_semantic",
    "rule",
    "asset",
    "subtype",
    "template",
]


class UnitLabel(BaseModel):
    schema_version: str = SCHEMA_VERSION
    unit_id: str
    labels: list[UnitLabelName]
    expected_yield: list[EntityKind]
    required: bool
    heuristic_locked: list[UnitLabelName]
    confidence: float


# --- S2/S3: evidence & provenance ------------------------------------------

class Evidence(BaseModel):
    """What the extractor claims. Attached by LLMs at entity level and at value-bearing
    sub-paths (see EVIDENCE_PATHS)."""

    unit_ids: list[str]
    quotes: list[str] = Field(default_factory=list)


MatchQuality = Literal["exact", "normalized", "unit", "fuzzy", "failed"]
Verification = Literal["value_verified", "span_verified", "unverified"]


class EvidenceSpan(BaseModel):
    doc_ref: str
    unit_ids: list[str]
    start: int
    end: int
    quote: str
    match: MatchQuality


class ValueCheck(BaseModel):
    status: Literal["pass", "fail", "n/a"]
    detail: Optional[str] = None


class ProvenanceRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    entity_id: str
    field: str
    spans: list[EvidenceSpan]
    value_check: ValueCheck
    verification: Verification


EVIDENCE_PATHS: dict[EntityKind, list[str]] = {
    "token_primitive": ["", "value.default", "value.variants[*].value"],
    "token_semantic": ["", "value.default", "value.variants[*].value"],
    "rule": ["", "governance.preferred_form", "effect", "snippets"],
    "asset": [""],
    "subtype": [""],
    "template": ["", "body"],
}

# --- S2: run variants / S4: ensemble ----------------------------------------

class RunVariant(BaseModel):
    run_id: str
    model: str
    temperature: float = 0.0
    replicate: int = 0


class ExtractionMeta(BaseModel):
    runs: int
    support: int
    field_agreement: dict[str, float] = Field(default_factory=dict)
    confidence: Literal["high", "medium", "low"]
    champion_run: str
    dissent_unit_ids: list[str] = Field(default_factory=list)


# --- S5: critic --------------------------------------------------------------

FindingType = Literal[
    "omission",
    "fabrication",
    "value_distortion",
    "wrong_condition",
    "wrong_typing",
    "bad_cluster",
    "governance_miss",
    "other",
]
PatchOp = Literal["add", "update", "delete", "split", "merge"]


class Patch(BaseModel):
    op: PatchOp
    entity_kind: EntityKind
    target_entity_ids: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    schema_version: str = SCHEMA_VERSION
    finding_id: str
    round: int
    finding_type: FindingType
    severity: Literal["info", "minor", "major", "critical"]
    target_entity_id: Optional[str] = None
    unit_ids: list[str] = Field(default_factory=list)
    description: str
    proposed_patch: Optional[Patch] = None
    resolution: Literal[
        "applied",
        "rejected_mechanical",
        "rejected_verification",
        "deferred_human",
        "open",
    ] = "open"


# --- S6: ledger ---------------------------------------------------------------

class LedgerRow(BaseModel):
    unit_id: str
    required: bool
    expected_yield: list[EntityKind]
    claimed_by: list[str]
    status: Literal["covered", "unclaimed", "over_claimed", "excluded"]


class CoverageReport(BaseModel):
    schema_version: str = SCHEMA_VERSION
    brand: str
    rounds: int
    value_coverage: float
    normative_coverage: float
    verbatim_coverage: float
    per_blob: dict[str, dict[str, float]]
    unclaimed_unit_ids: list[str]
    over_claimed_unit_ids: list[str]
    orphan_entity_ids: list[str]
    rows: list[LedgerRow]


# --- S6/S8: triage -----------------------------------------------------------

TriageQueue = Literal[
    "unclaimed_unit",
    "unverified_value",
    "over_claimed",
    "conflict",
]


class Disposition(BaseModel):
    status: Literal["open", "waived", "deferred"] = "open"
    reason: Optional[
        Literal[
            "classifier_false_positive",
            "duplicate",
            "out_of_scope",
            "source_ambiguous",
            "accepted_risk",
            "other",
        ]
    ] = None
    note: str = ""
    owner: Optional[str] = None


class TriageItem(BaseModel):
    schema_version: str = SCHEMA_VERSION
    queue: TriageQueue
    key: str
    subject_id: str
    context: str
    disposition: Disposition = Field(default_factory=Disposition)


# --- S9/S10: guards, specificity, contexts ----------------------------------

class GuardTerm(BaseModel):
    op: Literal["eq", "in", "has_tag"]
    values: list[str]


Guard = dict[str, GuardTerm]


class Binding(BaseModel):
    """A candidate assignment of a value to an element_path under a guard."""

    element_path: str
    token_id: Optional[str] = None
    value: Any
    guard: Guard
    source_kind: Literal["rule_binding", "token_variant", "token_default"]
    source_id: str
    hardness: Literal["hard_constraint", "strong_default", "soft_guidance"]
    scope: Literal["org_baseline", "brand", "campaign"]
    selector_rank: int
    precedence: int


SPECIFICITY_DOC = """Total order (higher tuple wins), evaluated left→right:
(hardness: hard=3|strong=2|soft=1,
 scope: campaign=3|brand=2|org_baseline=1,
 selector_rank,
 n_bound_axes: len(guard),
 source_kind: rule_binding=2|token_variant=1|token_default=0,
 precedence,
 source_id)               # final deterministic tiebreak — equal-through-precedence
                          # with DIFFERENT values is a Conflict, id never silently decides values
"""


class Conflict(BaseModel):
    kind: Literal["hard_hard", "equal_specificity", "intra_token", "verbatim_clash"]
    element_path: Optional[str] = None
    a_id: str
    b_id: str
    overlap_guard: Guard
    detail: str


class ContextKey(BaseModel):
    """Email-level axes only (§5.10.1). Canonical string form is the cache/file key."""

    audience: str = "dtp_patient"
    surface: str = "email"
    campaign: str = "none"
    theme: str = "none"
    content_tags: list[str] = Field(default_factory=list)

    def canonical(self) -> str:
        tags = "+".join(self.content_tags) or "none"
        return (
            f"audience={self.audience};campaign={self.campaign};"
            f"surface={self.surface};tags={tags};theme={self.theme}"
        )


# --- helpers -----------------------------------------------------------------

_T = TypeVar("_T", bound=BaseModel)


def slugify(s: str, max_len: int = 48) -> str:
    """Compatible with indexing.build_kb.slugify."""
    normalized = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return normalized[:max_len].rstrip("_") or "x"


def _canonical_json_obj(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return _canonical_json_obj(obj.model_dump(mode="json"))
    if isinstance(obj, dict):
        return {str(k): _canonical_json_obj(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, list):
        return [_canonical_json_obj(v) for v in obj]
    if isinstance(obj, tuple):
        return [_canonical_json_obj(v) for v in obj]
    return obj


def stable_hash(obj: Any) -> str:
    """SHA1 of canonical JSON (sorted dict keys; list order preserved), first 16 hex chars."""
    canon = _canonical_json_obj(obj)
    payload = json.dumps(canon, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def read_jsonl(path: Path, model: type[_T] | None = None) -> list[Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[Any] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        rows.append(model.model_validate(data) if model is not None else data)
    return rows


def write_jsonl(path: Path, items: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    lines: list[str] = []
    for item in items:
        if isinstance(item, BaseModel):
            payload = item.model_dump(mode="json")
        else:
            payload = item
        lines.append(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    os.replace(tmp, path)


# --- KB snapshot -------------------------------------------------------------

_PREDICATE_SEEDS: dict[str, list[str]] = {
    "background_group": ["dark", "light"],
    "breakpoint": ["desktop", "mobile"],
    "position_in_email": ["first", "last"],
}


def _predicate_value_strings(kind: str, value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        keyed: dict[str, Any] = {
            "background_group": "group",
            "background_token": "token_id",
            "theme": "theme",
            "content_tag": "tag",
            "campaign": "name",
            "breakpoint": "breakpoint",
            "adjacent_section_state": "state",
            "position_in_email": "position",
            "first_mention": "term",
        }
        field = keyed.get(kind)
        if field is not None and field in value:
            return [str(value[field])]
        if len(value) == 1:
            axis, inner = next(iter(value.items()))
            return _predicate_value_strings(str(axis), inner)
        out: list[str] = []
        for axis, inner in value.items():
            out.extend(_predicate_value_strings(str(axis), inner))
        return out
    return [str(value)]


def _add_predicate_values(domains: dict[str, set[str]], kind: str, value: Any) -> None:
    for item in _predicate_value_strings(kind, value):
        domains.setdefault(kind, set()).add(item)


def _scan_predicate_dict(domains: dict[str, set[str]], when: Any) -> None:
    if not isinstance(when, dict):
        return
    for axis, raw in when.items():
        _add_predicate_values(domains, str(axis), raw)


def _scan_predicate(domains: dict[str, set[str]], predicate: Predicate) -> None:
    _add_predicate_values(domains, predicate.kind, predicate.value)


def _scan_content_tags(domains: dict[str, set[str]], tags: Any) -> None:
    if not isinstance(tags, list):
        return
    for tag in tags:
        if tag is not None:
            domains.setdefault("content_tag", set()).add(str(tag))


def _collect_predicate_domains(
    rules: dict[str, BrandRule],
    tokens: dict[str, BrandToken],
    subtypes: dict[str, ContentSubType],
    templates: dict[str, DesignTemplate],
) -> dict[str, list[str]]:
    domains: dict[str, set[str]] = {
        kind: set(_PREDICATE_SEEDS.get(kind, [])) for kind in PREDICATE_REGISTRY
    }

    for rule in rules.values():
        for predicate in rule.applies_when or []:
            _scan_predicate(domains, predicate)

    for token in tokens.values():
        value = token.value
        if isinstance(value, dict):
            for variant in value.get("variants") or []:
                if isinstance(variant, dict):
                    _scan_predicate_dict(domains, variant.get("when"))
        gate = (token.gated or {}).get("gate") if token.gated else None
        if isinstance(gate, dict):
            _scan_predicate(domains, Predicate.model_validate(gate))

    for subtype in subtypes.values():
        usage = subtype.assembly if isinstance(subtype.assembly, dict) else None
        if usage:
            _scan_content_tags(domains, usage.get("requires_content_tags"))

    for template in templates.values():
        usage = template.usage_conditions if isinstance(template.usage_conditions, dict) else None
        if usage:
            _scan_content_tags(domains, usage.get("requires_content_tags"))

    return {kind: sorted(values) for kind, values in sorted(domains.items())}


def _load_entity_dir(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    for file_path in sorted(path.glob("*.json")):
        if file_path.name.startswith("_"):
            continue
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        out[str(raw["id"])] = raw
    return out


class KBSnapshot(BaseModel):
    """Thin typed loader over an on-disk brand KB."""

    brand: str
    rules: dict[str, BrandRule]
    tokens: dict[str, BrandToken]
    assets: dict[str, DesignAsset]
    subtypes: dict[str, ContentSubType]
    templates: dict[str, DesignTemplate]
    predicate_domains: dict[str, list[str]]

    @classmethod
    def load(cls, brand: str) -> KBSnapshot:
        root = config.kb_dir(brand)
        if not root.exists():
            raise FileNotFoundError(f"KB for brand '{brand}' not built yet: {root}")

        rules = {k: BrandRule.model_validate(v) for k, v in _load_entity_dir(root / "rules").items()}
        tokens = {k: BrandToken.model_validate(v) for k, v in _load_entity_dir(root / "tokens").items()}
        assets = {k: DesignAsset.model_validate(v) for k, v in _load_entity_dir(root / "assets").items()}
        subtypes = {
            k: ContentSubType.model_validate(v) for k, v in _load_entity_dir(root / "subtypes").items()
        }
        templates = {
            k: DesignTemplate.model_validate(v)
            for k, v in _load_entity_dir(root / "templates" / "_meta").items()
        }
        predicate_domains = _collect_predicate_domains(rules, tokens, subtypes, templates)

        return cls(
            brand=brand,
            rules=rules,
            tokens=tokens,
            assets=assets,
            subtypes=subtypes,
            templates=templates,
            predicate_domains=predicate_domains,
        )
