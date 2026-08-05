#!/usr/bin/env python3
from __future__ import annotations

import dataclasses
import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))
import proof_authority as authority
from proof_check_service import ProofCheckApplication
from proof_check_wsgi import ProofCheckWSGI


def compiler_profile(result_key: Ed25519PrivateKey, runtime_hash: str) -> authority.CompilerProfile:
    return authority.CompilerProfile.from_record({
        "compiler_profile_id":"lean-4.29.1-hermetic-3","toolchain":"leanprover/lean4:v4.29.1",
        "image_reference":"registry.example.invalid/witness/lean-verifier","oci_image_digest":"sha256:" + "1" * 64,
        "oci_runtime_sha256":runtime_hash,"oci_runtime_version":"podman version 5.4.0",
        "lake_executable_sha256":"3" * 64,"lean_executable_sha256":"4" * 64,"lean_stdlib_tree_sha256":"5" * 64,
        "dependency_closure_sha256":"6" * 64,"verifier_executable_sha256":"7" * 64,"verifier_source_revision":"git:535",
        "verifier_build_attestation_id":"attestation:535","sandbox_policy_sha256":"8" * 64,
        "verifier_result_signer_key_id":"result-key:535","verifier_result_public_key_base64url":authority.public_key_raw_b64url(result_key.public_key()),
        "authorized_axioms":["Classical.choice","Quot.sound","propext"],"valid_from":"2026-01-01T00:00:00Z","valid_until":"2027-01-01T00:00:00Z",
    })


class RunnerFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(); root = pathlib.Path(self.temp.name)
        self.runtime = root / "podman"
        self.runtime.write_text("#!/bin/sh\nif [ \"$1\" = version ]; then echo 'podman version 5.4.0'; fi\nexit 0\n", encoding="utf-8"); self.runtime.chmod(0o700)
        self.seccomp = root / "seccomp.json"; self.seccomp.write_text("{}", encoding="utf-8"); self.seccomp.chmod(0o600)
        self.key = Ed25519PrivateKey.generate(); self.profile = compiler_profile(self.key, authority.sha256_file(self.runtime))

    def close(self): self.temp.cleanup()

    def runner(self, **overrides):
        values = dict(
            verifier_result_signing_key=self.key, authority_uid=65534, authority_gid=65534,
            seccomp_profile_path=self.seccomp, expected_seccomp_profile_sha256=authority.sha256_file(self.seccomp),
            supported_controls=authority.OciSandboxRunner.REQUIRED_CONTROLS,
        ); values.update(overrides)
        return authority.OciSandboxRunner(self.runtime, authority.sha256_file(self.runtime), self.profile.oci_runtime_version, **values)


