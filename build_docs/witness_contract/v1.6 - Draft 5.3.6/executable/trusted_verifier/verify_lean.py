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
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

from bounded_subprocess import run_bounded

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from proof_authority import (  # noqa: E402
    AtomicResultPublisher, CanonicalSchemaValidator, canonical_bytes,
    canonical_json_loads, sha256_bytes, sha256_file,
)

PROFILE = Path("/input/control/effective-profile.json")
INSPECTOR = Path("/opt/witness-authority/bin/inspect-lean")
INVOCATION = Path("/input/control/effective-sandbox-invocation.json")
MAX_INPUT = 1024 * 1024
SCHEMAS = Path("/opt/witness-authority/schemas")


def read_canonical(path: Path, maximum: int = MAX_INPUT) -> dict:
    data = path.read_bytes()
    if len(data) > maximum:
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


def _evidence(control: str, status: str, source: str, observation: str) -> dict:
    return {
        "control": control, "status": status, "source": source,
        "observation_sha256": sha256_bytes(observation.encode("utf-8")),
    }


def inspect_runtime_controls(invocation: dict) -> tuple[list[str], list[dict]]:
    """Measure controls visible from inside the trusted domain.

    Missing kernel observations are unverified; configured intent is never
    promoted to measured evidence.
    """
    verified: set[str] = set()
    evidence: list[dict] = []
    def observed(control: str, ok: bool, source: str, value: str) -> None:
        evidence.append(_evidence(control, "measured_pass" if ok else "measured_fail", source, value))
        if ok:
            verified.add(control)
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
    network_path = Path("/sys/class/net")
    if network_path.is_dir():
        interfaces = {path.name for path in network_path.iterdir()}
        observed("network_none", interfaces.issubset({"lo"}), "/sys/class/net", ",".join(sorted(interfaces)))
    else:
        evidence.append(_evidence("network_none", "unverified_missing_observation", "/sys/class/net", "missing"))
    mount_text = Path("/proc/self/mountinfo").read_text(encoding="utf-8", errors="replace")
    mount_lines = mount_text.splitlines()
    root_lines = [line for line in mount_lines if len(line.split()) > 5 and line.split()[4] == "/"]
    if root_lines and "ro" in root_lines[0].split()[5].split(","):
        verified.add("read_only_rootfs")
    expected_mounts = {item["destination"]: item["mode"] for item in invocation.get("mount_manifest", [])}
    observed_mounts = {line.split()[4]: line.split()[5].split(",") for line in mount_lines if len(line.split()) > 5}
    if expected_mounts and all(path in observed_mounts and ((mode == "ro") == ("ro" in observed_mounts[path])) for path, mode in expected_mounts.items()):
        verified.add("mount_manifest")
    current_path = Path("/proc/self/attr/current")
    current_label = current_path.read_text(encoding="utf-8", errors="replace") if current_path.is_file() else ""
    selected_lsm = invocation.get("apparmor_profile") or invocation.get("selinux_label")
    observed("lsm_profile", bool(selected_lsm and selected_lsm in current_label), str(current_path), current_label or "missing")
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
    expected_environment = dict(value.split("=", 1) for value in invocation.get("environment_allowlist", []))
    environment_matches = bool(expected_environment) and all(os.environ.get(key, "") == value for key, value in expected_environment.items())
    environment_matches = environment_matches and os.environ.get("PYTHONPATH", "") == ""
    observed("environment_allowlist", environment_matches, "process_environment", json.dumps({key: os.environ.get(key) for key in sorted(expected_environment)}, sort_keys=True))
    return sorted(verified), sorted(evidence, key=lambda item: item["control"])


