#!/usr/bin/env python3
"""Repeat the complete Draft 5.3.15 validator with bounded outer orchestration."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "executable/validators/validate_draft5_3_15_corpus.py"
REPORT_PATH = ROOT / "DRAFT5_3_15_VALIDATION_REPORT.json"
DESCRIPTOR_PATH = ROOT / "CANONICAL_CORPUS_v1_6_draft_5_3_15.json"
DESCRIPTOR = json.loads(DESCRIPTOR_PATH.read_text(encoding="utf-8"))
REQUIRED_PHASE_COUNT = len(DESCRIPTOR["required_validation_phases"])
OPTIONAL_PHASE_COUNT = len(DESCRIPTOR["optional_validation_phases"])

SPECIFICATION = importlib.util.spec_from_file_location("draft5315_reliability_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPECIFICATION)
assert SPECIFICATION and SPECIFICATION.loader
sys.modules[SPECIFICATION.name] = VALIDATOR
SPECIFICATION.loader.exec_module(VALIDATOR)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True, help="exact interpreter executable")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument(
        "--maximum-additional-runs", type=int,
        help="checkpoint after at most this many new repetitions; the campaign target is unchanged",
    )
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    if arguments.runs < 1 or arguments.runs > 100:
        parser.error("--runs must be between 1 and 100")

    output = pathlib.Path(arguments.output)
    if output.is_file():
        prior = json.loads(output.read_text(encoding="utf-8"))
        if (
            prior.get("package_version") != "v1.6-draft-5.3.15"
            or prior.get("python_executable") != arguments.python
            or prior.get("requested_repetitions") != arguments.runs
        ):
            raise SystemExit("existing reliability checkpoint does not match this campaign")
        completed_runs = list(prior.get("runs", []))
        started_at_text = prior["started_at"]
        interpreter_version = prior.get("python_version")
    else:
        completed_runs = []
        started_at_text = datetime.now(timezone.utc).isoformat()
        interpreter_version = None

    def write_checkpoint(status: str) -> None:
        evidence = {
            "schema_version": "validator_reliability_evidence/v1",
            "package_version": "v1.6-draft-5.3.15",
            "target_python_version": "3.13" if interpreter_version and interpreter_version.startswith("3.13.") else "3.12" if interpreter_version and interpreter_version.startswith("3.12.") else None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "started_at": started_at_text,
            "python_executable": arguments.python,
            "python_version": interpreter_version,
            "requested_repetitions": arguments.runs,
            "completed_repetitions": len(completed_runs),
            "complete_validator": "executable/validators/validate_draft5_3_15_corpus.py",
            "required_phase_count": REQUIRED_PHASE_COUNT,
            "optional_activation_phase_count": OPTIONAL_PHASE_COUNT,
            "status": status,
            "runs": completed_runs,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    final_sequence = arguments.runs
    if arguments.maximum_additional_runs is not None:
        if arguments.maximum_additional_runs < 1:
            parser.error("--maximum-additional-runs must be positive")
        final_sequence = min(arguments.runs, len(completed_runs) + arguments.maximum_additional_runs)
    for sequence in range(len(completed_runs) + 1, final_sequence + 1):
        print(f"[repetition:start] {sequence}/{arguments.runs}", flush=True)
        process = VALIDATOR._run_bounded_text_command(
            [arguments.python, str(VALIDATOR_PATH), "--bootstrap-reliability"], cwd=ROOT,
            timeout_seconds=900, stage=f"complete-validator-repetition:{sequence}",
            emit_progress=False,
        )
        if process["timed_out"] or process["returncode"] != 0:
            raise SystemExit(
                f"validator repetition {sequence} failed: timeout={process['timed_out']} "
                f"exit={process['returncode']}\n{process['stderr']}"
            )
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        statuses = {status: sum(phase["status"] == status for phase in report["phases"])
                    for status in ("passed", "failed", "skipped")}
        if (
            report.get("overall_status") not in {"passed", "bootstrap_passed_not_publishable"}
            or report.get("all_required_passed") is not True
            or statuses != {"passed": REQUIRED_PHASE_COUNT, "failed": 0, "skipped": OPTIONAL_PHASE_COUNT}
        ):
            raise SystemExit(f"validator repetition {sequence} report is not closed: {statuses}")
        warning_phase = next(
            phase for phase in report["phases"]
            if phase["name"] == "warning_free_regression_execution"
        )
        completed_runs.append({
            "sequence": sequence,
            "duration_seconds": process["duration_seconds"],
            "validator_exit_code": process["returncode"],
            "report_sha256": sha256(REPORT_PATH),
            "required_phases_passed": REQUIRED_PHASE_COUNT,
            "optional_phases_skipped": OPTIONAL_PHASE_COUNT,
            "warning_free_phase_status": warning_phase["status"],
            "capture_backend": process["capture_backend"],
            "bounded_reap": process["bounded_reap"],
            "surviving_descendants": process["surviving_descendants"],
            "parent_capture_descriptors_closed": process["parent_capture_descriptors_closed"],
        })
        interpreter_version = report["phases"][1]["details"]["python"]
        write_checkpoint("in_progress" if sequence < arguments.runs else "passed")
        print(f"[repetition:done] {sequence}/{arguments.runs}", flush=True)

    if len(completed_runs) == arguments.runs:
        write_checkpoint("passed")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
