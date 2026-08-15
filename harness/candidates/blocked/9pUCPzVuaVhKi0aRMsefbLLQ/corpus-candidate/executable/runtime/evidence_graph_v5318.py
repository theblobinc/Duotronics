#!/usr/bin/env python3
"""5.3.18 authority-domain, measurement, evidence-edge, and checkpoint helpers."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "validation"))
from identity import canonical_bytes, duoid  # noqa: E402


DOMAIN_FIELDS = (
    "authority_namespace",
    "authority_profile",
    "production_eligible",
    "trust_registry_snapshot_id",
)
STABILITY_CLASSES = {
    "semantic-deterministic",
    "artifact-reproducible",
    "execution-volatile",
}


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class AuthorityDomain:
    authority_namespace: str
    authority_profile: str
    production_eligible: bool
    trust_registry_snapshot_id: str

    @classmethod
    def from_object(cls, value: Mapping[str, Any]) -> "AuthorityDomain":
        try:
            result = cls(**{field: value[field] for field in DOMAIN_FIELDS})
        except KeyError as error:
            raise EvidenceError(f"missing authority-domain field: {error.args[0]}") from error
        result.validate()
        return result

    def validate(self) -> None:
        if self.authority_profile not in {"sandbox-test-only", "production"}:
            raise EvidenceError("unknown authority profile")
        if self.authority_profile == "sandbox-test-only" and self.production_eligible:
            raise EvidenceError("sandbox evidence cannot be production eligible")
        if self.authority_profile == "production" and not self.production_eligible:
            raise EvidenceError("production profile must be explicitly production eligible")
        if self.authority_profile == "sandbox-test-only" and "/sandbox/" not in self.authority_namespace:
            raise EvidenceError("sandbox profile requires a sandbox namespace")
        if self.authority_profile == "production" and "/production/" not in self.authority_namespace:
            raise EvidenceError("production profile requires a production namespace")


def require_same_domain(*objects: Mapping[str, Any]) -> AuthorityDomain:
    if not objects:
        raise EvidenceError("at least one domain-bound object is required")
    domains = [AuthorityDomain.from_object(value) for value in objects]
    if any(domain != domains[0] for domain in domains[1:]):
        raise EvidenceError("cross-domain evidence linkage is forbidden")
    return domains[0]


def measurement_content_id(measurement_without_id: Mapping[str, Any]) -> str:
    value = {key: child for key, child in measurement_without_id.items() if key != "measurement_id"}
    return duoid("DUOTRONIC/PROBE-MEASUREMENT/v1", canonical_bytes(value))


def revalidation_content_id(revalidation_without_id: Mapping[str, Any]) -> str:
    value = {key: child for key, child in revalidation_without_id.items() if key != "revalidation_id"}
    return duoid("DUOTRONIC/REVALIDATION-MEASUREMENT/v1", canonical_bytes(value))


def evidence_edge_content_id(edge_without_id: Mapping[str, Any]) -> str:
    value = {key: child for key, child in edge_without_id.items() if key != "edge_content_id"}
    return duoid("DUOTRONIC/EVIDENCE-GRAPH-EDGE/v1", canonical_bytes(value))


def validate_measurement_pair(
    original: Mapping[str, Any],
    revalidation: Mapping[str, Any],
) -> None:
    require_same_domain(original, revalidation)
    if revalidation.get("original_measurement_id") != original.get("measurement_id"):
        raise EvidenceError("revalidation does not reference the original measurement")
    if revalidation.get("comparison_policy_id") != original.get("comparison_policy_id"):
        raise EvidenceError("comparison policy changed during revalidation")
    if not original.get("successful") or not revalidation.get("revalidation_successful"):
        raise EvidenceError("original probe and fresh revalidation must both succeed")
    stability = original.get("stability_class")
    if stability not in STABILITY_CLASSES:
        raise EvidenceError("unknown measurement stability class")
    exact_equal = (
        original.get("exact_result_content_id")
        == revalidation.get("fresh_exact_result_content_id")
    )
    projection_equal = (
        original.get("stable_projection_content_id")
        == revalidation.get("fresh_stable_projection_content_id")
    )
    if bool(revalidation.get("stable_projection_matches")) != projection_equal:
        raise EvidenceError("reported stable-projection comparison is inconsistent")
    if stability == "artifact-reproducible" and not exact_equal:
        raise EvidenceError("artifact-reproducible measurement changed bytes")
    if stability in {"semantic-deterministic", "execution-volatile"} and not projection_equal:
        raise EvidenceError("stable semantic projection changed")
    if stability != "execution-volatile" and original.get("volatile_fields"):
        raise EvidenceError("volatile fields are only valid for execution-volatile probes")


def validate_edge(
    edge: Mapping[str, Any],
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    registered_relations: Iterable[str],
) -> None:
    require_same_domain(edge, source, target)
    if edge.get("source_content_id") not in {
        source.get("measurement_id"), source.get("revalidation_id"),
        source.get("edge_content_id"), source.get("content_id"),
    }:
        raise EvidenceError("edge source identifier does not bind its source")
    if edge.get("target_content_id") not in {
        target.get("measurement_id"), target.get("revalidation_id"),
        target.get("edge_content_id"), target.get("content_id"),
    }:
        raise EvidenceError("edge target identifier does not bind its target")
    if edge.get("relation_type") not in set(registered_relations):
        raise EvidenceError("unregistered evidence relation")
    expected = evidence_edge_content_id(edge)
    if edge.get("edge_content_id") != expected:
        raise EvidenceError("evidence edge identifier mismatch")


def merkle_root(ordered_leaf_ids: Sequence[str]) -> str:
    if not ordered_leaf_ids:
        raise EvidenceError("checkpoint requires at least one leaf")
    nodes = [
        duoid("DUOTRONIC/EVIDENCE-MERKLE-LEAF/v1", str(index).encode(), leaf.encode())
        for index, leaf in enumerate(ordered_leaf_ids)
    ]
    while len(nodes) > 1:
        if len(nodes) % 2:
            nodes.append(nodes[-1])
        nodes = [
            duoid("DUOTRONIC/EVIDENCE-MERKLE-NODE/v1", nodes[i].encode(), nodes[i + 1].encode())
            for i in range(0, len(nodes), 2)
        ]
    return nodes[0]


def graph_snapshot_root(ordered_edge_ids: Sequence[str], authority_namespace: str,
                        registry_snapshot_id: str) -> str:
    return duoid(
        "DUOTRONIC/EVIDENCE-GRAPH-SNAPSHOT/v1",
        authority_namespace.encode(),
        registry_snapshot_id.encode(),
        merkle_root(ordered_edge_ids).encode(),
        str(len(ordered_edge_ids)).encode(),
    )


def validate_gate_set(gate_ids: Sequence[str]) -> None:
    required = {f"gate-{number:02d}" for number in range(1, 13)}
    if len(gate_ids) != 12 or set(gate_ids) != required:
        raise EvidenceError("activation requires exactly the twelve registered gates")
