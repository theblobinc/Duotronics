#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys
import tempfile
import threading
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))

from proof_check_service import ProofCheckApplication  # noqa: E402
from proof_authority import CanonicalSchemaValidator, EffectiveResourceLimits  # noqa: E402


class RequestBoundaryValidator:
    def __init__(self): self.real = CanonicalSchemaValidator(ROOT / "schemas")
    def validate(self, surface, value):
        if surface == "proof_check_request": self.real.validate(surface, value)


class FakeAuthority:
    def __init__(self):
        self.arguments = None

    def verify(self, **arguments):
        self.arguments = arguments
        return {"result": "passed", "lean_compiler_witness_id": "lean:test", "policy_decision_id": arguments["policy_decision_id"], "policy_decision_sha256": arguments["policy_decision_sha256"]}


class FakePolicyResolver:
    def __init__(self): self.arguments = None
    def resolve(self, policy_decision_id, **arguments):
        self.arguments = {"policy_decision_id": policy_decision_id, **arguments}
        return types.SimpleNamespace(policy_decision_id=policy_decision_id, canonical_record_sha256="a" * 64, effective_limits=lambda: EffectiveResourceLimits(600, 1000000, 134217728, 536870912, 4194304, 1048576, 1048576, 1048576, 2097152))


class ProofCheckServiceTests(unittest.TestCase):
    def request(self):
        return {
            "request_id": "request:1", "idempotency_key": "idempotency:1", "subject_id": "principal:1",
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
            policy = FakePolicyResolver()
            result = ProofCheckApplication(authority, store, policy, schema_validator=RequestBoundaryValidator()).handle(self.request())
        self.assertEqual(authority.arguments["compiler_profile_id"], "profile:governed")
        self.assertEqual(result["policy_decision_id"], "policy:1")
        self.assertEqual(authority.arguments["policy_decision_sha256"], "a" * 64)
        self.assertEqual(policy.arguments["subject_id"], "principal:1")
        self.assertEqual(result["compiler_witness"]["lean_compiler_witness_id"], "lean:test")

    def test_request_cannot_supply_path_hash_environment_or_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            application = ProofCheckApplication(FakeAuthority(), pathlib.Path(directory), FakePolicyResolver(), schema_validator=RequestBoundaryValidator())
            for forbidden, value in (
                ("lake_executable", "/tmp/fake-lake"),
                ("expected_lake_sha256", "0" * 64),
                ("environment", {"LEAN_PATH": "/attacker"}),
                ("created_at", "2020-01-01T00:00:00Z"),
            ):
                request = self.request()
                request[forbidden] = value
                with self.assertRaisesRegex(ValueError, "schema validation"):
                    application.handle(request)

    def test_bundle_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            request = self.request()
            request["proof_artifact_relative_path"] = "../outside.lean"
            with self.assertRaisesRegex(ValueError, "proof_artifact_relative_path"):
                ProofCheckApplication(FakeAuthority(), pathlib.Path(directory), FakePolicyResolver(), schema_validator=RequestBoundaryValidator()).handle(request)

    def test_concurrent_identical_idempotency_key_shares_one_execution(self):
        class SlowAuthority(FakeAuthority):
            def __init__(self):
                super().__init__(); self.calls = 0; self.entered = threading.Event(); self.release = threading.Event()
            def verify(self, **arguments):
                self.calls += 1; self.entered.set(); self.release.wait(5)
                return super().verify(**arguments)

        with tempfile.TemporaryDirectory() as directory:
            store = pathlib.Path(directory); bundle = store / "bundle-1"; bundle.mkdir()
            (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            authority = SlowAuthority(); application = ProofCheckApplication(authority, store, FakePolicyResolver(), schema_validator=RequestBoundaryValidator())
            results = []
            first = threading.Thread(target=lambda: results.append(application.handle(self.request())))
            second = threading.Thread(target=lambda: results.append(application.handle(self.request())))
            first.start(); self.assertTrue(authority.entered.wait(2)); second.start(); authority.release.set()
            first.join(5); second.join(5)
        self.assertEqual(authority.calls, 1); self.assertEqual(len(results), 2); self.assertEqual(results[0], results[1])


if __name__ == "__main__":
    unittest.main()
