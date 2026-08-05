#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import inspect
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "executable/runtime/proof_authority.py"
SPEC = importlib.util.spec_from_file_location("proof_authority_tests", MODULE_PATH)
authority = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = authority
SPEC.loader.exec_module(authority)


def profile_record() -> dict:
    return {
        "compiler_profile_id": "lean-4.29.1-hermetic-1",
        "toolchain": "leanprover/lean4:v4.29.1",
        "image_reference": "registry.example.invalid/witness/lean-verifier",
        "execution_image_digest": "sha256:" + "1" * 64,
        "lake_executable_sha256": "2" * 64,
        "lean_executable_sha256": "3" * 64,
        "lean_stdlib_tree_sha256": "4" * 64,
        "dependency_closure_sha256": "5" * 64,
        "verifier_binary_sha256": "6" * 64,
        "sandbox_policy_sha256": "7" * 64,
        "authorized_axioms": ["Classical.choice", "Quot.sound", "propext"],
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2027-01-01T00:00:00Z",
    }


class FakeHermeticRunner(authority.OciSandboxRunner):
    def __init__(self, mode: str = "pass"):
        self.mode = mode
        self.seen_request = None
        self.seen_snapshot = None
        self.seen_generated = None

    def run(self, *, profile, snapshot_root, generated_module, request, timeout_seconds):
        self.seen_request = request
        self.seen_snapshot = snapshot_root
        self.seen_generated = generated_module
        result = {
            "schema_version": "wc_lean_verifier_result/v1",
            "status": "passed",
            "request_sha256": authority.sha256_bytes(authority.canonical_bytes(request)),
            "compiler_profile_id": profile.compiler_profile_id,
            "claim_content_sha256": request["claim_content_sha256"],
            "theorem_statement_sha256": request["theorem_statement_sha256"],
            "proof_artifact_sha256": request["proof_artifact_sha256"],
            "immutable_snapshot_sha256": request["immutable_snapshot_sha256"],
            "generated_witness_module_sha256": request["generated_witness_module_sha256"],
            "lake_executable_sha256": profile.lake_executable_sha256,
            "lean_executable_sha256": profile.lean_executable_sha256,
            "lean_stdlib_tree_sha256": profile.lean_stdlib_tree_sha256,
            "dependency_closure_sha256": profile.dependency_closure_sha256,
            "execution_image_digest": profile.execution_image_digest,
            "verifier_binary_sha256": profile.verifier_binary_sha256,
            "declaration_found": True,
            "declaration_type_matches": True,
            "axiom_dependencies": [],
            "build_from_source": True,
            "prebuilt_artifacts_used": False,
            "warnings_as_errors": True,
        }
        if self.mode == "statement_mismatch":
            result["declaration_type_matches"] = False
            result["status"] = "failed"
        elif self.mode == "comment_only":
            result["declaration_found"] = False
            result["status"] = "failed"
        elif self.mode == "sorry":
            result["axiom_dependencies"] = ["sorryAx"]
        elif self.mode == "unauthorized_axiom":
            result["axiom_dependencies"] = ["Unsafe.magic"]
        elif self.mode == "stale_binary":
            result["prebuilt_artifacts_used"] = True
        elif self.mode == "wrong_request":
            result["request_sha256"] = "0" * 64
        elif self.mode == "wrong_lean":
            result["lean_executable_sha256"] = "0" * 64
        elif self.mode == "unstructured":
            return authority.SandboxExecution(0, None, "does not depend on any axioms", "", False, ("fake",))
        elif self.mode == "noncanonical_axioms":
            result["axiom_dependencies"] = ["propext", "propext"]
        return authority.SandboxExecution(0, result, "diagnostic", "", False, ("governed-image", profile.compiler_profile_id))


class Clock:
    def __init__(self):
        self.value = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        current = self.value
        self.value += timedelta(seconds=1)
        return current


class ProofAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.governance_private = Ed25519PrivateKey.generate()
        self.verifier_private = Ed25519PrivateKey.generate()
        registry_unsigned = {
            "schema_version": "governed_compiler_registry/v1",
            "registry_id": "registry:2026-07-31",
            "governance_key_id": "governance:test",
            "profiles": [profile_record()],
            "created_at": "2026-07-31T00:00:00Z",
        }
        self.registry = authority.sign_record(registry_unsigned, self.governance_private)

    def project(self):
        temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(temp.name)
        (root / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
        (root / "lean-toolchain").write_text("leanprover/lean4:v4.29.1\n", encoding="utf-8")
        (root / "lakefile.lean").write_text("import Lake\npackage submitted\n", encoding="utf-8")
        return temp, root

    def service(self, mode="pass", clock=None):
        runner = FakeHermeticRunner(mode)
        service = authority.ProofAuthorityService(
            governed_registry=self.registry,
            governance_public_key=self.governance_private.public_key(),
            verifier_principal_id="verifier:test",
            key_id="key:test",
            signing_key=self.verifier_private,
            runner=runner,
            clock=clock or Clock(),
            timestamp_source="test_trusted_clock",
        )
        return service, runner

    def verify(self, service, root, **overrides):
        values = {
            "compiler_profile_id": "lean-4.29.1-hermetic-1",
            "claim_id": "claim:1",
            "canonical_claim": {"statement": "True"},
            "theorem_statement": "True",
            "theorem_name": "t",
            "proof_artifact": root / "Proof.lean",
            "source_root": root,
        }
        values.update(overrides)
        return service.verify(**values)

    def test_valid_structured_result_passes_and_signature_verifies(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service()
            record = self.verify(service, root)
        self.assertEqual(record["result"], "passed")
        self.assertTrue(record["statement_binding_confirmed"])
        self.assertTrue(record["hermetic_environment"])
        self.assertTrue(authority.verify_record(record, self.verifier_private.public_key()))

    def test_true_source_claimed_false_fails(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("statement_mismatch")
            record = self.verify(service, root, theorem_statement="False")
        self.assertNotEqual(record["result"], "passed")

    def test_comment_only_declaration_fails(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("comment_only")
            record = self.verify(service, root, theorem_name="ghost")
        self.assertNotEqual(record["result"], "passed")

    def test_sorry_ax_fails(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("sorry")
            record = self.verify(service, root)
        self.assertEqual(record["theorem_status"], "sorry_stub")

    def test_unauthorized_attributed_axiom_fails(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("unauthorized_axiom")
            record = self.verify(service, root)
        self.assertEqual(record["theorem_status"], "axiom_dependent")

    def test_proof_outside_source_tree_is_rejected(self):
        temp, root = self.project()
        other = tempfile.TemporaryDirectory()
        with temp, other:
            artifact = pathlib.Path(other.name) / "Elsewhere.lean"
            artifact.write_text("theorem t : True := by trivial\n", encoding="utf-8")
            service, _ = self.service()
            with self.assertRaisesRegex(ValueError, "outside source root"):
                self.verify(service, root, proof_artifact=artifact)

    def test_prebuilt_olean_is_rejected_before_runner(self):
        temp, root = self.project()
        with temp:
            (root / "Proof.olean").write_bytes(b"stale")
            service, runner = self.service()
            with self.assertRaisesRegex(ValueError, "prebuilt"):
                self.verify(service, root)
            self.assertIsNone(runner.seen_request)

    def test_native_plugin_is_rejected_before_runner(self):
        temp, root = self.project()
        with temp:
            (root / "plugin.so").write_bytes(b"native")
            service, runner = self.service()
            with self.assertRaisesRegex(ValueError, "native"):
                self.verify(service, root)
            self.assertIsNone(runner.seen_request)

    def test_submitted_lakefile_is_not_a_command_source(self):
        temp, root = self.project()
        with temp:
            (root / "lakefile.lean").write_text("import Lake\n-- malicious project metadata\n", encoding="utf-8")
            service, _ = self.service()
            record = self.verify(service, root)
        self.assertEqual(record["command"], ["governed-image", "lean-4.29.1-hermetic-1"])

    def test_request_api_has_no_path_hash_or_created_at_parameters(self):
        parameters = set(inspect.signature(authority.ProofAuthorityService.verify).parameters)
        forbidden = {"lake_executable", "lean_executable", "expected_lake_sha256", "created_at", "environment"}
        self.assertFalse(parameters.intersection(forbidden))
        self.assertIn("compiler_profile_id", parameters)

    def test_bad_registry_signature_is_rejected(self):
        tampered = json.loads(json.dumps(self.registry))
        tampered["profiles"][0]["lean_executable_sha256"] = "9" * 64
        with self.assertRaisesRegex(ValueError, "governance-signed"):
            authority.ProofAuthorityService(
                governed_registry=tampered,
                governance_public_key=self.governance_private.public_key(),
                verifier_principal_id="v", key_id="k", signing_key=self.verifier_private,
                runner=FakeHermeticRunner(),
            )

    def test_unknown_compiler_profile_is_rejected(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service()
            with self.assertRaisesRegex(ValueError, "not present"):
                self.verify(service, root, compiler_profile_id="caller-invented")

    def test_toolchain_mismatch_is_rejected(self):
        temp, root = self.project()
        with temp:
            (root / "lean-toolchain").write_text("leanprover/lean4:v4.28.0\n", encoding="utf-8")
            service, _ = self.service()
            with self.assertRaisesRegex(ValueError, "toolchain"):
                self.verify(service, root)

    def test_human_readable_fake_axiom_output_cannot_pass(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("unstructured")
            record = self.verify(service, root)
        self.assertNotEqual(record["result"], "passed")
        self.assertFalse(record["structured_inspection_complete"])

    def test_wrong_structured_request_hash_cannot_pass(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("wrong_request")
            record = self.verify(service, root)
        self.assertNotEqual(record["result"], "passed")

    def test_wrong_actual_lean_digest_cannot_pass(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("wrong_lean")
            record = self.verify(service, root)
        self.assertNotEqual(record["result"], "passed")

    def test_duplicate_axiom_result_is_not_canonical(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("noncanonical_axioms")
            record = self.verify(service, root)
        self.assertNotEqual(record["result"], "passed")

    def test_stale_binary_use_cannot_pass(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("stale_binary")
            record = self.verify(service, root)
        self.assertNotEqual(record["result"], "passed")

    def test_generated_target_and_witness_id_are_deterministic(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service(clock=Clock())
            first = self.verify(service, root)
            second = self.verify(service, root)
        self.assertEqual(first["generated_witness_module_path"], second["generated_witness_module_path"])
        self.assertEqual(first["lean_compiler_witness_id"], second["lean_compiler_witness_id"])
        self.assertNotEqual(first["created_at"], second["created_at"])

    def test_term_binding_uses_no_tactic_block(self):
        text = authority.generated_witness_module(proof_module="Proof", theorem_statement="True", theorem_name="t")
        self.assertIn("example : (True) := t", text)
        self.assertNotIn("by\n", text)
        self.assertNotIn("#print axioms", text)

    def test_snapshot_hash_changes_with_source(self):
        temp, root = self.project()
        with temp:
            first = authority.content_tree_sha256(root)
            (root / "Proof.lean").write_text("theorem t : True := True.intro\n", encoding="utf-8")
            second = authority.content_tree_sha256(root)
        self.assertNotEqual(first, second)

    def test_symlinked_source_is_rejected(self):
        temp, root = self.project()
        outside = tempfile.TemporaryDirectory()
        with temp, outside:
            target = pathlib.Path(outside.name) / "Target.lean"
            target.write_text("theorem x : True := by trivial\n", encoding="utf-8")
            (root / "Linked.lean").symlink_to(target)
            service, _ = self.service()
            with self.assertRaisesRegex(ValueError, "symbolic links"):
                self.verify(service, root)


if __name__ == "__main__":
    unittest.main()
