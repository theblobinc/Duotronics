#!/usr/bin/env python3
"""Strict 5.3.18 TLA runner: inherited manifest plus authority-domain isolation."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT_RUNNER = ROOT / "executable/formal/run_tla_model_check.py"
MODULE = "AuthorityDomainV5318"
SPEC = ROOT / f"formal/tlaplus/{MODULE}.tla"
CFG = ROOT / f"formal/tlaplus/{MODULE}.cfg"


def locate_tlc() -> Path | None:
    candidates = []
    if os.environ.get("TLA2TOOLS_JAR"):
        candidates.append(Path(os.environ["TLA2TOOLS_JAR"]))
    candidates.extend([ROOT / "tools/tla2tools.jar", ROOT / "tools/tla2tools-1.8.0.jar"])
    return next((path for path in candidates if path.is_file()), None)


def extension_static_errors() -> list[str]:
    errors = []
    if not SPEC.is_file():
        errors.append(f"missing spec: {SPEC.relative_to(ROOT)}")
        return errors
    if not CFG.is_file():
        errors.append(f"missing config: {CFG.relative_to(ROOT)}")
        return errors
    spec = SPEC.read_text(encoding="utf-8")
    cfg = CFG.read_text(encoding="utf-8")
    for token in (f"MODULE {MODULE}", "Spec ==", "AllGatesBeforeActive ==", "NoSandboxPromotion ==", "TypeInvariant ==", "===="):
        if token not in spec:
            errors.append(f"spec missing {token}")
    for token in ("SPECIFICATION Spec", "AllGatesBeforeActive", "NoSandboxPromotion", "TypeInvariant"):
        if token not in cfg:
            errors.append(f"config missing {token}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["advisory", "strict"], default="advisory")
    parser.add_argument("--module", default="all")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    run_parent = args.module != MODULE
    parent_report = None
    parent_code = 0
    if run_parent:
        parent_argv = [sys.executable, str(PARENT_RUNNER), "--mode", args.mode, "--json", "--timeout", str(args.timeout)]
        if args.module != "all":
            parent_argv.extend(["--module", args.module])
        parent = subprocess.run(
            parent_argv,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=max(120, args.timeout * 20),
            check=False,
        )
        parent_code = parent.returncode
        try:
            parent_report = json.loads(parent.stdout)
        except json.JSONDecodeError:
            parent_report = {
                "status": "invalid_parent_report",
                "stdout_tail": parent.stdout[-4000:],
                "stderr_tail": parent.stderr[-4000:],
            }

    run_extension = args.module in {"all", MODULE}
    errors = extension_static_errors() if run_extension else []
    jar = locate_tlc()
    extension = {"module": MODULE, "static_errors": errors, "return_code": 0}
    if run_extension and not errors:
        if jar:
            with tempfile.TemporaryDirectory(prefix="tlc-v5318-") as metadir:
                command = [
                    "java", "-cp", str(jar), "tlc2.TLC",
                    "-deadlock", "-metadir", metadir,
                    "-config", CFG.name, MODULE,
                ]
                try:
                    proc = subprocess.run(
                        command,
                        cwd=SPEC.parent,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        timeout=args.timeout,
                        check=False,
                    )
                    extension.update({
                        "return_code": proc.returncode,
                        "command": command,
                        "output_tail": proc.stdout[-4000:],
                    })
                except subprocess.TimeoutExpired:
                    extension.update({
                        "return_code": 124,
                        "command": command,
                        "output_tail": f"TLC timed out after {args.timeout} seconds",
                    })
        elif args.mode == "strict":
            extension.update({"return_code": 2, "output_tail": "TLC unavailable"})
    elif errors:
        extension["return_code"] = 1

    passed = parent_code == 0 and extension["return_code"] == 0
    modules = []
    if parent_report:
        modules.extend(parent_report.get("modules_checked", []))
    if run_extension:
        modules.append(MODULE)
    report = {
        "schema_version": "tla_model_check_result/v1.1-5.3.18",
        "mode": args.mode,
        "status": "pass" if passed else "fail",
        "tlc_available": jar is not None,
        "tlc_jar": str(jar) if jar else None,
        "modules_checked": modules,
        "parent": parent_report,
        "extension": extension,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("TLA 5.3.18 validation status:", report["status"])
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
