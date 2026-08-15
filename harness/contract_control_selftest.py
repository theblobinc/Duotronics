#!/usr/bin/env python3
"""Deterministic tests for multi-version contract and runtime lifecycle control."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("contract_control", ROOT / "contract_control.py")
assert SPEC and SPEC.loader
control = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(control)

RUNTIME_CONFIG = Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/app/duotronic_runtime/config.py")
CONFIG_SPEC = importlib.util.spec_from_file_location("runtime_config_contract_test", RUNTIME_CONFIG)
assert CONFIG_SPEC and CONFIG_SPEC.loader
runtime_config = importlib.util.module_from_spec(CONFIG_SPEC)
sys.modules[CONFIG_SPEC.name] = runtime_config
CONFIG_SPEC.loader.exec_module(runtime_config)


class ContractControlTests(unittest.TestCase):
    def test_version_names_are_confined(self) -> None:
        self.assertEqual(control.valid_name("v1.6 - Draft 5.3.18"), "v1.6 - Draft 5.3.18")
        for bad in ("../escape", "/absolute", "x/y", "..", ".hidden"):
            with self.assertRaises(ValueError, msg=bad):
                control.valid_name(bad)

    def test_scoped_resolution_and_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspaces = base / "workspaces"
            published = base / "published"
            workspaces.mkdir()
            published.mkdir()
            (workspaces / "same").mkdir()
            (published / "same").mkdir()
            with patch.object(control, "WORKSPACE_ROOT", workspaces), patch.object(control, "CONTRACT_ROOT", published):
                self.assertEqual(control.resolve_ref("workspace:same")[0], "workspace")
                self.assertEqual(control.resolve_ref("published:same")[0], "published")
                with self.assertRaises(ValueError):
                    control.resolve_ref("same")

    def test_snapshot_is_shake256_512_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("alpha")
            first = control.snapshot("workspace", root)
            second = control.snapshot("workspace", root)
            self.assertEqual(first["corpus_root"], second["corpus_root"])
            self.assertTrue(first["corpus_root"].startswith("shake256-512:"))
            self.assertEqual(first["algorithm"], "SHAKE256-512")

    def test_qualification_requires_exact_contract_and_all_release_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve()
            report = {
                "tested_corpus_path": str(path),
                "state": "verified",
                "activation_eligible": True,
                "qualification_complete": True,
                "runtime_handoff_eligible": True,
                "cleanup": {"cleaned": True},
                "host_sandbox_controls": {"passed": True},
            }
            self.assertEqual(control.report_is_qualified(report, path), (True, []))
            report["state"] = "blocked"
            ok, reasons = control.report_is_qualified(report, path)
            self.assertFalse(ok)
            self.assertIn("aggregate_not_verified", reasons)

    def test_development_activation_has_explicit_confirmation(self) -> None:
        self.assertEqual(control.DEVELOPMENT_CONFIRMATION, "ALLOW_NONAUTHORITATIVE_DEVELOPMENT_ACTIVATION")
        source = (ROOT / "contract_control.py").read_text()
        self.assertIn("activation_mode", source)
        self.assertIn("non_authoritative", source)
        self.assertIn("activation_failed_rolled_back", source)

    def test_published_contracts_cannot_be_discarded(self) -> None:
        source = (ROOT / "contract_control.py").read_text()
        self.assertIn("published contracts cannot be discarded", source)
        self.assertIn("DISCARD_WITNESS_CONTRACT_WORKSPACE", source)

    def test_harness_run_is_multi_version_and_records_exact_path(self) -> None:
        source = (ROOT / "activation_harness.py").read_text()
        run_body = source.split("def command_run", 1)[1].split("def command_build", 1)[0]
        self.assertNotIn("contract_target_invariant()", run_body)
        self.assertIn('"HARNESS_CONTRACT_REF": contract_ref or corpus.name', source)
        self.assertIn('run.add_argument("--contract-ref")', source)
        self.assertIn('"tested_corpus_path"', run_body)
        self.assertIn('"tested_contract_ref"', run_body)

    def test_sandbox_subject_and_validator_are_version_dynamic(self) -> None:
        source = (ROOT / "activation_sandbox.py").read_text()
        self.assertIn("HARNESS_CONTRACT_REF", source)
        self.assertIn("ACTIVATION-SUBJECT/v2", source)
        self.assertIn("select_contract_descriptor", source)
        self.assertIn('descriptor.get("validator")', source)
        self.assertIn('"contract_ref": CONTRACT_REF', source)

    def test_runtime_compose_mounts_history_read_only_for_both_services(self) -> None:
        compose = Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/compose.yaml").read_text()
        self.assertEqual(compose.count("/runtime/corpus-history:ro,Z"), 2)
        self.assertEqual(compose.count("ACTIVE_WITNESS_CONTRACT_STATE:"), 2)

    def test_runtime_active_state_resolution_is_confined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            history = base / "history"
            history.mkdir()
            selected = history / "v-good"
            selected.mkdir()
            state = base / "active.json"
            state.write_text(json.dumps({"directory_name": "v-good"}))
            env = {
                "CORPUS_DIR": str(base / "fallback"),
                "CORPUS_HISTORY_DIR": str(history),
                "ACTIVE_WITNESS_CONTRACT_STATE": str(state),
            }
            with patch.dict(os.environ, env, clear=False):
                self.assertEqual(runtime_config.active_corpus_dir(), selected.resolve())
            state.write_text(json.dumps({"directory_name": "../escape"}))
            with patch.dict(os.environ, env, clear=False):
                self.assertEqual(runtime_config.active_corpus_dir(), base / "fallback")

    def test_runtime_mutation_only_occurs_in_explicit_actions(self) -> None:
        source = (ROOT / "contract_control.py").read_text()
        before_activate = source.split("def command_activate", 1)[0]
        self.assertNotIn("restart_and_health(audit)", before_activate)
        self.assertIn("def command_rollback", source)
        self.assertIn("ROLLBACK_ACTIVE_WITNESS_CONTRACT", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
