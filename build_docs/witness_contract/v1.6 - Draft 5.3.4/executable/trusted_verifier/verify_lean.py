#!/usr/bin/env python3
"""Trusted-domain verifier-result producer for the governed OCI image.

The Lean inspector is a separately built trusted executable.  Submitted code
cannot select it, its arguments, its profile, its signing key, or its result
directory.  The only accepted final result is canonical, bounded, and signed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
from proof_authority import AtomicResultPublisher, canonical_bytes, canonical_json_loads, sha256_bytes, sha256_file  # noqa: E402

PROFILE = Path("/input/control/effective-profile.json")
INSPECTOR = Path("/opt/witness-authority/bin/inspect-lean")
INVOCATION = Path("/input/control/effective-sandbox-invocation.json")
MAX_INPUT = 1024 * 1024


def read_canonical(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) > MAX_INPUT:
        raise ValueError("canonical input is oversized")
    value = canonical_json_loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("canonical input root is not an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--result-dir", required=True)
    args = parser.parse_args()
    request_path = Path(args.request)
    result_directory = Path(args.result_dir)
    request = read_canonical(request_path)
    profile = read_canonical(PROFILE)
    invocation = read_canonical(INVOCATION)
    if request.get("schema_version") != "wc_lean_verifier_request/v2":
        return 64
    for executable, field in ((INSPECTOR, "verifier_executable_sha256"), (Path("/opt/lean/bin/lean"), "lean_executable_sha256"), (Path("/opt/lean/bin/lake"), "lake_executable_sha256")):
        if not executable.is_file() or sha256_file(executable) != profile[field]:
            return 65
    started = datetime.now(timezone.utc).isoformat()
    minimal_environment = {"HOME": "/nonexistent", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "SOURCE_DATE_EPOCH": "0", "LEAN_ABORT_ON_PANIC": "1"}
    try:
        process = subprocess.run([str(INSPECTOR), "--request", str(request_path), "--source", "/input/source", "--generated", "/input/generated", "--handoff", "/handoff"], text=True, capture_output=True, timeout=600, env=minimal_environment, cwd="/work")
    except subprocess.TimeoutExpired:
        return 124
    if len(process.stdout.encode("utf-8")) > MAX_INPUT or len(process.stderr.encode("utf-8")) > MAX_INPUT:
        return 66
    try:
        inspection = canonical_json_loads(process.stdout)
    except Exception:
        return 67
    required = {"declaration_found", "declaration_type_matches", "expected_type_expression_hash", "actual_type_expression_hash", "direct_dependencies", "transitive_dependencies_root", "axiom_set", "axiom_set_sha256", "forbidden_axiom_set", "sorry_ax_present", "unsafe_dependency_present", "opaque_dependency_policy_result"}
    if not isinstance(inspection, dict) or not required.issubset(inspection):
        return 68
    finished = datetime.now(timezone.utc).isoformat()
    status = "passed" if process.returncode == 0 and inspection["declaration_found"] and inspection["declaration_type_matches"] and not inspection["sorry_ax_present"] and not inspection["unsafe_dependency_present"] and not inspection["forbidden_axiom_set"] else "failed"
    unsigned = {
        "schema_version": "wc_lean_verifier_result/v2", "status": status,
        "request_id": request["request_id"], "request_sha256": sha256_bytes(canonical_bytes(request)),
        "compiler_profile_id": request["compiler_profile_id"], "claim_content_sha256": request["claim_content_sha256"],
        "theorem_statement_sha256": request["theorem_statement_sha256"], "proof_artifact_sha256": request["proof_artifact_sha256"],
        "immutable_snapshot_id": request["immutable_snapshot_id"], "immutable_snapshot_tree_sha256": request["immutable_snapshot_tree_sha256"],
        "generated_binding_module_sha256": request["generated_binding_module_sha256"],
        "lake_executable_sha256": profile["lake_executable_sha256"], "lean_executable_sha256": profile["lean_executable_sha256"],
        "lean_stdlib_tree_sha256": profile["lean_stdlib_tree_sha256"], "dependency_closure_sha256": profile["dependency_closure_sha256"],
        "oci_image_digest": profile["oci_image_digest"], "oci_runtime_sha256": profile["oci_runtime_sha256"],
        "oci_runtime_version": profile["oci_runtime_version"], "verifier_executable_sha256": profile["verifier_executable_sha256"],
        "sandbox_policy_sha256": profile["sandbox_policy_sha256"], "effective_sandbox_invocation_sha256": sha256_bytes(canonical_bytes(invocation)),
        "theorem_declaration": request["theorem_name"], **{field: inspection[field] for field in required},
        "normalization_policy": "lean_isDefEq_reducibility_regular/v1", "build_from_source": True,
        "prebuilt_artifacts_used": False, "warnings_as_errors": True, "exit_status": process.returncode,
        "timeout_status": "completed", "execution_started_at": started, "execution_finished_at": finished,
        "verifier_result_signer_key_id": profile["verifier_result_signer_key_id"],
    }
    # This file is a trusted-domain inspection, not the final authority result.
    # A separate protected host authority signs and atomically publishes the
    # final result after rechecking the invocation and governed profile.
    publisher = AtomicResultPublisher(
        result_directory, expected_uid=os.getuid(), create=False,
        final_name="verifier-inspection.json",
    )
    publisher.publish_unsigned(unsigned)
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
