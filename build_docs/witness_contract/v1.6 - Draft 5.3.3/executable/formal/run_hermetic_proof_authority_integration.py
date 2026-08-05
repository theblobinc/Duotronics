#!/usr/bin/env python3
"""Run genuine Lean cases through the approved Draft 5.3.3 execution image."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))

from proof_authority import load_production_authority_service  # noqa: E402


def write_project(root: Path, source: str, toolchain: str, lakefile: str = "import Lake\npackage submitted\n") -> None:
    (root / "Proof.lean").write_text(source, encoding="utf-8")
    (root / "lean-toolchain").write_text(toolchain + "\n", encoding="utf-8")
    (root / "lakefile.lean").write_text(lakefile, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-root", default="/etc/witness-authority")
    parser.add_argument("--profile")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    config_root = Path(args.config_root)
    try:
        service = load_production_authority_service(config_root)
    except Exception as error:
        result = {
            "schema_version": "hermetic_lean_integration_result/v1",
            "status": "strict_fail_authority_config_unavailable",
            "real_lean_executed": False,
            "authority_activation_permitted": False,
            "error": str(error),
            "cases": [],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    profile_id = args.profile or next(iter(service.profiles))
    toolchain = service.profiles[profile_id].toolchain
    cases = [
        ("valid", "theorem t : True := by trivial\n", "True", "t", True),
        ("statement_mismatch", "theorem t : True := by trivial\n", "False", "t", False),
        ("comment_only", "/- theorem ghost : False := by contradiction -/\n", "False", "ghost", False),
        ("sorry_ax", "theorem t : True := by\n  exact sorry\n", "True", "t", False),
        ("attributed_axiom", "axiom unsafeWitness : False\ntheorem t : False := unsafeWitness\n", "False", "t", False),
        ("malicious_lakefile", "theorem t : True := by trivial\n", "True", "t", True),
    ]
    results = []
    all_expected = True
    for name, source, statement, theorem, expected_pass in cases:
        with tempfile.TemporaryDirectory(prefix=f"wc-real-lean-{name}-") as directory:
            root = Path(directory)
            lakefile = "import Lake\npackage submitted\n" if name != "malicious_lakefile" else "import Lake\n-- submitted metadata must never execute\npackage hostile\n"
            write_project(root, source, toolchain, lakefile)
            record = service.verify(
                compiler_profile_id=profile_id,
                claim_id=f"integration:{name}",
                canonical_claim={"case": name, "statement": statement},
                theorem_statement=statement,
                theorem_name=theorem,
                proof_artifact=root / "Proof.lean",
                source_root=root,
            )
            observed = record["result"] == "passed"
            matches = observed == expected_pass
            all_expected = all_expected and matches
            results.append({"case": name, "expected_pass": expected_pass, "observed_pass": observed, "matches": matches})
    with tempfile.TemporaryDirectory(prefix="wc-real-lean-stale-olean-") as directory:
        root = Path(directory)
        write_project(root, "theorem t : True := by trivial\n", toolchain)
        (root / "Proof.olean").write_bytes(b"forbidden-prebuilt-output")
        rejected = False
        try:
            service.verify(
                compiler_profile_id=profile_id, claim_id="integration:stale-olean",
                canonical_claim={"case": "stale-olean"}, theorem_statement="True", theorem_name="t",
                proof_artifact=root / "Proof.lean", source_root=root,
            )
        except ValueError:
            rejected = True
        all_expected = all_expected and rejected
        results.append({"case": "stale_olean", "expected_rejection": True, "observed_rejection": rejected, "matches": rejected})
    result = {
        "schema_version": "hermetic_lean_integration_result/v1",
        "status": "passed" if all_expected else "failed",
        "real_lean_executed": True,
        "authority_activation_permitted": all_expected,
        "compiler_profile_id": profile_id,
        "cases": results,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all_expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
