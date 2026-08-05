#!/usr/bin/env python3
"""Behavioral regressions for the Draft 5.3.7 corrective boundary."""

from __future__ import annotations

import importlib.util
import pathlib
import resource
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "executable/runtime"
TRUSTED = ROOT / "executable/trusted_verifier"
sys.path.insert(0, str(RUNTIME))
sys.path.insert(0, str(TRUSTED))

AUTH_SPEC = importlib.util.spec_from_file_location(
    "proof_authority_tests_537", RUNTIME / "proof_authority.py"
)
authority = importlib.util.module_from_spec(AUTH_SPEC)
assert AUTH_SPEC and AUTH_SPEC.loader
sys.modules[AUTH_SPEC.name] = authority
AUTH_SPEC.loader.exec_module(authority)

VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_lean_tests_537", TRUSTED / "verify_lean.py"
)
verify_lean = importlib.util.module_from_spec(VERIFY_SPEC)
assert VERIFY_SPEC and VERIFY_SPEC.loader
sys.modules[VERIFY_SPEC.name] = verify_lean
VERIFY_SPEC.loader.exec_module(verify_lean)

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_draft537_tests", ROOT / "executable/validators/validate_draft5_3_7_corpus.py"
)
validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
sys.modules[VALIDATOR_SPEC.name] = validator
VALIDATOR_SPEC.loader.exec_module(validator)


def profile_record(result_key: Ed25519PrivateKey, runtime_hash: str) -> dict:
    return {
        "compiler_profile_id": "lean-4.29.1-hermetic-2",
        "toolchain": "leanprover/lean4:v4.29.1",
        "image_reference": "registry.example.invalid/witness/lean-verifier",
        "oci_image_digest": "sha256:" + "1" * 64,
        "oci_runtime_sha256": runtime_hash,
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
        "verifier_result_public_key_base64url": authority.public_key_raw_b64url(
            result_key.public_key()
        ),
        "authorized_axioms": ["Classical.choice", "Quot.sound", "propext"],
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2027-01-01T00:00:00Z",
    }


class Draft537SandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = pathlib.Path(self.temporary.name)
        self.runtime = root / "runtime"
        self.runtime.write_text(
            "#!/bin/sh\nif [ \"$1\" = version ]; then echo 'podman version 5.4.0'; fi\nexit 0\n",
            encoding="utf-8",
        )
        self.runtime.chmod(0o700)
        self.seccomp = root / "seccomp.json"
        self.seccomp.write_text("{}", encoding="utf-8")
        self.seccomp.chmod(0o600)
        self.result_key = Ed25519PrivateKey.generate()
        runtime_hash = authority.sha256_file(self.runtime)
        self.profile = authority.CompilerProfile.from_record(
            profile_record(self.result_key, runtime_hash)
        )
        self.runner = authority.OciSandboxRunner(
            self.runtime,
            runtime_hash,
            self.profile.oci_runtime_version,
            verifier_result_signing_key=self.result_key,
            authority_uid=65534,
            authority_gid=65534,
            seccomp_profile_path=self.seccomp,
            expected_seccomp_profile_sha256=authority.sha256_file(self.seccomp),
            supported_controls=authority.OciSandboxRunner.REQUIRED_CONTROLS,
        )
        self.limits = authority.EffectiveResourceLimits(
            600,
            512 * 1024 * 1024,
            128 * 1024 * 1024,
            512 * 1024 * 1024,
            4 * 1024 * 1024,
            1024 * 1024,
            1024 * 1024,
            1024 * 1024,
            2 * 1024 * 1024,
        )

    def invocation(self, domain: str):
        entrypoint = (
            "/opt/witness-authority/bin/compile-lean"
            if domain == "untrusted_compilation"
            else "/opt/witness-authority/bin/verify-lean"
        )
        return self.runner._invocation(
            domain=domain,
            profile=self.profile,
            entrypoint=entrypoint,
            arguments=(),
            mounts=(
                {
                    "source": "snapshot:" + "a" * 64,
                    "host_path": "/tmp/source",
                    "destination": "/input/source",
                    "mode": "ro",
                    "domain": domain,
                    "purpose": "sealed_source",
                    "lifecycle": "request",
                },
            ),
            limits=self.limits,
            uid=65534,
            gid=65534,
        )

    def test_compiler_domain_uses_compiler_artifact_file_size_limit(self):
        invocation = self.invocation("untrusted_compilation")
        self.assertEqual(
            invocation.domain_file_size_limit,
            self.limits.compiler_artifact_file_bytes,
        )
        self.assertIn(
            "--ulimit=fsize=134217728:134217728", invocation.executed_argv
        )

    def test_inspection_domain_uses_inspection_output_bytes_limit(self):
        invocation = self.invocation("trusted_inspection")
        self.assertEqual(
            invocation.domain_file_size_limit, self.limits.inspection_output_bytes
        )
        self.assertIn("--ulimit=fsize=4194304:4194304", invocation.executed_argv)

    def test_preexecution_invocation_has_no_accepted_controls(self):
        self.assertEqual(self.invocation("trusted_inspection").accepted_controls, ())

    def test_preexecution_invocation_has_no_applied_controls(self):
        self.assertEqual(self.invocation("trusted_inspection").applied_controls, ())

    def test_requested_controls_are_not_treated_as_evidence(self):
        invocation = self.invocation("trusted_inspection")
        self.assertTrue(invocation.requested_controls)
        self.assertFalse(invocation.accepted_controls)
        self.assertFalse(invocation.applied_controls)

    def test_emitted_controls_are_derived_from_exact_argv(self):
        invocation = self.invocation("trusted_inspection")
        parsed = self.runner._emitted_controls_from_argv(invocation.executed_argv)
        self.assertEqual(parsed, invocation.emitted_controls)
        reduced = tuple(
            value
            for value in invocation.executed_argv
            if not value.startswith("--ulimit=fsize=")
        )
        self.assertNotIn(
            "rlimit_fsize", self.runner._emitted_controls_from_argv(reduced)
        )

    def test_unknown_domain_fails_closed(self):
        with self.assertRaises(authority.AuthorityFailure):
            self.invocation("unknown_domain")

    def test_malformed_and_above_policy_domain_limits_fail_closed(self):
        base = self.invocation("trusted_inspection")
        for value in (True, 0, -1, authority.MAX_INSPECTION_BYTES + 1, 1.5):
            with self.subTest(value=value):
                changed = replace(base, inspection_output_bytes_limit=value)
                with self.assertRaises(authority.AuthorityFailure):
                    _ = changed.domain_file_size_limit

    def test_rlimit_fsize_is_bound_into_invocation_digest(self):
        base = self.invocation("trusted_inspection")
        changed = replace(
            base,
            inspection_output_bytes_limit=base.inspection_output_bytes_limit - 1,
        )
        self.assertNotEqual(base.sha256, changed.sha256)
        self.assertNotEqual(
            base.as_dict()["normalized_executed_argv_sha256"],
            changed.as_dict()["normalized_executed_argv_sha256"],
        )

    def test_obsolete_file_size_limit_field_is_rejected(self):
        invocation = self.invocation("trusted_inspection").as_dict()
        invocation["file_size_limit"] = invocation["domain_file_size_limit"]
        validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        with self.assertRaises(authority.AuthorityFailure):
            validator.validate("sandbox_invocation", invocation)


