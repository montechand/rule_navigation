"""One-time migration: design bibles (semi-structured markdown blobs) -> structured KB.

TOKEN-FIRST variant. Per brand:
  Pass A1a (1 call) : exhaustive PRIMITIVE token extraction from the whole bible —
                      every concrete styling value (hex, opacity stop, px step, radius,
                      weight, casing, alignment, treatment, ...).
  Pass A1b (1 call) : SEMANTIC token extraction — element-path bindings (cta.button.fill,
                      callout.fill.opacity, h1.color, ...) whose values $ref primitives
                      and whose conditional IF/ELSE lives in value.variants[].when.
  Pass A2  (1 call) : rest of the catalog (assets, governance, subtypes, asset_groups),
                      referencing token ids.
  Pass B (per blob) : cluster each blob (= rule_group) into coherent topic-level
                      brand_rule rows that BIND tokens instead of restating values.
                      Parallel with a semaphore.
  Pass C (deterministic): validate/coerce enums, derive token_ids/asset_ids, build
                      graph.json (incl. semantic->primitive resolves_to edges), indices,
                      schema docs, and per-group review files.

LLM outputs are cached by content hash under indexing/_cache/{brand}/ so re-runs after
code changes don't re-pay extraction.

Usage:
  .venv/bin/python -m indexing.build_kb --brand lisraya ibsrela [--force]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError
from rich.console import Console

from shared import config
from shared.llm import Usage, complete_json
from shared.schemas import (
    ASSET_TYPES,
    AUDIENCES,
    CONSTRAINT_TYPES,
    CONTENT_TYPES,
    EVALUATION_SCOPES,
    GOV_TYPES,
    HARDNESS,
    POLARITIES,
    PREDICATE_REGISTRY,
    RELATIONS,
    RULE_CLASSES,
    SCOPES,
    SECTION_TYPES,
    SEVERITIES,
    SUBTYPE_KINDS,
    TOKEN_KINDS,
    TOKEN_TIERS,
    TOKEN_TYPES,
    VERDICTS,
    AssetGroup,
    BrandRule,
    BrandToken,
    ContentSubType,
    DesignAsset,
    Governance,
    Predicate,
    RuleGroup,
    RuleRelation,
    Selector,
)
from indexing import schema_docs

console = Console()
CACHE_DIR = Path(__file__).parent / "_cache"

RULE_CLASS_ALIASES = {
    "color": "color_application", "colors": "color_application", "colour": "color_application",
    "copy": "copy_editorial", "editorial": "copy_editorial", "content": "copy_editorial",
    "tone": "voice_tone", "voice": "voice_tone",
    "icon": "iconography", "icons": "iconography",
    "image": "imagery", "images": "imagery", "photography": "imagery",
    "type": "typography", "font": "typography", "fonts": "typography",
    "grid": "layout", "structure": "assembly", "governance": "copy_editorial",
    "buttons": "cta", "button": "cta",
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def slugify(s: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s[:max_len].rstrip("_") or "x"


def _cache_path(brand: str, kind: str, content: str) -> Path:
    h = hashlib.sha1(f"{kind}|{config.EXTRACT_MODEL}|{content}".encode()).hexdigest()[:16]
    return CACHE_DIR / brand / f"{kind}_{h}.json"


async def cached_json_call(brand: str, kind: str, system: str, user: str,
                           usage: Usage, max_tokens: int = 32000) -> Any:
    cp = _cache_path(brand, kind, system + "\n" + user)
    if cp.exists():
        return json.loads(cp.read_text())
    result = await complete_json(config.EXTRACT_MODEL, system, user, max_tokens=max_tokens, usage=usage)
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(result, indent=2))
    return result


def load_bible(brand: str) -> dict[str, list[str]]:
    raw = json.loads(config.DESIGN_BIBLES[brand].read_text())
    # Shape: {"website": {category: [blob, ...]}}
    return raw.get("website", raw)


# ---------------------------------------------------------------------------
# Pass A — token-first entity catalog
# ---------------------------------------------------------------------------

CATALOG_SYSTEM = """You are a meticulous data-migration engineer. You convert a pharma brand's
design bible (markdown blobs) into a structured entity catalog. Extract ONLY what the
document states; never invent values. Output a single JSON object, no prose."""

TOKEN_FIELDS_COMMON = """    "derived_from": {{"base_token_id": "...", "op": "tint|opacity|mix", "amount": <0-1>}} | null,
    "aliases": ["..."], "tier": "primary|secondary_accent|tertiary|campaign" | null,
    "scope": "global" | "campaign:<name>" | "partnership:<name>",
    "audience": "dtp_patient|hcp|caregiver" | null, "usage_ratio": <0-1> | null,
    "gated": {{"is_gated": true, "gate": {{"kind": "content_tag", "value": "lpga"}}}} | null,
    "notes": "<semantic meaning / source phrasing>" | null"""

TOKENS_PRIMITIVE_PROMPT = """Brand: {brand}

Extract EVERY PRIMITIVE brand token from the design bible below. A primitive token is one
raw reusable styling value. Be EXHAUSTIVE — every concrete value the document commits to
is a token. Expect a large catalog; do not summarize or merge distinct values.

Return JSON:
{{
  "tokens": [{{
    "id": "tok_{brand}_<type>_<name>",
    "token_type": one of {token_types},
    "key": "<type>.<tier_or_group>.<name>"  (e.g. "color.primary.brand_blue", "opacity.callout.80", "radius.accent_shape.large", "spacing.step.24", "case.headline.title_case"),
    "value": {{"default": <value>, "variants": [{{"when": {{"surface"|"breakpoint": "..."}}, "value": <value>}}] | null}},
{common}
  }}]
}}

Extract as primitives (non-exhaustive checklist — mine the whole document):
- colors: every named hex (all palettes incl. campaign/partnership), with aliases
- gradients: every approved gradient with its stops and angle
- opacity/tint stops: every %, e.g. 30/40/60/70/75/80, wave-layer transparency
- fonts: families + per-surface substitution variants (print vs email/ppt fallback)
- weights: every named weight in use (Light/Regular/SemiBold/Bold/ExtraBold/Black/Heavy/800...)
- type_scale: every level spec (H1/H2/H3/body/secondary/footnote/ISI...) with px sizes,
  desktop-vs-mobile variants, line-heights
