#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import inspect
import json
import os
import pathlib
import stat
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "executable/runtime/proof_authority.py"
SPEC = importlib.util.spec_from_file_location("proof_authority_tests_534", MODULE_PATH)
authority = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = authority
SPEC.loader.exec_module(authority)


def profile_record(result_key: Ed25519PrivateKey) -> dict:
    return {
        "compiler_profile_id": "lean-4.29.1-hermetic-2",
        "toolchain": "leanprover/lean4:v4.29.1",
        "image_reference": "registry.example.invalid/witness/lean-verifier",
        "oci_image_digest": "sha256:" + "1" * 64,
        "oci_runtime_sha256": "2" * 64,
        "oci_runtime_version": "podman version 5.4.0",
        "lake_executable_sha256": "3" * 64,
        "lean_executable_sha256": "4" * 64,
        "lean_stdlib_tree_sha256": "5" * 64,
        "dependency_closure_sha256": "6" * 64,
        "verifier_executable_sha256": "7" * 64,
        "verifier_source_revision": "git:0123456789abcdef",
        "verifier_build_attestation_id": "attestation:verifier:test",
        "sandbox_policy_sha256": "8" * 64,
        "verifier_result_signer_key_id": "result-key:test",
        "verifier_result_public_key_base64url": authority.public_key_raw_b64url(result_key.public_key()),
        "authorized_axioms": ["Classical.choice", "Quot.sound", "propext"],
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2027-01-01T00:00:00Z",
    }


class Clock:
    def __init__(self):
        self.value = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        current = self.value
        self.value += timedelta(seconds=1)
        return current


