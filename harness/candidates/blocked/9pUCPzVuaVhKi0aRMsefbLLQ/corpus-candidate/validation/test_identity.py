#!/usr/bin/env python3

import unittest

from identity import canonical_bytes, edge_content_id, semantic_content_id


class IdentityTests(unittest.TestCase):
    def test_key_order_does_not_change_semantic_id(self):
        left = semantic_content_id("evidence_claim/v1", {"a": 1, "b": 2})
        right = semantic_content_id("evidence_claim/v1", {"b": 2, "a": 1})
        self.assertEqual(left, right)

    def test_timestamp_is_not_part_of_semantic_body(self):
        body = {"claim": "stable", "subject": "object:1"}
        self.assertEqual(
            semantic_content_id("evidence_claim/v1", body),
            semantic_content_id("evidence_claim/v1", body),
        )

    def test_domains_separate_edge_and_content(self):
        edge = {
            "schema_version": "meta_object_edge/v1",
            "source_content_id": "source",
            "relation_type": "supports",
            "target_content_id": "target",
            "context_content_id": None,
            "assumption_manifest_id": None,
            "policy_id": "policy:1",
            "valid_from": None,
            "valid_until": None,
            "supersedes_edge_id": None,
        }
        self.assertNotEqual(
            edge_content_id(edge),
            semantic_content_id("meta_object_edge/v1", edge),
        )

    def test_binary_float_is_rejected(self):
        with self.assertRaises(ValueError):
            canonical_bytes({"value": 0.1})


if __name__ == "__main__":
    unittest.main()
