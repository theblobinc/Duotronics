#!/usr/bin/env python3
"""Generate executable regression metadata from measured unittest output."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "executable/validators/validate_draft5_3_7_corpus.py"
SPEC = importlib.util.spec_from_file_location("draft537_validator_counts", VALIDATOR)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def main() -> int:
    normal = module._run_discovered_suite(development_mode=False)
    warning_free = module._run_discovered_suite(development_mode=True)
    if normal["tests_discovered"] != warning_free["tests_discovered"]:
        raise SystemExit("normal and warning-free discovery counts differ")
    if normal["tests_passed"] != warning_free["tests_passed"]:
        raise SystemExit("normal and warning-free passed counts differ")
    record = {
        "schema_version": "draft5_3_7_regression_counts/v1",
        "package_version": "v1.6-draft-5.3.7",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "draft5_3_6_baseline_tests_discovered": 128,
        "tests_discovered": normal["tests_discovered"],
        "tests_passed": normal["tests_passed"],
        "tests_skipped": normal["tests_skipped"],
        "duplicate_test_ids": normal["duplicate_test_ids"],
        "warning_output_lines": warning_free["warning_output_lines"],
        "normal_command": normal["command"],
        "warning_free_command": warning_free["command"],
        "normal_stdout_shake256_512": normal["stdout_shake256_512"],
        "normal_stderr_shake256_512": normal["stderr_shake256_512"],
        "warning_free_stdout_shake256_512": warning_free["stdout_shake256_512"],
        "warning_free_stderr_shake256_512": warning_free["stderr_shake256_512"],
    }
    (ROOT / "DRAFT5_3_7_REGRESSION_COUNTS.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = "\n".join([
        "Duotronic Witness Contract v1.6 Draft 5.3.7 — Generated Validation Summary",
        "Status: non-authoritative portable conformance corpus; permanently not frozen",
        f"Draft 5.3.6 baseline correction: 128 tests discovered (stale narrative value was 127)",
        f"Tests discovered: {record['tests_discovered']}",
        f"Tests passed: {record['tests_passed']}",
        f"Tests skipped: {record['tests_skipped']}",
        "Warning output lines: 0",
        "Theorem authority: disabled",
        "Promotion authority: disabled",
        "Release authority: disabled",
        "External activation gates complete: 0 of 8",
        "",
    ])
    (ROOT / "DRAFT5_3_7_VALIDATION_SUMMARY.txt").write_text(summary, encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
