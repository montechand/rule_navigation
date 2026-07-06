"""Pydantic models for the v0.2 brand-rules data model, blueprints, and run results.

Vocabularies mirror newest_email_pipeline/data_models/model_iteration_0/model_dictionary.md.
`null` = unconstrained (applies to all); `[]` = explicitly none.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Closed vocabularies (v0.2 dictionary)
# ---------------------------------------------------------------------------

RULE_CLASSES = [
    "typography", "color_application", "cta", "layout", "spacing", "imagery",
    "iconography", "copy_editorial", "voice_tone", "accessibility", "assembly",
]
SECTION_TYPES = [
    "hero", "intro", "efficacy", "safety", "patient_story", "affordability",
    "symptom_trio", "cta", "callout", "chart", "top_matter", "end_matter",
]
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
TOKEN_TYPES = ["color", "font", "type_scale", "spacing", "radius", "gradient", "opacity"]
TOKEN_TIERS = ["primary", "secondary_accent", "tertiary", "campaign"]
ASSET_TYPES = [
    "photo", "icon", "logo_lockup", "svg_shape", "wave", "background",
    "campaign_lockup", "cta_image",
]
GOV_TYPES = ["regulatory", "legal", "mlr_claim", "disclosure", "trademark"]
VERDICTS = ["allowed", "forbidden", "allowed_with_disclosure", "requires_qualifier", "verbatim_only"]
SEVERITIES = ["info", "warn", "block"]
RELATIONS = ["refines", "conflicts", "cross_reference", "cluster", "co_applies"]
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
    governance_ids: list[str] = Field(default_factory=list)
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
    variants: Optional[list[dict[str, Any]]] = None  # [{when: {...}, value: ...}]


class BrandToken(BaseModel):
    id: str
    brand_id: str
    token_type: str
    key: str  # "{type}.{tier}.{name}"
    value: Any = None  # TokenValue-shaped dict or scalar
    derived_from: Optional[dict[str, Any]] = None  # {base_token_id, op, amount}
    aliases: list[str] = Field(default_factory=list)
    tier: Optional[str] = None
    scope: str = "global"  # global | campaign:{name} | partnership:{name}
    audience: Optional[str] = None
    usage_ratio: Optional[float] = None
    gated: Optional[dict[str, Any]] = None  # {is_gated, gate}
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
    notes: Optional[str] = None
    status: Status = "active"
    version: int = 1


class Governance(BaseModel):
    id: str
    brand_id: str
    gov_type: str
    subject: str
    match: Optional[dict[str, Any]] = None  # {method, threshold?}
    verdict: str
    preferred_form: Optional[str] = None
    severity: str = "warn"
    rationale: Optional[str] = None
    evidence: Optional[list[Any]] = None
    audience: Optional[str] = None
    content_types: Optional[list[str]] = None
    effective_from: Optional[str] = None
    expires_at: Optional[str] = None
    status: Status = "active"
    version: int = 1


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
    targeted_rules: list[RuleVerdict] = Field(default_factory=list)
    email_wide_rules: list[RuleVerdict] = Field(default_factory=list)
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
