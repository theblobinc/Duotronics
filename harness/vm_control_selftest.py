#!/usr/bin/env python3
"""Deterministic tests for the libvirt boundary and attestation workflow."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vm = load("vm_control", ROOT / "vm_control.py")
attest = load("external_attestation_workflow", ROOT / "external_attestation_workflow.py")
guest = load("guest_runner", ROOT / "vm" / "guest" / "guest_runner.py")


class BoundaryTests(unittest.TestCase):
    def test_vm_policy_isolates_sandbox_authority_from_production(self):
        config = json.loads((ROOT / "vm" / "harness-vm.json").read_text())
        self.assertFalse(config["host_podman_allowed"])
        self.assertTrue(config["guest_rootless_podman_required"])
        self.assertFalse(config["production_runtime_network_access"])
        self.assertFalse(config["production_runtime_activation_enabled"])
        self.assertTrue(config["sandbox_runtime_enabled"])
        self.assertTrue(config["sandbox_authority_activation_enabled"])
        self.assertEqual(config["sandbox_authority_profile"], "sandbox-test-only")
        self.assertFalse(config["sandbox_production_eligible"])

    def test_host_controller_has_no_podman_subprocess(self):
        source = (ROOT / "vm_control.py").read_text()
        compile(source, "vm_control.py", "exec")
        self.assertNotIn('["podman"', source)
        self.assertIn('forbidden = {"podman", "podman-compose", "buildah"}', source)
        self.assertIn("host Podman invocation is prohibited", source)
        self.assertIn('"host_podman_invoked": False', source)

    def test_guest_runner_is_named_operation_api(self):
        source = (ROOT / "vm" / "guest" / "guest_runner.py").read_text()
        compile(source, "guest_runner.py", "exec")
        self.assertIn('["podman", "--remote=false", "info"', source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("add_parser(\"shell\")", source)
        self.assertNotIn("add_parser(\"exec\")", source)
        self.assertIn("image_refresh = refresh_activation_image(run, args.timeout)", source)
        self.assertIn("duotronic-witness-harness-image-refresh/v1", source)
        for operation in ("health", "status", "prepare", "prepare-source", "build", "execute", "sandbox-activate", "cleanup"):
            self.assertIn(f'add_parser("{operation}")', source)

    def test_contract_controller_dispatches_sandbox_to_vm(self):
        source = (ROOT / "contract_control.py").read_text()
        self.assertIn('VM_CONTROL = HARNESS_ROOT / "vm_control.py"', source)
        body = source.split("def command_sandbox", 1)[1].split("\n\ndef ", 1)[0]
        self.assertIn("str(VM_CONTROL)", body)
        self.assertNotIn("ACTIVATION_HARNESS", body)

    def test_bootstrap_is_fail_closed_and_image_verified(self):
        source = (ROOT / "vm" / "bootstrap-host.sh").read_text()
        self.assertIn("set -euo pipefail", source)
        self.assertIn("image_verify.py", source)
        self.assertIn("refusing to overwrite", source)
        self.assertIn("qemu:///system", source)
        self.assertNotIn("podman", source.lower())

    def test_auto_shutdown_default_and_force_is_explicit(self):
        config = json.loads((ROOT / "vm" / "harness-vm.json").read_text())
        self.assertTrue(config["auto_shutdown_after_run"])
        source = (ROOT / "vm_control.py").read_text()
        self.assertIn("explicit --force is required", source)
        self.assertIn("automatic_shutdown_requested", source)

    def test_sigterm_converts_to_cleanup_exception(self):
        with self.assertRaises(vm.ControllerTermination):
            vm.handle_termination(15, None)


class AttestationTests(unittest.TestCase):
    def test_all_twelve_gates_are_covered(self):
        registry = json.loads((ROOT / "activation_gate_registry_v1.json").read_text())
        self.assertEqual(len(attest.GATES), 12)
        self.assertEqual(set(attest.GATES), {gate["gate_id"] for gate in registry["gates"]})

    def test_workflow_never_signs_or_accepts_legacy_suites(self):
        source = (ROOT / "external_attestation_workflow.py").read_text()
        self.assertIn("never signs evidence", source)
        self.assertIn('"ML-DSA-87"', source)
        self.assertIn('"SHAKE256-512"', source)
        self.assertNotIn("Ed25519", source)
        self.assertNotIn("SHA-256", source)
        self.assertNotIn("private_key", source)
        self.assertNotIn("sign(", source)

    def test_evidence_is_bound_to_exact_probe_run_and_measurement(self):
        sandbox = (ROOT / "activation_sandbox.py").read_text()
        self.assertIn('"probe_run_mismatch"', sandbox)
        self.assertIn("expected_run_id", sandbox)
        workflow = (ROOT / "external_attestation_workflow.py").read_text()
        self.assertIn("evidence probe run does not match this challenge", workflow)
        self.assertIn("evidence measurement does not match this challenge", workflow)
        controller = (ROOT / "vm_control.py").read_text()
        self.assertIn("--attestation-run-id", controller)
        self.assertIn("--evidence-run-id", controller)

    def test_sandbox_attestor_is_test_only_and_does_not_persist_private_keys(self):
        source = (ROOT / "sandbox_attestor.py").read_text()
        compile(source, "sandbox_attestor.py", "exec")
        self.assertIn('PROFILE = "sandbox-test-only"', source)
        self.assertIn('"production_eligible": False', source)
        self.assertIn('"managed_by_harness": False', source)
        self.assertIn("ml_dsa_87.generate_keypair()", source)
        self.assertIn("ml_dsa_87.sign(secret_key, payload)", source)
        self.assertNotIn("secret_key_base64", source)
        self.assertNotIn("private_key_base64", source)
        self.assertIn("len(requests) != 12", source)

    def test_governance_and_key_ceremony_self_issuance_remains_forbidden(self):
        forbidden = {gate_id for gate_id, gate in attest.GATES.items() if gate.get("self_issuance_forbidden")}
        self.assertEqual(forbidden, {"external_governance_authorization", "production_key_ceremony"})

    def test_ingest_is_confined_to_evidence_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "logs" / "unit"
            run.mkdir(parents=True)
            evidence_root = root / "evidence"
            evidence_root.mkdir()
            outside = root / "outside.json"
            outside.write_text("{}")
            with patch.object(attest, "LOG_ROOT", root / "logs"), patch.object(attest, "EVIDENCE_ROOT", evidence_root):
                with self.assertRaises(ValueError):
                    attest.ingest(Namespace(run_id="unit", evidence_file=str(outside)))

    def test_export_records_pq_profile_and_forbidden_issuers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "logs" / "unit"
            source = run / "vm-guest" / "harness-logs" / "probe"
            source.mkdir(parents=True)
            (source / "external-attestation-requests.json").write_text(json.dumps({"requests": [{"gate_id": "strict_lean", "measurement_id": "duoid:shake256-512:test", "probe": {"run_id": "probe-unit"}}]}))
            with patch.object(attest, "LOG_ROOT", root / "logs"):
                self.assertEqual(attest.export_requests(Namespace(run_id="unit")), 0)
            bundle = json.loads((run / "attestation" / "request-bundle.json").read_text())
            self.assertEqual(bundle["signature_suite_required"], "ML-DSA-87")
            self.assertEqual(bundle["payload_hash_required"], "SHAKE256-512")
            self.assertEqual(bundle["self_issuance_forbidden"], ["external_governance_authorization", "production_key_ceremony"])


class PairedCycleBoundaryTests(unittest.TestCase):
    def test_current_runtime_snapshot_is_filtered_and_guest_only(self):
        source = (ROOT / "vm_control.py").read_text(encoding="utf-8")
        self.assertIn("def sync_runtime_parent", source)
        self.assertIn('"sync-runtime-parent"', source)
        self.assertIn('"*.key", "*.pem", "id_rsa*"', source)
        self.assertIn('"contains_production_credentials": False', source)
        self.assertNotIn('capture(["podman"', source)

    def test_paired_cycle_requires_runtime_qualification_and_all_twelve_gates(self):
        host = (ROOT / "vm_control.py").read_text(encoding="utf-8")
        guest = (ROOT / "vm" / "guest" / "guest_runner.py").read_text(encoding="utf-8")
        self.assertIn('report.get("verified_gate_count") == 12', host)
        self.assertIn("activation_exit = sandbox_activate(args)", guest)
        self.assertIn('"verified_gate_count": 12 if active else 0', guest)
        self.assertIn('"production_eligible": False', guest)

    def test_paired_lab_has_no_production_runtime_or_model_endpoint(self):
        source = (ROOT / "paired_vm_lab.py").read_text(encoding="utf-8")
        self.assertIn('"production_runtime_connected": False', source)
        self.assertIn('"production_eligible": False', source)
        self.assertNotIn("10.77.0.2", source)
        self.assertNotIn("11434", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
