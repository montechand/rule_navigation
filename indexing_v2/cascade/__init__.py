"""Precompiled rule and token cascade."""

from indexing_v2.cascade.compile import (
    CascadeSheet,
    ContextIndex,
    ContextIndexEntry,
    ShadowedBinding,
    compile_cascade,
    get_sheet,
)
from indexing_v2.cascade.contexts import enumerate_contexts, observed_content_tag_combos
from indexing_v2.cascade.resolve import (
    ResolvedCandidate,
    ResolvedProperty,
    TokenResolutionError,
    collect_bindings,
    resolve_element,
    specificity,
    specificity_without_id,
)

__all__ = [
    "CascadeSheet",
    "ContextIndex",
    "ContextIndexEntry",
    "ResolvedCandidate",
    "ResolvedProperty",
    "ShadowedBinding",
    "TokenResolutionError",
    "collect_bindings",
    "compile_cascade",
    "enumerate_contexts",
    "get_sheet",
    "observed_content_tag_combos",
    "resolve_element",
    "specificity",
    "specificity_without_id",
]