class Draft537RuntimeInspectionTests(unittest.TestCase):
    def invocation(self, *, domain="trusted_inspection", limit=1024 * 1024):
        return {
            "domain": domain,
            "entrypoint": str(pathlib.Path(sys.argv[0]).resolve()),
            "container_uid": 65534,
            "container_gid": 65534,
            "working_directory": str(pathlib.Path.cwd()),
            "apparmor_profile": "",
            "selinux_label": "",
            "mount_manifest": [],
            "compiler_artifact_file_size_limit": 2 * 1024 * 1024,
            "inspection_output_bytes_limit": limit,
            "domain_file_size_limit": limit,
            "open_file_limit": 1024,
            "pid_limit": 4096,
            "memory_limit": "8g",
            "cpu_limit": "64",
            "environment_allowlist": [],
            "runtime_created_environment_keys": [],
        }

    def _inspect_with_fsize(self, invocation: dict, observed_fsize: int):
        original = resource.getrlimit

        def measured(which):
            if which == resource.RLIMIT_FSIZE:
                return observed_fsize, observed_fsize
            return original(which)

        with mock.patch.object(verify_lean.resource, "getrlimit", side_effect=measured):
            return verify_lean.inspect_runtime_controls(invocation)

    def test_matching_rlimit_fsize_is_measured(self):
        invocation = self.invocation()
        measured, evidence = self._inspect_with_fsize(
            invocation, invocation["domain_file_size_limit"]
        )
        self.assertIn("rlimit_fsize", measured)
        self.assertTrue(
            any(
                item["control"] == "rlimit_fsize"
                and item["status"] == "measured_pass"
                for item in evidence
            )
        )

    def test_excessive_rlimit_fsize_fails(self):
        invocation = self.invocation()
        measured, evidence = self._inspect_with_fsize(
            invocation, invocation["domain_file_size_limit"] + 1
        )
        self.assertNotIn("rlimit_fsize", measured)
        self.assertTrue(
            any(
                item["control"] == "rlimit_fsize"
                and item["status"] == "measured_fail"
                for item in evidence
            )
        )

    def test_missing_domain_limit_fails_closed(self):
        invocation = self.invocation()
        del invocation["inspection_output_bytes_limit"]
        with self.assertRaises(ValueError):
            verify_lean.domain_file_size_limit(invocation)

    def test_boolean_domain_limit_fails_closed(self):
        invocation = self.invocation(limit=True)
        with self.assertRaises(ValueError):
            verify_lean.domain_file_size_limit(invocation)

    def test_wrong_domain_limit_fails_closed(self):
        invocation = self.invocation(domain="untrusted_compilation")
        invocation["domain_file_size_limit"] = invocation[
            "inspection_output_bytes_limit"
        ]
        with self.assertRaises(ValueError):
            verify_lean.domain_file_size_limit(invocation)

    def test_obsolete_limit_fails_real_inspection_path(self):
        invocation = self.invocation()
        invocation["file_size_limit"] = invocation["domain_file_size_limit"]
        with self.assertRaises(ValueError):
            verify_lean.inspect_runtime_controls(invocation)

    def test_environment_measurement_rejects_every_undeclared_key(self):
        invocation = self.invocation()
        invocation["environment_allowlist"] = ["HOME=/nonexistent", "PATH=/usr/bin:/bin", "PYTHONPATH="]
        invocation["runtime_created_environment_keys"] = ["HOSTNAME"]
        permitted = {"HOME": "/nonexistent", "PATH": "/usr/bin:/bin", "PYTHONPATH": "", "HOSTNAME": "runtime-name"}
        with mock.patch.dict(verify_lean.os.environ, permitted, clear=True):
            measured, evidence = verify_lean.inspect_runtime_controls(invocation)
        self.assertIn("environment_allowlist", measured)
        self.assertTrue(any(item["control"] == "environment_allowlist" and item["status"] == "measured_pass" for item in evidence))
        with mock.patch.dict(verify_lean.os.environ, {**permitted, "ATTACKER_EXTRA": "1"}, clear=True):
            measured, evidence = verify_lean.inspect_runtime_controls(invocation)
        self.assertNotIn("environment_allowlist", measured)
        self.assertTrue(any(item["control"] == "environment_allowlist" and item["status"] == "measured_fail" for item in evidence))

    def test_explicit_entrypoint_has_measured_evidence(self):
        invocation = self.invocation()
        _, evidence = verify_lean.inspect_runtime_controls(invocation)
        self.assertTrue(any(item["control"] == "explicit_entrypoint" and item["status"] == "measured_pass" for item in evidence))


