"""Build and update the staged acceptance report artifact."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "fixtures"
GOLDEN_TRACES_DIR = ROOT / "golden_traces"
META_FIXTURES_DIR = ROOT / "meta_fixtures"
META_GOLDEN_TRACES_DIR = ROOT / "meta_golden_traces"

sys.path.insert(0, str(ROOT))

from harness_lib.schema_versions import ACTIVE_SPEC_TARGET, resolve_schema_snapshot


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _artifact_counts() -> dict[str, int]:
    return {
        "fixture_packs": len(list(FIXTURES_DIR.glob("*.yaml"))),
        "golden_traces": len(list(GOLDEN_TRACES_DIR.glob("*.yaml"))),
        "meta_fixture_packs": len(list(META_FIXTURES_DIR.glob("*.yaml"))),
        "meta_golden_traces": len(list(META_GOLDEN_TRACES_DIR.glob("*.yaml"))),
    }


def _load_report(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_report(path: Path, report: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _read_output_excerpt(path: Path | None, max_lines: int = 40) -> list[str]:
    if path is None or not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-max_lines:]


def _last_non_empty_line(lines: list[str]) -> str | None:
    for line in reversed(lines):
        if line.strip():
            return line.strip()
    return None


def _recompute_summary(report: dict[str, Any], *, forced_status: str | None = None) -> None:
    stages = report.get("stages", {})
    total = len(stages)
    passed = sum(1 for stage in stages.values() if stage.get("status") == "passed")
    failed = sum(1 for stage in stages.values() if stage.get("status") == "failed")
    if forced_status is not None:
        status = forced_status
    elif failed:
        status = "failed"
    elif report.get("finished_at_utc"):
        status = "passed"
    else:
        status = "running"
    report["summary"] = {
        "status": status,
        "total_stages": total,
        "passed_stages": passed,
        "failed_stages": failed,
    }


def _command_string(parts: list[str]) -> str:
    return " ".join(parts).strip()


def command_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    target_schema_version = args.target_schema_version or args.schema_version
    report = {
        "report_schema": "conformance-acceptance-report@v1",
        "generated_at_utc": _timestamp(),
        "finished_at_utc": None,
        "selection": {
            "schema_version": args.schema_version,
            "target_schema_version": target_schema_version,
        },
        "spec_target": dict(ACTIVE_SPEC_TARGET),
        "registry_snapshot": resolve_schema_snapshot(args.schema_version),
        "artifact_counts": _artifact_counts(),
        "stages": {},
    }
    _recompute_summary(report)
    _write_report(path, report)
    return 0


def command_add_stage(args: argparse.Namespace) -> int:
    path = Path(args.path)
    report = _load_report(path)
    output_file = Path(args.output_file) if args.output_file else None
    output_excerpt = _read_output_excerpt(output_file)
    stage = {
        "label": args.label,
        "kind": args.kind,
        "command": args.command,
        "exit_code": args.exit_code,
        "status": "passed" if args.exit_code == 0 else "failed",
        "duration_seconds": args.duration_seconds,
        "recorded_at_utc": _timestamp(),
        "result_summary": _last_non_empty_line(output_excerpt),
        "output_excerpt": output_excerpt,
    }
    if args.pytest_report:
        pytest_report_path = Path(args.pytest_report)
        if pytest_report_path.exists():
            pytest_report = _load_report(pytest_report_path)
            stage["pytest_report"] = pytest_report
            if args.stage_id == "full_suite":
                report["coverage_matrix"] = pytest_report.get("coverage_matrix")
                report["pytest_summary"] = pytest_report.get("summary")
    report.setdefault("stages", {})[args.stage_id] = stage
    _recompute_summary(report)
    _write_report(path, report)
    return 0


def command_finalize(args: argparse.Namespace) -> int:
    path = Path(args.path)
    report = _load_report(path)
    report["finished_at_utc"] = _timestamp()
    _recompute_summary(report, forced_status=args.status)
    _write_report(path, report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--path", required=True)
    init_parser.add_argument("--schema-version", required=True)
    init_parser.add_argument("--target-schema-version")
    init_parser.set_defaults(func=command_init)

    add_stage_parser = subparsers.add_parser("add-stage")
    add_stage_parser.add_argument("--path", required=True)
    add_stage_parser.add_argument("--stage-id", required=True)
    add_stage_parser.add_argument("--label", required=True)
    add_stage_parser.add_argument("--kind", required=True)
    add_stage_parser.add_argument("--exit-code", required=True, type=int)
    add_stage_parser.add_argument("--duration-seconds", required=True, type=int)
    add_stage_parser.add_argument("--command", required=True)
    add_stage_parser.add_argument("--output-file")
    add_stage_parser.add_argument("--pytest-report")
    add_stage_parser.set_defaults(func=command_add_stage)

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--path", required=True)
    finalize_parser.add_argument("--status", choices=("passed", "failed"), required=True)
    finalize_parser.set_defaults(func=command_finalize)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())