"""Pydantic models for the v0.2 brand-rules data model, blueprints, and run results.

Vocabularies mirror newest_email_pipeline/data_models/model_iteration_0/model_dictionary.md.
`null` = unconstrained (applies to all); `[]` = explicitly none.

section_types / relations / token_types are DYNAMIC registries (shared/registries.json):
seeded cores plus model-discovered entries registered permanently at build time via the
`other.<name>` convention. The constants below are convenience snapshots loaded at import
time (core + all discovered, all brands); brand-aware consumers should go through
shared.registries / KB.section_types instead.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .registries import get_registries

_REG = get_registries()

# ---------------------------------------------------------------------------
# Closed vocabularies (v0.2 dictionary + dynamic registries)
# ---------------------------------------------------------------------------

RULE_CLASSES = [
    "typography", "color_application", "cta", "layout", "spacing", "imagery",
    "iconography", "copy_editorial", "voice_tone", "accessibility", "assembly",
]
SECTION_TYPES = _REG.section_types()  # core + discovered (all brands)
PREDICATE_REGISTRY = [
    "background_group", "background_token", "theme", "content_tag", "campaign",
    "breakpoint", "adjacent_section_state", "position_in_email", "first_mention",
]
CONSTRAINT_TYPES = [
    "binding", "cardinality", "ordering", "pairing", "exclusivity", "verbatim_content",
]
POLARITIES = ["must", "must_not", "should", "should_not", "may"]
HARDNESS = ["hard_constraint", "strong_default", "soft_guidance"]
SCOPES = ["org_baseline", "brand", "campaign"]
EVALUATION_SCOPES = ["element", "sentence", "section", "email"]
AUDIENCES = ["dtp_patient", "hcp", "caregiver"]
CONTENT_TYPES = ["email", "banner", "social", "print", "web", "ppt"]
SOURCES = ["design_bible", "brand_guide_pdf", "prior_approved_asset", "user_written"]
# "other" = validated fallback for unclassifiable values; other.<name> = discovery.
TOKEN_TYPES = _REG.token_types() + ["other"]
TOKEN_KINDS = ["primitive", "semantic"]
TOKEN_TIERS = ["primary", "secondary_accent", "tertiary", "campaign"]
ASSET_TYPES = [
    "photo", "icon", "logo_lockup", "svg_shape", "graphic_device", "background",
    "campaign_lockup", "cta_image",
]
# Vocab for the embedded brand_rule.governance facet (the standalone governance entity
# was retired — governance statements are brand_rules with this attribute set).
GOV_TYPES = ["regulatory", "legal", "mlr_claim", "disclosure", "trademark"]
VERDICTS = ["allowed", "forbidden", "allowed_with_disclosure", "requires_qualifier", "verbatim_only"]
SEVERITIES = ["info", "warn", "block"]
RELATIONS = _REG.relations()
SUBTYPE_KINDS = ["dimension_format", "platform_format", "email_component"]
CHANNELS = ["display", "social", "email", "print"]

Status = Literal["draft", "active", "deprecated", "superseded"]


# ---------------------------------------------------------------------------
# Embedded value objects on brand_rule
# ---------------------------------------------------------------------------

class Selector(BaseModel):
    """Where in the artifact the rule attaches. null section_types = all sections."""
    section_types: Optional[list[str]] = None
    element_path: Optional[str] = None  # dotted, e.g. "cta.button.fill"


class Predicate(BaseModel):
    """One applies_when condition, classified into the closed registry."""
    kind: str  # one of PREDICATE_REGISTRY
    value: Optional[Any] = None  # e.g. {"group": "dark"} / "lpga" / {"position": "first"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

class BrandRule(BaseModel):
    id: str
    brand_id: str
    rule_class: str
    tags: Optional[list[str]] = None
    audience: Optional[str] = None  # null = all
    content_types: Optional[list[str]] = None  # null = all
    content_sub_type_ids: Optional[list[str]] = None  # null = all sub-types
    scope: str = "brand"
    selector: Selector = Field(default_factory=Selector)
    applies_when: Optional[list[Predicate]] = None
    evaluation_scope: str = "section"
    constraint_type: Optional[str] = None
    effect: Optional[dict[str, Any]] = None  # typed by constraint_type; best-effort
    polarity: str = "must"
    hardness: str = "strong_default"
    precedence: int = 0
    token_ids: list[str] = Field(default_factory=list)  # derived
    asset_ids: list[str] = Field(default_factory=list)  # derived
    # Governance/compliance payload — governance is a FACET of a rule, not a separate
    # entity. Present on rules that adjudicate claims/required language/trademark use:
    # {gov_type, verdict, preferred_form?, match?, severity}. Such rules are almost
    # always hardness=hard_constraint; preferred_form carries the exact verbatim string.
    governance: Optional[dict[str, Any]] = None
    rule_text: str
    intent: str = ""
    snippets: Optional[str] = None
    summary: Optional[str] = None  # one-liner, filled by summarize_embed
    source: str = "design_bible"
    doc_ref: Optional[str] = None
    group_id: Optional[str] = None
    status: Status = "active"
    supersedes: Optional[str] = None
    version: int = 1


class TokenValue(BaseModel):
    default: Any = None
    variants: Optional[list[dict[str, Any]]] = None  # [{when: {predicate...}, value: ...}]


class BrandToken(BaseModel):
    """Token-first model: every concrete styling value or element-level binding is a token.

    kind=primitive — a raw reusable value (a hex, an opacity stop, a px step, a radius,
      a weight, an alignment, a casing, a treatment).
    kind=semantic — an element-path-addressed binding (e.g. `cta.button.fill`,
      `callout.fill.opacity`, `h1.color`) whose value references primitives via
      {"$ref": "tok_..."} and whose conditional logic (the IF/ELSE formerly encoded in
      rules) lives in value.variants[].when predicates and/or `gated`.
    """

    id: str
    brand_id: str
    token_type: str
    kind: str = "primitive"  # primitive | semantic
    key: str  # "{type}.{tier_or_element}.{name}"
    value: Any = None  # TokenValue-shaped dict or scalar; {"$ref": "tok_..."} for token refs
    element_paths: Optional[list[str]] = None  # semantic tokens: where this binds
    derived_from: Optional[dict[str, Any]] = None  # {base_token_id, op, amount}
    aliases: list[str] = Field(default_factory=list)
    tier: Optional[str] = None
    scope: str = "global"  # global | campaign:{name} | partnership:{name}
    audience: Optional[str] = None
    usage_ratio: Optional[float] = None
    gated: Optional[dict[str, Any]] = None  # {is_gated, gate: predicate}
    notes: Optional[str] = None
    status: Status = "active"
    version: int = 1


class DesignAsset(BaseModel):
    id: str
    brand_id: str
    asset_type: str
    uri: Optional[str] = None
    mime: Optional[str] = None
    dims: Optional[dict[str, Any]] = None
    description: str = ""
    alt_text: Optional[str] = None
    contains_token_ids: list[str] = Field(default_factory=list)
    required_pairing_token_ids: list[str] = Field(default_factory=list)
    usage_conditions: Optional[dict[str, Any]] = None
    slot_compatibility: Optional[list[str]] = None
    group_id: Optional[str] = None
    group_order: Optional[int] = None
    visible_to_user: bool = True
    source: Optional[str] = None
    status: Status = "active"
    version: int = 1


class ContentSubType(BaseModel):
    """Structural CLASS or format — only what the source itself defines as a reusable
    component/format (a named component-library entry, a locked supplied component, a
    dimension format). Concrete approved artifacts are design_template rows, NOT classes.
    """

    id: str
    brand_id: str
    kind: str
    content_type: str = "email"
    name: str
    size: Optional[dict[str, Any]] = None
    platform: Optional[str] = None
    channel: str = "email"
    audience: Optional[str] = None
    best_for: Optional[str] = None
    slots: Optional[list[str] | dict[str, Any]] = None
    reference_dims: Optional[dict[str, Any]] = None
    assembly: Optional[dict[str, Any]] = None  # {position, repeatable, locked}
    # fills = this class IS that section role (locked Top Matter fills [top_matter]).
    # hosts = this class CAN CARRY those roles (Primary 1-Col hosts [hero, intro, ...]).
    # Only fills feeds rule surfacing; hosts is an affordance hint.
    fills_section_types: Optional[list[str]] = None
    hosts_section_types: Optional[list[str]] = None
    notes: Optional[str] = None
    status: Status = "active"
    version: int = 1


class DesignTemplate(BaseModel):
    """Concrete approved artifact (MJML/HTML block): a template-library entry or an
    approved snippet embedded verbatim in the design bible. Instances, not classes —
    rules do NOT scope to templates; they scope to classes/roles and templates inherit
    via instance_of / fills_section. Per-instance selection conditions live here.
    """

    id: str  # tpl_{brand}_{slug}
    brand_id: str
    name: str
    description: Optional[str] = None
    source: str = "template_library"  # template_library | design_bible
    template_ref: Optional[str] = None  # external library id
    file: Optional[str] = None  # kb-relative path to the stored body
    instance_of: Optional[str] = None  # FK -> content_sub_type (when it realizes a class)
    fills_section_types: Optional[list[str]] = None
    group_id: Optional[str] = None  # FK -> template_group
    group_order: Optional[int] = None
    usage_conditions: Optional[dict[str, Any]] = None  # {requires_content_tags: [...], ...}
    audience: Optional[str] = None
    notes: Optional[str] = None
    status: Status = "active"
    version: int = 1


class TemplateGroup(BaseModel):
    """Pick-one set of alternate templates (e.g. the brand's approved email headers)."""

    id: str  # tgr_{brand}_{slug}
    brand_id: str
    name: str
    semantics: Optional[str] = None  # e.g. "assemble exactly one member per email"


class RuleRelation(BaseModel):
    src_rule_id: str
    dst_rule_id: str
    relation: str
    note: Optional[str] = None


class RuleGroup(BaseModel):
    id: str
    brand_id: str
    source: str = "design_bible"
    doc_ref: Optional[str] = None
    original_text: str


class AssetGroup(BaseModel):
    id: str
    brand_id: str
    name: str
    semantics: Optional[str] = None


# ---------------------------------------------------------------------------
# Blueprint input contract (matches existing content_blueprint fixtures)
# ---------------------------------------------------------------------------

class BlueprintSection(BaseModel):
    order: int
    section_id: str
    headline: Optional[str] = None
    copy_outline: Optional[str] = None
    section_summary: Optional[str] = None
    design_concept: Optional[str] = None
    clinical_fact_covered: Optional[str] = None
    rationale: Optional[str] = None
    use_uploaded_image: Optional[bool] = None
    assigned_images: list[str] = Field(default_factory=list)
    group_ids: list[str] = Field(default_factory=list)

    def render(self, include_design_concept: bool = True) -> str:
        """Compact text form given to the agents."""
        parts = [f"section_id: {self.section_id} (order {self.order})"]
        if self.headline:
            parts.append(f"headline: {self.headline}")
        if self.section_summary:
            parts.append(f"summary: {self.section_summary}")
        if self.copy_outline:
            parts.append(f"copy_outline: {self.copy_outline}")
        if self.clinical_fact_covered:
            parts.append(f"clinical_fact: {self.clinical_fact_covered}")
        if include_design_concept and self.design_concept:
            parts.append(f"design_concept: {self.design_concept}")
        if self.use_uploaded_image:
            parts.append("has_image: yes")
        return "\n".join(parts)


class Blueprint(BaseModel):
    content_type: str = "email"
    email_summary: Optional[str] = None
    content_blueprint: list[BlueprintSection]


# ---------------------------------------------------------------------------
# Run output contract
# ---------------------------------------------------------------------------

class RuleVerdict(BaseModel):
    id: str
    why: str = ""


class SectionResult(BaseModel):
    section_id: str
    section_types: list[str] = Field(default_factory=list)  # agent's vocab mapping
    targeted_rules: list[RuleVerdict] = Field(default_factory=list)
    email_wide_rules: list[RuleVerdict] = Field(default_factory=list)
    excluded_rules: list[RuleVerdict] = Field(default_factory=list)  # candidates dropped, why = disqualifier
    stats: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class EmailWideRule(BaseModel):
    id: str
    voted_by: list[str] = Field(default_factory=list)
    why: str = ""


class RunResult(BaseModel):
    arch: str
    brand: str
    blueprint_path: str
    design_concept_used: bool
    sections: list[SectionResult]
    email_wide_rules: list[EmailWideRule]
    stats: dict[str, Any] = Field(default_factory=dict)
