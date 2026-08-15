#!/usr/bin/env python3
"""Deterministic safety, Compose, qualification, and authority-boundary tests."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("activation_harness", ROOT / "activation_harness.py")
assert SPEC and SPEC.loader
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)

EXPECTED_GATES = [
    "strict_lean", "strict_tlc", "governed_hermetic_execution",
    "image_build_attestation", "verifier_build_attestation",
    "reproducible_inspector_build", "committed_source_provenance",
    "external_governance_authorization", "post_quantum_provider_attestation",
    "production_key_ceremony", "encrypted_recovery_drill",
    "mixed_version_rollback_drill",
]


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads((ROOT / "activation_gate_registry_v1.json").read_text())
        self.schema = json.loads((ROOT / "activation_evidence_schema_v1.json").read_text())

    def test_host_target_matches_the_5_3_17_registry(self) -> None:
        self.assertEqual(self.registry["contract_version"], "v1.6-draft-5.3.17")
        self.assertTrue(str(harness.DEFAULT_CORPUS).endswith("v1.6 - Draft 5.3.17"))
        self.assertTrue(harness.IMAGE.endswith(":5.3.17"))
        self.assertIn(":5.3.17", (ROOT / "compose.activation.yaml").read_text())

    def test_registry_has_exactly_the_twelve_contract_gates(self) -> None:
        ids = [gate["gate_id"] for gate in self.registry["gates"]]
        self.assertEqual(ids, EXPECTED_GATES)
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_gate_requires_external_signed_evidence(self) -> None:
        for gate in self.registry["gates"]:
            self.assertTrue(gate["evidence_required"], gate["gate_id"])
            self.assertTrue(gate["issuer_scopes"], gate["gate_id"])
            self.assertGreater(gate["timeout_seconds"], 0, gate["gate_id"])

    def test_governance_and_key_ceremony_forbid_self_issuance(self) -> None:
        by_id = {gate["gate_id"]: gate for gate in self.registry["gates"]}
        self.assertTrue(by_id["external_governance_authorization"]["self_issuance_forbidden"])
        self.assertTrue(by_id["production_key_ceremony"]["self_issuance_forbidden"])

    def test_evidence_profile_is_post_quantum_and_version_locked(self) -> None:
        rendered = json.dumps(self.schema).lower()
        self.assertIn("ml-dsa-87", rendered)
        self.assertIn("shake256-512", rendered)
        self.assertIn("v1\\\\.6-draft-", rendered)
        self.assertNotIn("ed25519", rendered)
        self.assertNotIn("sha-256", rendered)
        self.assertNotIn("sha256", rendered)


class ComposePolicyTests(unittest.TestCase):
    def compose(self) -> dict:
        return harness.build_compose_document(
            container_name="duotronic-wc-gates-unit", run_id="unit",
            corpus=Path("/corpus"), source=Path("/source"),
            evidence=Path("/evidence"), output=Path("/output"),
            gates=EXPECTED_GATES,
        )

    def test_compose_service_has_mandatory_rootless_sandbox_controls(self) -> None:
        service = self.compose()["services"]["activation-gates"]
        self.assertEqual(service["networks"], ["activation-isolated"])
        self.assertTrue(self.compose()["networks"]["activation-isolated"]["internal"])
        self.assertTrue(service["read_only"])
        self.assertEqual(service["userns_mode"], "keep-id")
        self.assertEqual(service["cap_drop"], ["ALL"])
        self.assertIn("no-new-privileges", service["security_opt"])
        self.assertEqual(service["pids_limit"], 512)
        self.assertNotIn("ulimits", service)
        self.assertEqual(service["mem_limit"], "4g")
        self.assertEqual(service["cpus"], 4)
        self.assertIn("/corpus:/corpus-ro:ro", service["volumes"])
        self.assertIn("/work:rw,nosuid,nodev,size=2048m", service["tmpfs"])
        self.assertIn("/source:/source:ro", service["volumes"])
        self.assertIn("/evidence:/evidence:ro", service["volumes"])
        self.assertIn("/output:/output:rw", service["volumes"])
        self.assertEqual(service["command"].count("--gate"), 12)
        self.assertEqual(service["environment"]["PYTHONPATH"], "/work/corpus")
        self.assertEqual(service["environment"]["TLA2TOOLS_JAR"], "/opt/tla2tools/tla2tools.jar")
        self.assertEqual(service["environment"]["JAVA_TOOL_OPTIONS"], "-XX:+UseParallelGC")
        self.assertNotIn("privileged", service)

    def test_execution_uses_podman_compose_not_direct_podman_run(self) -> None:
        argv = harness.compose_up_argv("dwc-qual-unit", Path("/output/compose.json"))
        self.assertEqual(argv[:3], ["podman", "--remote=false", "compose"])
        self.assertIn("--abort-on-container-exit", argv)
        self.assertIn("--exit-code-from", argv)
        host = (ROOT / "activation_harness.py").read_text()
        self.assertNotIn('"podman", "--remote=false", "run"', host)

    def test_containerfile_pins_toolchains_and_runs_non_root(self) -> None:
        containerfile = (ROOT / "Containerfile.activation").read_text()
        basefile = (ROOT / "Containerfile.toolchain-base").read_text()
        for token in (
            "FROM localhost/duotronic-wc-toolchain-base:lean4.29.1-java17-pq-v1",
            "USER harness", "TLA2TOOLS_VERSION=1.8.0", "TLA2TOOLS_SHA512=",
            "sha512sum -c -", "TLA2TOOLS_JAR=/opt/tla2tools/tla2tools.jar",
            "PYTHONPATH=/work/corpus", "ENTRYPOINT",
        ):
            self.assertIn(token, containerfile)
        for token in (
            "LEAN_VERSION=4.29.1", "openjdk-17-jre-headless",
            "pqcrypto==0.3.4", "cryptography==46.0.0", "USER harness",
        ):
            self.assertIn(token, basefile)
        self.assertNotIn("podman.sock", containerfile + basefile)

    def test_formal_and_portable_probes_execute_inside_sandbox(self) -> None:
        sandbox = (ROOT / "activation_sandbox.py").read_text()
        compile(sandbox, "activation_sandbox.py", "exec")
        self.assertIn("run_lean_build.py", sandbox)
        self.assertIn("run_tla_model_check.py", sandbox)
        self.assertIn('select_descriptor_tool("lean_runner"', sandbox)
        self.assertIn('select_descriptor_tool("tla_runner"', sandbox)
        self.assertEqual(sandbox.count('"--mode", "strict", "--json"'), 2)
        self.assertIn("select_contract_descriptor", sandbox)
        self.assertIn('descriptor.get("validator")', sandbox)
        self.assertIn("test_identity.py", sandbox)
        self.assertIn("build_trusted_inspector.py", sandbox)
        self.assertIn("prepare_working_corpus", sandbox)
        self.assertIn('CORPUS_SOURCE = Path("/corpus-ro")', sandbox)
        self.assertIn('CORPUS = WORK_ROOT / "corpus"', sandbox)
        self.assertIn("working-corpus.json", sandbox)
        self.assertIn("toolchain-inventory.json", sandbox)
        self.assertIn("qualification-suite.json", sandbox)
        self.assertIn("runtime_connected", sandbox)

    def test_external_challenge_is_stable_and_evidence_independent(self) -> None:
        sandbox = (ROOT / "activation_sandbox.py").read_text()
        body = sandbox.split("def evidence_claim_probe", 1)[1].split("\n\nPROBES =", 1)[0]
        self.assertNotIn("load_evidence", body)
        self.assertIn("external_execution_required", body)
        self.assertIn("required_claims_missing", sandbox)
        self.assertIn("external-attestation-requests.json", sandbox)
        self.assertIn('"state": report_state', sandbox)

    def test_host_and_sandbox_cannot_activate_or_connect_runtime(self) -> None:
        host = (ROOT / "activation_harness.py").read_text()
        sandbox = (ROOT / "activation_sandbox.py").read_text()
        self.assertIn('"authority_activated": False', host)
        self.assertIn('"authority_activated": False', sandbox)
        self.assertIn('"runtime_connected": False', host)
        self.assertIn('"runtime_connected": False', sandbox)
        self.assertIn('if controls["passed"]:', host)


class LifecycleTests(unittest.TestCase):
    def test_cgroup_process_limit_is_applied_before_release(self) -> None:
        class FakeLog:
            def write_json(self, _name, _value):
                return None
            def emit(self, _event, **_fields):
                return None

        with patch.object(
            harness,
            "run_capture",
            side_effect=[
                {"exit_code": 0, "stdout": "container-id\n", "stderr": ""},
                {"exit_code": 0, "stdout": "512\n", "stderr": ""},
            ],
        ) as capture:
            proof = harness.enforce_process_limit(
                FakeLog(), "duotronic-wc-gates-unit", limit=512
            )
        self.assertTrue(proof["applied"])
        self.assertEqual(proof["observed_cgroup_pids_max"], 512)
        self.assertEqual(capture.call_args_list[0].args[2], [
            "podman", "--remote=false", "container", "update",
            "--pids-limit", "512", "duotronic-wc-gates-unit",
        ])
        self.assertEqual(capture.call_args_list[1].args[2], [
            "podman", "--remote=false", "exec", "duotronic-wc-gates-unit",
            "cat", "/sys/fs/cgroup/pids.max",
        ])

    def test_live_controls_require_internal_attached_network_and_cgroup_limit(self) -> None:
        network_name = "dwc-qual-unit_activation-isolated"
        item = {
            "HostConfig": {
                "NetworkMode": "bridge",
                "CapDrop": [
                    "CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_FOWNER", "CAP_FSETID",
                    "CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_SETFCAP", "CAP_SETGID",
                    "CAP_SETPCAP", "CAP_SETUID", "CAP_SYS_CHROOT",
                ],
                "CapAdd": [],
                "PidsLimit": 512,
                "ReadonlyRootfs": True,
                "SecurityOpt": ["no-new-privileges"],
            },
            "Config": {
                "User": "1000:1000",
                "CreateCommand": ["podman", "create", "--net", network_name],
            },
            "NetworkSettings": {"Networks": {network_name: {}}},
            "Mounts": [
                {"Destination": "/corpus-ro", "RW": False},
                {"Destination": "/source", "RW": False},
                {"Destination": "/evidence", "RW": False},
            ],
        }
        controls = harness.inspect_sandbox_controls(
            item,
            {"network_name": network_name, "internal": True},
            {"applied": True, "observed_cgroup_pids_max": 512},
        )
        self.assertTrue(controls["passed"])
        self.assertEqual(controls["observed_cgroup_pids_max"], 512)
        self.assertEqual(controls["podman_metadata_pids_limit"], 512)

    def test_cleanup_requires_absence_postcondition(self) -> None:
        class FakeLog:
            def write_json(self, _name, _value):
                return None
            def emit(self, _event, **_fields):
                return None

        calls = []
        def fake_capture(_log, phase, argv, **_kwargs):
            calls.append((phase, argv))
            if phase == "container-force-remove":
                return {"exit_code": 0}
            return {"exit_code": 1}

        with patch.object(harness, "run_capture", side_effect=fake_capture):
            proof = harness.force_cleanup(FakeLog(), "duotronic-wc-gates-unit")
        self.assertTrue(proof["cleaned"])
        self.assertEqual(calls[0][1], [
            "podman", "--remote=false", "rm", "--force", "--ignore",
            "duotronic-wc-gates-unit",
        ])
        self.assertEqual(calls[1][1], [
            "podman", "--remote=false", "container", "exists",
            "duotronic-wc-gates-unit",
        ])

    def test_each_invocation_creates_a_dedicated_log_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(harness, "LOG_ROOT", Path(directory)):
                log = harness.RunLog("unit")
                log.command("sample", ["true"])
                log.write_json("aggregate-report.json", {
                    "authority_activated": False, "runtime_connected": False,
                })
                expected = {
                    "host.log.ndjson", "host.log", "commands.jsonl",
                    "aggregate-report.json",
                }
                self.assertTrue(expected.issubset({item.name for item in log.directory.iterdir()}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