def validate_handoff(schema_validator: CanonicalSchemaValidator, invocation: dict) -> tuple[dict, str]:
    manifest_path = Path("/handoff/compile-manifest.json")
    maximum = int(invocation["handoff_total_bytes_limit"])
    manifest = read_canonical(manifest_path, maximum=min(maximum, MAX_INPUT))
    schema_validator.validate("handoff_manifest", manifest)
    if manifest["maximum_artifact_bytes"] != int(invocation["compiler_artifact_file_size_limit"]):
        raise ValueError("handoff per-artifact limit differs from the sealed invocation")
    if manifest["maximum_handoff_bytes"] != maximum:
        raise ValueError("handoff aggregate limit differs from the sealed invocation")
    actual_files = sorted(
        path for path in Path("/handoff").rglob("*")
        if path.is_file() and path != manifest_path
    )
    actual_paths = {path.relative_to("/handoff").as_posix() for path in actual_files}
    declared_paths = {item["path"] for item in manifest["artifacts"]}
    if len(declared_paths) != len(manifest["artifacts"]) or manifest["artifact_count"] != len(manifest["artifacts"]):
        raise ValueError("handoff artifact paths or count are not unique and exact")
    if actual_paths != declared_paths:
        raise ValueError("handoff file set differs from compile manifest")
    artifact_by_path = {item["path"]: item for item in manifest["artifacts"]}
    binding_path = manifest["binding_olean_path"]
    if binding_path not in artifact_by_path or artifact_by_path[binding_path]["sha256"] != manifest["binding_olean_sha256"]:
        raise ValueError("binding olean is not exactly represented by the handoff artifact set")
    module_paths = [item["olean_path"] for item in manifest["compiled_modules"]]
    if len(module_paths) != len(set(module_paths)) or binding_path not in module_paths:
        raise ValueError("compiled module set is duplicated or omits the binding target")
    for module in manifest["compiled_modules"]:
        artifact = artifact_by_path.get(module["olean_path"])
        if artifact is None or artifact["sha256"] != module["olean_sha256"]:
            raise ValueError("compiled module identity differs from the exact handoff artifact")
    total = 0
    for item in manifest["artifacts"]:
        path = Path("/handoff") / item["path"]
        info = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("handoff artifact identity is unsafe")
        if format(info.st_mode & 0o777, "04o") != item["mode"] or info.st_size != item["size_bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError("handoff artifact metadata or digest mismatch")
        total += info.st_size
    if total != manifest["total_handoff_bytes"] or total > maximum:
        raise ValueError("handoff aggregate-byte policy violated")
    return manifest, sha256_file(manifest_path)


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
    schema_validator = CanonicalSchemaValidator(SCHEMAS)
    schema_validator.validate("verifier_request", request)
    schema_validator.validate("sandbox_invocation", invocation)
    if request.get("schema_version") != "wc_lean_verifier_request/v4":
        return 64
    try:
        handoff_manifest, handoff_manifest_sha256 = validate_handoff(schema_validator, invocation)
    except Exception:
        return 69
    for executable, field in ((INSPECTOR, "verifier_executable_sha256"), (Path("/opt/lean/bin/lean"), "lean_executable_sha256"), (Path("/opt/lean/bin/lake"), "lake_executable_sha256")):
        if not executable.is_file() or sha256_file(executable) != profile[field]:
            return 65
    started = datetime.now(timezone.utc).isoformat()
    minimal_environment = {"HOME": "/nonexistent", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "SOURCE_DATE_EPOCH": "0", "LEAN_ABORT_ON_PANIC": "1", "PYTHONPATH": ""}
    process = run_bounded(
        [str(INSPECTOR), "--request", str(request_path), "--source", "/input/source", "--generated", "/input/generated", "--handoff", "/handoff"],
        cwd="/work", env=minimal_environment, timeout=int(invocation["timeout"]),
        stdout_limit=int(invocation["stdout_bytes_limit"]),
        stderr_limit=int(invocation["stderr_bytes_limit"]),
        combined_limit=int(invocation["combined_output_bytes_limit"]),
    )
    if process.timed_out:
        return 124
    if process.output_limit_exceeded:
        return 66
    try:
        inspection = canonical_json_loads(process.stdout)
    except Exception:
        return 67
    try:
        schema_validator.validate("inspector_result", inspection)
    except Exception:
        return 68
    for field in ("direct_dependencies", "dependency_closure", "axiom_set", "forbidden_axiom_set"):
        values = inspection.get(field)
        if not isinstance(values, list) or values != sorted(set(values)) or not all(isinstance(value, str) and value for value in values):
            return 68
    measured_controls, control_evidence = inspect_runtime_controls(invocation)
    structured = {
        "declaration_found": inspection["declaration_found"],
        "declaration_type_matches": inspection["declaration_type_matches"],
        "expected_type_expression_fingerprint": inspection["expected_type_expression_fingerprint"],
        "actual_type_expression_fingerprint": inspection["actual_type_expression_fingerprint"],
        "expected_type_expression_hash": sha256_bytes(inspection["expected_type_expression_fingerprint"].encode("utf-8")),
        "actual_type_expression_hash": sha256_bytes(inspection["actual_type_expression_fingerprint"].encode("utf-8")),
        "direct_dependencies": inspection["direct_dependencies"],
        "dependency_closure": inspection["dependency_closure"],
        "transitive_dependencies_root": sha256_bytes(canonical_bytes(inspection["dependency_closure"])),
        "axiom_set": inspection["axiom_set"],
        "axiom_set_sha256": sha256_bytes(canonical_bytes(inspection["axiom_set"])),
        "forbidden_axiom_set": inspection["forbidden_axiom_set"],
        "sorry_ax_present": inspection["sorry_ax_present"],
        "unsafe_dependency_present": inspection["unsafe_dependency_present"],
        "opaque_dependency_policy_result": inspection["opaque_dependency_policy_result"],
        "handoff_manifest_sha256": handoff_manifest_sha256,
    }
    finished = datetime.now(timezone.utc).isoformat()
    status = "passed" if process.returncode == 0 and structured["declaration_found"] and structured["declaration_type_matches"] and structured["opaque_dependency_policy_result"] == "passed" and not structured["sorry_ax_present"] and not structured["unsafe_dependency_present"] and not structured["forbidden_axiom_set"] else "failed"
    unsigned = {
        "schema_version": "wc_lean_verifier_result/v4", "status": status,
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
        "normalized_executed_argv_sha256": invocation["normalized_executed_argv_sha256"],
        "effective_resource_limits": request["effective_resource_limits"],
        "effective_resource_limits_sha256": request["effective_resource_limits_sha256"],
        "theorem_declaration": request["theorem_name"], **structured,
        "normalization_policy": "lean_isDefEq_reducibility_regular/v1", "build_from_source": True,
        "prebuilt_artifacts_used": False, "warnings_as_errors": True, "exit_status": process.returncode,
        "timeout_status": "completed", "execution_started_at": started, "execution_finished_at": finished,
        "verifier_result_signer_key_id": profile["verifier_result_signer_key_id"],
        "requested_controls": sorted(invocation["requested_controls"]),
        "emitted_controls": sorted(invocation["emitted_controls"]),
        "accepted_controls": sorted(invocation["accepted_controls"]),
        "measured_controls": measured_controls,
        "derived_controls": [],
        "control_evidence": control_evidence,
        "stdout_sha256": process.stdout_sha256, "stderr_sha256": process.stderr_sha256,
        "output_limit_exceeded": process.output_limit_exceeded,
    }
    preview = dict(unsigned)
    preview["signed_payload_sha256"] = sha256_bytes(canonical_bytes(unsigned))
    preview["signature"] = "A" * 86
    schema_validator.validate("verifier_result", preview)
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
