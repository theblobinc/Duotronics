#!/usr/bin/env python3
"""Strict 5.3.18 Lean runner: inherited corpus plus the authority-domain extension."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT_RUNNER = ROOT / "executable/formal/run_lean_build.py"
EXTENSION = ROOT / "formal/lean4/AuthorityDomainV5318.lean"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["advisory", "strict"], default="advisory")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    parent = subprocess.run(
        [sys.executable, str(PARENT_RUNNER), "--mode", args.mode, "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=360,
        check=False,
    )
    try:
        parent_report = json.loads(parent.stdout)
    except json.JSONDecodeError:
        parent_report = {
            "status": "invalid_parent_report",
            "stdout_tail": parent.stdout[-4000:],
            "stderr_tail": parent.stderr[-4000:],
        }

    source = EXTENSION.read_text(encoding="utf-8") if EXTENSION.is_file() else ""
    code_only = re.sub(r"/-.*?-/", "", source, flags=re.S)
    code_only = re.sub(r"--.*", "", code_only)
    forbidden = [
        marker for marker in ("sorry", "admit")
        if re.search(rf"\b{marker}\b", code_only)
    ]
    axioms = re.findall(r"^\s*axiom\s+([A-Za-z0-9_.]+)", code_only, flags=re.M)

    lake = shutil.which("lake")
    extension_command = [
        lake or "lake",
        "env",
        "lean",
        "-o",
        "/tmp/AuthorityDomainV5318.olean",
        str(EXTENSION),
    ]
    if not EXTENSION.is_file():
        extension = {"status": "missing_extension", "exit_code": 2}
    elif forbidden or axioms:
        extension = {
            "status": "failed_static_scan",
            "exit_code": 1,
            "forbidden_markers": forbidden,
            "axioms": axioms,
        }
    elif not lake:
        extension = {
            "status": "advisory_pass_lake_unavailable" if args.mode == "advisory" else "strict_fail_lake_unavailable",
            "exit_code": 0 if args.mode == "advisory" else 2,
        }
    else:
        proc = subprocess.run(
            extension_command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
            env={
                **os.environ,
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "TZ": "UTC",
                "SOURCE_DATE_EPOCH": "0",
            },
        )
        extension = {
            "status": "passed" if proc.returncode == 0 else "failed_lean_build",
            "exit_code": proc.returncode,
            "command": extension_command,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "theorems": re.findall(r"^\s*theorem\s+([A-Za-z0-9_.]+)", code_only, flags=re.M),
            "forbidden_markers": forbidden,
            "axioms": axioms,
        }

    passed = parent.returncode == 0 and extension["exit_code"] == 0
    report = {
        "schema_version": "lean_build_result/v1.1-5.3.18",
        "mode": args.mode,
        "status": "passed" if passed else "failed",
        "parent_runner": str(PARENT_RUNNER.relative_to(ROOT)),
        "extension_file": str(EXTENSION.relative_to(ROOT)),
        "parent": parent_report,
        "extension": extension,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Lean 5.3.18 build status:", report["status"])
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
