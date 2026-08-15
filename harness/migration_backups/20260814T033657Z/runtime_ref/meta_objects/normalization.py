from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from .ontology import get_ontology
from .provenance import normalize_provenance
from .types import EvidenceClass, MetaObjectAssertionBundle, MetaObjectInstance, MetaRelation, RecurrenceEdge


def _stable_json(payload: dict | list) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _normalize_name(value: str) -> str:
    return "_".join(str(value or "").strip().lower().split())


def _normalize_tags(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({_normalize_name(value) for value in values if str(value or "").strip()}))


def _normalize_attributes(attributes: dict[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    attributes = attributes or {}
    normalized_items: list[tuple[str, Any]] = []
    for key in sorted(attributes):
        value = attributes[key]
        normalized_key = _normalize_name(key)
        if isinstance(value, list):
            normalized_value = tuple(sorted(str(item).strip() for item in value))
        elif isinstance(value, dict):
            normalized_value = tuple((child_key, value[child_key]) for child_key in sorted(value))
        else:
            normalized_value = value
        normalized_items.append((normalized_key, normalized_value))
    return tuple(normalized_items)


def build_meta_object_instance(given: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_meta_object(given)
    return {
        "schema_version": "meta-object-build-result@v1",
        "status": "ok",
        "object": normalized,
        "diagnostics": {"ontology_version": normalized["ontology_version"]},
        "failure_reasons": [],
    }


def normalize_meta_object(given: dict[str, Any] | MetaObjectInstance) -> dict[str, Any]:
    if isinstance(given, MetaObjectInstance):
        payload = given.to_dict()
    else:
        payload = dict(given)
    ontology = get_ontology()

    type_name = _normalize_name(payload.get("type_name") or payload.get("canonical_name") or payload.get("object_type"))
    canonical_name = _normalize_name(payload.get("canonical_name") or type_name)
    category = payload.get("category_path") or payload.get("category") or "untyped/unknown"
    category_path = ontology.resolve_category_path(category)
    evidence_class = payload.get("evidence_class", EvidenceClass.LEXICAL_MATCH.value)
    confidence = round(float(payload.get("confidence", 0.0)), 6)
    object_id = _normalize_name(payload.get("object_id") or f"{type_name}:{canonical_name}:{payload.get('source_id', '')}")

    normalized = {
        "schema_version": "meta-object-instance@v1",
        "object_id": object_id,
        "type_name": type_name,
        "canonical_name": canonical_name,
        "category_path": category_path,
        "evidence_class": str(evidence_class),
        "confidence": confidence,
        "source_id": str(payload.get("source_id", "")).strip(),
        "modality": _normalize_name(payload.get("modality", "text")),
        "attributes": list(_normalize_attributes(payload.get("attributes"))),
        "provenance": list(normalize_provenance(payload.get("provenance"))),
        "tags": list(_normalize_tags(payload.get("tags", []))),
        "ontology_version": ontology.version(),
        "normalization_version": "meta-bundle@v1",
    }
    normalized["canonical_digest"] = "sha256:" + hashlib.sha256(_stable_json(normalized).encode()).hexdigest()[:16]
    return normalized


def canonicalize_meta_bundle(given: dict[str, Any] | MetaObjectAssertionBundle) -> dict[str, Any]:
    if isinstance(given, MetaObjectAssertionBundle):
        payload = given.to_dict()
    else:
        payload = dict(given)

    assertion_payloads = [normalize_meta_object(assertion) for assertion in payload.get("assertions", [])]
    assertion_payloads.sort(key=lambda assertion: (assertion["category_path"], assertion["canonical_name"], assertion["object_id"]))

    relation_payloads = []
    for relation in payload.get("relations", []):
        if isinstance(relation, MetaRelation):
            relation_data = relation.to_dict()
        else:
            relation_data = dict(relation)
        relation_payloads.append({key: relation_data[key] for key in sorted(relation_data)})
    relation_payloads.sort(key=lambda relation: (relation.get("relation_type", ""), relation.get("source_object_id", ""), relation.get("target_object_id", "")))

    recurrence_payloads = []
    for edge in payload.get("recurrence_edges", []):
        if isinstance(edge, RecurrenceEdge):
            edge_data = edge.to_dict()
        else:
            edge_data = dict(edge)
        recurrence_payloads.append({key: edge_data[key] for key in sorted(edge_data)})
    recurrence_payloads.sort(key=lambda edge: (edge.get("edge_type", ""), edge.get("source_object_id", ""), edge.get("target_object_id", ""), edge.get("gap", 0)))

    canonical_bundle = {
        "schema_version": "meta-object-assertion-bundle@v1",
        "bundle_id": _normalize_name(payload.get("bundle_id", "meta-bundle")),
        "assertions": assertion_payloads,
        "relations": relation_payloads,
        "recurrence_edges": recurrence_payloads,
        "ontology_version": get_ontology().version(),
        "normalization_version": "meta-bundle@v1",
    }
    canonical_bundle["bundle_hash"] = "sha256:" + hashlib.sha256(_stable_json(canonical_bundle).encode()).hexdigest()[:16]
    return canonical_bundle


def compute_meta_summary(given: dict[str, Any] | MetaObjectAssertionBundle) -> dict[str, Any]:
    canonical_bundle = canonicalize_meta_bundle(given)
    counts_by_category: dict[str, int] = {}
    confidences: list[float] = []
    for assertion in canonical_bundle["assertions"]:
        counts_by_category[assertion["category_path"]] = counts_by_category.get(assertion["category_path"], 0) + 1
        confidences.append(float(assertion["confidence"]))

    return {
        "schema_version": "meta-summary@v1",
        "status": "ok",
        "bundle_hash": canonical_bundle["bundle_hash"],
        "assertion_count": len(canonical_bundle["assertions"]),
        "relation_count": len(canonical_bundle["relations"]),
        "recurrence_edge_count": len(canonical_bundle["recurrence_edges"]),
        "counts_by_category": counts_by_category,
        "confidence_min": min(confidences) if confidences else 0.0,
        "confidence_max": max(confidences) if confidences else 0.0,
        "failure_reasons": [],
    }
