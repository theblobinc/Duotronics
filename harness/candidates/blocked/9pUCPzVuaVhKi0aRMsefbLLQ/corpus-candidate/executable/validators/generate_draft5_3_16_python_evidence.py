#!/usr/bin/env python3
"""Generate per-interpreter evidence and deterministically merge Draft 5.3.16."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "validation/python_matrix/draft5_3_16"
MATRIX_PATH = ROOT / "DRAFT5_3_16_PYTHON_MATRIX_VALIDATION.json"
COUNTS_PATH = ROOT / "DRAFT5_3_16_REGRESSION_COUNTS.json"
SUMMARY_PATH = ROOT / "DRAFT5_3_16_VALIDATION_SUMMARY.txt"
METADATA_PATH = ROOT / "PACKAGE_METADATA_v1_6_draft_5_3_16.json"
TARGETS = ("3.12", "3.13")

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(path: Path) -> str:
    return hashlib.shake_256(path.read_bytes()).hexdigest(64)


def major_minor(version: str) -> str:
    components = version.split(".")
    if len(components) < 2 or not all(item.isdigit() for item in components[:2]):
        raise ValueError(f"invalid Python version: {version}")
    return ".".join(components[:2])


def evidence_path(target: str) -> Path:
    return EVIDENCE_DIR / f"python_{target.replace('.', '_')}.json"


def unavailable_path(target: str) -> Path:
    return EVIDENCE_DIR / f"unavailable_{target.replace('.', '_')}.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")



def _run_suite_direct(*, development_mode: bool) -> dict[str, Any]:
    command = [sys.executable]
    if development_mode:
        command.extend(["-X", "dev", "-W", "error"])
    command.append("executable/validators/run_unittest_structured.py")
    process = subprocess.Popen(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    try:
        stdout, stderr = process.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        raise SystemExit("structured regression suite exceeded its bounded timeout")
    marker = re.search(r"^WC_UNITTEST_RESULT=(\{.*\})$", stdout, re.MULTILINE)
    if process.returncode != 0 or marker is None:
        raise SystemExit(f"structured regression suite failed:\n{stdout}\n{stderr}")
    structured = json.loads(marker.group(1))
    warning_lines = [
        line for line in (stdout + "\n" + stderr).splitlines()
        if re.search(r"\b(?:ResourceWarning|DeprecationWarning|RuntimeWarning|UserWarning|SyntaxWarning|FutureWarning|ImportWarning|UnicodeWarning|BytesWarning|EncodingWarning):", line)
    ]
    if warning_lines:
        raise SystemExit(f"warning output is forbidden: {warning_lines}")
    if structured["tests_passed"] != structured["tests_discovered"] or structured["tests_skipped"] != 0:
        raise SystemExit("structured regression counts are not clean")
    return {
        "command": command, **structured, "warning_output_lines": warning_lines,
        "stdout_shake256_512": hashlib.shake_256(stdout.encode("utf-8")).hexdigest(64),
        "stderr_shake256_512": hashlib.shake_256(stderr.encode("utf-8")).hexdigest(64),
    }

def record_current_interpreter() -> Path:
    normal = _run_suite_direct(development_mode=False)
    warning_free = _run_suite_direct(development_mode=True)
    if normal["python_version"] != warning_free["python_version"]:
        raise SystemExit("normal and warning-as-error runs used different interpreters")
    if normal["tests_discovered"] != warning_free["tests_discovered"] or normal["tests_passed"] != warning_free["tests_passed"]:
        raise SystemExit("normal and warning-as-error test counts differ")
    target = major_minor(normal["python_version"])
    if target not in TARGETS:
        raise SystemExit(f"Python {target} is outside the Draft 5.3.16 target matrix")
    record = {
        "schema_version": "python_interpreter_validation/v1",
        "package_version": "v1.6-draft-5.3.16",
        "target_python_version": target,
        "python_version": normal["python_version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count_source": "unittest.TestResult",
        "warning_detection": "independent_of_count_extraction",
        "tests_discovered": normal["tests_discovered"],
        "tests_run": normal["tests_run"],
        "tests_passed": normal["tests_passed"],
        "tests_failed": normal["tests_failed"],
        "tests_errored": normal["tests_errored"],
        "tests_skipped": normal["tests_skipped"],
        "duplicate_test_ids": normal["duplicate_test_ids"],
        "normal_status": "passed",
        "development_warnings_as_errors_status": "passed",
        "warning_output_lines": warning_free["warning_output_lines"],
        "normal_command": normal["command"],
        "warning_free_command": warning_free["command"],
        "normal_stdout_shake256_512": normal["stdout_shake256_512"],
        "normal_stderr_shake256_512": normal["stderr_shake256_512"],
        "development_stdout_shake256_512": warning_free["stdout_shake256_512"],
        "development_stderr_shake256_512": warning_free["stderr_shake256_512"],
    }
    path = evidence_path(target)
    write_json(path, record)
    unavailable_path(target).unlink(missing_ok=True)
    return path


def mark_unavailable(target: str, reason: str) -> Path:
    target = major_minor(target)
    if target not in TARGETS:
        raise SystemExit(f"unavailable target is outside {TARGETS}: {target}")
    if evidence_path(target).is_file():
        raise SystemExit(f"cannot mark validated Python {target} unavailable")
    record = {
        "schema_version": "python_interpreter_unavailable/v1",
        "package_version": "v1.6-draft-5.3.16",
        "target_python_version": target,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "interpreter_unavailable",
        "reason": reason,
        "authority_effect": "no_current_revision_execution_claim",
    }
    path = unavailable_path(target)
    write_json(path, record)
    return path


def load_records(prefix: str) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(EVIDENCE_DIR.glob(f"{prefix}_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        records.append((path, record))
    return records


def merge() -> dict[str, Any]:
    runs_by_target: dict[str, tuple[Path, dict[str, Any]]] = {}
    unavailable_by_target: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path, record in load_records("python"):
        target = record.get("target_python_version")
        if target not in TARGETS or major_minor(record.get("python_version", "")) != target or target in runs_by_target:
            raise SystemExit(f"invalid or duplicate per-interpreter validation evidence: {path}")
        runs_by_target[target] = (path, record)
    for path, record in load_records("unavailable"):
        target = record.get("target_python_version")
        if target not in TARGETS or record.get("status") != "interpreter_unavailable" or target in unavailable_by_target:
            raise SystemExit(f"invalid or duplicate unavailable-interpreter evidence: {path}")
        unavailable_by_target[target] = (path, record)
    overlap = set(runs_by_target) & set(unavailable_by_target)
    if overlap:
        raise SystemExit(f"validated and unavailable Python targets overlap: {sorted(overlap)}")
    if set(runs_by_target) | set(unavailable_by_target) != set(TARGETS):
        raise SystemExit("every target Python major/minor must appear exactly once")
    if not runs_by_target:
        raise SystemExit("at least one validated interpreter record is required")

    run_counts = {
        (record["tests_discovered"], record["tests_run"], record["tests_passed"], record["tests_failed"], record["tests_errored"], record["tests_skipped"])
        for _, record in runs_by_target.values()
    }
    if len(run_counts) != 1:
        raise SystemExit("validated Python interpreters disagree on regression totals")

    runs = []
    unavailable_runs = []
    evidence_set = []
    generated_times = []
    for target in TARGETS:
        if target in runs_by_target:
            path, record = runs_by_target[target]
            relative = path.relative_to(ROOT).as_posix()
            entry = {**record, "evidence_file": relative, "evidence_shake256_512": digest(path)}
            runs.append(entry)
        else:
            path, record = unavailable_by_target[target]
            relative = path.relative_to(ROOT).as_posix()
            entry = {**record, "evidence_file": relative, "evidence_shake256_512": digest(path)}
            unavailable_runs.append(entry)
        evidence_set.append({"path": relative, "shake256_512": digest(path), "target_python_version": target})
        generated_times.append(record["generated_at"])

    matrix = {
        "schema_version": "python_matrix_validation/v4",
        "package_version": "v1.6-draft-5.3.16",
        "generated_at": max(generated_times),
        "count_source": "unittest.TestResult",
        "warning_detection": "independent_of_count_extraction",
        "assembly": "merge_hash_covered_per_interpreter_records",
        "target_python_versions": list(TARGETS),
        "validated_python_versions": [item["python_version"] for item in runs],
        "unavailable_python_versions": [item["target_python_version"] for item in unavailable_runs],
        "runs": runs,
        "unavailable_runs": unavailable_runs,
        "evidence_set_shake256_512": hashlib.shake_256(canonical_bytes(evidence_set)).hexdigest(64),
        "overall_status": "passed" if not unavailable_runs else "passed_with_declared_environment_qualification",
    }
    write_json(MATRIX_PATH, matrix)

    representative = runs[0]
    counts = {
        "schema_version": "draft5_3_16_regression_counts/v1",
        "package_version": "v1.6-draft-5.3.16",
        "generated_at": matrix["generated_at"],
        "draft5_3_15_baseline_tests_discovered": 303,
        "target_python_versions": list(TARGETS),
        "validated_python_versions": matrix["validated_python_versions"],
        "unavailable_python_versions": matrix["unavailable_python_versions"],
        "count_source": "unittest.TestResult",
        "tests_discovered": representative["tests_discovered"],
        "tests_run": representative["tests_run"],
        "tests_passed": representative["tests_passed"],
        "tests_failed": representative["tests_failed"],
        "tests_errored": representative["tests_errored"],
        "tests_skipped": representative["tests_skipped"],
        "duplicate_test_ids": representative["duplicate_test_ids"],
        "warning_output_lines": representative["warning_output_lines"],
        "python_matrix_shake256_512": digest(MATRIX_PATH),
    }
    write_json(COUNTS_PATH, counts)
    if METADATA_PATH.is_file():
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        metadata["target_python_versions"] = matrix["target_python_versions"]
        metadata["validated_python_versions"] = matrix["validated_python_versions"]
        metadata["unavailable_python_versions"] = matrix["unavailable_python_versions"]
        write_json(METADATA_PATH, metadata)
    unavailable_text = ", ".join(matrix["unavailable_python_versions"]) or "none"
    summary = "\n".join([
        "Duotronic Witness Contract v1.6 Draft 5.3.16 — Generated Validation Summary",
        "Status: non-authoritative portable conformance corpus; permanently not frozen",
        "Target Python versions: 3.12 and 3.13",
        f"Validated Python versions: {', '.join(matrix['validated_python_versions'])}",
        f"Unavailable Python versions: {unavailable_text}",
        "Evidence assembly: merge of one hash-covered record per interpreter target",
        "Count source: unittest.TestResult",
        "Draft 5.3.15 baseline: 303 tests discovered",
        f"Tests discovered: {counts['tests_discovered']}",
        f"Tests passed: {counts['tests_passed']}",
        f"Tests skipped: {counts['tests_skipped']}",
        "Warning output lines: 0",
        "Theorem authority: disabled",
        "Promotion authority: disabled",
        "Release authority: disabled",
        "External activation gates complete: 0 of 8",
        "",
    ])
    SUMMARY_PATH.write_text(summary, encoding="utf-8")
    return matrix


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-only", action="store_true")
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--mark-unavailable")
    parser.add_argument("--reason", default="interpreter was not present in the validation environment")
    arguments = parser.parse_args()
    selected = sum((arguments.record_only, arguments.merge_only, arguments.mark_unavailable is not None))
    if selected > 1:
        parser.error("choose only one of --record-only, --merge-only, or --mark-unavailable")
    if arguments.mark_unavailable is not None:
        path = mark_unavailable(arguments.mark_unavailable, arguments.reason)
        print(path.relative_to(ROOT).as_posix())
        return 0
    if not arguments.merge_only:
        path = record_current_interpreter()
        print(path.relative_to(ROOT).as_posix())
    if not arguments.record_only:
        print(json.dumps(merge(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