- line_height and letter_spacing values stated anywhere
- case: casing conventions as values (title_case, sentence_case, all_caps)
- spacing/padding/margin: the base unit and every step and every named padding spec
  (section padding by type, gutters, card padding, image-text gaps, rhythm gaps)
- size/dimension: canvas widths, breakpoints, button dimensions, touch-target minimums,
  icon minimum sizes, component reference dims
- radius: every corner-radius spec including exact multi-value signatures
  (e.g. "49.52px 1.76px 40px 1.76px"), pill radii, uniform radii
- border/shadow specs (rule weights, drop shadows with color+blur)
- ratio: palette usage ratios, grid ratios, radius ratios (e.g. 5:1)
- alignment values (left/center) where the doc commits to them
- image_treatment / icon_style: named treatments (warm lifestyle photography,
  accent-shape crop, minimal line icons with rounded caps, circular green-tinted icons)
- breakpoints as their own tokens

Rules of thumb:
- One value = one token. The SAME hex appearing under two names = ONE token with aliases.
- Derived values (40% tint of X, top layer at 70% over base) -> derived_from.
- Reserved/conditional values (teal only with LPGA; Avenir Heavy only for boxed warning)
  -> gated with a predicate {{kind, value}} from: {predicates}.
- Use lowercase snake_case ids. Do not invent values not in the document.

DESIGN BIBLE:
{bible}
"""

TOKENS_SEMANTIC_PROMPT = """Brand: {brand}

Below is the design bible plus the already-extracted PRIMITIVE token catalog. Now extract
EVERY SEMANTIC token: an element-path-addressed binding that says WHICH value applies
WHERE, and under WHAT condition. This layer absorbs the IF/ELSE logic of the brand system
— background-conditional swaps, breakpoint swaps, surface swaps, campaign/scene pairings.
Be EXHAUSTIVE: every element-level styling commitment in the document becomes a semantic
token. Expect roughly one semantic token per styled element property.

