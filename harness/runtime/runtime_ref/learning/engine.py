from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ViewProfile:
    view_id: str
    purposes: tuple[str, ...]
    formal_guardrails: tuple[str, ...]
    operations: tuple[str, ...]


@dataclass(frozen=True)
class ConceptProfile:
    concept_id: str
    canonical_name: str
    formal_kernel: str
    views: dict[str, ViewProfile] = field(default_factory=dict)
    bridges: dict[tuple[str, str], str] = field(default_factory=dict)
    common_misconceptions: dict[str, str] = field(default_factory=dict)


TENSOR_PROFILE = ConceptProfile(
    concept_id="tensor",
    canonical_name="Tensor",
    formal_kernel=(
        "A tensor is a context-dependent mathematical object that may be represented "
        "by arrays after choosing a basis, but is not exhausted by that representation."
    ),
    views={
        "tensor_computational_array": ViewProfile(
            view_id="tensor_computational_array",
            purposes=("programming", "machine_learning", "implementation", "array"),
            formal_guardrails=(
                "array_representation_requires_basis_or_coordinate_choice",
                "component_shape_is_not_the_full_tensor_identity",
            ),
            operations=("index_components", "reshape_or_contract_axes", "track_shape_and_basis"),
        ),
        "tensor_functional_multilinear": ViewProfile(
            view_id="tensor_functional_multilinear",
            purposes=("proof", "linear_algebra", "multilinear"),
            formal_guardrails=("inputs_must_be_linear_in_each_argument",),
            operations=("evaluate_on_vectors", "verify_multilinearity"),
        ),
        "tensor_geometric_transform": ViewProfile(
            view_id="tensor_geometric_transform",
            purposes=("geometry", "physics", "coordinates", "transform"),
            formal_guardrails=("components_must_obey_transformation_rules",),
            operations=("change_basis", "compare_coordinate_components"),
        ),
        "tensor_abstract_product": ViewProfile(
            view_id="tensor_abstract_product",
            purposes=("abstract", "category", "universal_property"),
            formal_guardrails=("universal_property_defines_the_product",),
            operations=("construct_tensor_product", "map_bilinear_forms"),
        ),
    },
    bridges={
        ("tensor_computational_array", "tensor_geometric_transform"): "tensor_array_to_geometric",
        ("tensor_computational_array", "tensor_functional_multilinear"): "tensor_array_to_multilinear",
    },
    common_misconceptions={
        "tensor_is_just_any_array": "An array can represent a tensor after basis choices; it is not the whole concept.",
        "rank_equals_dimension": "Rank and dimension depend on the tensor context and operation being discussed.",
    },
)


CONCEPTS = {"tensor": TENSOR_PROFILE}


def route_learning_view(payload: Mapping[str, object]) -> dict:
    concept_id = str(payload.get("concept_id", "tensor"))
    concept = CONCEPTS.get(concept_id)
    if concept is None:
        return {
            "schema_version": "learning-route-result@v1",
            "status": "rejected",
            "failure_reasons": ["unknown_concept"],
            "diagnostics": {"known_concepts": sorted(CONCEPTS)},
        }

    purpose = str(payload.get("learner_intent", payload.get("purpose", "programming"))).lower()
    assertion = str(payload.get("learner_assertion", "")).lower()
    selected = next(
        (
            view
            for view in concept.views.values()
            if purpose in view.purposes or any(token in purpose for token in view.purposes)
        ),
        concept.views["tensor_computational_array"],
    )

    warnings = [message for key, message in concept.common_misconceptions.items() if key.replace("_", " ") in assertion]
    if "just" in assertion and "array" in assertion:
        warnings.append(concept.common_misconceptions["tensor_is_just_any_array"])

    bridge_ids = [bridge for (source, _target), bridge in concept.bridges.items() if source == selected.view_id]
    return {
        "schema_version": "learning-route-result@v1",
        "status": "accepted",
        "concept_id": concept.concept_id,
        "canonical_name": concept.canonical_name,
        "selected_view_id": selected.view_id,
        "selection_reason": f"matched learner_intent:{purpose}",
        "formal_kernel": concept.formal_kernel,
        "formal_guardrails": list(selected.formal_guardrails),
        "operations": list(selected.operations),
        "bridge_ids": bridge_ids,
        "misconception_warnings": warnings,
        "diagnostics": {
            "valid_view_count": len(concept.views),
            "unselected_valid_views": sorted(set(concept.views) - {selected.view_id}),
            "answer_must_declare_bridge": bool(bridge_ids),
        },
        "failure_reasons": [],
    }
