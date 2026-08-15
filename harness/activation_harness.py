#!/usr/bin/env python3
"""Host orchestrator for isolated, multi-version Witness Contract qualification."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LOG_ROOT = ROOT / "logs"
REGISTRY_PATH = ROOT / "activation_gate_registry_v1.json"
CONTAINERFILE = ROOT / "Containerfile.activation"
TOOLCHAIN_CONTAINERFILE = ROOT / "Containerfile.toolchain-base"
COMPOSE_TEMPLATE = ROOT / "compose.activation.yaml"
IMAGE = "localhost/duotronic-wc-activation-harness:5.3.17"
TOOLCHAIN_IMAGE = "localhost/duotronic-wc-toolchain-base:lean4.29.1-java17-pq-v1"
CONTAINER_PREFIX = "duotronic-wc-gates-"
PROJECT_PREFIX = "dwc-qual-"
DEFAULT_CORPUS = Path("/var/www/xavi/Duotronics/build_docs/witness_contract/v1.6 - Draft 5.3.17")
DEFAULT_SOURCE = Path("/var/www/xavi/Duotronics")
DEFAULT_EVIDENCE = ROOT / "evidence"
MAX_CAPTURE_CHARS = 2_000_000
PODMAN_DEPLOY_PRIORITY_LOCK = Path("/var/www/xavi/updates/.podman-deploy-priority")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id(action: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{action}-{uuid.uuid4().hex[:10]}"


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


class RunLog:
    """Durable per-invocation human, structured, command, and artifact logging."""

    def __init__(self, action: str) -> None:
        self.run_id = new_run_id(action)
        self.directory = LOG_ROOT / self.run_id
        self.directory.mkdir(parents=True, mode=0o755)
        os.chmod(self.directory, 0o755)
        self.ndjson = self.directory / "host.log.ndjson"
        self.text = self.directory / "host.log"
        self.commands = self.directory / "commands.jsonl"
        self.emit(
            "invocation_start", action=action, pid=os.getpid(), uid=os.geteuid(),
            gid=os.getegid(), cwd=os.getcwd(), argv=sys.argv,
        )

    def emit(self, event: str, **fields: Any) -> None:
        row = {"at": utc_now(), "run_id": self.run_id, "event": event, **fields}
        line = json.dumps(row, sort_keys=True, ensure_ascii=False)
        with self.ndjson.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        human = f"{row['at']} {event}"
        if fields:
            human += " " + json.dumps(fields, sort_keys=True, ensure_ascii=False)
        with self.text.open("a", encoding="utf-8") as handle:
            handle.write(human + "\n")

    def command(self, phase: str, argv: list[str], cwd: Path | None = None) -> None:
        row = {
            "at": utc_now(), "run_id": self.run_id, "phase": phase, "argv": argv,
            "shell_command_for_display_only": shlex.join(argv), "cwd": str(cwd or ROOT),
        }
        with self.commands.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.emit("command_recorded", phase=phase, argv=argv, cwd=row["cwd"])

    def write_json(self, name: str, value: Any) -> Path:
        path = self.directory / name
        atomic_json(path, value)
        self.emit("artifact_written", path=str(path), bytes=path.stat().st_size)
        return path


def run_capture(
    log: RunLog, phase: str, argv: list[str], *, timeout: int = 60, cwd: Path = ROOT
) -> dict[str, Any]:
    log.command(phase, argv, cwd)
    started = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout)
        payload = {
            "phase": phase, "argv": argv, "exit_code": result.returncode,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "stdout": result.stdout[-MAX_CAPTURE_CHARS:],
            "stderr": result.stderr[-MAX_CAPTURE_CHARS:], "timed_out": False,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as error:
        missing = isinstance(error, FileNotFoundError)
        payload = {
            "phase": phase, "argv": argv, "exit_code": 127 if missing else 124,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "stdout": str(getattr(error, "stdout", "") or "")[-MAX_CAPTURE_CHARS:],
            "stderr": str(error)[-MAX_CAPTURE_CHARS:], "timed_out": not missing,
        }
    (log.directory / f"{phase}.stdout.log").write_text(payload["stdout"], encoding="utf-8")
    (log.directory / f"{phase}.stderr.log").write_text(payload["stderr"], encoding="utf-8")
    log.write_json(f"{phase}.result.json", payload)
    log.emit(
        "command_finished", phase=phase, exit_code=payload["exit_code"],
        elapsed_seconds=payload["elapsed_seconds"], timed_out=payload["timed_out"],
    )
    return payload



def run_stream_capture(
    log: RunLog, phase: str, argv: list[str], *, timeout: int, cwd: Path = ROOT
) -> dict[str, Any]:
    """Stream a long command to MCP and durable files while retaining a bounded result."""
    log.command(phase, argv, cwd)
    stdout_path = log.directory / f"{phase}.stdout.log"
    stderr_path = log.directory / f"{phase}.stderr.log"
    started = time.monotonic()
    process = subprocess.Popen(
        argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        bufsize=1, start_new_session=True,
    )
    captured: dict[str, list[str]] = {"stdout": [], "stderr": []}

    def pump(pipe: Any, path: Path, name: str, destination: Any) -> None:
        with path.open("w", encoding="utf-8", errors="replace") as handle:
            for line in iter(pipe.readline, ""):
                handle.write(line)
                handle.flush()
                destination.write(line)
                destination.flush()
                captured[name].append(line)
                if sum(len(item) for item in captured[name]) > MAX_CAPTURE_CHARS:
                    captured[name] = ["".join(captured[name])[-MAX_CAPTURE_CHARS:]]
                log.emit("command_output", phase=phase, stream=name, line=line.rstrip("\n"))
        pipe.close()

    assert process.stdout is not None and process.stderr is not None
    threads = [
        threading.Thread(target=pump, args=(process.stdout, stdout_path, "stdout", sys.stdout), daemon=True),
        threading.Thread(target=pump, args=(process.stderr, stderr_path, "stderr", sys.stderr), daemon=True),
    ]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        exit_code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=20)
        exit_code = 124
    for thread in threads:
        thread.join(timeout=20)
    payload = {
        "phase": phase, "argv": argv, "exit_code": exit_code,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "stdout": "".join(captured["stdout"])[-MAX_CAPTURE_CHARS:],
        "stderr": "".join(captured["stderr"])[-MAX_CAPTURE_CHARS:],
        "timed_out": timed_out,
    }
    log.write_json(f"{phase}.result.json", payload)
    log.emit(
        "command_finished", phase=phase, exit_code=exit_code,
        elapsed_seconds=payload["elapsed_seconds"], timed_out=timed_out,
    )
    return payload

def podman_rootless_preflight(log: RunLog) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "host_uid_non_root": os.geteuid() != 0,
        "podman_on_path": False,
        "podman_compose_provider": False,
        "local_execution_forced": True,
        "remote_transport_unset": not any(
            os.environ.get(name) for name in ("CONTAINER_HOST", "DOCKER_HOST", "PODMAN_HOST")
        ),
        "podman_reports_rootless": False,
    }
    version = run_capture(log, "podman-version", ["podman", "--version"])
    checks["podman_on_path"] = version["exit_code"] == 0
    compose = run_capture(
        log, "podman-compose-version", ["podman", "--remote=false", "compose", "version"], timeout=60
    )
    checks["podman_compose_provider"] = compose["exit_code"] == 0
    info = run_capture(
        log, "podman-rootless",
        ["podman", "--remote=false", "info", "--format", "{{.Host.Security.Rootless}}"], timeout=30,
    )
    rootless_text = info["stdout"].strip().lower()
    checks["podman_reports_rootless"] = info["exit_code"] == 0 and rootless_text == "true"
    passed = all(
        checks[name] for name in (
            "host_uid_non_root", "podman_on_path", "podman_compose_provider",
            "local_execution_forced", "remote_transport_unset",
        )
    )
    result = {
        "passed": passed, "checks": checks, "podman_rootless_raw": rootless_text,
        "rootless_basis": (
            "non-root EUID, forced local Podman transport, and an available Compose provider; "
            "Podman info is corroborating telemetry"
        ),
    }
    log.write_json("rootless-preflight.json", result)
    log.emit("rootless_preflight", passed=passed, checks=checks)
    return result



def contract_target_invariant() -> dict[str, Any]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    expected = "v1.6-draft-5.3.17"
    checks = {
        "registry_version": registry.get("contract_version") == expected,
        "image_tag": IMAGE.endswith(":5.3.17"),
        "default_corpus": str(DEFAULT_CORPUS).endswith("v1.6 - Draft 5.3.17"),
        "compose_template": ":5.3.17" in COMPOSE_TEMPLATE.read_text(encoding="utf-8"),
    }
    return {"passed": all(checks.values()), "expected": expected, "checks": checks}

def image_inspect(
    log: RunLog, image: str = IMAGE, *, phase: str = "image-inspect",
    artifact_name: str = "image-metadata.json",
) -> dict[str, Any]:
    result = run_capture(
        log, phase,
        ["podman", "--remote=false", "image", "inspect", image], timeout=90,
    )
    metadata: dict[str, Any] = {"present": result["exit_code"] == 0, "image": image}
    if result["exit_code"] == 0:
        try:
            inspected = json.loads(result["stdout"])
            item = inspected[0] if isinstance(inspected, list) and inspected else inspected
            metadata.update({
                "id": item.get("Id"), "digest": item.get("Digest"),
                "repo_digests": item.get("RepoDigests", []), "created": item.get("Created"),
                "architecture": item.get("Architecture"), "os": item.get("Os"),
                "labels": item.get("Labels", {}),
            })
        except (json.JSONDecodeError, AttributeError):
            metadata["parse_error"] = True
    log.write_json(artifact_name, metadata)
    return metadata


def validate_input_directory(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"{label} is not a directory: {resolved}")
    return resolved


def registry_gate_ids() -> list[str]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return [item["gate_id"] for item in registry["gates"]]


def build_compose_document(
    *, container_name: str, run_id: str, corpus: Path, source: Path,
    evidence: Path, output: Path, gates: list[str], qualification_mode: str = "full",
    evidence_run_id: str | None = None, authority_profile: str = "production",
    authority_namespace: str = "duotronic://authority/production", contract_ref: str | None = None,
) -> dict[str, Any]:
    uid, gid = os.geteuid(), os.getegid()
    command = ["--run-id", run_id, "--qualification-mode", qualification_mode]
    if evidence_run_id:
        command.extend(["--evidence-run-id", evidence_run_id])
    for gate in gates:
        command.extend(["--gate", gate])
    return {
        "version": "3.8",
        "networks": {"activation-isolated": {"internal": True}},
        "services": {
            "activation-gates": {
                "image": IMAGE,
                "container_name": container_name,
                "networks": ["activation-isolated"],
                "read_only": True,
                "user": f"{uid}:{gid}",
                "userns_mode": "keep-id",
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges"],
                "pids_limit": 512,
                "mem_limit": "4g",
                "cpus": 4,
                "tmpfs": [
                    "/tmp:rw,noexec,nosuid,nodev,size=512m",
                    "/work:rw,nosuid,nodev,size=2048m",
                ],
                "volumes": [
                    f"{corpus}:/corpus-ro:ro",
                    f"{source}:/source:ro",
                    f"{evidence}:/evidence:ro",
                    f"{output}:/output:rw",
                ],
                "environment": {
                    "HARNESS_ROOTLESS": "true",
                    "HARNESS_HOST_RUN_ID": run_id,
                    "HARNESS_CONTRACT_REF": contract_ref or corpus.name,
                    "HARNESS_AUTHORITY_PROFILE": authority_profile,
                    "HARNESS_AUTHORITY_NAMESPACE": authority_namespace,
                    "HARNESS_START_BARRIER": "/output/sandbox.start",
                    "PYTHONHASHSEED": "0",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": "/work/corpus",
                    "TLA2TOOLS_JAR": "/opt/tla2tools/tla2tools.jar",
                    "JAVA_TOOL_OPTIONS": "-XX:+UseParallelGC",
                },
                "command": command,
                "restart": "no",
            }
        },
    }


def compose_up_argv(project: str, compose_path: Path) -> list[str]:
    return [
        "podman", "--remote=false", "compose", "-p", project, "-f", str(compose_path),
        "up", "--no-build", "--abort-on-container-exit", "--exit-code-from", "activation-gates",
    ]


def compose_down_argv(project: str, compose_path: Path) -> list[str]:
    return [
        "podman", "--remote=false", "compose", "-p", project, "-f", str(compose_path),
        "down", "--remove-orphans", "--volumes",
    ]


class Interrupted(Exception):
    pass


def _signal_handler(signum: int, _frame: Any) -> None:
    raise Interrupted(f"received signal {signum}")


def force_cleanup(
    log: RunLog, container_name: str, project: str | None = None, compose_path: Path | None = None
) -> dict[str, Any]:
    down_code: int | None = None
    if project and compose_path:
        down = run_capture(log, "compose-down", compose_down_argv(project, compose_path), timeout=180)
        down_code = down["exit_code"]
    remove = run_capture(
        log, "container-force-remove",
        ["podman", "--remote=false", "rm", "--force", "--ignore", container_name], timeout=60,
    )
    exists = run_capture(
        log, "container-postcondition",
        ["podman", "--remote=false", "container", "exists", container_name], timeout=30,
    )
    network_name = f"{project}_activation-isolated" if project else None
    network_remove_code: int | None = None
    network_exists_code: int | None = None
    if network_name:
        network_remove = run_capture(
            log, "network-force-remove",
            ["podman", "--remote=false", "network", "rm", "--force", network_name],
            timeout=60,
        )
        network_remove_code = network_remove["exit_code"]
        network_exists = run_capture(
            log, "network-postcondition",
            ["podman", "--remote=false", "network", "exists", network_name], timeout=30,
        )
        network_exists_code = network_exists["exit_code"]
    network_absent = network_exists_code is None or network_exists_code != 0
    cleaned = (
        remove["exit_code"] == 0
        and exists["exit_code"] != 0
        and network_absent
        and down_code in (None, 0)
    )
    proof = {
        "compose_project": project,
        "compose_down_exit_code": down_code,
        "container_name": container_name,
        "force_remove_exit_code": remove["exit_code"],
        "postcondition_exists_exit_code": exists["exit_code"],
        "container_absent": exists["exit_code"] != 0,
        "network_name": network_name,
        "network_force_remove_exit_code": network_remove_code,
        "network_postcondition_exists_exit_code": network_exists_code,
        "network_absent": network_absent,
        "cleaned": cleaned,
    }
    log.write_json("cleanup-proof.json", proof)
    log.emit("cleanup_complete", **proof)
    return proof


def tee_pipe(pipe: Any, path: Path, log: RunLog, stream_name: str) -> None:
    with path.open("w", encoding="utf-8", errors="replace") as handle:
        for line in iter(pipe.readline, ""):
            handle.write(line)
            handle.flush()
            log.emit("compose_output", stream=stream_name, line=line.rstrip("\n"))
    pipe.close()


def wait_for_live_inspect(log: RunLog, container_name: str, timeout: int = 180) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        last = run_capture(
            log, "container-live-inspect",
            ["podman", "--remote=false", "container", "inspect", container_name], timeout=20,
        )
        if last["exit_code"] == 0:
            try:
                parsed = json.loads(last["stdout"])
                item = parsed[0] if isinstance(parsed, list) else parsed
                state = item.get("State", {})
                if bool(state.get("Running")):
                    log.write_json("live-container-inspect.json", item)
                    return {"captured": True, "inspect": item}
                if str(state.get("Status", "")).lower() in {"exited", "stopped", "dead"}:
                    log.write_json("live-container-inspect.json", item)
                    return {
                        "captured": False,
                        "reason": "container_exited_before_start_barrier",
                        "inspect": item,
                    }
            except json.JSONDecodeError:
                pass
        time.sleep(1)
    return {"captured": False, "last": last or {}}


def enforce_process_limit(log: RunLog, container_name: str, limit: int = 512) -> dict[str, Any]:
    result = run_capture(
        log, "container-update-pids-limit",
        [
            "podman", "--remote=false", "container", "update",
            "--pids-limit", str(limit), container_name,
        ],
        timeout=60,
    )
    measurement = run_capture(
        log, "container-measure-pids-limit",
        [
            "podman", "--remote=false", "exec", container_name,
            "cat", "/sys/fs/cgroup/pids.max",
        ],
        timeout=30,
    )
    observed: int | None = None
    try:
        observed = int(measurement["stdout"].strip())
    except (TypeError, ValueError):
        pass
    proof = {
        "requested_pids_limit": limit,
        "update_exit_code": result["exit_code"],
        "measurement_exit_code": measurement["exit_code"],
        "observed_cgroup_pids_max": observed,
        "applied": (
            result["exit_code"] == 0
            and measurement["exit_code"] == 0
            and observed is not None
            and 0 < observed <= limit
        ),
    }
    log.write_json("process-limit-enforcement.json", proof)
    log.emit("process_limit_enforced", **proof)
    return proof


def inspect_internal_network(log: RunLog, project: str) -> dict[str, Any]:
    network_name = f"{project}_activation-isolated"
    result = run_capture(
        log, "network-live-inspect",
        ["podman", "--remote=false", "network", "inspect", network_name],
        timeout=30,
    )
    proof: dict[str, Any] = {
        "network_name": network_name,
        "inspect_exit_code": result["exit_code"],
        "internal": False,
    }
    if result["exit_code"] == 0:
        try:
            parsed = json.loads(result["stdout"])
            item = parsed[0] if isinstance(parsed, list) and parsed else parsed
            proof["internal"] = bool(item.get("internal", item.get("Internal", False)))
            proof["driver"] = item.get("driver", item.get("Driver"))
        except (json.JSONDecodeError, AttributeError):
            proof["parse_error"] = True
    proof["passed"] = result["exit_code"] == 0 and proof["internal"]
    log.write_json("internal-network-inspect.json", proof)
    log.emit("internal_network_inspected", **proof)
    return proof


def inspect_sandbox_controls(
    item: dict[str, Any],
    network_proof: dict[str, Any] | None = None,
    process_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    host = item.get("HostConfig", {})
    config = item.get("Config", {})
    network_mode = str(host.get("NetworkMode", "")).lower()
    cap_drop = [str(value).lower() for value in (host.get("CapDrop") or [])]
    security = [str(value).lower() for value in (host.get("SecurityOpt") or [])]
    create_command = [str(value).lower() for value in (config.get("CreateCommand") or [])]
    expected_dropped_caps = {
        "cap_chown", "cap_dac_override", "cap_fowner", "cap_fsetid", "cap_kill",
        "cap_net_bind_service", "cap_setfcap", "cap_setgid", "cap_setpcap",
        "cap_setuid", "cap_sys_chroot",
    }
    attached_networks = {
        str(name).lower()
        for name in ((item.get("NetworkSettings") or {}).get("Networks") or {})
    }
    cli_networks = {
        create_command[index + 1]
        for index, token in enumerate(create_command[:-1])
        if token in {"--net", "--network"}
    }
    expected_network = str((network_proof or {}).get("network_name", "")).lower()
    network_attached = (
        network_mode == "none"
        or expected_network in attached_networks
        or expected_network in cli_networks
    )
    mounts = item.get("Mounts", [])
    read_only_inputs = all(
        any(
            mount.get("Destination") == destination and not bool(mount.get("RW"))
            for mount in mounts
        )
        for destination in ("/corpus-ro", "/source", "/evidence")
    )
    pids_limit = int(host.get("PidsLimit") or 0)
    checks = {
        "network_externally_isolated": (
            network_mode == "none"
            or (
                bool((network_proof or {}).get("internal"))
                and bool(expected_network)
                and network_attached
            )
        ),
        "read_only_rootfs": bool(host.get("ReadonlyRootfs")),
        "capabilities_dropped": "all" in cap_drop or (
            expected_dropped_caps.issubset(set(cap_drop)) and not (host.get("CapAdd") or [])
        ),
        "process_limit_512": bool((process_proof or {}).get("applied")) and 0 < int((process_proof or {}).get("observed_cgroup_pids_max") or 0) <= 512,
        "no_new_privileges": any("no-new-privileges" in value for value in security),
        "read_only_inputs": read_only_inputs,
        "non_root_container_user": str(config.get("User", "")) not in ("", "0", "0:0", "root"),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "observed_cgroup_pids_max": (process_proof or {}).get("observed_cgroup_pids_max"),
        "podman_metadata_pids_limit": pids_limit,
        "attached_networks": sorted(attached_networks),
        "compose_cli_networks": sorted(cli_networks),
    }


def aggregate_sandbox_report(
    log: RunLog, compose_exit: int, cleanup: dict[str, Any],
    image: dict[str, Any], live: dict[str, Any], controls: dict[str, Any],
) -> dict[str, Any]:
    path = log.directory / "sandbox-report.json"
    if path.is_file():
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {"state": "failed", "reason": "sandbox_report_invalid_json"}
    else:
        report = {"state": "failed", "reason": "sandbox_report_missing"}
    if "state" not in report:
        gate_states = {
            str(item.get("state", "error"))
            for item in report.get("gates", [])
            if isinstance(item, dict)
        }
        if (
            not report.get("qualification_suite", {}).get("passed")
            or gate_states.intersection({"failed", "error"})
        ):
            report["state"] = "failed"
        elif gate_states and gate_states == {"verified"}:
            report["state"] = "verified"
        else:
            report["state"] = "blocked"
        report["state_inferred_by_host"] = True
    report.update({
        "host_run_id": log.run_id,
        "compose_exit_code": compose_exit,
        "compose_sandbox": True,
        "live_inspect_captured": live.get("captured", False),
        "host_sandbox_controls": controls,
        "image": image,
        "cleanup": cleanup,
        "authority_activated": False,
        "runtime_connected": False,
    })
    sandbox_ok = report.get("state") in ("verified", "blocked")
    report["qualification_complete"] = bool(
        report.get("qualification_suite", {}).get("passed")
        and sandbox_ok and cleanup.get("cleaned") and controls.get("passed")
    )
    report["runtime_handoff_eligible"] = bool(
        report.get("activation_eligible") and report["qualification_complete"]
    )
    log.write_json("aggregate-report.json", report)
    return report


def command_run(args: argparse.Namespace, log: RunLog) -> int:
    # The image/evidence protocol is versioned independently from the mounted
    # development corpus. Any confined corpus version may therefore be tested.
    preflight = podman_rootless_preflight(log)
    if not preflight["passed"]:
        log.write_json("aggregate-report.json", {
            "run_id": log.run_id, "qualification_complete": False,
            "runtime_handoff_eligible": False, "authority_activated": False,
            "runtime_connected": False, "reason": "rootless_compose_preflight_failed",
            "preflight": preflight,
        })
        return 3
    try:
        corpus = validate_input_directory(args.corpus, "corpus")
        source = validate_input_directory(args.source, "source")
        evidence = args.evidence.expanduser().resolve()
        evidence.mkdir(parents=True, exist_ok=True)
        evidence = validate_input_directory(evidence, "evidence")
    except (FileNotFoundError, ValueError) as error:
        log.emit("input_validation_failed", error=str(error))
        log.write_json("aggregate-report.json", {
            "run_id": log.run_id, "qualification_complete": False,
            "runtime_handoff_eligible": False, "authority_activated": False,
            "runtime_connected": False, "reason": "input_validation_failed", "error": str(error),
        })
        return 3

    all_gates = registry_gate_ids()
    gates = args.gate or all_gates
    unknown = sorted(set(gates) - set(all_gates))
    if unknown:
        log.write_json("aggregate-report.json", {
            "run_id": log.run_id, "qualification_complete": False,
            "runtime_handoff_eligible": False, "authority_activated": False,
            "runtime_connected": False, "reason": "unknown_gate", "gates": unknown,
        })
        return 3
    if not image_inspect(log)["present"]:
        log.write_json("aggregate-report.json", {
            "run_id": log.run_id, "qualification_complete": False,
            "runtime_handoff_eligible": False, "authority_activated": False,
            "runtime_connected": False, "reason": "sandbox_image_missing",
        })
        return 3

    suffix = uuid.uuid4().hex[:12]
    container_name = CONTAINER_PREFIX + suffix
    project = PROJECT_PREFIX + suffix
    compose_document = build_compose_document(
        container_name=container_name, run_id=log.run_id, corpus=corpus, source=source,
        evidence=evidence, output=log.directory, gates=gates,
        qualification_mode=args.qualification_mode,
        evidence_run_id=args.evidence_run_id,
        authority_profile=args.authority_profile,
        authority_namespace=args.authority_namespace,
        contract_ref=args.contract_ref,
    )
    compose_path = log.write_json("compose.resolved.json", compose_document)
    log.emit(
        "qualification_boundary", runtime_connected=False, production_runtime_connected=False,
        authority_profile=args.authority_profile, authority_namespace=args.authority_namespace,
        corpus_mount="read-only", execution="rootless-podman-compose", selected_gates=gates,
    )
    up_argv = compose_up_argv(project, compose_path)
    log.command("compose-up", up_argv)
    stdout_path = log.directory / "compose.stdout.log"
    stderr_path = log.directory / "compose.stderr.log"
    process: subprocess.Popen[str] | None = None
    threads: list[threading.Thread] = []
    live: dict[str, Any] = {"captured": False}
    controls: dict[str, Any] = {"passed": False, "checks": {}}
    compose_exit = 125
    cleanup: dict[str, Any] = {}
    previous_handlers: dict[int, Any] = {}

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, _signal_handler)
        process = subprocess.Popen(
            up_argv, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=1, start_new_session=True,
        )
        assert process.stdout is not None and process.stderr is not None
        threads = [
            threading.Thread(
                target=tee_pipe, args=(process.stdout, stdout_path, log, "stdout"), daemon=True
            ),
            threading.Thread(
                target=tee_pipe, args=(process.stderr, stderr_path, log, "stderr"), daemon=True
            ),
        ]
        for thread in threads:
            thread.start()
        live = wait_for_live_inspect(log, container_name)
        if live.get("captured"):
            process_limit = enforce_process_limit(log, container_name)
            network_proof = inspect_internal_network(log, project)
            if process_limit["applied"] and network_proof["passed"]:
                refreshed = wait_for_live_inspect(log, container_name, timeout=30)
                if refreshed.get("captured"):
                    live = refreshed
                    controls = inspect_sandbox_controls(live["inspect"], network_proof, process_limit)
                else:
                    controls = {
                        "passed": False,
                        "checks": {},
                        "reason": "post_control_live_inspect_not_captured",
                    }
            else:
                controls = {
                    "passed": False,
                    "checks": {},
                    "reason": "host_control_enforcement_failed",
                    "process_limit": process_limit,
                    "network": network_proof,
                }
            log.write_json("sandbox-controls.json", controls)
            if controls["passed"]:
                (log.directory / "sandbox.start").write_text("inspected\n", encoding="utf-8")
                log.emit("sandbox_start_released", controls=controls)
            else:
                log.emit("sandbox_start_failed", reason="sandbox_controls_failed", controls=controls)
                process.terminate()
        else:
            log.emit("sandbox_start_failed", reason="live_inspect_not_captured")
            process.terminate()
        try:
            compose_exit = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            log.emit("compose_timeout", timeout_seconds=args.timeout)
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=20)
            compose_exit = 124
    except Interrupted as error:
        log.emit("interrupted", error=str(error))
        if process and process.poll() is None:
            process.terminate()
        compose_exit = 130
    except (OSError, subprocess.SubprocessError) as error:
        log.emit("compose_launch_failed", error=str(error))
        compose_exit = 125
    finally:
        for thread in threads:
            thread.join(timeout=10)
        cleanup = force_cleanup(log, container_name, project, compose_path)
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)

    image = image_inspect(log)
    report = aggregate_sandbox_report(log, compose_exit, cleanup, image, live, controls)
    report["tested_corpus_path"] = str(corpus)
    report["tested_contract_ref"] = corpus.name
    report["qualification_mode"] = args.qualification_mode
    log.write_json("aggregate-report.json", report)
    log.emit(
        "invocation_complete", exit_code=compose_exit,
        qualification_complete=report.get("qualification_complete", False),
        runtime_handoff_eligible=report.get("runtime_handoff_eligible", False),
    )
    if report.get("runtime_handoff_eligible"):
        return 0
    if compose_exit in (124, 125, 130) or not cleanup.get("cleaned"):
        return 3
    return 2 if report.get("state") == "blocked" else 1


def command_build(args: argparse.Namespace, log: RunLog) -> int:
    target = contract_target_invariant()
    log.write_json("contract-target-invariant.json", target)
    if not target["passed"]:
        return 3
    if PODMAN_DEPLOY_PRIORITY_LOCK.exists():
        report = {
            "run_id": log.run_id,
            "state": "deferred",
            "reason": "podman_deploy_priority",
            "lock": str(PODMAN_DEPLOY_PRIORITY_LOCK),
            "authority_activated": False,
            "runtime_connected": False,
        }
        log.write_json("build-report.json", report)
        log.emit("build_deferred", reason="podman_deploy_priority", lock=str(PODMAN_DEPLOY_PRIORITY_LOCK))
        return 0
    preflight = podman_rootless_preflight(log)
    if not preflight["passed"]:
        return 3
    toolchain = image_inspect(
        log, TOOLCHAIN_IMAGE, phase="toolchain-image-inspect",
        artifact_name="toolchain-image-metadata.json",
    )
    if not toolchain.get("present"):
        report = {
            "run_id": log.run_id, "state": "blocked",
            "reason": "toolchain_base_missing",
            "required_image": TOOLCHAIN_IMAGE,
            "next_action": "run build-toolchain, then rerun build",
            "authority_activated": False, "runtime_connected": False,
        }
        log.write_json("build-report.json", report)
        return 3
    argv = [
        "podman", "--remote=false", "build", "--pull=never",
        "--file", str(CONTAINERFILE), "--tag", IMAGE, str(ROOT),
    ]
    result = run_stream_capture(log, "image-build", argv, timeout=args.timeout)
    metadata = image_inspect(log)
    report = {
        "run_id": log.run_id, "build_exit_code": result["exit_code"],
        "image": metadata, "authority_activated": False, "runtime_connected": False,
    }
    log.write_json("build-report.json", report)
    return 0 if result["exit_code"] == 0 and metadata.get("present") else 1


def command_build_toolchain(args: argparse.Namespace, log: RunLog) -> int:
    if PODMAN_DEPLOY_PRIORITY_LOCK.exists():
        log.write_json("toolchain-build-report.json", {
            "run_id": log.run_id, "state": "deferred",
            "reason": "podman_deploy_priority", "lock": str(PODMAN_DEPLOY_PRIORITY_LOCK),
            "authority_activated": False, "runtime_connected": False,
        })
        return 0
    preflight = podman_rootless_preflight(log)
    if not preflight["passed"]:
        return 3
    argv = [
        "podman", "--remote=false", "build", "--pull=missing",
        "--file", str(TOOLCHAIN_CONTAINERFILE), "--tag", TOOLCHAIN_IMAGE, str(ROOT),
    ]
    result = run_stream_capture(log, "toolchain-image-build", argv, timeout=args.timeout)
    metadata = image_inspect(
        log, TOOLCHAIN_IMAGE, phase="toolchain-image-inspect",
        artifact_name="toolchain-image-metadata.json",
    )
    log.write_json("toolchain-build-report.json", {
        "run_id": log.run_id, "build_exit_code": result["exit_code"],
        "image": metadata, "authority_activated": False, "runtime_connected": False,
    })
    return 0 if result["exit_code"] == 0 and metadata.get("present") else 1


def command_status(_args: argparse.Namespace, log: RunLog) -> int:
    preflight = podman_rootless_preflight(log)
    image = image_inspect(log)
    containers = run_capture(
        log, "container-status",
        [
            "podman", "--remote=false", "ps", "--all",
            "--filter", f"name=^{CONTAINER_PREFIX}", "--format", "json",
        ], timeout=60,
    )
    recent = [
        str(path) for path in sorted(LOG_ROOT.glob("*"), reverse=True)[:10] if path.is_dir()
    ]
    report = {
        "run_id": log.run_id, "preflight": preflight, "image": image,
        "container_query_exit_code": containers["exit_code"],
        "active_container_query": containers["stdout"], "recent_log_bundles": recent,
        "compose_template_present": COMPOSE_TEMPLATE.is_file(),
        "authority_activated": False, "runtime_connected": False,
    }
    log.write_json("status-report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if preflight["passed"] else 1


def command_cleanup(_args: argparse.Namespace, log: RunLog) -> int:
    query = run_capture(
        log, "cleanup-query",
        [
            "podman", "--remote=false", "ps", "--all",
            "--filter", f"name=^{CONTAINER_PREFIX}", "--format", "{{.Names}}",
        ], timeout=60,
    )
    names = [
        line.strip() for line in query["stdout"].splitlines()
        if line.strip().startswith(CONTAINER_PREFIX)
    ]
    outcomes = []
    for name in names:
        outcomes.append(force_cleanup(log, name))
    passed = query["exit_code"] == 0 and all(item["cleaned"] for item in outcomes)
    log.write_json("cleanup-report.json", {
        "run_id": log.run_id, "containers": outcomes, "passed": passed,
        "authority_activated": False, "runtime_connected": False,
    })
    return 0 if passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Isolated multi-version pre-runtime Witness Contract qualification suite"
    )
    sub = parser.add_subparsers(dest="action", required=True)
    build = sub.add_parser("build")
    build.add_argument("--timeout", type=int, default=1800)
    build_toolchain = sub.add_parser("build-toolchain")
    build_toolchain.add_argument("--timeout", type=int, default=3600)
    run = sub.add_parser("run")
    run.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    run.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    run.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    run.add_argument("--evidence-run-id")
    run.add_argument("--gate", action="append", choices=registry_gate_ids())
    run.add_argument("--qualification-mode", choices=("full", "targeted"), default="full")
    run.add_argument("--authority-profile", choices=("production", "sandbox-test-only"), default="production")
    run.add_argument("--authority-namespace", default="duotronic://authority/production")
    run.add_argument("--contract-ref")
    run.add_argument("--timeout", type=int, default=3600)
    sub.add_parser("status")
    sub.add_parser("cleanup")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    log = RunLog(args.action)
    try:
        if args.action == "build":
            code = command_build(args, log)
        elif args.action == "build-toolchain":
            code = command_build_toolchain(args, log)
        elif args.action == "run":
            code = command_run(args, log)
        elif args.action == "status":
            code = command_status(args, log)
        else:
            code = command_cleanup(args, log)
    except Exception as error:
        log.emit("unhandled_exception", error=repr(error))
        log.write_json("fatal-report.json", {
            "run_id": log.run_id, "error": repr(error), "authority_activated": False,
            "runtime_connected": False,
        })
        raise
    finally:
        log.emit("invocation_end")
    print(str(log.directory))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
