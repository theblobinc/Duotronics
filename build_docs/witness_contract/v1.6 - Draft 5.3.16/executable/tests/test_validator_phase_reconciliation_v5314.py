#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "executable/validators/validate_draft5_3_14_corpus.py"
SPEC = importlib.util.spec_from_file_location("validator_phase_reconciliation_v5314", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class ValidatorPhaseReconciliationV5314Tests(unittest.TestCase):
    def test_descriptor_required_phase_omitted_from_runner_is_missing(self):
        summary = validator.reconcile_required_phases(
            ["descriptor", "new_required_phase"],
            [{"name": "descriptor", "status": "passed", "required": True}],
        )
        self.assertEqual(summary["required_missing"], ["new_required_phase"])
        self.assertFalse(summary["all_required_passed"])

    def test_required_skip_is_computed(self):
        summary = validator.reconcile_required_phases(
            ["descriptor", "hash_closure"],
            [
                {"name": "descriptor", "status": "passed", "required": True},
                {"name": "hash_closure", "status": "skipped", "required": True},
            ],
        )
        self.assertEqual(summary["required_skipped"], ["hash_closure"])
        self.assertFalse(summary["all_required_passed"])

    def test_duplicate_required_identifier_is_rejected(self):
        summary = validator.reconcile_required_phases(
            ["descriptor", "descriptor"],
            [{"name": "descriptor", "status": "passed", "required": True}],
        )
        self.assertEqual(summary["required_duplicates"], ["descriptor"])
        self.assertFalse(summary["all_required_passed"])

    def test_intentional_hang_kills_descendant_group_and_records_diagnostics(self):
        result = validator.run_phase_isolated("__validator_intentional_hang", True, timeout_seconds=0.15)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["timed_out"])
        self.assertGreater(result["worker_pid"], 0)
        self.assertGreater(result["worker_process_group"], 0)
        self.assertIsNotNone(result["worker_exit_code"])
        self.assertGreaterEqual(result["stdout_bytes"], 0)
        self.assertGreaterEqual(result["stderr_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