class FakeTwoDomainRunner:
    INVOCATION_HASH = "9" * 64
    ARGV_HASH = "8" * 64
    CONTROLS = tuple(sorted({
        "explicit_entrypoint", "working_directory", "network_none", "read_only_rootfs",
        "capabilities_dropped", "no_new_privileges", "seccomp", "lsm_profile",
        "private_user_namespace", "non_root_user", "pid_limit", "memory_limit", "cpu_limit",
        "rlimit_fsize", "open_file_limit", "environment_allowlist", "mount_manifest",
    }))

    def __init__(self, result_key: Ed25519PrivateKey, mode: str = "pass", mutate_original: pathlib.Path | None = None):
        self.result_key = result_key
        self.mode = mode
        self.mutate_original = mutate_original
        self.seen_request = None
        self.snapshot_artifact_bytes = None
        self.generated_mode = None
        self.run_count = 0

    def run(self, *, profile, snapshot_root, generated_module, request, timeout_seconds):
        self.run_count += 1
        self.seen_request = request
        self.snapshot_artifact_bytes = (snapshot_root / request["proof_artifact_relative_path"]).read_bytes()
        self.generated_mode = stat.S_IMODE(generated_module.stat().st_mode)
        if self.mutate_original is not None:
            self.mutate_original.write_text("theorem t : False := by contradiction\n", encoding="utf-8")
        if self.mode == "mutate_snapshot":
            target = snapshot_root / request["proof_artifact_relative_path"]
            target.chmod(0o644)
            target.write_text("theorem t : False := by contradiction\n", encoding="utf-8")
        type_hash = authority.sha256_bytes(b"elaborated:True")
        axioms: list[str] = []
        forbidden: list[str] = []
        result = {
            "schema_version": "wc_lean_verifier_result/v6",
            "status": "passed",
            "request_id": request["request_id"],
            "request_sha256": authority.sha256_bytes(authority.canonical_bytes(request)),
            "service_request_id": request["service_request_id"],
            "authenticated_principal_id": request["authenticated_principal_id"],
            "source_bundle_id": request["source_bundle_id"],
            "compiler_profile_id": profile.compiler_profile_id,
            "claim_content_sha256": request["claim_content_sha256"],
            "policy_decision_id": request["policy_decision_id"],
            "policy_decision_sha256": request["policy_decision_sha256"],
            "theorem_statement_sha256": request["theorem_statement_sha256"],
            "proof_artifact_sha256": request["proof_artifact_sha256"],
            "immutable_snapshot_id": request["immutable_snapshot_id"],
            "immutable_snapshot_tree_sha256": request["immutable_snapshot_tree_sha256"],
            "generated_binding_module_sha256": request["generated_binding_module_sha256"],
            "lake_executable_sha256": profile.lake_executable_sha256,
            "lean_executable_sha256": profile.lean_executable_sha256,
            "lean_stdlib_tree_sha256": profile.lean_stdlib_tree_sha256,
            "dependency_closure_sha256": profile.dependency_closure_sha256,
            "oci_image_digest": profile.oci_image_digest,
            "oci_runtime_sha256": profile.oci_runtime_sha256,
            "oci_runtime_version": profile.oci_runtime_version,
            "oci_runtime_version_output_sha256": authority.sha256_bytes(profile.oci_runtime_version.encode("utf-8")),
            "verifier_executable_sha256": profile.verifier_executable_sha256,
            "sandbox_policy_sha256": profile.sandbox_policy_sha256,
            "effective_sandbox_invocation_sha256": self.INVOCATION_HASH,
            "normalized_executed_argv_sha256": self.ARGV_HASH,
            "handoff_manifest_sha256": "7" * 64,
            "effective_resource_limits": request["effective_resource_limits"],
            "effective_resource_limits_sha256": request["effective_resource_limits_sha256"],
            "domain_file_size_limit": request["effective_resource_limits"]["inspection_output_bytes"],
            "theorem_declaration": request["theorem_name"],
            "declaration_found": True,
            "declaration_type_matches": True,
            "expected_type_expression_hash": type_hash,
            "actual_type_expression_hash": type_hash,
            "expected_type_expression_fingerprint": "expr:true",
            "actual_type_expression_fingerprint": "expr:true",
            "normalization_policy": "lean_isDefEq_reducibility_regular/v1",
            "direct_dependencies": ["Init.True"],
            "dependency_closure": ["Init.True"],
            "transitive_dependencies_root": authority.sha256_bytes(b"deps"),
            "axiom_set": axioms,
            "axiom_set_sha256": authority.sha256_bytes(authority.canonical_bytes(axioms)),
            "forbidden_axiom_set": forbidden,
            "sorry_ax_present": False,
            "unsafe_dependency_present": False,
            "opaque_dependency_policy_result": "passed",
            "build_from_source": True,
            "prebuilt_artifacts_used": False,
            "warnings_as_errors": True,
            "exit_status": 0,
            "timeout_status": "completed",
            "execution_started_at": "2026-07-31T12:00:00Z",
            "execution_finished_at": "2026-07-31T12:00:01Z",
            "verifier_result_signer_key_id": profile.verifier_result_signer_key_id,
            "requested_controls": list(self.CONTROLS), "emitted_controls": list(self.CONTROLS),
            "accepted_controls": list(self.CONTROLS), "applied_controls": list(self.CONTROLS),
            "measured_controls": list(self.CONTROLS),
            "derived_controls": list(self._security()),
            "control_evidence": [
                *[
                    {"control": control, "status": "measured_pass", "source": "fake_governed_measurement", "observation_sha256": authority.sha256_bytes(control.encode("utf-8"))}
                    for control in self.CONTROLS
                ],
                *[
                    {"control": control, "status": "derived_pass", "source": "fake_sealed_topology", "observation_sha256": authority.sha256_bytes(control.encode("utf-8"))}
                    for control in self._security()
                ],
            ],
            "stdout_sha256": authority.sha256_bytes(b""), "stderr_sha256": authority.sha256_bytes(b""),
            "output_limit_exceeded": False,
        }
        if self.mode == "vary_timestamp":
            result["execution_started_at"] = f"2026-07-31T12:00:{self.run_count:02d}Z"
            result["execution_finished_at"] = f"2026-07-31T12:01:{self.run_count:02d}Z"
        if self.mode == "statement_mismatch":
            result["declaration_type_matches"] = False; result["actual_type_expression_hash"] = "a" * 64; result["status"] = "failed"
        elif self.mode == "comment_only":
            result["declaration_found"] = False; result["status"] = "failed"
        elif self.mode == "sorry":
            result["axiom_set"] = ["sorryAx"]; result["axiom_set_sha256"] = authority.sha256_bytes(authority.canonical_bytes(["sorryAx"])); result["sorry_ax_present"] = True; result["status"] = "failed"
        elif self.mode == "forbidden_axiom":
            result["axiom_set"] = ["Unsafe.magic"]; result["axiom_set_sha256"] = authority.sha256_bytes(authority.canonical_bytes(["Unsafe.magic"])); result["forbidden_axiom_set"] = ["Unsafe.magic"]; result["status"] = "failed"
        elif self.mode == "unsafe":
            result["unsafe_dependency_present"] = True; result["status"] = "failed"
        elif self.mode == "wrong_request":
            result["request_sha256"] = "0" * 64
        elif self.mode == "wrong_snapshot":
            result["immutable_snapshot_tree_sha256"] = "0" * 64
        elif self.mode == "wrong_invocation":
            result["effective_sandbox_invocation_sha256"] = "0" * 64
        elif self.mode == "duplicate_axiom":
            result["axiom_set"] = ["propext", "propext"]
        elif self.mode == "unsigned":
            signed = result
        elif self.mode == "wrong_signer":
            signed = authority.sign_record(result, Ed25519PrivateKey.generate())
        elif self.mode == "unstructured":
            return authority.SandboxExecution(
                0, None, "fake canonical JSON", "", False, ("compile",), ("verify",),
                self.INVOCATION_HASH, self._security(), self.CONTROLS, self.CONTROLS,
                self.CONTROLS, normalized_executed_argv_sha256=self.ARGV_HASH,
                domain_file_size_limit=request["effective_resource_limits"]["inspection_output_bytes"],
            )
        if self.mode not in {"unsigned", "wrong_signer"}:
            signed = authority.sign_record(result, self.result_key)
        security = self._security()
        if self.mode == "missing_isolation":
            security = tuple(item for item in security if item != "result_channel_isolated")
        return authority.SandboxExecution(
            0, signed, "diagnostic only", "", False,
            ("compile", "--mount=/input/source:ro", "--mount=/input/generated:ro", "--mount=/handoff:rw"),
            ("verify", "--request=/input/control/request.json", "--mount=/trusted-result:rw"),
            self.INVOCATION_HASH, security, self.CONTROLS, self.CONTROLS, self.CONTROLS,
            False, authority.sha256_bytes(b"diagnostic only"), authority.sha256_bytes(b""),
            emitted_controls=self.CONTROLS, accepted_controls=self.CONTROLS,
            measured_controls=self.CONTROLS, derived_controls=self._security(),
            control_evidence=tuple(result["control_evidence"]),
            normalized_executed_argv=("verify",), normalized_executed_argv_sha256=self.ARGV_HASH,
            domain_file_size_limit=request["effective_resource_limits"]["inspection_output_bytes"],
        )

    @staticmethod
    def _security():
        return ("result_channel_isolated", "trusted_inspection_only")


class ProofAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.governance_private = Ed25519PrivateKey.generate()
        self.witness_private = Ed25519PrivateKey.generate()
        self.result_private = Ed25519PrivateKey.generate()
        registry_unsigned = {
            "schema_version": "governed_compiler_registry/v2",
            "registry_id": "registry:2026-07-31:534",
            "governance_key_id": "governance:test",
            "profiles": [profile_record(self.result_private)],
            "created_at": "2026-07-31T00:00:00Z",
        }
        self.registry = authority.sign_record(registry_unsigned, self.governance_private)

    def project(self):
        temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(temp.name)
        (root / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
        (root / "Imported.lean").write_text("theorem imported : True := by trivial\n", encoding="utf-8")
        (root / "lean-toolchain").write_text("leanprover/lean4:v4.29.1\n", encoding="utf-8")
        (root / "lakefile.lean").write_text("import Lake\npackage submitted\n", encoding="utf-8")
        (root / "lake-manifest.json").write_text("{\"packages\":[]}", encoding="utf-8")
        return temp, root

    def service(self, mode="pass", *, runner=None, clock=None):
        selected = runner or FakeTwoDomainRunner(self.result_private, mode)
        service = authority.ProofAuthorityService(
            governed_registry=self.registry,
            governance_public_key=self.governance_private.public_key(),
            verifier_principal_id="verifier:test", key_id="witness-key:test",
            signing_key=self.witness_private, runner=selected, clock=clock or Clock(),
            timestamp_source="test_trusted_clock", authority_snapshot_id="authority-snapshot:test",
            authority_ledger_high_water_sequence=42,
        )
        return service, selected

    def verify(self, service, root, **overrides):
        values = {
            "compiler_profile_id": "lean-4.29.1-hermetic-2", "claim_id": "claim:1",
            "canonical_claim": {"statement": "True"}, "theorem_statement": "True",
            "theorem_name": "t", "proof_artifact": root / "Proof.lean", "source_root": root,
            "service_request_id": "request:service:1", "authenticated_principal_id": "principal:1",
            "source_bundle_id": "bundle:1",
            "policy_decision_id": "policy:proof:test", "policy_decision_sha256": "a" * 64,
        }
        values.update(overrides)
        return service.verify(**values)

    def test_valid_signed_result_passes_and_binds_complete_closure(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service(); record = self.verify(service, root)
        self.assertEqual(record["result"], "passed")
        self.assertTrue(record["result_channel_isolated"])
        self.assertEqual(record["authority_ledger_high_water_sequence"], 42)
        self.assertEqual(
            authority.sha256_bytes(record["verifier_result_signed_payload_canonical_json"].encode("utf-8")),
            record["verifier_result_payload_sha256"],
        )
        self.assertTrue(authority.verify_record(record, self.witness_private.public_key()))

    def test_result_must_have_authorized_signature(self):
        for mode in ("unsigned", "wrong_signer"):
            with self.subTest(mode=mode):
                temp, root = self.project()
                with temp:
                    service, _ = self.service(mode); record = self.verify(service, root)
                self.assertNotEqual(record["result"], "passed")
                self.assertEqual(record["failure_code"], "verifier_result_signature_invalid")

    def test_true_source_claimed_false_fails(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("statement_mismatch"); record = self.verify(service, root, theorem_statement="False")
        self.assertEqual(record["failure_code"], "theorem_type_mismatch")

    def test_comment_only_declaration_fails(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("comment_only"); record = self.verify(service, root, theorem_name="ghost")
        self.assertEqual(record["failure_code"], "theorem_declaration_missing")

    def test_sorry_forbidden_axiom_and_unsafe_dependency_fail(self):
        expected = {"sorry": "sorry_axiom_present", "forbidden_axiom": "forbidden_axiom_present", "unsafe": "unsafe_dependency_present"}
        for mode, code in expected.items():
            with self.subTest(mode=mode):
                temp, root = self.project()
                with temp:
                    service, _ = self.service(mode); record = self.verify(service, root)
                self.assertEqual(record["failure_code"], code)

    def test_result_identity_mismatches_and_noncanonical_sets_fail(self):
        for mode in ("wrong_request", "wrong_snapshot", "wrong_invocation", "duplicate_axiom", "unstructured"):
            with self.subTest(mode=mode):
                temp, root = self.project()
                with temp:
                    service, _ = self.service(mode); record = self.verify(service, root)
                self.assertNotEqual(record["result"], "passed")

    def test_missing_isolation_property_cannot_pass(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("missing_isolation"); record = self.verify(service, root)
        self.assertNotEqual(record["result"], "passed")
        self.assertFalse(record["result_channel_isolated"])

    def test_untrusted_domain_has_no_request_or_result_mount(self):
        temp, root = self.project()
        with temp:
            service, runner = self.service(); self.verify(service, root)
        command = " ".join(runner.run.__self__.seen_request and ("compile", "--mount=/input/source:ro", "--mount=/input/generated:ro", "--mount=/handoff:rw"))
        self.assertNotIn("control", command)
        self.assertNotIn("result", command)

    def test_artifact_and_metadata_hashes_come_from_snapshot(self):
        temp, root = self.project()
        with temp:
            service, runner = self.service(); record = self.verify(service, root)
            self.assertEqual(record["proof_artifact_sha256"], authority.sha256_bytes(runner.snapshot_artifact_bytes))
            self.assertEqual(record["lakefile_sha256"], authority.sha256_file(root / "lakefile.lean"))
            self.assertEqual(record["lake_manifest_sha256"], authority.sha256_file(root / "lake-manifest.json"))
            self.assertEqual(record["lean_toolchain_sha256"], authority.sha256_file(root / "lean-toolchain"))

    def test_mutation_before_snapshot_is_captured_not_prehashed(self):
        temp, root = self.project()
        with temp:
            original = authority.sha256_file(root / "Proof.lean")
            (root / "Proof.lean").write_text("theorem t : True := True.intro\n", encoding="utf-8")
            service, runner = self.service(); record = self.verify(service, root)
        self.assertNotEqual(original, record["proof_artifact_sha256"])
        self.assertEqual(record["proof_artifact_sha256"], authority.sha256_bytes(runner.snapshot_artifact_bytes))

    def test_source_mutation_during_snapshot_is_rejected(self):
        temp, root = self.project()
        with temp, tempfile.TemporaryDirectory() as destination:
            changed = False
            def mutate(relative):
                nonlocal changed
                if not changed and relative.as_posix() == "Proof.lean":
                    changed = True
                    (root / "Proof.lean").write_text("theorem t : True := True.intro\n", encoding="utf-8")
            with self.assertRaisesRegex(authority.AuthorityFailure, "source changed"):
                authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot", after_file_copy=mutate)

    def test_metadata_and_transitive_import_mutation_during_snapshot_is_rejected(self):
        for name in ("lakefile.lean", "lake-manifest.json", "lean-toolchain", "Imported.lean"):
            with self.subTest(name=name):
                temp, root = self.project()
                with temp, tempfile.TemporaryDirectory() as destination:
                    changed = False
                    def mutate(relative, target=name):
                        nonlocal changed
                        if not changed and relative.as_posix() == target:
                            changed = True; (root / target).write_text((root / target).read_text(encoding="utf-8") + "\n", encoding="utf-8")
                    with self.assertRaises(authority.AuthorityFailure):
                        authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot", after_file_copy=mutate)

    def test_mutation_of_original_after_sealing_has_no_effect(self):
        temp, root = self.project()
        with temp:
            runner = FakeTwoDomainRunner(self.result_private, mutate_original=root / "Proof.lean")
            service, _ = self.service(runner=runner); record = self.verify(service, root)
        self.assertEqual(record["result"], "passed")
        self.assertEqual(record["proof_artifact_sha256"], authority.sha256_bytes(runner.snapshot_artifact_bytes))

    def test_mutation_of_sealed_snapshot_is_detected_after_execution(self):
        temp, root = self.project()
        with temp:
            service, _ = self.service("mutate_snapshot")
            with self.assertRaises(authority.AuthorityFailure):
                self.verify(service, root)

    def test_symlink_hardlink_fifo_prebuilt_and_native_source_are_rejected(self):
        cases = ("symlink", "hardlink", "fifo", "olean", "native")
        for case in cases:
            with self.subTest(case=case):
                temp, root = self.project()
                with temp:
                    if case == "symlink": (root / "Linked.lean").symlink_to(root / "Imported.lean")
                    elif case == "hardlink": os.link(root / "Imported.lean", root / "Hard.lean")
                    elif case == "fifo": os.mkfifo(root / "pipe")
                    elif case == "olean": (root / "Proof.olean").write_bytes(b"stale")
                    else: (root / "plugin.so").write_bytes(b"native")
                    service, _ = self.service()
                    with self.assertRaises((ValueError, authority.AuthorityFailure)):
                        self.verify(service, root)

    def test_proof_outside_tree_and_traversal_are_rejected(self):
        temp, root = self.project()
        with temp, tempfile.TemporaryDirectory() as other:
            artifact = pathlib.Path(other) / "Elsewhere.lean"; artifact.write_text("theorem t : True := by trivial\n", encoding="utf-8")
            service, _ = self.service()
            with self.assertRaises(ValueError): self.verify(service, root, proof_artifact=artifact)
        for value in ("../Proof.lean", "/Proof.lean", "a\\b.lean"):
            with self.assertRaises(ValueError): authority._safe_relative_path(value)
        with tempfile.TemporaryDirectory() as parent:
            real = pathlib.Path(parent) / "real"; real.mkdir()
            (real / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            linked = pathlib.Path(parent) / "linked"; linked.symlink_to(real, target_is_directory=True)
            service, _ = self.service()
            with self.assertRaises(ValueError):
                self.verify(service, linked, proof_artifact=linked / "Proof.lean")

    def test_generated_module_is_deterministic_minimal_and_read_only(self):
        temp, root = self.project()
        with temp:
            service, runner = self.service(clock=Clock()); first = self.verify(service, root); second = self.verify(service, root)
        self.assertEqual(first["generated_binding_module_path"], second["generated_binding_module_path"])
        self.assertEqual(first["semantic_witness_content_id"], second["semantic_witness_content_id"])
        self.assertEqual(runner.generated_mode, 0o444)
        text = authority.generated_witness_module(proof_module="Proof", theorem_statement="True", theorem_name="t")
        self.assertIn("theorem BoundClaim : (True) := t", text); self.assertNotIn("by\n", text); self.assertNotIn("#eval", text)

    def test_semantic_witness_identity_excludes_execution_timestamps(self):
        temp, root = self.project()
        with temp:
            runner = FakeTwoDomainRunner(self.result_private, "vary_timestamp")
            service, _ = self.service(runner=runner, clock=Clock())
            first = self.verify(service, root)
            second = self.verify(service, root)
        self.assertNotEqual(first["created_at"], second["created_at"])
        self.assertEqual(first["semantic_witness_content_id"], second["semantic_witness_content_id"])
        self.assertEqual(first["lean_compiler_witness_id"], second["lean_compiler_witness_id"])

    def test_semantic_identity_excludes_ephemeral_host_path_execution_hashes(self):
        class VaryingExecutionRunner(FakeTwoDomainRunner):
            def run(self, **arguments):
                execution = super().run(**arguments)
                invocation_hash = authority.sha256_bytes(f"/tmp/random-invocation-{self.run_count}".encode("utf-8"))
                argv_hash = authority.sha256_bytes(f"--volume=/tmp/random-{self.run_count}:/input/source:ro".encode("utf-8"))
                unsigned = authority.signed_payload(execution.structured_result)
                unsigned["effective_sandbox_invocation_sha256"] = invocation_hash
                unsigned["normalized_executed_argv_sha256"] = argv_hash
                signed = authority.sign_record(unsigned, self.result_key)
                return replace(
                    execution, structured_result=signed,
                    effective_sandbox_invocation_sha256=invocation_hash,
                    normalized_executed_argv_sha256=argv_hash,
                )

        temp, root = self.project()
        with temp:
            runner = VaryingExecutionRunner(self.result_private)
            service, _ = self.service(runner=runner, clock=Clock())
            first = self.verify(service, root)
            second = self.verify(service, root)
        self.assertEqual(first["semantic_witness_content_id"], second["semantic_witness_content_id"])
        self.assertNotEqual(first["execution_evidence_content_id"], second["execution_evidence_content_id"])
        self.assertNotEqual(first["effective_sandbox_invocation_sha256"], second["effective_sandbox_invocation_sha256"])

    def test_request_api_cannot_supply_paths_hashes_environment_or_timestamp(self):
        parameters = set(inspect.signature(authority.ProofAuthorityService.verify).parameters)
        forbidden = {"lake_executable", "lean_executable", "expected_lake_sha256", "created_at", "environment", "oci_runtime"}
        self.assertFalse(parameters.intersection(forbidden))
        self.assertIn("compiler_profile_id", parameters)

    def test_bad_registry_unknown_profile_and_toolchain_mismatch_are_rejected(self):
        tampered = json.loads(json.dumps(self.registry)); tampered["profiles"][0]["lean_executable_sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            authority.ProofAuthorityService(
                governed_registry=tampered, governance_public_key=self.governance_private.public_key(),
                verifier_principal_id="v", key_id="k", signing_key=self.witness_private,
                runner=FakeTwoDomainRunner(self.result_private), authority_snapshot_id="s", authority_ledger_high_water_sequence=0,
            )
        temp, root = self.project()
        with temp:
            service, _ = self.service()
            with self.assertRaises(ValueError): self.verify(service, root, compiler_profile_id="caller-invented")
            (root / "lean-toolchain").write_text("leanprover/lean4:v4.28.0\n", encoding="utf-8")
            with self.assertRaises(ValueError): self.verify(service, root)

    def test_atomic_result_publication_rejects_symlink_hardlink_and_oversize(self):
        for kind in ("symlink", "hardlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as parent:
                directory = pathlib.Path(parent) / "private"
                publisher = authority.AtomicResultPublisher(directory)
                target = pathlib.Path(parent) / "target"; target.write_text("x", encoding="utf-8")
                final = directory / "verifier-result.json"
                if kind == "symlink": final.symlink_to(target)
                else: os.link(target, final)
                with self.assertRaises(FileExistsError): publisher.publish({"schema_version": "test/v1"}, self.result_private)
        with tempfile.TemporaryDirectory() as parent:
            publisher = authority.AtomicResultPublisher(pathlib.Path(parent) / "private", maximum=16)
            with self.assertRaises(authority.AuthorityFailure): publisher.publish({"value": "x" * 100}, self.result_private)

    def test_atomic_result_is_private_canonical_signed_and_single_link(self):
        with tempfile.TemporaryDirectory() as parent:
            publisher = authority.AtomicResultPublisher(pathlib.Path(parent) / "private")
            path = publisher.publish({"schema_version": "test/v1", "value": 1}, self.result_private)
            info = path.stat(); record = authority.read_private_result(path)
        self.assertEqual(stat.S_IMODE(info.st_mode), 0o600); self.assertEqual(info.st_nlink, 1)
        self.assertTrue(authority.verify_record(record, self.result_private.public_key()))

    def test_private_result_reader_rejects_wrong_mode_and_noncanonical_json(self):
        with tempfile.TemporaryDirectory() as parent:
            path = pathlib.Path(parent) / "result.json"; path.write_text('{"b":1,"a":2}', encoding="utf-8"); path.chmod(0o600)
            with self.assertRaises(authority.AuthorityFailure): authority.read_private_result(path)
            path.write_text('{}', encoding="utf-8"); path.chmod(0o644)
            with self.assertRaises(authority.AuthorityFailure): authority.read_private_result(path)

    def test_trusted_root_loader_rejects_group_write_symlink_hardlink_and_traversal(self):
        with tempfile.TemporaryDirectory() as parent:
            root = pathlib.Path(parent) / "trust"; root.mkdir(mode=0o700)
            file = root / "config.json"; file.write_text("{}", encoding="utf-8"); file.chmod(0o600)
            self.assertEqual(authority.secure_read_bytes(root, "config.json", expected_uid=os.getuid()), b"{}")
            root.chmod(0o770)
            with self.assertRaises(RuntimeError): authority.secure_read_bytes(root, "config.json", expected_uid=os.getuid())
            root.chmod(0o700); (root / "link.json").symlink_to(file)
            with self.assertRaises(OSError): authority.secure_read_bytes(root, "link.json", expected_uid=os.getuid())
            os.link(file, root / "hard.json")
            with self.assertRaises(RuntimeError): authority.secure_read_bytes(root, "hard.json", expected_uid=os.getuid())
            with self.assertRaises(ValueError): authority.secure_read_bytes(root, "../config.json", expected_uid=os.getuid())
        with tempfile.TemporaryDirectory() as unsafe_parent:
            trust = pathlib.Path(unsafe_parent) / "trust"; trust.mkdir(mode=0o700)
            with self.assertRaises(RuntimeError):
                authority.validate_trusted_root_ancestry(trust, expected_uid=os.getuid())
        authority.validate_trusted_root_ancestry(pathlib.Path("/"), expected_uid=os.getuid())

    def test_event_set_root_is_ordered_and_duplicate_safe(self):
        events = [[1, "a" * 64], [2, "b" * 64]]
        root = authority.authority_event_set_root(events)
        self.assertEqual(root, authority.authority_event_set_root(list(events)))
        with self.assertRaises(ValueError): authority.authority_event_set_root(list(reversed(events)))
        with self.assertRaises(ValueError): authority.authority_event_set_root([[1, "a" * 64], [1, "b" * 64]])

    def test_real_oci_command_binds_private_host_paths_and_complete_argv(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = pathlib.Path(directory) / "runtime"
            runtime.write_text("#!/bin/sh\nif [ \"$1\" = version ]; then echo 'podman version 5.4.0'; fi\nexit 0\n", encoding="utf-8")
            runtime.chmod(0o700)
            seccomp = pathlib.Path(directory) / "seccomp.json"; seccomp.write_text("{}", encoding="utf-8"); seccomp.chmod(0o600)
            seccomp_hash = authority.sha256_file(seccomp)
            runtime_hash = authority.sha256_file(runtime)
            record = profile_record(self.result_private)
            record["oci_runtime_sha256"] = runtime_hash
            profile = authority.CompilerProfile.from_record(record)
            runner = authority.OciSandboxRunner(
                runtime, runtime_hash, profile.oci_runtime_version,
                verifier_result_signing_key=self.result_private, authority_uid=65534, authority_gid=65534,
                seccomp_profile_path=seccomp, expected_seccomp_profile_sha256=seccomp_hash,
                supported_controls=authority.OciSandboxRunner.REQUIRED_CONTROLS,
            )
            linked_runtime = pathlib.Path(directory) / "runtime-link"
            linked_runtime.symlink_to(runtime)
            with self.assertRaises(ValueError):
                authority.OciSandboxRunner(
                    linked_runtime, runtime_hash, profile.oci_runtime_version,
                    verifier_result_signing_key=self.result_private, authority_uid=65534, authority_gid=65534,
                    seccomp_profile_path=seccomp, expected_seccomp_profile_sha256=seccomp_hash,
                )
            limits = authority.EffectiveResourceLimits(600, 1000, 128 * 1024 * 1024, 512 * 1024 * 1024, 4 * 1024 * 1024, 1024 * 1024, 1024 * 1024, 1024 * 1024, 2 * 1024 * 1024)
            logical = ({"source": "snapshot:" + "a" * 64, "host_path": "/tmp/random-a", "destination": "/input/source", "mode": "ro", "domain": "untrusted_compilation", "purpose": "sealed_source", "lifecycle": "request"},)
            invocation = runner._invocation(
                domain="untrusted_compilation", profile=profile,
                entrypoint="/opt/witness-authority/bin/compile-lean", arguments=(),
                mounts=logical, limits=limits, uid=65534, gid=65534,
            )
            repeated = runner._invocation(
                domain="untrusted_compilation", profile=profile,
                entrypoint="/opt/witness-authority/bin/compile-lean", arguments=(),
                mounts=logical, limits=limits, uid=65534, gid=65534,
            )
            changed_mount = ({**logical[0], "host_path": "/tmp/random-b"},)
            changed = runner._invocation(domain="untrusted_compilation", profile=profile, entrypoint="/opt/witness-authority/bin/compile-lean", arguments=(), mounts=changed_mount, limits=limits, uid=65534, gid=65534)
            first = runner._command(invocation)
            second = runner._command(changed)
        self.assertEqual(invocation.sha256, repeated.sha256)
        self.assertNotEqual(invocation.sha256, changed.sha256)
        self.assertNotEqual(first, second)
        self.assertNotIn("/input/control", " ".join(first))
        self.assertNotIn("trusted-result", " ".join(first))
        self.assertIn("--ulimit=fsize=134217728:134217728", first)
        self.assertIn("--entrypoint=/opt/witness-authority/bin/compile-lean", first)


if __name__ == "__main__":
    unittest.main()