class Draft537ValidationMetadataTests(unittest.TestCase):
    @staticmethod
    def metadata(count=10):
        return {
            "tests_discovered": count,
            "tests_passed": count,
            "tests_skipped": 0,
            "duplicate_test_ids": [],
            "warning_output_lines": [],
        }

    def test_validation_report_uses_discovered_test_count(self):
        record = self.metadata(10)
        narrative = validator.validate_regression_count_consistency(
            record, dict(record), "Tests discovered: 10\nTests passed: 10\n"
        )
        self.assertEqual(narrative["tests_discovered"], 10)

    def test_stale_regression_count_fails_validation(self):
        with self.assertRaises(AssertionError):
            validator.validate_regression_count_consistency(
                self.metadata(9), self.metadata(10),
                "Tests discovered: 9\nTests passed: 9\n",
            )

    def test_discovered_and_passed_counts_must_match(self):
        record = self.metadata(10)
        record["tests_passed"] = 9
        with self.assertRaises(AssertionError):
            validator.validate_regression_run_metadata(record)

    def test_unexpected_skipped_test_fails_release_validation(self):
        record = self.metadata(10)
        record["tests_skipped"] = 1
        with self.assertRaises(AssertionError):
            validator.validate_regression_run_metadata(record)

    def test_regression_suite_is_warning_free(self):
        validator.validate_regression_run_metadata(self.metadata())

    def test_resourcewarning_fails_required_validation(self):
        record = self.metadata()
        record["warning_output_lines"] = ["ResourceWarning: unclosed database"]
        with self.assertRaises(AssertionError):
            validator.validate_regression_run_metadata(record)

    def test_sql_test_connections_are_closed(self):
        cleanup_factories = (
            "executable/tests/test_sql_authority_lifecycle.py",
            "executable/tests/test_sql_authority_lifecycle_v533.py",
            "executable/tests/test_sql_authority_lifecycle_v534.py",
        )
        for relative in cleanup_factories:
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("self.addCleanup(database.close)", source)
        policy = (ROOT / "executable/tests/test_sql_policy_binding_v535.py").read_text(encoding="utf-8")
        self.assertIn("self.addCleanup(self.connection.close)", policy)


if __name__ == "__main__":
    unittest.main()
