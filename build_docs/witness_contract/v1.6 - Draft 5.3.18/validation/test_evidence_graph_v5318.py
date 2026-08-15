#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executable" / "runtime"))
from evidence_graph_v5318 import (  # noqa: E402
    EvidenceError, evidence_edge_content_id, graph_snapshot_root, merkle_root,
    validate_edge, validate_gate_set, validate_measurement_pair,
)

DUMMY = "duoid:shake256-512:" + "A" * 86
DUMMY2 = "duoid:shake256-512:" + "B" * 86
DOMAIN = {
    "authority_namespace": "duotronic://authority/sandbox/witness-harness-vm",
    "authority_profile": "sandbox-test-only",
    "production_eligible": False,
    "trust_registry_snapshot_id": DUMMY,
}


class EvidenceGraphTests(unittest.TestCase):
    def original(self):
        return {
            **DOMAIN,
            "measurement_id": DUMMY,
            "comparison_policy_id": "lean-success/v1",
            "stability_class": "execution-volatile",
            "exact_result_content_id": DUMMY,
            "stable_projection_content_id": DUMMY2,
            "volatile_fields": ["timing", "process_id"],
            "successful": True,
        }

    def fresh(self):
        return {
            **DOMAIN,
            "revalidation_id": DUMMY2,
            "original_measurement_id": DUMMY,
            "comparison_policy_id": "lean-success/v1",
            "fresh_exact_result_content_id": "duoid:shake256-512:" + "C" * 86,
            "fresh_stable_projection_content_id": DUMMY2,
            "stable_projection_matches": True,
            "revalidation_successful": True,
        }

    def test_volatile_exact_output_may_change(self):
        validate_measurement_pair(self.original(), self.fresh())

    def test_stable_projection_must_match(self):
        value = self.fresh()
        value["fresh_stable_projection_content_id"] = DUMMY
        with self.assertRaises(EvidenceError):
            validate_measurement_pair(self.original(), value)

    def test_sandbox_cannot_be_production_eligible(self):
        value = self.fresh()
        value["production_eligible"] = True
        with self.assertRaises(EvidenceError):
            validate_measurement_pair(self.original(), value)

    def test_cross_domain_rejected(self):
        value = self.fresh()
        value["authority_namespace"] = "duotronic://authority/sandbox/other"
        with self.assertRaises(EvidenceError):
            validate_measurement_pair(self.original(), value)

    def test_artifact_class_requires_exact_bytes(self):
        original = self.original()
        original["stability_class"] = "artifact-reproducible"
        original["volatile_fields"] = []
        with self.assertRaises(EvidenceError):
            validate_measurement_pair(original, self.fresh())

    def test_edge_binds_domain_endpoints_and_relation(self):
        source = {**DOMAIN, "content_id": DUMMY}
        target = {**DOMAIN, "content_id": DUMMY2}
        edge = {
            **DOMAIN,
            "schema_version": "evidence_graph_edge/v1",
            "source_content_id": DUMMY,
            "target_content_id": DUMMY2,
            "relation_type": "measured_by",
            "policy_id": "edge-policy/v1",
            "created_at": "2026-08-13T16:00:00Z",
            "supersedes_edge_id": None,
        }
        edge["edge_content_id"] = evidence_edge_content_id(edge)
        validate_edge(edge, source, target, {"measured_by"})

    def test_edge_mutation_rejected(self):
        source = {**DOMAIN, "content_id": DUMMY}
        target = {**DOMAIN, "content_id": DUMMY2}
        edge = {
            **DOMAIN, "schema_version": "evidence_graph_edge/v1",
            "source_content_id": DUMMY, "target_content_id": DUMMY2,
            "relation_type": "measured_by", "policy_id": "edge-policy/v1",
            "created_at": "2026-08-13T16:00:00Z", "supersedes_edge_id": None,
        }
        edge["edge_content_id"] = evidence_edge_content_id(edge)
        edge["relation_type"] = "attested_by"
        with self.assertRaises(EvidenceError):
            validate_edge(edge, source, target, {"measured_by", "attested_by"})

    def test_merkle_order_and_domain_are_bound(self):
        leaves = [DUMMY, DUMMY2]
        self.assertNotEqual(merkle_root(leaves), merkle_root(list(reversed(leaves))))
        self.assertNotEqual(
            graph_snapshot_root(leaves, DOMAIN["authority_namespace"], DUMMY),
            graph_snapshot_root(leaves, "duotronic://authority/sandbox/other", DUMMY),
        )

    def test_exact_twelve_gate_set(self):
        validate_gate_set([f"gate-{n:02d}" for n in range(1, 13)])
        with self.assertRaises(EvidenceError):
            validate_gate_set(["gate-01"] * 12)


if __name__ == "__main__":
    unittest.main()
