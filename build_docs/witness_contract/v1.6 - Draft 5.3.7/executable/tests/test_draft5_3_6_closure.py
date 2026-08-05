#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sqlite3
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "executable/runtime"))

import proof_authority as authority  # noqa: E402
from proof_check_service import DurableIdempotencyStore  # noqa: E402


class Draft536ClosureTests(unittest.TestCase):
    def setUp(self):
        self.schemas = authority.CanonicalSchemaValidator(ROOT / "schemas")

    def test_boolean_opaque_policy_result_is_schema_invalid(self):
        fixture = json.loads((ROOT / "executable/tests/fixtures/draft5_3_6/invalid/lean_inspector_result_v1.json").read_text())
        with self.assertRaises(authority.AuthorityFailure):
            self.schemas.validate("inspector_result", fixture["payload"])

    def test_real_inspector_invokes_isdefeq_and_structural_fingerprint(self):
        inspector = (ROOT / "formal/draft5_3_6/lean/WitnessAuthority/InspectorMain.lean").read_text()
        verifier = (ROOT / "formal/draft5_3_6/lean/WitnessAuthority/Verifier.lean").read_text()
        self.assertIn("inspectDeclaration env theoremName bindingInfo.type", inspector)
        self.assertIn("isDefEq declarationInfo.type expectedType", verifier)
        self.assertIn("expressionFingerprint", verifier)
        self.assertNotIn("toString bindingInfo.type", inspector)

    def test_recursive_dependency_closure_and_pass_gate_are_explicit(self):
        verifier = (ROOT / "formal/draft5_3_6/lean/WitnessAuthority/Verifier.lean").read_text()
        runtime = (ROOT / "executable/runtime/proof_authority.py").read_text()
        self.assertIn("partial def dependencyClosure", verifier)
        self.assertIn("constantDependencies info ++ rest", verifier)
        self.assertIn('structured.get("opaque_dependency_policy_result") == "passed"', runtime)

    def test_sandbox_has_single_source_mounts_and_exact_argv_hash(self):
        source = (ROOT / "executable/runtime/proof_authority.py").read_text()
        self.assertNotIn("def _command(self, invocation: EffectiveSandboxInvocation, runtime_mounts", source)
        self.assertIn("mount['host_path']", source)
        self.assertIn('record["normalized_executed_argv_sha256"]', source)

    def test_policy_permissions_become_effective_limits(self):
        record = authority.ResolvedPolicyDecision("p", {}, "1" * 64, 1, 7)
        limits = record.effective_limits()
        self.assertEqual(limits.timeout_seconds, 1)
        self.assertEqual(limits.source_total_bytes, 7)
        self.assertEqual(limits.compiler_artifact_file_bytes, 128 * 1024 * 1024)

    def test_request_schema_rejects_non_string_claim_and_non_object_claim(self):
        valid = json.loads((ROOT / "executable/tests/fixtures/draft5_3_6/valid/proof_check_request_v1.json").read_text())["payload"]
        for field, value in (("claim_id", 7), ("canonical_claim", []), ("proof_artifact_relative_path", "../Proof.lean")):
            with self.subTest(field=field):
                changed = dict(valid); changed[field] = value
                with self.assertRaises(authority.AuthorityFailure):
                    self.schemas.validate("proof_check_request", changed)

    def test_production_trust_inputs_are_schema_validated_before_use(self):
        authority_source = (ROOT / "executable/runtime/proof_authority.py").read_text()
        service_source = (ROOT / "executable/runtime/proof_check_service.py").read_text()
        for call in (
            'schema_validator.validate("compiler_registry", registry)',
            'schema_validator.validate("trusted_artifact_registry", trusted_artifact_registry)',
            'schema_validator.validate("platform_capability", platform)',
        ):
            self.assertIn(call, authority_source)
        self.assertIn('validator.validate("proof_policy_registry", policy_registry)', service_source)

    def test_compile_manifest_is_consumed_and_exact_file_set_checked(self):
        source = (ROOT / "executable/trusted_verifier/verify_lean.py").read_text()
        self.assertIn("validate_handoff", source)
        self.assertIn("actual_paths != declared_paths", source)
        self.assertIn("binding olean is not exactly represented", source)
        self.assertIn("compiled module identity differs", source)
        self.assertIn("per-artifact limit differs from the sealed invocation", source)
        self.assertIn("handoff aggregate-byte policy violated", source)

    def test_missing_network_observation_is_unverified(self):
        source = (ROOT / "executable/trusted_verifier/verify_lean.py").read_text()
        self.assertIn('"unverified_missing_observation"', source)
        self.assertNotIn("else set()", source)
        self.assertIn("selected_lsm", source)

    def test_compilation_and_publication_file_limits_are_separate(self):
        source = (ROOT / "executable/runtime/proof_authority.py").read_text()
        self.assertIn("compiler_artifact_file_size_limit", source)
        self.assertIn("inspection_output_bytes_limit", source)
        self.assertIn("final_result_bytes_limit", source)
        self.assertNotIn("file_size_limit=MAX_RESULT_BYTES", source)

    def test_idempotency_survives_restart_and_is_principal_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "idem.sqlite"
            first = DurableIdempotencyStore(path)
            action, owner = first.acquire("alice", "key", "1" * 64)
            self.assertEqual(action, "execute")
            first.complete("alice", "key", str(owner), "1" * 64, {"status": "passed"})
            second = DurableIdempotencyStore(path)
            self.assertEqual(second.acquire("alice", "key", "1" * 64), ("completed", {"status": "passed"}))
            action, _ = second.acquire("bob", "key", "2" * 64)
            self.assertEqual(action, "execute")

    def test_stale_idempotency_lease_is_recoverable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "idem.sqlite"
            store = DurableIdempotencyStore(path, lease_seconds=60)
            action, original = store.acquire("alice", "key", "1" * 64)
            self.assertEqual(action, "execute")
            with sqlite3.connect(path) as connection:
                connection.execute("UPDATE proof_check_idempotency SET lease_expires_at=?", (time.time() - 1,))
            action, recovered = store.acquire("alice", "key", "1" * 64)
            self.assertEqual(action, "execute")
            self.assertNotEqual(original, recovered)

    def test_trust_root_claims_are_attestation_registry_bound(self):
        source = (ROOT / "executable/runtime/proof_authority.py").read_text()
        self.assertIn("verify_trusted_artifact_registry", source)
        for role in ("database_migrations", "trusted_inspector", "oci_image_metadata", "dependency_manifest"):
            self.assertIn(role, source)


if __name__ == "__main__":
    unittest.main()
