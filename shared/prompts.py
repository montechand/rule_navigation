"""Prompt pieces shared across architectures so the comparison stays fair:
same task framing, same schema primer, same section rendering."""

from __future__ import annotations

from .kb import KB
from .schemas import Blueprint, BlueprintSection

TASK_BRIEF = """## Task

You are given an email blueprint (summary + section list) and ONE target section. Navigate
the brand-rules knowledge base and return the PRECISE set of rules that apply to that
section, split into two buckets:

- targeted_rule_ids — rules that specifically constrain THIS section:
  * selector.section_types matches the section's mapped section type(s)
  * conditional rules (applies_when) whose predicates this section plausibly satisfies,
    e.g. its background/design concept, its position in the email, content tags in its copy
  * rules about devices the section contains (a callout panel inside an intro section pulls
    callout rules; a chart pulls chart rules; a button pulls cta rules)
- email_wide_rule_ids — baseline rules that apply to the whole email / every section:
  * selector.section_types = null (applies everywhere)
  * evaluation_scope = email (per-email cardinality, theme consistency, footnote ordering)
  * global typography / accessibility / spacing / assembly defaults
  Only include email-wide rules genuinely relevant to generating content (not rules for
  surfaces other than email, not rules for audiences that don't match).

Quality bar: you are benchmarked on false negatives first — a missed applicable rule is
the worst failure. But do not dump the whole KB either: a rule belongs in `targeted` only
if a designer building THIS section must obey it, and in `email_wide` only if every
section must obey it. Exclude rules scoped to other sections, other audiences, other
content types (print/ppt/banner), and locked components the section doesn't touch
(top_matter/end_matter rules only apply to sections adjacent to them, if at all).

Method notes:
- First map the blueprint's free-form section_id to the section vocabulary — it is
  dynamic per brand (curated core + brand-discovered devices; get_section_vocab lists it).
  A section may map to several types, e.g. a benefits panel = intro + callout.
- Classes vs templates: content_sub_type rows are structural CLASSES (component library,
  locked matter, formats) — rules scope to them via content_sub_type_ids (null = all
  sub-types). Concrete approved artifacts are design_template rows that fill section
  roles, may realize a class (instance_of), sit in pick-one groups, and carry their own
  usage_conditions. rules_for_subtype = class view; rules_for_template = instance view.
- Conditional (applies_when) rules: include them when the section's design concept or copy
  makes the condition plausible; the generator downstream re-checks predicates.
- Token-first layering: concrete values and their conditional switching live in the
  brand_token layer (primitives + semantic element-path bindings with variants); rules are
  topic clusters that BIND tokens. A concrete detail in the design concept (a hex, an
  opacity, a radius, an alignment) is often fastest resolved by finding its token
  (search_tokens/query_tokens) and following rules_for_token to the governing rules.
  Your final answer is still RULE ids, never token ids.
- Audience: these emails are patient-facing (dtp_patient) unless stated otherwise — exclude
  hcp-only rules.
"""


def schema_primer(kb: KB) -> str:
    parts = ["## Knowledge base"]
    overview = kb.schema_doc("overview")
    if overview:
        parts.append(overview)
    vocab = kb.schema_doc("section_vocab")
    if vocab:
        parts.append(vocab)
    return "\n\n".join(parts)


def render_blueprint_context(bp: Blueprint, target: BlueprintSection,
                             include_design_concept: bool) -> str:
    lines = ["## Email blueprint"]
    if bp.email_summary:
        lines.append(f"email_summary: {bp.email_summary}")
    lines.append("sections (in order): " + ", ".join(
        f"{s.order}:{s.section_id}" + (" <== TARGET" if s.section_id == target.section_id and s.order == target.order else "")
        for s in bp.content_blueprint
    ))
    lines.append("")
    lines.append("## TARGET SECTION")
    lines.append(target.render(include_design_concept=include_design_concept))
    position = "first" if target.order == min(s.order for s in bp.content_blueprint) else (
        "last" if target.order == max(s.order for s in bp.content_blueprint) else "middle")
    lines.append(f"position_in_email: {position} (of the content sections)")
    return "\n".join(lines)
