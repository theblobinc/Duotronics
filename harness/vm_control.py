#!/usr/bin/env python3
"""Host controller for the on-demand libvirt witness-harness VM.

No code path invokes host Podman. Contract tooling and rootless Podman Compose
execute only after crossing the SSH boundary into the dedicated guest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
CONFIG_PATH = ROOT / "vm" / "harness-vm.json"
LOG_ROOT = ROOT / "logs"
EVIDENCE_ROOT = ROOT / "evidence"
EXTERNAL_DATA_ROOT = ROOT / "external_data"
PROPOSAL_ROOT = ROOT / "proposals"
PAIRED_CANDIDATE_ROOT = ROOT / "candidates"
RUNTIME_ROOT = REPO / "build_docs" / "runtime" / "duotronic_srnn_open_runtime-v3"
RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
GATE_RE = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._ -]{0,129}$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config() -> dict[str, Any]:
    value = json.loads(CONFIG_PATH.read_text())
    if value.get("host_podman_allowed") is not False:
        raise ValueError("host_podman_allowed must remain false")
    if value.get("production_runtime_activation_enabled") is not False:
        raise ValueError("production runtime activation must remain disabled inside the VM")
    if value.get("production_runtime_network_access") is not False:
        raise ValueError("production runtime networking must remain disabled inside the VM")
    if value.get("sandbox_runtime_enabled") is not True or value.get("sandbox_authority_activation_enabled") is not True:
        raise ValueError("sandbox runtime and sandbox authority must be enabled")
    if value.get("sandbox_production_eligible") is not False:
        raise ValueError("sandbox authority must never be production eligible")
    return value


CFG = load_config()


def capture(argv: list[str], *, timeout: int = 60, cwd: Path | None = None, check: bool = False) -> dict[str, Any]:
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        value = {"argv": argv, "exit_code": 127, "stdout": "", "stderr": str(exc)}
        if check:
            raise RuntimeError(json.dumps(value)) from exc
        return value
    value = {
        "argv": argv,
        "exit_code": result.returncode,
        "stdout": result.stdout[-30000:],
        "stderr": result.stderr[-30000:],
    }
    if check and result.returncode != 0:
        raise RuntimeError(json.dumps(value))
    return value


class Audit:
    def __init__(self, action: str, run_id: str | None = None) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_id = run_id or f"{stamp}-vm-{action}-{uuid.uuid4().hex[:10]}"
        if not RUN_RE.fullmatch(self.run_id):
            raise ValueError("invalid run id")
        self.directory = LOG_ROOT / self.run_id
        self.directory.mkdir(parents=True, exist_ok=True)
        self.events = self.directory / "vm-control.jsonl"
        self.emit("start", action=action, host_podman_invoked=False, runtime_connected=False)

    def emit(self, event: str, **fields: Any) -> None:
        row = {"at": now(), "run_id": self.run_id, "event": event, **fields}
        with self.events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def command(self, phase: str, argv: list[str], *, timeout: int = 60, check: bool = False) -> dict[str, Any]:
        forbidden = {"podman", "podman-compose", "buildah"}
        if argv and Path(argv[0]).name in forbidden:
            raise RuntimeError("host Podman invocation is prohibited")
        self.emit("command_start", phase=phase, argv=argv)
        result = capture(argv, timeout=timeout, check=check)
        self.emit("command_finish", phase=phase, exit_code=result["exit_code"])
        with (self.directory / "commands.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"phase": phase, **result}, sort_keys=True) + "\n")
        return result

    def finish(self, state: str, **fields: Any) -> int:
        result = {
            "schema": "duotronic-witness-harness-vm-result/v1",
            "run_id": self.run_id,
            "state": state,
            "host_podman_invoked": False,
            "runtime_connected": False,
            "authority_activated": False,
            "log_directory": str(self.directory),
            **fields,
        }
        (self.directory / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.emit("finish", state=state)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if state in {"ready", "running", "stopped", "synchronized", "completed"} else 2


def virsh(*args: str) -> list[str]:
    return ["virsh", "-c", CFG["libvirt_uri"], *args]


def domain_state(audit: Audit) -> str:
    result = audit.command("domain-state", virsh("domstate", CFG["domain"]), timeout=20)
    if result["exit_code"] != 0:
        return "undefined"
    return result["stdout"].strip().lower()


def guest_ip(audit: Audit) -> str:
    override = ROOT / "state" / "vm" / "ip-address"
    if override.is_file():
        candidate = override.read_text().strip()
        if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", candidate):
            return candidate
    for source in ("agent", "lease"):
        result = audit.command("guest-address-" + source, virsh("domifaddr", CFG["domain"], "--source", source), timeout=20)
        if result["exit_code"] == 0:
            for match in re.finditer(r"\b((?:\d{1,3}\.){3}\d{1,3})/\d+", result["stdout"]):
                candidate = match.group(1)
                if candidate.startswith("127.") or candidate == "0.0.0.0":
                    continue
                return candidate
    raise RuntimeError("guest IPv4 address unavailable")


def ssh_base(ip: str) -> list[str]:
    return [
        "ssh", "-i", CFG["ssh_private_key"], "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={CFG['ssh_known_hosts']}",
        "-o", "ConnectTimeout=10", f"{CFG['guest_user']}@{ip}",
    ]


def rsync_ssh() -> str:
    return " ".join([
        "ssh", "-i", CFG["ssh_private_key"], "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={CFG['ssh_known_hosts']}",
    ])


def wait_ssh(audit: Audit) -> str:
    deadline = time.monotonic() + int(CFG["ssh_ready_timeout_seconds"])
    last = ""
    while time.monotonic() < deadline:
        try:
            ip = guest_ip(audit)
        except RuntimeError as exc:
            last = str(exc)
            time.sleep(2)
            continue
        cloud_init = audit.command(
            "guest-cloud-init",
            ssh_base(ip) + ["/usr/bin/cloud-init", "status", "--wait"],
            timeout=35,
        )
        if cloud_init["exit_code"] == 0:
            podman = audit.command(
                "guest-podman-health",
                ssh_base(ip) + ["/usr/bin/podman", "--remote=false", "info"],
                timeout=35,
            )
            if podman["exit_code"] == 0:
                return ip
            last = podman["stderr"] or podman["stdout"]
        else:
            last = cloud_init["stderr"] or cloud_init["stdout"]
        time.sleep(3)
    raise TimeoutError("guest did not become ready: " + last[-1000:])


def ensure_started(audit: Audit) -> str:
    state = domain_state(audit)
    if state == "undefined":
        raise RuntimeError("VM is not defined; run the administrator bootstrap first")
    if state not in {"running", "idle"}:
        audit.command("domain-start", virsh("start", CFG["domain"]), timeout=90, check=True)
    return wait_ssh(audit)


def stop_vm(audit: Audit, force: bool = False) -> None:
    state = domain_state(audit)
    if state in {"shut off", "undefined"}:
        return
    audit.command("domain-shutdown", virsh("shutdown", CFG["domain"]), timeout=30)
    deadline = time.monotonic() + int(CFG["shutdown_timeout_seconds"])
    while time.monotonic() < deadline:
        if domain_state(audit) == "shut off":
            return
        time.sleep(2)
    if force:
        audit.command("domain-destroy", virsh("destroy", CFG["domain"]), timeout=30, check=True)
        return
    raise TimeoutError("guest did not shut down; explicit --force is required for destroy")


def resolve_contract(version: str) -> Path:
    if not VERSION_RE.fullmatch(version) or ".." in version:
        raise ValueError("invalid contract version")
    if version.startswith("workspace:"):
        target = ROOT / "workspaces" / version.split(":", 1)[1]
    elif version.startswith("published:"):
        target = REPO / "build_docs" / "witness_contract" / version.split(":", 1)[1]
    else:
        candidates = [ROOT / "workspaces" / version, REPO / "build_docs" / "witness_contract" / version]
        existing = [path for path in candidates if path.is_dir()]
        if len(existing) != 1:
            raise ValueError("contract reference must resolve unambiguously")
        target = existing[0]
    target = target.resolve()
    if not target.is_dir() or target.is_symlink():
        raise ValueError("contract directory unavailable or symlinked")
    return target


def source_status(audit: Audit) -> dict[str, Any]:
    status = audit.command("source-status", ["git", "status", "--porcelain=v1", "--untracked-files=all"], timeout=120)
    head = audit.command("source-head", ["git", "rev-parse", "HEAD"], timeout=30, check=True)
    origin = audit.command("source-origin", ["git", "remote", "get-url", "origin"], timeout=30)
    return {
        "clean": status["exit_code"] == 0 and not status["stdout"].strip(),
        "commit_id": head["stdout"].strip(),
        "remote_origin": origin["stdout"].strip() if origin["exit_code"] == 0 else None,
        "captured_at": now(),
        "dirty_state_commitment": hashlib.shake_256(status["stdout"].encode()).hexdigest(64),
        "sandbox_snapshot_only": True,
        "production_eligible": False,
    }


def sync_harness(audit: Audit, ip: str) -> None:
    remote = f"{CFG['guest_user']}@{ip}"
    audit.command("sync-harness", [
        "rsync", "-a", "--delete", "--exclude", "logs/", "--exclude", "state/",
        "--exclude", "workspaces/", "--exclude", "evidence/", "-e", rsync_ssh(),
        str(ROOT) + "/", f"{remote}:{CFG['guest_harness_root']}/",
    ], timeout=300, check=True)


def sync_inputs(audit: Audit, ip: str, contract: Path, challenge_run: Path | None = None) -> None:
    remote = f"{CFG['guest_user']}@{ip}"
    runner = f"{CFG['guest_harness_root']}/vm/guest/guest_runner.py"
    sync_harness(audit, ip)
    audit.command("guest-prepare", ssh_base(ip) + ["/usr/bin/python3", runner, "prepare", "--run-id", audit.run_id], timeout=60, check=True)
    remote_run = f"{remote}:{CFG['guest_run_root']}/{audit.run_id}"
    audit.command("sync-corpus", ["rsync", "-a", "--delete", "-e", rsync_ssh(), str(contract) + "/", remote_run + "/corpus/"], timeout=900, check=True)
    per_run = (challenge_run or audit.directory) / "attestation" / "inbox"
    audit.command("sync-evidence", ["rsync", "-a", "--delete", "-e", rsync_ssh(), str(EVIDENCE_ROOT) + "/", remote_run + "/evidence/"], timeout=300, check=True)
    if per_run.is_dir():
        audit.command("sync-run-evidence", ["rsync", "-a", "-e", rsync_ssh(), str(per_run) + "/", remote_run + "/evidence/"], timeout=120, check=True)
    bundle = audit.directory / "source.bundle"
    audit.command("source-bundle", ["git", "bundle", "create", str(bundle), "HEAD"], timeout=600, check=True)
    status_value = source_status(audit)
    (audit.directory / "source-status.json").write_text(json.dumps(status_value, indent=2, sort_keys=True) + "\n")
    audit.command("sync-source-bundle", ["rsync", "-a", "-e", rsync_ssh(), str(bundle), str(audit.directory / "source-status.json"), remote_run + "/"], timeout=600, check=True)
    audit.command("guest-source", ssh_base(ip) + ["/usr/bin/python3", runner, "prepare-source", "--run-id", audit.run_id], timeout=600, check=True)


def sync_runtime_parent(audit: Audit, ip: str) -> None:
    """Snapshot current runtime source, including dirty development files, without secrets/state."""
    if not RUNTIME_ROOT.is_dir() or RUNTIME_ROOT.is_symlink():
        raise FileNotFoundError("runtime v3 source directory unavailable")
    remote = f"{CFG['guest_user']}@{ip}"
    remote_path = f"{CFG['guest_run_root']}/{audit.run_id}/runtime-parent"
    audit.command(
        "prepare-runtime-parent",
        ssh_base(ip) + ["/usr/bin/mkdir", "-p", remote_path],
        timeout=60,
        check=True,
    )
    exclusions = [
        ".git/", ".env", ".env.local", ".env.*.local", ".env.production", ".env.development", ".env.test",
        ".env.backup*", "data/", "logs/", ".pytest_cache/", "__pycache__/",
        ".venv/", "*.pyc", "*.pyo", "*.key", "*.pem", "id_rsa*", "*private_key*",
        "*secret*", "*token*", "*.backup-*", "config/bounded_commands.json", "config/*.backup*",
    ]
    literal_secret = re.compile(r'(?i)["\\\'](?:password|secret|token|api[_-]?key|private[_-]?key)["\\\']\\s*:\\s*["\\\'][^"\\\']{16,}["\\\']')
    suspicious: list[str] = []
    config_root = RUNTIME_ROOT / "config"
    if config_root.is_dir():
        for path in config_root.rglob("*"):
            if not path.is_file() or path.is_symlink() or path.name == "bounded_commands.json" or "backup" in path.name.lower():
                continue
            if path.stat().st_size > 2_000_000:
                continue
            try:
                value = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if literal_secret.search(value):
                suspicious.append(path.relative_to(RUNTIME_ROOT).as_posix())
    if suspicious:
        raise ValueError("runtime snapshot credential audit blocked files: " + ", ".join(sorted(suspicious)))
    argv = ["rsync", "-a", "--delete", "--safe-links"]
    for pattern in exclusions:
        argv.extend(["--exclude", pattern])
    argv.extend(["-e", rsync_ssh(), str(RUNTIME_ROOT) + "/", f"{remote}:{remote_path}/"])
    receipt = {
        "schema": "duotronic-runtime-parent-snapshot/v1",
        "captured_at": now(),
        "source": str(RUNTIME_ROOT),
        "destination": remote_path,
        "exclusions": exclusions,
        "sandbox_snapshot_only": True,
        "production_eligible": False,
        "contains_production_credentials": False,
        "credential_literal_scan": "passed",
        "excluded_runtime_control_registry": "config/bounded_commands.json",
    }
    (audit.directory / "runtime-parent-source.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    audit.command("sync-runtime-parent", argv, timeout=1200, check=True)


def collect(audit: Audit, ip: str) -> None:
    remote = f"{CFG['guest_user']}@{ip}:{CFG['guest_run_root']}/{audit.run_id}/"
    target = audit.directory / "vm-guest"
    target.mkdir(parents=True, exist_ok=True)
    audit.command("collect", ["rsync", "-a", "-e", rsync_ssh(), remote, str(target) + "/"], timeout=900, check=True)


def do_status(_: argparse.Namespace) -> int:
    audit = Audit("status")
    tools = {name: shutil.which(name) for name in ("virsh", "ssh", "rsync")}
    state = domain_state(audit) if tools["virsh"] else "host-not-installed"
    return audit.finish("ready" if state not in {"undefined", "host-not-installed"} else "blocked", domain_state=state, tools=tools)


def do_start(_: argparse.Namespace) -> int:
    audit = Audit("start")
    ip = ensure_started(audit)
    return audit.finish("running", guest_ip=ip)


def do_stop(args: argparse.Namespace) -> int:
    audit = Audit("stop")
    stop_vm(audit, force=args.force)
    return audit.finish("stopped", forced=args.force)


def do_build(args: argparse.Namespace) -> int:
    audit = Audit("build")
    ip = ensure_started(audit)
    state = "blocked"
    result: dict[str, Any] = {"exit_code": 70}
    error: str | None = None
    try:
        sync_harness(audit, ip)
        runner = f"{CFG['guest_harness_root']}/vm/guest/guest_runner.py"
        result = audit.command("guest-build", ssh_base(ip) + [
            "/usr/bin/python3", runner, "build", "--run-id", audit.run_id,
            "--layer", args.layer, "--timeout", str(args.timeout),
        ], timeout=args.timeout * 2 + 600)
        collect(audit, ip)
        state = "completed" if result["exit_code"] == 0 else "blocked"
    except Exception as exc:
        error = str(exc)
        audit.emit("build_failed", error=error)
    finally:
        if CFG.get("auto_shutdown_after_run") and not args.keep_running:
            try:
                stop_vm(audit, force=False)
            except Exception as exc:
                audit.emit("automatic_shutdown_failed", error=str(exc))
                if error is None:
                    error = "automatic shutdown failed: " + str(exc)
                    state = "blocked"
    return audit.finish(
        state,
        layer=args.layer,
        guest_exit_code=result["exit_code"],
        error=error,
        automatic_shutdown_requested=bool(CFG.get("auto_shutdown_after_run") and not args.keep_running),
    )


def do_run(args: argparse.Namespace) -> int:
    audit = Audit("gate-run")
    contract = resolve_contract(args.version)
    challenge_run: Path | None = None
    evidence_run_id: str | None = None
    if args.attestation_run_id:
        if not RUN_RE.fullmatch(args.attestation_run_id):
            raise ValueError("invalid attestation run id")
        challenge_run = (LOG_ROOT / args.attestation_run_id).resolve()
        if challenge_run.parent != LOG_ROOT.resolve() or not challenge_run.is_dir():
            raise ValueError("attestation challenge run unavailable")
        bundle_path = challenge_run / "attestation" / "request-bundle.json"
        bundle = json.loads(bundle_path.read_text())
        request_run_ids = {
            item.get("probe", {}).get("run_id")
            for item in bundle.get("requests", [])
            if item.get("probe", {}).get("run_id")
        }
        if len(request_run_ids) != 1:
            raise ValueError("attestation bundle must bind exactly one probe run")
        evidence_run_id = request_run_ids.pop()
    ip = ensure_started(audit)
    state = "blocked"
    result: dict[str, Any] = {"exit_code": 70}
    error: str | None = None
    try:
        sync_inputs(audit, ip, contract, challenge_run)
        runner = f"{CFG['guest_harness_root']}/vm/guest/guest_runner.py"
        argv = ssh_base(ip) + [
            "/usr/bin/python3", runner, "execute", "--run-id", audit.run_id,
            "--qualification-mode", args.qualification_mode, "--timeout", str(args.timeout),
        ]
        if evidence_run_id:
            argv.extend(["--evidence-run-id", evidence_run_id])
        if args.gate:
            if not GATE_RE.fullmatch(args.gate):
                raise ValueError("invalid gate")
            argv.extend(["--gate", args.gate])
        result = audit.command("guest-execute", argv, timeout=args.timeout + 600)
        collect(audit, ip)
        state = "completed" if result["exit_code"] == 0 else "blocked"
    except Exception as exc:
        error = str(exc)
        audit.emit("run_failed", error=error)
    finally:
        if CFG.get("auto_shutdown_after_run") and not args.keep_running:
            try:
                stop_vm(audit, force=False)
            except Exception as exc:
                audit.emit("automatic_shutdown_failed", error=str(exc))
                if error is None:
                    error = "automatic shutdown failed: " + str(exc)
                    state = "blocked"
    return audit.finish(
        state,
        contract=str(contract),
        selected_gate=args.gate,
        guest_exit_code=result["exit_code"],
        error=error,
        automatic_shutdown_requested=bool(CFG.get("auto_shutdown_after_run") and not args.keep_running),
        attestation_run_id=args.attestation_run_id,
        evidence_probe_run_id=evidence_run_id,
    )




def do_sandbox_status(args: argparse.Namespace) -> int:
    """Read persisted sandbox-runtime authority without contacting production."""
    audit = Audit("sandbox-status")
    ip = ensure_started(audit)
    state = "blocked"
    guest_status: dict[str, Any] | None = None
    error: str | None = None
    result: dict[str, Any] = {"exit_code": 70}
    try:
        sync_harness(audit, ip)
        runner = f"{CFG['guest_harness_root']}/vm/guest/guest_runner.py"
        result = audit.command(
            "guest-sandbox-status",
            ssh_base(ip) + ["/usr/bin/python3", runner, "status"],
            timeout=180,
        )
        if result["exit_code"] == 0:
            guest_status = json.loads(result["stdout"])
            state = "completed"
        else:
            error = "guest sandbox status failed"
    except Exception as exc:
        error = str(exc)
        audit.emit("sandbox_status_failed", error=error)
    finally:
        if CFG.get("auto_shutdown_after_run") and not args.keep_running:
            try:
                stop_vm(audit, force=False)
            except Exception as exc:
                audit.emit("automatic_shutdown_failed", error=str(exc))
                if error is None:
                    error = "automatic shutdown failed: " + str(exc)
                    state = "blocked"
    active = bool(guest_status and guest_status.get("authority_activated") is True)
    return audit.finish(
        state,
        guest_exit_code=result["exit_code"],
        error=error,
        authority_activated=active,
        authority_scope="sandbox-only" if active else "none",
        authority_profile=CFG["sandbox_authority_profile"],
        authority_namespace=CFG["sandbox_authority_namespace"],
        production_eligible=False,
        production_authority_activated=False,
        production_runtime_connected=False,
        sandbox_authority=guest_status.get("sandbox_authority") if guest_status else None,
        automatic_shutdown_requested=bool(
            CFG.get("auto_shutdown_after_run") and not args.keep_running
        ),
    )


def do_sandbox_activate(args: argparse.Namespace) -> int:
    """Qualify, independently attest, verify, and activate the VM sandbox only."""
    audit = Audit("sandbox-activate")
    contract = resolve_contract(args.version)
    ip = ensure_started(audit)
    state = "blocked"
    result: dict[str, Any] = {"exit_code": 70}
    activation: dict[str, Any] | None = None
    error: str | None = None
    try:
        sync_inputs(audit, ip, contract)
        runner = f"{CFG['guest_harness_root']}/vm/guest/guest_runner.py"
        result = audit.command(
            "guest-sandbox-activate",
            ssh_base(ip) + [
                "/usr/bin/python3", runner, "sandbox-activate",
                "--run-id", audit.run_id,
                "--authority-namespace", CFG["sandbox_authority_namespace"],
                "--timeout", str(args.timeout),
            ],
            timeout=args.timeout * 3 + 1200,
        )
        collect(audit, ip)
        activation_path = audit.directory / "vm-guest" / "guest" / "sandbox-activation.json"
        if activation_path.is_file():
            activation = json.loads(activation_path.read_text(encoding="utf-8"))
        valid = bool(
            activation
            and activation.get("state") == "active"
            and activation.get("authority_activated") is True
            and activation.get("authority_scope") == "sandbox-only"
            and activation.get("authority_profile") == CFG["sandbox_authority_profile"]
            and activation.get("authority_namespace") == CFG["sandbox_authority_namespace"]
            and activation.get("production_eligible") is False
            and activation.get("production_authority_activated") is False
            and activation.get("production_runtime_connected") is False
            and activation.get("verified_gate_count") == 12
        )
        state = "completed" if result["exit_code"] == 0 and valid else "blocked"
        if not valid:
            error = "guest did not produce a valid sandbox-only authority record"
    except Exception as exc:
        error = str(exc)
        audit.emit("sandbox_activation_failed", error=error)
    finally:
        if CFG.get("auto_shutdown_after_run") and not args.keep_running:
            try:
                stop_vm(audit, force=False)
            except Exception as exc:
                audit.emit("automatic_shutdown_failed", error=str(exc))
                if error is None:
                    error = "automatic shutdown failed: " + str(exc)
                    state = "blocked"
    return audit.finish(
        state,
        contract=str(contract),
        guest_exit_code=result["exit_code"],
        error=error,
        authority_activated=bool(activation and state == "completed"),
        authority_scope="sandbox-only" if activation and state == "completed" else "none",
        authority_profile=CFG["sandbox_authority_profile"],
        authority_namespace=CFG["sandbox_authority_namespace"],
        production_eligible=False,
        production_authority_activated=False,
        production_runtime_connected=False,
        verified_gate_count=activation.get("verified_gate_count", 0) if activation else 0,
        activation_id=activation.get("activation_id") if activation else None,
        automatic_shutdown_requested=bool(
            CFG.get("auto_shutdown_after_run") and not args.keep_running
        ),
    )


def _named_input(root: Path, name: str, *, directory: bool) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}", name) or ".." in name:
        raise ValueError("invalid named harness input")
    root.mkdir(parents=True, exist_ok=True)
    candidate = (root / name).resolve(strict=True)
    if candidate.parent != root.resolve(strict=True) or candidate.is_symlink():
        raise ValueError("named harness input escaped its root")
    if directory != candidate.is_dir():
        raise ValueError("named harness input has the wrong type")
    return candidate


def do_paired_cycle(args: argparse.Namespace) -> int:
    """Create and exercise a corpus/runtime pair entirely inside the VM."""
    audit = Audit("paired-cycle")
    contract = resolve_contract(args.version)
    ip = ensure_started(audit)
    state = "blocked"
    error: str | None = None
    result: dict[str, Any] = {"exit_code": 70}
    exported: str | None = None
    report: dict[str, Any] | None = None
    try:
        sync_inputs(audit, ip, contract)
        sync_runtime_parent(audit, ip)
        remote_run = f"{CFG['guest_run_root']}/{audit.run_id}"
        audit.command(
            "prepare-paired-inputs",
            ssh_base(ip) + ["/usr/bin/mkdir", "-p", remote_run + "/external-data", remote_run + "/proposal"],
            timeout=60, check=True,
        )
        staged_external = audit.directory / "external-data"
        staged_external.mkdir(parents=True, exist_ok=False)
        if args.external_data_set:
            source = _named_input(EXTERNAL_DATA_ROOT, args.external_data_set, directory=True)
            shutil.copytree(source, staged_external, dirs_exist_ok=True, symlinks=False)
        audit.command(
            "sync-external-data",
            ["rsync", "-a", "--delete", "-e", rsync_ssh(), str(staged_external) + "/", f"{CFG['guest_user']}@{ip}:{remote_run}/external-data/"],
            timeout=900, check=True,
        )
        if args.proposal:
            proposal = _named_input(PROPOSAL_ROOT, args.proposal, directory=False)
            audit.command(
                "sync-paired-proposal",
                ["rsync", "-a", "-e", rsync_ssh(), str(proposal), f"{CFG['guest_user']}@{ip}:{remote_run}/proposal/proposal.json"],
                timeout=120, check=True,
            )
        runner = f"{CFG['guest_harness_root']}/vm/guest/guest_runner.py"
        result = audit.command(
            "guest-paired-cycle",
            ssh_base(ip) + ["/usr/bin/python3", runner, "paired-cycle", "--run-id", audit.run_id, "--timeout", str(args.timeout)],
            timeout=args.timeout * 3 + 1800,
        )
        collect(audit, ip)
        report_path = audit.directory / "vm-guest" / "guest" / "paired-cycle.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            qualified = (
                result["exit_code"] == 0
                and report.get("state") == "active"
                and report.get("verified_gate_count") == 12
                and report.get("authority_activated") is True
                and report.get("production_eligible") is False
            )
            pair_id = str(report.get("pair_manifest", {}).get("pair_id", ""))
            suffix = re.sub(r"[^A-Za-z0-9]", "", pair_id)[-24:] or audit.run_id[-24:]
            lane = "qualified" if qualified else "blocked"
            destination = PAIRED_CANDIDATE_ROOT / lane / suffix
            source_pair = audit.directory / "vm-guest" / "paired-output" / "pair"
            if destination.exists():
                raise FileExistsError(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_pair, destination, symlinks=False)
            (destination / "qualification.json").write_text(
                json.dumps(
                    {
                        "schema": "duotronic-paired-candidate-qualification/v1",
                        "run_id": audit.run_id,
                        "state": "qualified" if qualified else "blocked",
                        "verified_gate_count": report.get("verified_gate_count", 0),
                        "authority_activated": report.get("authority_activated") is True,
                        "production_eligible": False,
                        "source_evidence": str(audit.directory),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            exported = str(destination)
            if qualified:
                state = "completed"
            else:
                error = "paired candidate exported to blocked lane; runtime qualification did not pass"
        else:
            error = "paired-cycle report missing"
    except Exception as exc:
        error = str(exc)
        audit.emit("paired_cycle_failed", error=error)
    finally:
        if CFG.get("auto_shutdown_after_run") and not args.keep_running:
            try:
                stop_vm(audit, force=False)
            except Exception as exc:
                audit.emit("automatic_shutdown_failed", error=str(exc))
                if error is None:
                    error = "automatic shutdown failed: " + str(exc)
                    state = "blocked"
    return audit.finish(
        state,
        contract=str(contract),
        guest_exit_code=result["exit_code"],
        paired_candidate_directory=exported,
        external_data_set=args.external_data_set,
        proposal=args.proposal,
        error=error,
        authority_activated=bool(report and report.get("authority_activated") is True),
        authority_scope="sandbox-only" if report and report.get("authority_activated") is True else "none",
        verified_gate_count=report.get("verified_gate_count", 0) if report else 0,
        paired_candidate_report=report,
        authority_profile=CFG["sandbox_authority_profile"],
        production_eligible=False,
        production_authority_activated=False,
        production_runtime_connected=False,
        host_podman_invoked=False,
        automatic_shutdown_requested=bool(CFG.get("auto_shutdown_after_run") and not args.keep_running),
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Libvirt-isolated witness harness control")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sandbox_status = sub.add_parser("sandbox-status")
    sandbox_status.add_argument("--keep-running", action="store_true")
    sub.add_parser("start")
    stop = sub.add_parser("stop")
    stop.add_argument("--force", action="store_true")
    build = sub.add_parser("build")
    build.add_argument("--layer", choices=("toolchain", "thin", "all"), default="all")
    build.add_argument("--timeout", type=int, default=3600)
    build.add_argument("--keep-running", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("--version", required=True)
    run.add_argument("--gate")
    run.add_argument("--attestation-run-id")
    run.add_argument("--qualification-mode", choices=("full", "targeted"), default="full")
    run.add_argument("--timeout", type=int, default=1800)
    run.add_argument("--keep-running", action="store_true")
    activate = sub.add_parser("sandbox-activate")
    activate.add_argument("--version", required=True)
    activate.add_argument("--timeout", type=int, default=3600)
    activate.add_argument("--keep-running", action="store_true")
    pair = sub.add_parser("paired-cycle")
    pair.add_argument("--version", required=True)
    pair.add_argument("--external-data-set")
    pair.add_argument("--proposal")
    pair.add_argument("--timeout", type=int, default=3600)
    pair.add_argument("--keep-running", action="store_true")
    return root


class ControllerTermination(Exception):
    """Convert supervisor termination into normal controller cleanup."""


def handle_termination(signum: int, _frame: Any) -> None:
    raise ControllerTermination(f"controller received signal {signum}")


def main() -> int:
    signal.signal(signal.SIGTERM, handle_termination)
    args = parser().parse_args()
    if args.command == "status":
        return do_status(args)
    if args.command == "sandbox-status":
        return do_sandbox_status(args)
    if args.command == "start":
        return do_start(args)
    if args.command == "stop":
        return do_stop(args)
    if args.command == "build":
        return do_build(args)
    if args.command == "run":
        return do_run(args)
    if args.command == "sandbox-activate":
        return do_sandbox_activate(args)
    if args.command == "paired-cycle":
        return do_paired_cycle(args)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