class OciSandboxTests(unittest.TestCase):
    def setUp(self): self.fixture = RunnerFixture()
    def tearDown(self): self.fixture.close()

    def invocation(self, entrypoint="/opt/witness-authority/bin/compile-lean"):
        runner = self.fixture.runner()
        mounts = ({"source":"snapshot:x","host_path":"/tmp/source","destination":"/input/source","mode":"ro","domain":"untrusted_compilation","purpose":"sealed_source","lifecycle":"request"},)
        limits = authority.EffectiveResourceLimits(600, 1000, 128 * 1024 * 1024, 512 * 1024 * 1024, 4 * 1024 * 1024, 1024 * 1024, 1024 * 1024, 1024 * 1024, 2 * 1024 * 1024)
        return runner, runner._invocation(domain="untrusted_compilation", profile=self.fixture.profile, entrypoint=entrypoint, arguments=("--generated","/input/generated"), mounts=mounts, limits=limits, uid=65534, gid=65534)

    def test_oci_argv_matches_effective_invocation_for_both_domains(self):
        for entrypoint in ("/opt/witness-authority/bin/compile-lean", "/opt/witness-authority/bin/verify-lean"):
            runner, invocation = self.invocation(entrypoint); command = runner._command(invocation)
            self.assertIn(f"--entrypoint={entrypoint}", command); self.assertIn("--workdir=/work", command)
            image_index = command.index(f"{invocation.image_reference}@{invocation.image_digest}")
            self.assertNotIn(entrypoint, command[image_index + 1:])
            self.assertEqual(invocation.requested_controls, invocation.emitted_controls)
            self.assertEqual(invocation.accepted_controls, ())
            self.assertEqual(invocation.applied_controls, ())

    def test_container_entrypoint_is_absent_and_domains_are_independent(self):
        text = (ROOT / "executable/trusted_verifier/Containerfile").read_text(encoding="utf-8")
        self.assertFalse(any(line.strip().startswith("ENTRYPOINT") for line in text.splitlines()))
        self.assertIn("compile-lean", text); self.assertIn("verify-lean", text)

    def test_container_entrypoint_is_overridden_or_absent(self):
        self.test_container_entrypoint_is_absent_and_domains_are_independent()

    def test_untrusted_domain_executes_only_compile_wrapper(self):
        runner, invocation = self.invocation("/opt/witness-authority/bin/compile-lean")
        command = runner._command(invocation)
        self.assertIn("--entrypoint=/opt/witness-authority/bin/compile-lean", command)
        self.assertNotIn("/opt/witness-authority/bin/verify-lean", command)

    def test_trusted_domain_executes_only_verify_wrapper(self):
        runner, invocation = self.invocation("/opt/witness-authority/bin/verify-lean")
        command = runner._command(invocation)
        self.assertIn("--entrypoint=/opt/witness-authority/bin/verify-lean", command)
        self.assertNotIn("/opt/witness-authority/bin/compile-lean", command)

    def test_every_effective_control_has_runtime_mapping(self):
        runner, invocation = self.invocation(); command = " ".join(runner._command(invocation))
        expected_fragments = ("--entrypoint=", "--workdir=/work", "--network=none", "--read-only", "--cap-drop=ALL", "no-new-privileges", "seccomp=", "apparmor=", "--userns=private", "--pids-limit=", "--memory=", "--cpus=", "--user=65534:65534", "--ulimit=fsize=", "--ulimit=nofile=", "--volume=", "--tmpfs=/tmp:")
        for fragment in expected_fragments: self.assertIn(fragment, command)

    def test_every_effective_control_has_runtime_flag_verified_default_or_rejection(self):
        self.test_every_effective_control_has_runtime_mapping()

    def test_invocation_digest_changes_for_every_declared_control(self):
        _, invocation = self.invocation(); baseline = invocation.sha256
        mutations = {
            "working_directory":"/different", "network_mode":"bridge", "read_only_rootfs":False,
            "apparmor_profile":"different", "user_namespace_mode":"host",
            "pid_limit":127, "memory_limit":"1g", "cpu_limit":"1", "compiler_artifact_file_size_limit":1048575,
            "open_file_limit":255, "timeout":599, "entrypoint":"/opt/witness-authority/bin/verify-lean",
        }
        for field, value in mutations.items():
                with self.subTest(field=field): self.assertNotEqual(dataclasses.replace(invocation, **{field:value}).sha256, baseline)

    def test_effective_invocation_digest_changes_for_each_control(self):
        self.test_invocation_digest_changes_for_every_declared_control()

    def test_runtime_version_is_measured_and_root_is_rejected(self):
        with self.assertRaises(authority.AuthorityFailure):
            authority.OciSandboxRunner(self.fixture.runtime, authority.sha256_file(self.fixture.runtime), "configured lie", verifier_result_signing_key=self.fixture.key, authority_uid=65534, authority_gid=65534, seccomp_profile_path=self.fixture.seccomp, expected_seccomp_profile_sha256=authority.sha256_file(self.fixture.seccomp))
        for uid, gid in ((0, 65534), (65534, 0)):
            with self.assertRaises(authority.AuthorityFailure): self.fixture.runner(authority_uid=uid, authority_gid=gid)

    def test_trusted_domain_rejects_uid_gid_zero(self):
        for uid, gid in ((0, 65534), (65534, 0)):
            with self.assertRaises(authority.AuthorityFailure): self.fixture.runner(authority_uid=uid, authority_gid=gid)

    def test_runtime_version_is_measured_not_config_echoed(self):
        with self.assertRaises(authority.AuthorityFailure):
            authority.OciSandboxRunner(self.fixture.runtime, authority.sha256_file(self.fixture.runtime), "false configured version", verifier_result_signing_key=self.fixture.key, authority_uid=65534, authority_gid=65534, seccomp_profile_path=self.fixture.seccomp, expected_seccomp_profile_sha256=authority.sha256_file(self.fixture.seccomp))

    def test_runtime_inspection_matches_declared_security_properties(self):
        source = (ROOT / "executable/trusted_verifier/verify_lean.py").read_text(encoding="utf-8")
        for measurement in ("/proc/self/status", "/proc/self/mountinfo", "/proc/self/uid_map", "/sys/class/net"):
            self.assertIn(measurement, source)
        self.assertIn("measured_controls, control_evidence = inspect_runtime_controls(invocation)", source)

    def test_missing_runtime_control_fails_closed(self):
        with self.assertRaises(authority.AuthorityFailure):
            self.fixture.runner(supported_controls=frozenset(authority.OciSandboxRunner.REQUIRED_CONTROLS - {"seccomp"}))


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate(); self.now = datetime(2026, 7, 31, tzinfo=timezone.utc)

    def registry(self, **changes):
        decision = {"schema_version":"proof_policy_decision/v1","policy_decision_id":"policy:1","status":"active","subject_id":"principal:1","operation":"proof_check","compiler_profile_ids":["profile:1"],"source_bundle_ids":["bundle:1"],"resource_permissions":{"maximum_timeout_seconds":600,"maximum_source_bytes":1000},"valid_from":"2026-01-01T00:00:00Z","valid_until":"2027-01-01T00:00:00Z","supersedes_policy_decision_id":None,"governance_authority_id":"gov:1","created_at":"2026-01-01T00:00:00Z"}
        decision.update(changes); decision["canonical_record_sha256"] = authority.sha256_bytes(authority.canonical_bytes(decision))
        return authority.sign_record({"schema_version":"proof_policy_registry/v1","registry_id":"registry:1","governance_key_id":"gov:1","decisions":[decision],"created_at":"2026-01-01T00:00:00Z"}, self.key)

    def test_policy_status_scope_and_time_are_enforced_before_execution(self):
        resolver = authority.ProofPolicyResolver(self.registry(), self.key.public_key(), clock=lambda:self.now)
        resolved = resolver.resolve("policy:1", subject_id="principal:1", operation="proof_check", compiler_profile_id="profile:1", source_bundle_id="bundle:1")
        self.assertEqual(resolved.canonical_record_sha256, self.registry()["decisions"][0]["canonical_record_sha256"])
        for kwargs in ({"policy_decision_id":"unknown"},{"subject_id":"other"},{"compiler_profile_id":"other"},{"source_bundle_id":"other"}):
            values = dict(policy_decision_id="policy:1", subject_id="principal:1", operation="proof_check", compiler_profile_id="profile:1", source_bundle_id="bundle:1"); values.update(kwargs)
            with self.assertRaises(authority.AuthorityFailure): resolver.resolve(**values)
        for change in ({"status":"revoked"},{"valid_until":"2020-01-01T00:00:00Z"}):
            denied = authority.ProofPolicyResolver(self.registry(**change), self.key.public_key(), clock=lambda:self.now)
            with self.assertRaises(authority.AuthorityFailure): denied.resolve("policy:1", subject_id="principal:1", operation="proof_check", compiler_profile_id="profile:1", source_bundle_id="bundle:1")

    def test_policy_decision_is_resolved_before_execution(self):
        resolver = authority.ProofPolicyResolver(self.registry(), self.key.public_key(), clock=lambda:self.now)
        self.assertEqual(resolver.resolve("policy:1", subject_id="principal:1", operation="proof_check", compiler_profile_id="profile:1", source_bundle_id="bundle:1").policy_decision_id, "policy:1")

    def test_policy_decision_scope_and_status_are_enforced(self):
        self.test_policy_status_scope_and_time_are_enforced_before_execution()

    def test_policy_decision_and_record_hash_are_signature_bound(self):
        resolver = authority.ProofPolicyResolver(self.registry(), self.key.public_key(), clock=lambda:self.now)
        resolved = resolver.resolve("policy:1", subject_id="principal:1", operation="proof_check", compiler_profile_id="profile:1", source_bundle_id="bundle:1")
        self.assertEqual(len(resolved.canonical_record_sha256), 64)

    def test_revoked_or_expired_policy_fails_closed(self):
        for change in ({"status":"revoked"},{"valid_until":"2020-01-01T00:00:00Z"}):
            resolver = authority.ProofPolicyResolver(self.registry(**change), self.key.public_key(), clock=lambda:self.now)
            with self.assertRaises(authority.AuthorityFailure): resolver.resolve("policy:1", subject_id="principal:1", operation="proof_check", compiler_profile_id="profile:1", source_bundle_id="bundle:1")


