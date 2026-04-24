"""Deterministic meta-object layer for the standalone runtime."""

from .normalization import canonicalize_meta_bundle, compute_meta_summary, normalize_meta_object
from .ontology import MetaObjectOntology, get_ontology
from .types import MetaObjectAssertionBundle, MetaObjectInstance, MetaObjectType

__all__ = [
    "MetaObjectAssertionBundle",
    "MetaObjectInstance",
    "MetaObjectOntology",
    "MetaObjectType",
    "canonicalize_meta_bundle",
    "compute_meta_summary",
    "get_ontology",
    "normalize_meta_object",
]
