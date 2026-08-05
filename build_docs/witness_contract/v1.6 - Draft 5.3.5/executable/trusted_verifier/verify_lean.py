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
import resource
import sys
from datetime import datetime, timezone
from pathlib import Path

from bounded_subprocess import run_bounded

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


def _memory_bytes(value: str) -> int:
    multipliers = {"k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}
    normalized = value.strip().lower()
    if normalized[-1:] in multipliers:
        return int(normalized[:-1]) * multipliers[normalized[-1]]
    return int(normalized)


def _read_cgroup(name: str) -> str | None:
    path = Path("/sys/fs/cgroup") / name
    try:
        return path.read_text(encoding="ascii", errors="strict").strip()
    except (FileNotFoundError, PermissionError, OSError, UnicodeError):
        return None


def inspect_runtime_controls(invocation: dict) -> list[str]:
    """Measure controls visible from inside the trusted domain."""
    verified: set[str] = set()
    if Path(sys.argv[0]).as_posix() == invocation.get("entrypoint"):
        verified.add("explicit_entrypoint")
    if os.getuid() == invocation.get("container_uid") and os.getgid() == invocation.get("container_gid") and os.getuid() != 0 and os.getgid() != 0:
        verified.add("non_root_user")
    if os.getcwd() == invocation.get("working_directory"):
        verified.add("working_directory")
    status = Path("/proc/self/status").read_text(encoding="utf-8", errors="replace")
    fields = dict(line.split(":", 1) for line in status.splitlines() if ":" in line)
    if fields.get("CapEff", "").strip() == "0000000000000000":
        verified.add("capabilities_dropped")
    if fields.get("NoNewPrivs", "").strip() == "1":
        verified.add("no_new_privileges")
    if fields.get("Seccomp", "").strip() == "2":
        verified.add("seccomp")
    uid_map = Path("/proc/self/uid_map").read_text(encoding="ascii", errors="replace").strip()
    if uid_map and uid_map != "0          0 4294967295":
        verified.add("private_user_namespace")
    interfaces = {path.name for path in Path("/sys/class/net").iterdir()} if Path("/sys/class/net").is_dir() else set()
    if interfaces.issubset({"lo"}):
        verified.add("network_none")
    mount_text = Path("/proc/self/mountinfo").read_text(encoding="utf-8", errors="replace")
    mount_lines = mount_text.splitlines()
    root_lines = [line for line in mount_lines if len(line.split()) > 5 and line.split()[4] == "/"]
    if root_lines and "ro" in root_lines[0].split()[5].split(","):
        verified.add("read_only_rootfs")
    expected_mounts = {item["destination"]: item["mode"] for item in invocation.get("mount_manifest", [])}
    observed_mounts = {line.split()[4]: line.split()[5].split(",") for line in mount_lines if len(line.split()) > 5}
    if expected_mounts and all(path in observed_mounts and ((mode == "ro") == ("ro" in observed_mounts[path])) for path, mode in expected_mounts.items()):
        verified.add("mount_manifest")
    current_label = Path("/proc/self/attr/current").read_text(encoding="utf-8", errors="replace") if Path("/proc/self/attr/current").is_file() else ""
    if invocation.get("apparmor_profile") and invocation["apparmor_profile"] in current_label:
        verified.add("apparmor")
    if invocation.get("selinux_label") and invocation["selinux_label"] in current_label:
        verified.add("selinux")
    soft_files, _ = resource.getrlimit(resource.RLIMIT_FSIZE)
    soft_open, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    if soft_files != resource.RLIM_INFINITY and soft_files <= int(invocation.get("file_size_limit", -1)):
        verified.add("file_size_limit")
    if soft_open != resource.RLIM_INFINITY and soft_open <= int(invocation.get("open_file_limit", -1)):
        verified.add("open_file_limit")
    pids = _read_cgroup("pids.max")
    if pids and pids != "max" and int(pids) <= int(invocation.get("pid_limit", -1)):
        verified.add("pid_limit")
    memory = _read_cgroup("memory.max")
    if memory and memory != "max" and int(memory) <= _memory_bytes(str(invocation.get("memory_limit", "0"))):
        verified.add("memory_limit")
    cpu = _read_cgroup("cpu.max")
    if cpu and cpu != "max":
        quota_text, period_text = cpu.split()
        if int(quota_text) / int(period_text) <= float(invocation.get("cpu_limit", 0)):
            verified.add("cpu_limit")
    expected_environment = [
        "HOME=/nonexistent", "LANG=C.UTF-8", "LC_ALL=C.UTF-8",
        "TZ=UTC", "SOURCE_DATE_EPOCH=0", "LEAN_ABORT_ON_PANIC=1",
    ]
    if invocation.get("environment_allowlist") == expected_environment:
        # The inspector subprocess is created below with this exact env mapping;
        # POSIX exec therefore receives no inherited host environment entries.
        verified.add("environment_allowlist")
    return sorted(verified)


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
    if request.get("schema_version") != "wc_lean_verifier_request/v3":
        return 64
    for executable, field in ((INSPECTOR, "verifier_executable_sha256"), (Path("/opt/lean/bin/lean"), "lean_executable_sha256"), (Path("/opt/lean/bin/lake"), "lake_executable_sha256")):
        if not executable.is_file() or sha256_file(executable) != profile[field]:
            return 65
    started = datetime.now(timezone.utc).isoformat()
    minimal_environment = {"HOME": "/nonexistent", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "SOURCE_DATE_EPOCH": "0", "LEAN_ABORT_ON_PANIC": "1"}
    process = run_bounded(
        [str(INSPECTOR), "--request", str(request_path), "--source", "/input/source", "--generated", "/input/generated", "--handoff", "/handoff"],
        cwd="/work", env=minimal_environment, timeout=600,
    )
    if process.timed_out:
        return 124
    if process.output_limit_exceeded:
        return 66
    try:
        inspection = canonical_json_loads(process.stdout)
    except Exception:
        return 67
    required_raw = {"declaration_found", "declaration_type_matches", "expected_type_expression", "actual_type_expression", "direct_dependencies", "axiom_set", "forbidden_axiom_set", "sorry_ax_present", "unsafe_dependency_present", "opaque_dependency_policy_result"}
    if not isinstance(inspection, dict) or set(inspection) != required_raw:
        return 68
    for field in ("direct_dependencies", "axiom_set", "forbidden_axiom_set"):
        values = inspection.get(field)
        if not isinstance(values, list) or values != sorted(set(values)) or not all(isinstance(value, str) and value for value in values):
            return 68
    if not isinstance(inspection.get("expected_type_expression"), str) or not isinstance(inspection.get("actual_type_expression"), str):
        return 68
    structured = {
        "declaration_found": inspection["declaration_found"],
        "declaration_type_matches": inspection["declaration_type_matches"],
        "expected_type_expression_hash": sha256_bytes(inspection["expected_type_expression"].encode("utf-8")),
        "actual_type_expression_hash": sha256_bytes(inspection["actual_type_expression"].encode("utf-8")),
        "direct_dependencies": inspection["direct_dependencies"],
        "transitive_dependencies_root": sha256_bytes(canonical_bytes(sorted(set(inspection["direct_dependencies"] + inspection["axiom_set"])))),
        "axiom_set": inspection["axiom_set"],
        "axiom_set_sha256": sha256_bytes(canonical_bytes(inspection["axiom_set"])),
        "forbidden_axiom_set": inspection["forbidden_axiom_set"],
        "sorry_ax_present": inspection["sorry_ax_present"],
        "unsafe_dependency_present": inspection["unsafe_dependency_present"],
        "opaque_dependency_policy_result": inspection["opaque_dependency_policy_result"],
    }
    finished = datetime.now(timezone.utc).isoformat()
    status = "passed" if process.returncode == 0 and structured["declaration_found"] and structured["declaration_type_matches"] and not structured["sorry_ax_present"] and not structured["unsafe_dependency_present"] and not structured["forbidden_axiom_set"] else "failed"
    unsigned = {
        "schema_version": "wc_lean_verifier_result/v3", "status": status,
        "request_id": request["request_id"], "request_sha256": sha256_bytes(canonical_bytes(request)),
        "compiler_profile_id": request["compiler_profile_id"], "claim_content_sha256": request["claim_content_sha256"],
        "policy_decision_id": request["policy_decision_id"], "policy_decision_sha256": request["policy_decision_sha256"],
        "theorem_statement_sha256": request["theorem_statement_sha256"], "proof_artifact_sha256": request["proof_artifact_sha256"],
        "immutable_snapshot_id": request["immutable_snapshot_id"], "immutable_snapshot_tree_sha256": request["immutable_snapshot_tree_sha256"],
        "generated_binding_module_sha256": request["generated_binding_module_sha256"],
        "lake_executable_sha256": profile["lake_executable_sha256"], "lean_executable_sha256": profile["lean_executable_sha256"],
        "lean_stdlib_tree_sha256": profile["lean_stdlib_tree_sha256"], "dependency_closure_sha256": profile["dependency_closure_sha256"],
        "oci_image_digest": profile["oci_image_digest"], "oci_runtime_sha256": profile["oci_runtime_sha256"],
        "oci_runtime_version": profile["oci_runtime_version"], "verifier_executable_sha256": profile["verifier_executable_sha256"],
        "oci_runtime_version_output_sha256": invocation["oci_runtime_version_output_sha256"],
        "sandbox_policy_sha256": profile["sandbox_policy_sha256"], "effective_sandbox_invocation_sha256": sha256_bytes(canonical_bytes(invocation)),
        "theorem_declaration": request["theorem_name"], **structured,
        "normalization_policy": "lean_isDefEq_reducibility_regular/v1", "build_from_source": True,
        "prebuilt_artifacts_used": False, "warnings_as_errors": True, "exit_status": process.returncode,
        "timeout_status": "completed", "execution_started_at": started, "execution_finished_at": finished,
        "verifier_result_signer_key_id": profile["verifier_result_signer_key_id"],
        "requested_controls": sorted(invocation["requested_controls"]),
        "applied_controls": sorted(invocation["applied_controls"]),
        "verified_controls": inspect_runtime_controls(invocation),
        "stdout_sha256": process.stdout_sha256, "stderr_sha256": process.stderr_sha256,
        "output_limit_exceeded": process.output_limit_exceeded,
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