Return JSON:
{{
  "tokens": [{{
    "id": "tok_{brand}_<element_path_with_underscores>",
    "token_type": one of {token_types} (the property's type: color for fills/text colors, radius for corners, ...),
    "key": "<element_path>"  (dotted, e.g. "cta.button.fill", "callout.fill.opacity", "h1.color", "body.link.color", "section.padding.sides"),
    "element_paths": ["<dotted path(s) this binds>"],
    "value": {{
      "default": {{"$ref": "tok_<primitive_id>"}} | <literal>,
      "variants": [{{"when": {{"<predicate>": <value>}}, "value": {{"$ref": "tok_..."}} | <literal>}}] | null
    }},
{common}
  }}]
}}

How to encode the IF/ELSE:
- "On light backgrounds green button with white label; on dark backgrounds white button
  with green label" becomes TWO semantic tokens (cta.button.fill, cta.button.label.color),
  each with default + variants keyed by {{"background_group": "light"|"dark"}}.
- Per-scene / per-campaign pairings -> variants keyed by {{"content_tag": ...}} or
  {{"campaign": ...}}; theme-driven values -> {{"theme": ...}}.
- Desktop/mobile -> {{"breakpoint": "desktop"|"mobile"}}; print/email/ppt -> {{"surface": ...}}.
- Position/adjacency conditions -> {{"position_in_email": ...}} or {{"adjacent_section_state": ...}}.
- `when` keys come from the predicate registry: {predicates} (plus "surface").
- Element paths: section-scoped where the doc scopes them (cta.button.fill, chart.header.color,
  callout.main.rule_color, hero.headline.color, isi.body.size, footnote.size,
  patient_story.quote.style, symptom_trio.icon.order, section.padding.top, ...).
- Reference primitives by {{"$ref": "tok_..."}} whenever the value exists in the primitive
  catalog; keep literals only for one-off values, and prefer promoting repeated literals.
- Gated/reserved element bindings -> gated. Campaign-scoped -> scope "campaign:<name>".
- Use ONLY primitive ids from the catalog below; never fabricate ids.

PRIMITIVE TOKEN CATALOG:
{primitives}

DESIGN BIBLE:
{bible}
"""

CATALOG_REST_PROMPT = """Brand: {brand}

The brand's token catalog has already been extracted (summary below). Now extract the
REST of the entity catalog from the design bible. Return JSON:

{{
  "assets": [{{
    "id": "ast_{brand}_<slug>", "asset_type": "photo|icon|logo_lockup|svg_shape|wave|background|campaign_lockup|cta_image",
    "uri": "<url or null>", "mime": null, "dims": null,
    "description": "...", "alt_text": null,
    "contains_token_ids": [], "required_pairing_token_ids": [],
    "usage_conditions": {{"requires_content_tags": [], "forbidden_content_tags": [], "max_per_email": null}} | null,
    "slot_compatibility": ["hero","cta_right","icon_row","background","inline"] | null,
    "group_id": "agr_{brand}_<slug>" | null, "group_order": <int> | null,
    "source": null
  }}],
  "governance": [{{
    "id": "gov_{brand}_<slug>", "gov_type": "regulatory|legal|mlr_claim|disclosure|trademark",
    "subject": "...", "match": {{"method": "semantic|lexical|exact"}},
    "verdict": "allowed|forbidden|allowed_with_disclosure|requires_qualifier|verbatim_only",
    "preferred_form": "<the exact verbatim string when one exists>" | null,
    "severity": "info|warn|block", "rationale": "...",
    "audience": null, "content_types": null
  }}],
  "subtypes": [{{
    "id": "sub_{brand}_<slug>", "kind": "email_component|dimension_format|platform_format",
    "content_type": "email", "name": "...", "channel": "email",
    "audience": null, "best_for": "..." | null,
    "slots": ["..."] | null, "reference_dims": {{"desktop": {{"w":600,"h":1138}}, "mobile": {{"w":375,"h":788}}}} | null,
    "assembly": {{"position": "first|last|any", "repeatable": <bool>, "locked": <bool>}} | null,
    "notes": null
  }}],
  "asset_groups": [{{"id": "agr_{brand}_<slug>", "name": "...", "semantics": "..."}}]
}}

Guidance:
- assets: every concrete asset the doc references — image URLs, waves, lockups, icon sets,
  CTA right-side images, background PNGs. Fill required_pairing_token_ids (token ids from
  the catalog below) when the doc locks an asset to a color, and usage_conditions for
  content-tag gating (e.g. lpga) or per-email caps.
- governance: verbatim disclosures, required qualifiers, approved messaging frameworks,
  trademark usage adjudications. preferred_form carries the exact required string.
- subtypes: the email component library (locked header/footer components, section
  components with their editable slots, reference dims, assembly constraints).
- asset_groups: named ordered sets (e.g. a fixed icon trio, wave variant families).
- Use lowercase snake_case slugs. Do not duplicate entities; merge aliases instead.

TOKEN CATALOG (ids you may reference):
{tokens}

DESIGN BIBLE:
{bible}
"""


# ---------------------------------------------------------------------------
# Pass B — rule atomization per group
# ---------------------------------------------------------------------------

RULES_SYSTEM = """You are a meticulous data-migration engineer converting one blob of a pharma
brand's design bible into topic-level CLUSTER brand_rule rows for a closed-vocabulary schema,
on top of an already-extracted token catalog that owns all concrete values and their
conditional switching. Faithfulness over invention: every field must be grounded in the blob.
Output a single JSON object, no prose."""

RULES_PROMPT = """Brand: {brand}
Blob id: {group_id} (doc_ref: {doc_ref})

Cluster the blob below into coherent brand_rule rows. Return JSON:

{{
  "rules": [{{
    "slug": "<short_snake_case_slug>",
    "rule_class": one of {rule_classes},
    "tags": [<same vocab, secondary facets>] | null,
    "audience": one of {audiences} | null (null = all; this brand's materials are mostly {default_audience}),
    "content_types": subset of {content_types} | null (null = all surfaces; use ["email"] when email-specific),
    "scope": one of {scopes},
    "selector": {{"section_types": subset of {section_types} | null, "element_path": "<dotted path like cta.button.fill>" | null}},
    "applies_when": [{{"kind": one of {predicates}, "value": <object/string>}}] | null,
    "evaluation_scope": one of {evaluation_scopes},
    "constraint_type": one of {constraint_types} | null,
    "effect": <typed payload, see below> | null,
    "polarity": one of {polarities},
    "hardness": one of {hardness},
    "precedence": <int, 0 default; higher = wins ties>,
    "governance_ids": [<gov_ ids from catalog>] | [],
    "rule_text": "<faithful, self-contained restatement; may quote the source>",
    "intent": "<one-line WHY>",
    "snippets": "<verbatim MJML/SVG/code from the blob if illustrative>" | null
  }}],
  "relations": [{{"src_slug": "...", "dst_slug": "...", "relation": one of {relations}, "note": "..."}}]
}}

Effect payload shapes by constraint_type:
- binding: [{{"element_path": "...", "token_id": "tok_..."}}]
- cardinality: {{"target": "<selector/asset/component>", "min": int|null, "max": int|null, "per": "element|sentence|section|email"}}
- ordering: {{"sequence": ["<target>", ...], "strict": bool}}
- pairing: {{"a": "<token/asset/scene_tag>", "b": "<token/asset/scene_tag>", "relation": "requires|forbids"}}
- exclusivity: {{"subject": "<token/style/element>", "reserved_for": "<selector or trigger>"}}
- verbatim_content: {{"content": "<text>" | null, "governance_id": "gov_..." | null, "trigger": <predicate> | null}}

Hard requirements — TOKEN-FIRST CLUSTERING:
1. CLUSTER, don't atomize: produce ONE rule per coherent topic/device in the blob
   (typically 1-6 rules per blob, not one per sentence). Related normative statements that
   share a topic, selector and conditions merge into one cluster rule. EVERY normative
   statement (must/never/always/only/max/min/reserved/required) must be covered by exactly
   one cluster — no statement lost, none duplicated across rules.
2. VALUES LIVE IN TOKENS: the token catalog below already owns every concrete value (hex,
   px, %, radius, weight, casing, alignment) AND the conditional switching (semantic
   tokens carry variants keyed by background_group/breakpoint/surface/etc). Rules must
   BIND tokens, not restate them:
   - effect binding assignments reference SEMANTIC token ids wherever one exists
     (e.g. bind cta.button.fill's token — its light/dark variants come with it).
   - rule_text states the constraint topic and relationships, naming token keys; cite at
     most a couple of representative values for readability, never full value tables.
   - Do NOT restate a semantic token's variant switching as applies_when. applies_when
     gates whether the RULE applies at all (campaign, content tags, position); value
     switching stays on the token.
3. Statements with NO token content (prose obligations, editorial style, voice, process,
   verbatim requirements, cardinality/ordering/pairing/exclusivity across elements) remain
   rules with the appropriate constraint_type; keep their operative wording in rule_text.
4. Reference catalog ids (tok_/ast_/gov_/sub_/agr_) inside effect wherever the blob refers
   to a cataloged value/asset/claim/component. Use ids EXACTLY as given. Purely descriptive
   value tables already captured by tokens need NO rule unless they state a usage constraint
   beyond the token's own value/gate.
5. scope: statements marked [BASELINE]/[GENERAL]/(Solstice production rules) -> "org_baseline";
   campaign-specific (e.g. named campaign lockups/palettes) -> "campaign"; else "brand".
6. hardness: exact values/locked specs/never-change -> "hard_constraint"; strong defaults ->
   "strong_default"; taste/tone guidance -> "soft_guidance". A cluster takes the hardness of
   its strictest member statement.
7. selector.section_types: null when the rule applies to any section; otherwise the specific
   sections. Map source phrasing to the closed vocabulary (e.g. "CTA section" -> ["cta"],
   "charts" -> ["chart"], "callout boxes" -> ["callout"], locked header/footer -> top_matter/end_matter).
8. constraint_type/effect are best-effort: if the cluster resists the typed shapes, set both
   null (rule_text stays authoritative). A binding-style cluster may carry many assignments
   in one effect. Never force a bad fit.
9. relations: only within this blob's rules (e.g. an exception refining a base rule ->
   "refines"). Use sparingly.

ENTITY CATALOG (ids you may reference):
{catalog}

BLOB:
{blob}
"""


def token_lines(tokens: list[dict[str, Any]]) -> list[str]:
    lines = []
    for t in tokens:
        v = t.get("value") or {}
        default = v.get("default") if isinstance(v, dict) else v
        n_variants = len(v.get("variants") or []) if isinstance(v, dict) else 0
        extra = []
        if t.get("kind") == "semantic" and t.get("element_paths"):
            extra.append(f"paths={t['element_paths']}")
        if n_variants:
            whens = sorted({k for var in v.get("variants", []) if isinstance(var, dict)
                            for k in (var.get("when") or {})})
            extra.append(f"variants_by={whens}")
        if t.get("aliases"):
            extra.append(f"aliases={t['aliases']}")
        if t.get("gated"):
            extra.append("GATED")
        if t.get("scope") and t["scope"] != "global":
            extra.append(t["scope"])
        lines.append(f"  {t['id']}  key={t.get('key')}  default={json.dumps(default, default=str)} {' '.join(extra)}")
    return lines


def catalog_summary(catalog: dict[str, list[dict[str, Any]]]) -> str:
    lines: list[str] = []
    prims = [t for t in catalog["tokens"] if t.get("kind") != "semantic"]
    sems = [t for t in catalog["tokens"] if t.get("kind") == "semantic"]
    lines.append(f"primitive tokens ({len(prims)}):")
    lines.extend(token_lines(prims))
    lines.append(f"semantic tokens ({len(sems)}) — element bindings; variants carry the IF/ELSE:")
    lines.extend(token_lines(sems))
    lines.append("assets:")
    for a in catalog["assets"]:
        desc = (a.get("description") or "")[:90]
        lines.append(f"  {a['id']}  type={a.get('asset_type')}  {desc}")
    lines.append("governance:")
    for g in catalog["governance"]:
        lines.append(f"  {g['id']}  type={g.get('gov_type')}  verdict={g.get('verdict')}  subject={(g.get('subject') or '')[:90]}")
    lines.append("subtypes:")
    for s in catalog["subtypes"]:
        lines.append(f"  {s['id']}  {s.get('name')}  locked={bool((s.get('assembly') or {}).get('locked'))}")
    lines.append("asset_groups:")
    for ag in catalog["asset_groups"]:
        lines.append(f"  {ag['id']}  {ag.get('name')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pass C — validation / coercion
# ---------------------------------------------------------------------------

class Warnings:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, msg: str) -> None:
        self.items.append(msg)


def coerce_enum(value: Any, vocab: list[str], default: Optional[str],
                field: str, ctx: str, warns: Warnings,
                aliases: Optional[dict[str, str]] = None) -> Optional[str]:
    if value is None:
        return default
    v = str(value).strip().lower()
    if v in vocab:
        return v
    if aliases and v in aliases:
        return aliases[v]
    warns.add(f"{ctx}: {field}={value!r} not in vocab; -> {default!r}")
    return default


def coerce_enum_list(values: Any, vocab: list[str], field: str, ctx: str,
                     warns: Warnings) -> Optional[list[str]]:
    if values is None:
        return None
    if not isinstance(values, list):
        values = [values]
    kept = [str(v).strip().lower() for v in values if str(v).strip().lower() in vocab]
    dropped = [v for v in values if str(v).strip().lower() not in vocab]
    if dropped:
        warns.add(f"{ctx}: {field} dropped invalid {dropped}")
    if not kept:
        return None  # unconstrained is safer than unreachable
    return kept


ID_SCAN_RE = re.compile(r"\b(?:tok|ast|gov|sub|agr)_[a-z0-9_]+\b")


def scan_ids(obj: Any) -> set[str]:
    return set(ID_SCAN_RE.findall(json.dumps(obj, default=str))) if obj is not None else set()


def validate_rule(raw: dict[str, Any], brand: str, group_id: str, doc_ref: str,
                  used_ids: set[str], catalog_ids: set[str], warns: Warnings) -> Optional[BrandRule]:
    slug = slugify(str(raw.get("slug") or raw.get("rule_text", "rule")[:40]))
    rule_id = f"rule_{brand}_{slug}"
    n = 2
    while rule_id in used_ids:
        rule_id = f"rule_{brand}_{slug}_{n}"
        n += 1
    used_ids.add(rule_id)
    ctx = rule_id

    rule_text = (raw.get("rule_text") or "").strip()
    if not rule_text:
        warns.add(f"{ctx}: empty rule_text; skipped")
        return None

    sel_raw = raw.get("selector") or {}
    selector = Selector(
        section_types=coerce_enum_list(sel_raw.get("section_types"), SECTION_TYPES,
                                       "selector.section_types", ctx, warns),
        element_path=sel_raw.get("element_path") or None,
    )

    applies_when = None
    if raw.get("applies_when"):
        preds = []
        for p in raw["applies_when"]:
            if not isinstance(p, dict):
                warns.add(f"{ctx}: malformed predicate {p!r} dropped")
                continue
            kind = str(p.get("kind", "")).strip().lower()
            if kind not in PREDICATE_REGISTRY:
                warns.add(f"{ctx}: predicate kind {kind!r} not in registry; dropped")
                continue
            preds.append(Predicate(kind=kind, value=p.get("value")))
        applies_when = preds or None

    constraint_type = raw.get("constraint_type")
    if constraint_type is not None:
        constraint_type = str(constraint_type).strip().lower()
        if constraint_type not in CONSTRAINT_TYPES:
            warns.add(f"{ctx}: constraint_type {constraint_type!r} invalid; -> null")
            constraint_type = None
    effect = raw.get("effect")

    gov_ids = [g for g in (raw.get("governance_ids") or []) if isinstance(g, str)]
    unknown_gov = [g for g in gov_ids if g not in catalog_ids]
    if unknown_gov:
        warns.add(f"{ctx}: unknown governance_ids {unknown_gov} dropped")
        gov_ids = [g for g in gov_ids if g in catalog_ids]

    # Derived indices from the structured effect (per dictionary: derived, never authored).
    referenced = scan_ids(effect) | scan_ids(applies_when and [p.model_dump() for p in applies_when])
    unknown_refs = {r for r in referenced if r not in catalog_ids}
    if unknown_refs:
        warns.add(f"{ctx}: effect references unknown ids {sorted(unknown_refs)} (kept in effect, not indexed)")
    known = referenced & catalog_ids
    token_ids = sorted(r for r in known if r.startswith("tok_"))
    asset_ids = sorted(r for r in known if r.startswith("ast_"))
    gov_ids = sorted(set(gov_ids) | {r for r in known if r.startswith("gov_")})

    sub_ids = raw.get("content_sub_type_ids")
    if sub_ids:
        valid_subs = [s for s in sub_ids if s in catalog_ids]
        if len(valid_subs) != len(sub_ids):
            warns.add(f"{ctx}: dropped unknown content_sub_type_ids")
        sub_ids = valid_subs or None

    try:
        precedence = int(raw.get("precedence") or 0)
    except (TypeError, ValueError):
        precedence = 0

    # Binding effects legitimately arrive as arrays; store uniformly as a dict.
    if isinstance(effect, list):
        effect = {"assignments": effect}
    elif not isinstance(effect, dict):
        effect = None

    return BrandRule(
        id=rule_id,
        brand_id=brand,
        rule_class=coerce_enum(raw.get("rule_class"), RULE_CLASSES, "layout",
                               "rule_class", ctx, warns, RULE_CLASS_ALIASES) or "layout",
        tags=coerce_enum_list(raw.get("tags"), RULE_CLASSES, "tags", ctx, warns),
        audience=coerce_enum(raw.get("audience"), AUDIENCES, None, "audience", ctx, warns),
        content_types=coerce_enum_list(raw.get("content_types"), CONTENT_TYPES,
                                       "content_types", ctx, warns),
        content_sub_type_ids=sub_ids,
        scope=coerce_enum(raw.get("scope"), SCOPES, "brand", "scope", ctx, warns) or "brand",
        selector=selector,
        applies_when=applies_when,
        evaluation_scope=coerce_enum(raw.get("evaluation_scope"), EVALUATION_SCOPES, "section",
                                     "evaluation_scope", ctx, warns) or "section",
        constraint_type=constraint_type,
        effect=effect if isinstance(effect, (dict, list)) else None,
        polarity=coerce_enum(raw.get("polarity"), POLARITIES, "must", "polarity", ctx, warns) or "must",
        hardness=coerce_enum(raw.get("hardness"), HARDNESS, "strong_default",
                             "hardness", ctx, warns) or "strong_default",
        precedence=precedence,
        token_ids=token_ids,
        asset_ids=asset_ids,
        governance_ids=gov_ids,
        rule_text=rule_text,
        intent=(raw.get("intent") or "").strip(),
        snippets=raw.get("snippets") or None,
        source="design_bible",
        doc_ref=doc_ref,
        group_id=group_id,
    )


# ---------------------------------------------------------------------------
# Catalog validation
# ---------------------------------------------------------------------------

def validate_catalog(raw: dict[str, Any], brand: str, warns: Warnings) -> dict[str, Any]:
    tokens: dict[str, BrandToken] = {}
    assets: dict[str, DesignAsset] = {}
    governance: dict[str, Governance] = {}
    subtypes: dict[str, ContentSubType] = {}
    asset_groups: dict[str, AssetGroup] = {}

    for t in raw.get("tokens", []):
        ctx = t.get("id", "token?")
        if ctx in tokens:
            warns.add(f"{ctx}: duplicate token id (primitive/semantic collision); kept first")
            continue
        try:
            element_paths = t.get("element_paths")
            if element_paths is not None and not isinstance(element_paths, list):
                element_paths = [str(element_paths)]
            tok = BrandToken(
                id=t["id"], brand_id=brand,
                token_type=coerce_enum(t.get("token_type"), TOKEN_TYPES, "other",
                                       "token_type", ctx, warns) or "other",
                kind=coerce_enum(t.get("kind"), TOKEN_KINDS, "primitive",
                                 "kind", ctx, warns) or "primitive",
                key=t.get("key") or t["id"],
                value=t.get("value"),
                element_paths=element_paths,
                derived_from=t.get("derived_from"),
                aliases=t.get("aliases") or [],
                tier=coerce_enum(t.get("tier"), TOKEN_TIERS, None, "tier", ctx, warns),
                scope=t.get("scope") or "global",
                audience=coerce_enum(t.get("audience"), AUDIENCES, None, "audience", ctx, warns),
                usage_ratio=t.get("usage_ratio"),
                gated=t.get("gated"),
                notes=t.get("notes"),
            )
            tokens[tok.id] = tok
        except (ValidationError, KeyError) as e:
            warns.add(f"{ctx}: token invalid, skipped ({e})")

    # Token->token $ref integrity: unknown refs are kept in value but flagged.
    for tok in tokens.values():
        refs = {r for r in scan_ids(tok.value) if r.startswith("tok_")} - {tok.id}
        unknown = [r for r in refs if r not in tokens]
        if unknown:
            warns.add(f"{tok.id}: value $refs unknown tokens {unknown}")

    for a in raw.get("assets", []):
        ctx = a.get("id", "asset?")
        try:
            asset = DesignAsset(
                id=a["id"], brand_id=brand,
                asset_type=coerce_enum(a.get("asset_type"), ASSET_TYPES, "photo",
                                       "asset_type", ctx, warns) or "photo",
                uri=a.get("uri"), mime=a.get("mime"), dims=a.get("dims"),
                description=a.get("description") or "",
                alt_text=a.get("alt_text"),
                contains_token_ids=[x for x in (a.get("contains_token_ids") or []) if x in tokens],
                required_pairing_token_ids=[x for x in (a.get("required_pairing_token_ids") or []) if x in tokens],
                usage_conditions=a.get("usage_conditions"),
                slot_compatibility=a.get("slot_compatibility"),
                group_id=a.get("group_id"),
                group_order=a.get("group_order"),
                source=a.get("source"),
            )
            assets[asset.id] = asset
        except (ValidationError, KeyError) as e:
            warns.add(f"{ctx}: asset invalid, skipped ({e})")

    for g in raw.get("governance", []):
        ctx = g.get("id", "gov?")
        try:
            gov = Governance(
                id=g["id"], brand_id=brand,
                gov_type=coerce_enum(g.get("gov_type"), GOV_TYPES, "mlr_claim",
                                     "gov_type", ctx, warns) or "mlr_claim",
                subject=g.get("subject") or "",
                match=g.get("match"),
                verdict=coerce_enum(g.get("verdict"), VERDICTS, "allowed",
                                    "verdict", ctx, warns) or "allowed",
                preferred_form=g.get("preferred_form"),
                severity=coerce_enum(g.get("severity"), SEVERITIES, "warn",
                                     "severity", ctx, warns) or "warn",
                rationale=g.get("rationale"),
                audience=coerce_enum(g.get("audience"), AUDIENCES, None, "audience", ctx, warns),
                content_types=coerce_enum_list(g.get("content_types"), CONTENT_TYPES,
                                               "content_types", ctx, warns),
            )
            governance[gov.id] = gov
        except (ValidationError, KeyError) as e:
            warns.add(f"{ctx}: governance invalid, skipped ({e})")

    for s in raw.get("subtypes", []):
        ctx = s.get("id", "subtype?")
        try:
            sub = ContentSubType(
                id=s["id"], brand_id=brand,
                kind=coerce_enum(s.get("kind"), SUBTYPE_KINDS, "email_component",
                                 "kind", ctx, warns) or "email_component",
                content_type=s.get("content_type") or "email",
                name=s.get("name") or s["id"],
                size=s.get("size"), platform=s.get("platform"),
                channel=s.get("channel") or "email",
                audience=coerce_enum(s.get("audience"), AUDIENCES, None, "audience", ctx, warns),
                best_for=s.get("best_for"), slots=s.get("slots"),
                reference_dims=s.get("reference_dims"), assembly=s.get("assembly"),
                notes=s.get("notes"),
            )
            subtypes[sub.id] = sub
        except (ValidationError, KeyError) as e:
            warns.add(f"{ctx}: subtype invalid, skipped ({e})")

    for ag in raw.get("asset_groups", []):
        ctx = ag.get("id", "asset_group?")
        try:
            grp = AssetGroup(id=ag["id"], brand_id=brand, name=ag.get("name") or ag["id"],
                             semantics=ag.get("semantics"))
            asset_groups[grp.id] = grp
        except (ValidationError, KeyError) as e:
            warns.add(f"{ctx}: asset_group invalid, skipped ({e})")

    # Drop dangling asset.group_id references.
    for asset in assets.values():
        if asset.group_id and asset.group_id not in asset_groups:
            warns.add(f"{asset.id}: unknown group_id {asset.group_id}; cleared")
            asset.group_id = None

    return {"tokens": tokens, "assets": assets, "governance": governance,
            "subtypes": subtypes, "asset_groups": asset_groups}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_graph(rules: dict[str, BrandRule], cat: dict[str, Any],
                relations: list[RuleRelation]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for s in SECTION_TYPES:
        nodes.append({"id": f"sec_{s}", "kind": "section_type", "label": s})
    for r in rules.values():
        nodes.append({"id": r.id, "kind": "rule", "label": (r.summary or r.rule_text)[:100],
                      "rule_class": r.rule_class, "scope": r.scope,
                      "all_sections": r.selector.section_types is None})
        for s in r.selector.section_types or []:
            edges.append({"src": r.id, "dst": f"sec_{s}", "type": "applies_to_section"})
        for t in r.token_ids:
            edges.append({"src": r.id, "dst": t, "type": "references_token"})
        for a in r.asset_ids:
            edges.append({"src": r.id, "dst": a, "type": "references_asset"})
        for g in r.governance_ids:
            edges.append({"src": r.id, "dst": g, "type": "governed_by"})
        for s in r.content_sub_type_ids or []:
            edges.append({"src": r.id, "dst": s, "type": "scoped_to_subtype"})
        if r.group_id:
            edges.append({"src": r.id, "dst": r.group_id, "type": "from_group"})

    for t in cat["tokens"].values():
        nodes.append({"id": t.id, "kind": "token", "token_kind": t.kind, "label": t.key})
        # semantic value $refs -> primitive tokens
        for ref in sorted({r for r in scan_ids(t.value) if r.startswith("tok_")} - {t.id}):
            if ref in cat["tokens"]:
                edges.append({"src": t.id, "dst": ref, "type": "resolves_to"})
        if t.derived_from and isinstance(t.derived_from, dict):
            base = t.derived_from.get("base_token_id")
            if base in cat["tokens"]:
                edges.append({"src": t.id, "dst": base, "type": "derived_from"})
    for a in cat["assets"].values():
        nodes.append({"id": a.id, "kind": "asset", "label": a.description[:100]})
        for t in a.contains_token_ids:
            edges.append({"src": a.id, "dst": t, "type": "contains_token"})
        for t in a.required_pairing_token_ids:
            edges.append({"src": a.id, "dst": t, "type": "requires_pairing_token"})
        if a.group_id:
            edges.append({"src": a.id, "dst": a.group_id, "type": "member_of",
                          "order": a.group_order})
    for g in cat["governance"].values():
        nodes.append({"id": g.id, "kind": "governance", "label": g.subject[:100]})
    for s in cat["subtypes"].values():
        nodes.append({"id": s.id, "kind": "subtype", "label": s.name})
    for ag in cat["asset_groups"].values():
        nodes.append({"id": ag.id, "kind": "asset_group", "label": ag.name})

    for rel in relations:
        edges.append({"src": rel.src_rule_id, "dst": rel.dst_rule_id,
                      "type": rel.relation, "note": rel.note})

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_kb(brand: str, rules: dict[str, BrandRule], cat: dict[str, Any],
             groups: dict[str, RuleGroup], relations: list[RuleRelation],
             warns: Warnings) -> None:
    root = config.kb_dir(brand)
    if root.exists():
        # Preserve vectors/ across rebuilds; everything else is regenerated.
        for child in root.iterdir():
            if child.name != "vectors":
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    root.mkdir(parents=True, exist_ok=True)

    # schema docs
    schema_dir = root / "schema"
    schema_dir.mkdir(exist_ok=True)
    for stem, content in schema_docs.entity_docs().items():
        (schema_dir / f"{stem}.md").write_text(content)
    counts = {"rules": len(rules), "tokens": len(cat["tokens"]),
              "tokens_primitive": sum(1 for t in cat["tokens"].values() if t.kind == "primitive"),
              "tokens_semantic": sum(1 for t in cat["tokens"].values() if t.kind == "semantic"),
              "assets": len(cat["assets"]),
              "governance": len(cat["governance"]), "subtypes": len(cat["subtypes"]),
              "rule_groups": len(groups), "asset_groups": len(cat["asset_groups"])}
    (schema_dir / "overview.md").write_text(schema_docs.overview_doc(brand, counts))

    # rules
    rules_dir = root / "rules"
    rules_dir.mkdir(exist_ok=True)
    index = []
    for r in rules.values():
        (rules_dir / f"{r.id}.json").write_text(json.dumps(r.model_dump(exclude_none=True), indent=2))
        index.append({
            "id": r.id, "rule_class": r.rule_class, "tags": r.tags or [],
            "sections": r.selector.section_types, "element_path": r.selector.element_path,
            "scope": r.scope, "hardness": r.hardness, "polarity": r.polarity,
            "constraint_type": r.constraint_type, "evaluation_scope": r.evaluation_scope,
            "audience": r.audience,
            "applies_when": [p.model_dump(exclude_none=True) for p in r.applies_when] if r.applies_when else None,
            "summary": r.summary or r.rule_text[:160],
        })
    (rules_dir / "_index.json").write_text(json.dumps(index, indent=2))

    # side entities
    for name, store in (("tokens", cat["tokens"]), ("assets", cat["assets"]),
                        ("subtypes", cat["subtypes"]), ("governance", cat["governance"])):
        d = root / name
        d.mkdir(exist_ok=True)
        idx = []
        for e in store.values():
            (d / f"{e.id}.json").write_text(json.dumps(e.model_dump(exclude_none=True), indent=2))
            if name == "tokens":
                variants_by = sorted({k for var in ((e.value or {}).get("variants") or [] if isinstance(e.value, dict) else [])
                                      if isinstance(var, dict) for k in (var.get("when") or {})})
                idx.append({"id": e.id, "kind": e.kind, "key": e.key, "type": e.token_type,
                            "default": (e.value or {}).get("default") if isinstance(e.value, dict) else e.value,
                            "element_paths": e.element_paths, "variants_by": variants_by or None,
                            "aliases": e.aliases, "gated": bool(e.gated),
                            "scope": e.scope if e.scope != "global" else None})
            elif name == "assets":
                idx.append({"id": e.id, "type": e.asset_type, "description": e.description[:120],
                            "uri": e.uri, "group_id": e.group_id})
            elif name == "subtypes":
                idx.append({"id": e.id, "name": e.name, "kind": e.kind,
                            "locked": bool((e.assembly or {}).get("locked"))})
            else:
                idx.append({"id": e.id, "type": e.gov_type, "verdict": e.verdict,
                            "subject": e.subject[:120]})
        (d / "_index.json").write_text(json.dumps(idx, indent=2))

    # groups + relations
    groups_dir = root / "groups"
    groups_dir.mkdir(exist_ok=True)
    (groups_dir / "rule_groups.json").write_text(
        json.dumps([g.model_dump(exclude_none=True) for g in groups.values()], indent=2))
    (groups_dir / "asset_groups.json").write_text(
        json.dumps([g.model_dump(exclude_none=True) for g in cat["asset_groups"].values()], indent=2))
    (groups_dir / "relations.json").write_text(
        json.dumps([r.model_dump(exclude_none=True) for r in relations], indent=2))

    # graph
    graph_dir = root / "graph"
    graph_dir.mkdir(exist_ok=True)
    (graph_dir / "graph.json").write_text(json.dumps(build_graph(rules, cat, relations), indent=2))

    # review files
    review_dir = root / "review"
    review_dir.mkdir(exist_ok=True)
    by_group: dict[str, list[BrandRule]] = {}
    for r in rules.values():
        by_group.setdefault(r.group_id or "?", []).append(r)
    for gid, g in groups.items():
        lines = [f"# Review: {gid}", "", f"doc_ref: `{g.doc_ref}`", "", "## Original text", "",
                 "````", g.original_text, "````", "", f"## Extracted rules ({len(by_group.get(gid, []))})", ""]
        for r in by_group.get(gid, []):
            lines.append(f"### {r.id}")
            lines.append(f"- class={r.rule_class} scope={r.scope} hardness={r.hardness} "
                         f"polarity={r.polarity} sections={r.selector.section_types} "
                         f"constraint={r.constraint_type}")
            lines.append(f"- rule_text: {r.rule_text}")
            lines.append(f"- intent: {r.intent}")
            lines.append("")
        (review_dir / f"{gid}.md").write_text("\n".join(lines))
    (review_dir / "warnings.md").write_text(
        "# Build warnings\n\n" + "\n".join(f"- {w}" for w in warns.items) if warns.items
        else "# Build warnings\n\n(none)")


# ---------------------------------------------------------------------------
# Main per-brand build
# ---------------------------------------------------------------------------

async def build_brand(brand: str, usage: Usage, concurrency: int = 4) -> None:
    console.print(f"[bold cyan]== Building KB for {brand} ==[/bold cyan]")
    bible = load_bible(brand)
    warns = Warnings()

    # Rule groups from blobs
    groups: dict[str, RuleGroup] = {}
    blobs: list[tuple[str, str, str]] = []  # (group_id, doc_ref, text)
    for category, items in bible.items():
        for i, blob in enumerate(items):
            gid = f"grp_{brand}_{slugify(category)}_{i:02d}"
            doc_ref = f"{category}[{i}]"
            groups[gid] = RuleGroup(id=gid, brand_id=brand, source="design_bible",
                                    doc_ref=doc_ref, original_text=blob)
            blobs.append((gid, doc_ref, blob))
    console.print(f"  {len(blobs)} rule_groups from {len(bible)} categories")

    # Pass A — token-first catalog
    full_bible_text = "\n\n".join(
        f"## CATEGORY: {cat_name}\n\n" + "\n\n---\n\n".join(items) for cat_name, items in bible.items()
    )
    default_audience = "dtp_patient (patient/DTC materials)" if brand == "lisraya" else "dtp_patient (DTP emails; some HCP-scope items)"
    common = TOKEN_FIELDS_COMMON

    # A1a primitives
    raw_prims = await cached_json_call(
        brand, "tokens_primitive", CATALOG_SYSTEM,
        TOKENS_PRIMITIVE_PROMPT.format(brand=brand, bible=full_bible_text,
                                       token_types=TOKEN_TYPES, common=common,
                                       predicates=PREDICATE_REGISTRY), usage)
    prim_tokens = [dict(t, kind="primitive") for t in raw_prims.get("tokens", []) if isinstance(t, dict)]
    console.print(f"  A1a: {len(prim_tokens)} primitive tokens")

    # A1b semantics (given primitives)
    raw_sems = await cached_json_call(
        brand, "tokens_semantic", CATALOG_SYSTEM,
        TOKENS_SEMANTIC_PROMPT.format(brand=brand, bible=full_bible_text,
                                      token_types=TOKEN_TYPES, common=common,
                                      predicates=PREDICATE_REGISTRY,
                                      primitives="\n".join(token_lines(prim_tokens))), usage)
    sem_tokens = [dict(t, kind="semantic") for t in raw_sems.get("tokens", []) if isinstance(t, dict)]
    console.print(f"  A1b: {len(sem_tokens)} semantic tokens")

    all_tokens = prim_tokens + sem_tokens

    # A2 rest of catalog (given tokens)
    raw_rest = await cached_json_call(
        brand, "catalog_rest", CATALOG_SYSTEM,
        CATALOG_REST_PROMPT.format(brand=brand, bible=full_bible_text,
                                   tokens="\n".join(token_lines(all_tokens))), usage)

    raw_catalog = {"tokens": all_tokens, **{k: raw_rest.get(k, []) for k in
                                            ("assets", "governance", "subtypes", "asset_groups")}}
    cat = validate_catalog(raw_catalog, brand, warns)
    catalog_ids = set(cat["tokens"]) | set(cat["assets"]) | set(cat["governance"]) \
        | set(cat["subtypes"]) | set(cat["asset_groups"])
    n_prim = sum(1 for t in cat["tokens"].values() if t.kind == "primitive")
    n_sem = len(cat["tokens"]) - n_prim
    console.print(f"  catalog: {len(cat['tokens'])} tokens ({n_prim} primitive / {n_sem} semantic), "
                  f"{len(cat['assets'])} assets, {len(cat['governance'])} governance, "
                  f"{len(cat['subtypes'])} subtypes, {len(cat['asset_groups'])} asset_groups")

    # Pass B — rules per blob, parallel
    cat_text = catalog_summary({
        "tokens": [t.model_dump() for t in cat["tokens"].values()],
        "assets": [a.model_dump() for a in cat["assets"].values()],
        "governance": [g.model_dump() for g in cat["governance"].values()],
        "subtypes": [s.model_dump() for s in cat["subtypes"].values()],
        "asset_groups": [g.model_dump() for g in cat["asset_groups"].values()],
    })
    sem = asyncio.Semaphore(concurrency)

    async def do_group(gid: str, doc_ref: str, blob: str) -> tuple[str, dict[str, Any]]:
        async with sem:
            prompt = RULES_PROMPT.format(
                brand=brand, group_id=gid, doc_ref=doc_ref,
                rule_classes=RULE_CLASSES, audiences=AUDIENCES, content_types=CONTENT_TYPES,
                scopes=SCOPES, section_types=SECTION_TYPES, predicates=PREDICATE_REGISTRY,
                evaluation_scopes=EVALUATION_SCOPES, constraint_types=CONSTRAINT_TYPES,
                polarities=POLARITIES, hardness=HARDNESS, relations=RELATIONS,
                default_audience=default_audience, catalog=cat_text, blob=blob,
            )
            result = await cached_json_call(brand, f"rules_{gid}", RULES_SYSTEM, prompt, usage)
            console.print(f"  [green]{gid}[/green]: {len(result.get('rules', []))} rules")
            return gid, result

    results = await asyncio.gather(*(do_group(g, d, b) for g, d, b in blobs))

    # Pass C — validate, ids, relations
    rules: dict[str, BrandRule] = {}
    used_ids: set[str] = set()
    relations: list[RuleRelation] = []
    for gid, res in results:
        doc_ref = groups[gid].doc_ref or gid
        slug_to_id: dict[str, str] = {}
        for raw_rule in res.get("rules", []):
            if not isinstance(raw_rule, dict):
                warns.add(f"{gid}: non-dict rule entry skipped")
                continue
            rule = validate_rule(raw_rule, brand, gid, doc_ref, used_ids, catalog_ids, warns)
            if rule is None:
                continue
            rules[rule.id] = rule
            if raw_rule.get("slug"):
                slug_to_id[slugify(str(raw_rule["slug"]))] = rule.id
        for rel in res.get("relations", []) or []:
            if not isinstance(rel, dict):
                continue
            src = slug_to_id.get(slugify(str(rel.get("src_slug", ""))))
            dst = slug_to_id.get(slugify(str(rel.get("dst_slug", ""))))
            rel_type = str(rel.get("relation", "")).strip().lower()
            if src and dst and src != dst and rel_type in RELATIONS:
                relations.append(RuleRelation(src_rule_id=src, dst_rule_id=dst,
                                              relation=rel_type, note=rel.get("note")))
            else:
                warns.add(f"{gid}: unresolved relation {rel}")

    console.print(f"  [bold]{len(rules)} rules[/bold], {len(relations)} relations, "
                  f"{len(warns.items)} warnings")
    write_kb(brand, rules, cat, groups, relations, warns)
    console.print(f"  KB written to {config.kb_dir(brand)}")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", nargs="+", default=list(config.BRANDS), choices=list(config.BRANDS))
    parser.add_argument("--force", action="store_true", help="ignore the LLM output cache")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    config.require_keys()
    if args.force:
        for b in args.brand:
            cache = CACHE_DIR / b
            if cache.exists():
                shutil.rmtree(cache)

    usage = Usage()
    for brand in args.brand:
        await build_brand(brand, usage, args.concurrency)
    console.print(f"[bold]Done.[/bold] Usage: {usage.as_dict()}")


if __name__ == "__main__":
    asyncio.run(main())
