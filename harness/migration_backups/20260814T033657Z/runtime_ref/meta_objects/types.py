from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class EvidenceClass(str, Enum):
    DIRECT_OBSERVATION = "direct_observation"
    LEXICAL_MATCH = "lexical_match"
    MODEL_INFERENCE = "model_inference"
    RELATIONAL_INFERENCE = "relational_inference"
    HYPOTHETICAL = "hypothetical"


class AbstractionLevel(str, Enum):
    L0_SIGNAL = "l0_signal"
    L1_OBJECT = "l1_object"
    L2_SCENE = "l2_scene"
    L3_MOTIF = "l3_motif"
    L4_DISCOURSE = "l4_discourse"
    L5_ARCHETYPE = "l5_archetype"


@dataclass(frozen=True)
class MetaObjectType:
    type_name: str
    canonical_name: str
    category_path: str
    abstraction_level: str = AbstractionLevel.L1_OBJECT.value
    aliases: tuple[str, ...] = ()
    description: str = ""
    ontology_version: str = "ontology@v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetaObjectInstance:
    object_id: str
    type_name: str
    canonical_name: str
    category_path: str
    evidence_class: str
    confidence: float
    source_id: str = ""
    modality: str = "text"
    attributes: tuple[tuple[str, Any], ...] = ()
    provenance: tuple[tuple[str, Any], ...] = ()
    tags: tuple[str, ...] = ()
    schema_version: str = "meta-object-instance@v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetaRelation:
    relation_id: str
    source_object_id: str
    target_object_id: str
    relation_type: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecurrenceEdge:
    source_object_id: str
    target_object_id: str
    edge_type: str
    gap: int = 0
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetaObjectAssertionBundle:
    bundle_id: str
    assertions: tuple[MetaObjectInstance, ...] = field(default_factory=tuple)
    relations: tuple[MetaRelation, ...] = field(default_factory=tuple)
    recurrence_edges: tuple[RecurrenceEdge, ...] = field(default_factory=tuple)
    ontology_version: str = "ontology@v1"
    normalization_version: str = "meta-bundle@v1"
    schema_version: str = "meta-object-assertion-bundle@v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "assertions": [assertion.to_dict() for assertion in self.assertions],
            "relations": [relation.to_dict() for relation in self.relations],
            "recurrence_edges": [edge.to_dict() for edge in self.recurrence_edges],
            "ontology_version": self.ontology_version,
            "normalization_version": self.normalization_version,
            "schema_version": self.schema_version,
        }
