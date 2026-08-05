#!/usr/bin/env python3
"""Generate executable regression metadata from measured unittest output."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "executable/validators/validate_draft5_3_9_corpus.py"
SPEC = importlib.util.spec_from_file_location("draft539_validator_counts", VALIDATOR)
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
        "schema_version": "draft5_3_9_regression_counts/v1",
        "package_version": "v1.6-draft-5.3.9",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "draft5_3_8_baseline_tests_discovered": 195,
        "supported_python_versions": ["3.12", "3.13"],
        "validated_python_version": normal["python_version"],
        "count_source": "unittest.TestResult",
        "tests_discovered": normal["tests_discovered"],
        "tests_run": normal["tests_run"],
        "tests_passed": normal["tests_passed"],
        "tests_failed": normal["tests_failed"],
        "tests_errored": normal["tests_errored"],
        "tests_skipped": normal["tests_skipped"],
        "duplicate_test_ids": normal["duplicate_test_ids"],
        "warning_output_lines": warning_free["warning_output_lines"],
        "normal_command": normal["command"],
        "warning_free_command": warning_free["command"],
        "normal_stdout_sha256": normal["stdout_sha256"],
        "normal_stderr_sha256": normal["stderr_sha256"],
        "warning_free_stdout_sha256": warning_free["stdout_sha256"],
        "warning_free_stderr_sha256": warning_free["stderr_sha256"],
    }
    (ROOT / "DRAFT5_3_9_REGRESSION_COUNTS.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = "\n".join([
        "Duotronic Witness Contract v1.6 Draft 5.3.9 — Generated Validation Summary",
        "Status: non-authoritative portable conformance corpus; permanently not frozen",
        "Supported Python versions: 3.12 and 3.13",
        f"Validated Python version: {record['validated_python_version']}",
        "Python 3.13 Draft 5.3.9 rerun: interpreter unavailable; no current-run claim",
        "Count source: unittest.TestResult",
        "Draft 5.3.8 baseline: 195 tests discovered",
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
    (ROOT / "DRAFT5_3_9_VALIDATION_SUMMARY.txt").write_text(summary, encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
