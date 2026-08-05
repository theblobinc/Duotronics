#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))

from proof_check_service import ProofCheckApplication  # noqa: E402


class FakeAuthority:
    def __init__(self):
        self.arguments = None

    def verify(self, **arguments):
        self.arguments = arguments
        return {"result": "passed", "lean_compiler_witness_id": "lean:test"}


class ProofCheckServiceTests(unittest.TestCase):
    def request(self):
        return {
            "compiler_profile_id": "profile:governed",
            "claim_id": "claim:1",
            "canonical_claim": {"statement": "True"},
            "theorem_statement": "True",
            "theorem_name": "t",
            "source_bundle_id": "bundle-1",
            "proof_artifact_relative_path": "Proof.lean",
            "policy_decision_id": "policy:1",
        }

    def test_exact_request_resolves_bundle_and_preserves_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            store = pathlib.Path(directory)
            bundle = store / "bundle-1"
            bundle.mkdir()
            (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            authority = FakeAuthority()
            result = ProofCheckApplication(authority, store).handle(self.request())
        self.assertEqual(authority.arguments["compiler_profile_id"], "profile:governed")
        self.assertEqual(result["policy_decision_id"], "policy:1")
        self.assertEqual(result["compiler_witness"]["lean_compiler_witness_id"], "lean:test")

    def test_request_cannot_supply_path_hash_environment_or_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            application = ProofCheckApplication(FakeAuthority(), pathlib.Path(directory))
            for forbidden, value in (
                ("lake_executable", "/tmp/fake-lake"),
                ("expected_lake_sha256", "0" * 64),
                ("environment", {"LEAN_PATH": "/attacker"}),
                ("created_at", "2020-01-01T00:00:00Z"),
            ):
                request = self.request()
                request[forbidden] = value
                with self.assertRaisesRegex(ValueError, "canonical request contract"):
                    application.handle(request)

    def test_bundle_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            request = self.request()
            request["proof_artifact_relative_path"] = "../outside.lean"
            with self.assertRaisesRegex(ValueError, "bundle-relative"):
                ProofCheckApplication(FakeAuthority(), pathlib.Path(directory)).handle(request)


if __name__ == "__main__":
    unittest.main()