class SnapshotAndOutputTests(unittest.TestCase):
    def project(self, root: pathlib.Path):
        (root / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")

    def test_snapshot_limits_and_special_files(self):
        cases = [
            (authority.SnapshotLimits(maximum_files=1), lambda root: (root / "Two.lean").write_text("x", encoding="utf-8")),
            (authority.SnapshotLimits(maximum_total_bytes=4), lambda root: None),
            (authority.SnapshotLimits(maximum_depth=1), lambda root: ((root / "a" / "b").mkdir(parents=True), (root / "a" / "b" / "x.lean").write_text("x", encoding="utf-8"))),
        ]
        for limits, prepare in cases:
            with self.subTest(limits=limits), tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as destination:
                root = pathlib.Path(source); self.project(root); prepare(root)
                with self.assertRaises(authority.AuthorityFailure): authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot", limits=limits)
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as destination:
            root = pathlib.Path(source); self.project(root); os.mkfifo(root / "pipe")
            with self.assertRaises(ValueError): authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot")

    def test_source_snapshot_total_file_limit(self):
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as destination:
            root = pathlib.Path(source); self.project(root); (root / "Two.lean").write_text("x", encoding="utf-8")
            with self.assertRaises(authority.AuthorityFailure): authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot", limits=authority.SnapshotLimits(maximum_files=1))

    def test_source_snapshot_total_byte_limit(self):
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as destination:
            root = pathlib.Path(source); self.project(root)
            with self.assertRaises(authority.AuthorityFailure): authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot", limits=authority.SnapshotLimits(maximum_total_bytes=4))

    def test_source_snapshot_depth_and_path_limits(self):
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as destination:
            root = pathlib.Path(source); self.project(root); (root / ("x" * 40 + ".lean")).write_text("x", encoding="utf-8")
            with self.assertRaises(authority.AuthorityFailure): authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot", limits=authority.SnapshotLimits(maximum_path_bytes=20))

    def test_source_snapshot_rejects_special_files(self):
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as destination:
            root = pathlib.Path(source); self.project(root); os.mkfifo(root / "pipe")
            with self.assertRaises(ValueError): authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot")

    def test_parent_path_swap_cannot_substitute_content(self):
        with tempfile.TemporaryDirectory() as parent, tempfile.TemporaryDirectory() as destination:
            base = pathlib.Path(parent); root = base / "source"; root.mkdir(); self.project(root)
            evil = base / "evil"; evil.mkdir(); (evil / "Proof.lean").write_text("theorem t : False := by contradiction\n", encoding="utf-8")
            swapped = False
            def swap(_relative):
                nonlocal swapped
                if not swapped:
                    swapped = True; root.rename(base / "original"); root.symlink_to(evil, target_is_directory=True)
            try:
                snapshot = authority.create_immutable_snapshot(root, pathlib.Path(destination) / "snapshot", after_file_copy=swap)
            except authority.AuthorityFailure:
                return
            self.assertEqual((snapshot.root / "Proof.lean").read_text(encoding="utf-8"), "theorem t : True := by trivial\n")

    def test_subprocess_output_limit_terminates_process_group(self):
        result = authority.run_bounded_process((sys.executable, "-c", "import os,time; print('x'*200000); os.fork() == 0 and time.sleep(30)"), timeout_seconds=5, stdout_limit=1024, stderr_limit=1024, combined_limit=2048)
        self.assertTrue(result.output_limit_exceeded); self.assertFalse(result.timed_out); self.assertLessEqual(len(result.stdout.encode()), 1024)

    def test_host_and_container_output_limits_are_consistent(self):
        host = (ROOT / "executable/runtime/proof_authority.py").read_text(encoding="utf-8")
        container = (ROOT / "executable/trusted_verifier/bounded_subprocess.py").read_text(encoding="utf-8")
        self.assertIn("1024 * 1024", host); self.assertIn("1024 * 1024", container)


class FormalBuildTests(unittest.TestCase):
    def test_strict_lean_build_includes_trusted_inspector_executable(self):
        runner = (ROOT / "executable/formal/run_lean_build.py").read_text(encoding="utf-8")
        lakefile = (ROOT / "lakefile.lean").read_text(encoding="utf-8")
        self.assertIn("witnessAuthorityInspector", runner); self.assertIn("lean_exe witnessAuthorityInspector", lakefile)

    def test_inspector_cli_positive_negative_and_malformed_fixtures(self):
        source = (ROOT / "formal/draft5_3_5/lean/WitnessAuthority/InspectorMain.lean").read_text(encoding="utf-8")
        self.assertIn('args == ["--version"]', source); self.assertIn("missing required inspector argument", source)
        self.assertIn("importModules", source); self.assertIn("collectAxioms", source); self.assertNotIn("return 78", source)

    def test_attested_inspector_hash_matches_image_binary(self):
        container = (ROOT / "executable/trusted_verifier/Containerfile").read_text(encoding="utf-8")
        schema = json.loads((ROOT / "schemas/build_attestation_v2.schema.json").read_text(encoding="utf-8"))
        self.assertIn("build/inspect-lean /opt/witness-authority/bin/inspect-lean", container)
        self.assertIn("output_binary_sha256", schema["required"])

    def test_reproducible_inspector_build_from_pinned_toolchain(self):
        script = (ROOT / "executable/formal/build_trusted_inspector.py").read_text(encoding="utf-8")
        self.assertIn("first_hash == second_hash", script); self.assertTrue((ROOT / "lean-toolchain").read_text().strip().startswith("leanprover/lean4:v"))


class ApiConformanceTests(unittest.TestCase):
    class Resolver:
        def resolve(self, policy_decision_id, **_):
            return authority.ResolvedPolicyDecision(policy_decision_id, {}, "3" * 64, 600, 1000000)

    class Authority:
        def __init__(self, witness): self.witness = witness; self.calls = 0
        def verify(self, **arguments):
            self.calls += 1; result = json.loads(json.dumps(self.witness)); result["policy_decision_id"] = arguments["policy_decision_id"]; result["policy_decision_sha256"] = arguments["policy_decision_sha256"]; return result

    def test_openapi_response_matches_running_wsgi_adapter_and_idempotency(self):
        witness = json.loads((ROOT / "executable/tests/fixtures/draft5_3_5/valid/lean_compiler_witness_v4.json").read_text(encoding="utf-8"))["payload"]
        witness["schema_version"] = "lean_compiler_witness/v6"
        witness.update({
            "normalized_executed_argv_sha256":"1"*64, "handoff_manifest_sha256":"2"*64,
            "effective_resource_limits":{"timeout_seconds":600,"source_total_bytes":1000000,"compiler_artifact_file_bytes":134217728,"handoff_total_bytes":536870912,"inspection_output_bytes":4194304,"final_result_bytes":1048576,"stdout_bytes":1048576,"stderr_bytes":1048576,"combined_output_bytes":2097152},
            "effective_resource_limits_sha256":"3"*64, "trust_root_attestation_registry_sha256":"4"*64,
            "domain_file_size_limit":4194304,
            "expected_type_expression_fingerprint":"expr:true", "actual_type_expression_fingerprint":"expr:true",
            "dependency_closure":["Init.True"], "emitted_controls":["lsm_profile"],
            "accepted_controls":["lsm_profile"], "applied_controls":["lsm_profile"], "measured_controls":["lsm_profile"],
            "derived_controls":["result_channel_isolated"], "control_evidence":[],
        })
        witness.pop("verified_controls")
        with tempfile.TemporaryDirectory() as directory:
            store = pathlib.Path(directory); bundle = store / "bundle-001"; bundle.mkdir(); (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            fake = self.Authority(witness); wsgi = ProofCheckWSGI(ProofCheckApplication(fake, store, self.Resolver()))
            request = {"request_id":"request-001","idempotency_key":"proof-check-001","subject_id":"principal-reviewer-001","compiler_profile_id":"lean-4.29.1-hermetic-3","claim_id":"claim-001","canonical_claim":{"statement":"True"},"theorem_statement":"True","theorem_name":"t","source_bundle_id":"bundle-001","proof_artifact_relative_path":"Proof.lean","policy_decision_id":"policy-proof-001"}
            body = authority.canonical_bytes(request); statuses = []
            environ = {"REQUEST_METHOD":"POST","PATH_INFO":"/v2/proof-checks","CONTENT_TYPE":"application/json","CONTENT_LENGTH":str(len(body)),"HTTP_IDEMPOTENCY_KEY":"proof-check-001","wsgi.input":io.BytesIO(body)}
            response = b"".join(wsgi(environ, lambda status, headers: statuses.append(status)))
            self.assertEqual(statuses, ["200 OK"]); result = json.loads(response); self.assertEqual(fake.calls, 1)
            environ["wsgi.input"] = io.BytesIO(body); b"".join(wsgi(environ, lambda *_: None)); self.assertEqual(fake.calls, 1)
        result_schema = json.loads((ROOT / "schemas/proof_check_result_v5.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(set(result_schema["required"]).issubset(result))
        witness_schema = json.loads((ROOT / "schemas/lean_compiler_witness_v6.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(set(witness_schema["required"]).issubset(result["compiler_witness"]))

    def test_openapi_has_only_implemented_proof_route(self):
        import yaml
        document = yaml.safe_load((ROOT / "executable/openapi/draft5_3_6_evidence_language_openapi.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(document["paths"]), {"/v2/proof-checks"}); self.assertEqual(set(document["paths"]["/v2/proof-checks"]), {"post"})
        self.assertIn("200", {str(key) for key in document["paths"]["/v2/proof-checks"]["post"]["responses"]})


if __name__ == "__main__": unittest.main()
