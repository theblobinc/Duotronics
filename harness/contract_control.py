#!/usr/bin/env python3
"""MCP-facing lifecycle controller for witness-contract development and runtime rollout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HARNESS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path("/var/www/xavi/Duotronics")
CONTRACT_ROOT = REPO_ROOT / "build_docs/witness_contract"
WORKSPACE_ROOT = HARNESS_ROOT / "workspaces"
LOG_ROOT = HARNESS_ROOT / "logs"
STATE_ROOT = HARNESS_ROOT / "state"
SNAPSHOT_ROOT = STATE_ROOT / "snapshots"
RUNTIME_ROOT = REPO_ROOT / "build_docs/runtime/duotronic_srnn_open_runtime-v3"
ACTIVE_STATE = RUNTIME_ROOT / "config/active_witness_contract.json"
STAGED_STATE = STATE_ROOT / "staged-contract.json"
RESTART_HELPER = RUNTIME_ROOT / "ops_agent/v3_maintenance/restart_runtime_only.sh"
VM_CONTROL = HARNESS_ROOT / "vm_control.py"
DEVELOPMENT_CONFIRMATION = "ALLOW_NONAUTHORITATIVE_DEVELOPMENT_ACTIVATION"
ROLLBACK_CONFIRMATION = "ROLLBACK_ACTIVE_WITNESS_CONTRACT"
DISCARD_CONFIRMATION = "DISCARD_WITNESS_CONTRACT_WORKSPACE"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,119}$")
IGNORED_PARTS = {".git", ".lake", ".pytest_cache", "__pycache__", ".hypothesis", ".mypy_cache"}
HASH_CHUNK = 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{uuid.uuid4().hex[:8]}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


class Audit:
    def __init__(self, action: str) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_id = f"{stamp}-contract-{action}-{uuid.uuid4().hex[:10]}"
        self.directory = LOG_ROOT / self.run_id
        self.directory.mkdir(parents=True, exist_ok=False)
        self.events = self.directory / "contract-control.jsonl"
        self.emit("start", action=action, argv=sys.argv, uid=os.geteuid(), runtime_connected=False)

    def emit(self, event: str, **fields: Any) -> None:
        row = {"at": now(), "run_id": self.run_id, "event": event, **fields}
        with self.events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def finish(self, result: dict[str, Any], exit_code: int = 0) -> int:
        result = {
            "run_id": self.run_id,
            "authority_activated": False,
            "result_log": str(self.directory),
            **result,
        }
        atomic_json(self.directory / "result.json", result)
        self.emit("finish", exit_code=exit_code, state=result.get("state"))
        print(json.dumps(result, indent=2, sort_keys=True))
        print(str(self.directory))
        return exit_code


def valid_name(value: str) -> str:
    if not NAME_RE.fullmatch(value) or value in {".", ".."} or ".." in value:
        raise ValueError("version must be a simple 1-120 character directory name without traversal")
    return value


def confined_child(root: Path, name: str, *, must_exist: bool = True) -> Path:
    name = valid_name(name)
    root_resolved = root.resolve(strict=True)
    candidate = root / name
    resolved = candidate.resolve(strict=must_exist)
    if resolved.parent != root_resolved:
        raise ValueError("version escaped its allowed root")
    if must_exist and (not resolved.is_dir() or candidate.is_symlink()):
        raise ValueError("version is not a normal directory")
    return candidate


def split_ref(ref: str) -> tuple[str | None, str]:
    if ":" in ref:
        scope, name = ref.split(":", 1)
        if scope not in {"workspace", "published"}:
            raise ValueError("version scope must be workspace: or published:")
        return scope, valid_name(name)
    return None, valid_name(ref)


def resolve_ref(ref: str, *, published_only: bool = False) -> tuple[str, Path]:
    scope, name = split_ref(ref)
    if published_only and scope == "workspace":
        raise ValueError("runtime actions require a published contract")
    candidates: list[tuple[str, Path]] = []
    if not published_only and scope in (None, "workspace"):
        candidate = WORKSPACE_ROOT / name
        if candidate.is_dir() and not candidate.is_symlink():
            candidates.append(("workspace", confined_child(WORKSPACE_ROOT, name)))
    if scope in (None, "published"):
        candidate = CONTRACT_ROOT / name
        if candidate.is_dir() and not candidate.is_symlink():
            candidates.append(("published", confined_child(CONTRACT_ROOT, name)))
    if not candidates:
        raise FileNotFoundError(f"contract version not found: {ref}")
    if len(candidates) > 1:
        raise ValueError(f"ambiguous version {name}; use workspace:{name} or published:{name}")
    return candidates[0]


def ignored(path: Path) -> bool:
    return any(part in IGNORED_PARTS for part in path.parts)


def files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            rel = path.relative_to(root)
            if not ignored(rel):
                yield path, rel


def inventory_one(scope: str, path: Path) -> dict[str, Any]:
    count = 0
    total = 0
    newest_ns = 0
    for item, _ in files(path):
        stat = item.stat()
        count += 1
        total += stat.st_size
        newest_ns = max(newest_ns, stat.st_mtime_ns)
    return {
        "ref": f"{scope}:{path.name}",
        "scope": scope,
        "name": path.name,
        "path": str(path),
        "file_count": count,
        "bytes": total,
        "newest_mtime_ns": newest_ns,
        "mutable": scope == "workspace",
        "runtime_eligible_scope": scope == "published",
    }


def all_versions() -> list[dict[str, Any]]:
    rows = []
    for scope, root in (("workspace", WORKSPACE_ROOT), ("published", CONTRACT_ROOT)):
        root.mkdir(parents=True, exist_ok=True)
        for path in sorted(root.iterdir()):
            if path.is_dir() and not path.is_symlink() and NAME_RE.fullmatch(path.name):
                rows.append(inventory_one(scope, path))
    return rows


def copy_ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORED_PARTS or name.endswith(".pyc")}


def command_list(_args: argparse.Namespace, audit: Audit) -> int:
    active = json.loads(ACTIVE_STATE.read_text()) if ACTIVE_STATE.is_file() else None
    staged = json.loads(STAGED_STATE.read_text()) if STAGED_STATE.is_file() else None
    rows = all_versions()
    return audit.finish({
        "state": "ok",
        "versions": rows,
        "count": len(rows),
        "active": active,
        "staged": staged,
        "runtime_connected": False,
    })


def command_create(args: argparse.Namespace, audit: Audit) -> int:
    name = valid_name(args.version)
    destination = confined_child(WORKSPACE_ROOT, name, must_exist=False)
    if destination.exists():
        raise FileExistsError(f"workspace already exists: {name}")
    parent_scope, parent = resolve_ref(args.parent)
    audit.emit("copy_start", parent=str(parent), destination=str(destination))
    temporary = WORKSPACE_ROOT / f".creating-{uuid.uuid4().hex}"
    shutil.copytree(parent, temporary, symlinks=False, ignore=copy_ignore)
    os.replace(temporary, destination)
    metadata = {
        "schema": "duotronic-witness-development-workspace/v1",
        "version": name,
        "parent_ref": f"{parent_scope}:{parent.name}",
        "created_at": now(),
        "mutable": True,
        "authority_activated": False,
        "runtime_connected": False,
    }
    atomic_json(STATE_ROOT / "workspaces" / f"{name}.json", metadata)
    return audit.finish({"state": "created", "workspace": inventory_one("workspace", destination), "metadata": metadata, "runtime_connected": False})


def digest_file(path: Path) -> str:
    digest = hashlib.shake_256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK), b""):
            digest.update(chunk)
    return "shake256-512:" + digest.hexdigest(64)


def snapshot(scope: str, path: Path) -> dict[str, Any]:
    entries = []
    tree = hashlib.shake_256()
    for item, rel in files(path):
        digest = digest_file(item)
        stat = item.stat()
        entry = {"path": rel.as_posix(), "bytes": stat.st_size, "digest": digest}
        entries.append(entry)
        tree.update(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode())
        tree.update(b"\n")
    return {
        "schema": "duotronic-witness-corpus-snapshot/v1",
        "algorithm": "SHAKE256-512",
        "ref": f"{scope}:{path.name}",
        "path": str(path),
        "created_at": now(),
        "file_count": len(entries),
        "bytes": sum(item["bytes"] for item in entries),
        "corpus_root": "shake256-512:" + tree.hexdigest(64),
        "files": entries,
    }


def command_snapshot(args: argparse.Namespace, audit: Audit) -> int:
    scope, path = resolve_ref(args.version)
    result = snapshot(scope, path)
    target = SNAPSHOT_ROOT / f"{scope}-{path.name}.json"
    atomic_json(target, result)
    return audit.finish({"state": "snapshotted", "snapshot": result, "snapshot_path": str(target), "runtime_connected": False})


def command_status(args: argparse.Namespace, audit: Audit) -> int:
    scope, path = resolve_ref(args.version)
    metadata_path = STATE_ROOT / "workspaces" / f"{path.name}.json"
    metadata = json.loads(metadata_path.read_text()) if metadata_path.is_file() else None
    return audit.finish({"state": "ok", "contract": inventory_one(scope, path), "workspace_metadata": metadata, "runtime_connected": False})


def workspace_parent(name: str) -> tuple[str, Path]:
    metadata_path = STATE_ROOT / "workspaces" / f"{name}.json"
    if not metadata_path.is_file():
        raise ValueError("workspace parent metadata is missing")
    metadata = json.loads(metadata_path.read_text())
    return resolve_ref(str(metadata["parent_ref"]))


def command_diff(args: argparse.Namespace, audit: Audit) -> int:
    scope, path = resolve_ref(args.version)
    if scope != "workspace":
        raise ValueError("diff requires a workspace")
    parent_scope, parent = workspace_parent(path.name)
    left = {rel.as_posix(): digest_file(item) for item, rel in files(parent)}
    right = {rel.as_posix(): digest_file(item) for item, rel in files(path)}
    added = sorted(right.keys() - left.keys())
    removed = sorted(left.keys() - right.keys())
    changed = sorted(name for name in right.keys() & left.keys() if right[name] != left[name])
    return audit.finish({
        "state": "ok",
        "workspace": f"workspace:{path.name}",
        "parent": f"{parent_scope}:{parent.name}",
        "added": added,
        "removed": removed,
        "changed": changed,
        "counts": {"added": len(added), "removed": len(removed), "changed": len(changed)},
        "runtime_connected": False,
    })


def command_sandbox(args: argparse.Namespace, audit: Audit) -> int:
    scope, path = resolve_ref(args.version)
    qualification_mode = "targeted" if args.gate else "full"
    argv = [
        sys.executable, str(VM_CONTROL), "run",
        "--version", f"{scope}:{path.name}",
        "--qualification-mode", qualification_mode,
        "--timeout", str(args.timeout),
    ]
    if args.gate:
        argv.extend(["--gate", args.gate])
    audit.emit("sandbox_start", contract_ref=f"{scope}:{path.name}", qualification_mode=qualification_mode, argv=argv)
    completed = subprocess.run(argv, cwd=HARNESS_ROOT, text=True, capture_output=True, timeout=args.timeout + 300, check=False)
    (audit.directory / "sandbox.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (audit.directory / "sandbox.stderr.log").write_text(completed.stderr, encoding="utf-8")
    return audit.finish({
        "state": "sandbox_complete" if completed.returncode in {0, 1, 2} else "sandbox_error",
        "contract_ref": f"{scope}:{path.name}",
        "sandbox_exit_code": completed.returncode,
        "selected_gate": args.gate,
        "runtime_connected": False,
    }, 0 if completed.returncode in {0, 1, 2} else 1)


def command_publish(args: argparse.Namespace, audit: Audit) -> int:
    scope, source = resolve_ref(args.version)
    if scope != "workspace":
        raise ValueError("publish requires a workspace")
    target_name = valid_name(args.as_version or source.name)
    destination = confined_child(CONTRACT_ROOT, target_name, must_exist=False)
    if destination.exists():
        raise FileExistsError(f"published contract already exists: {target_name}")
    prepublish = snapshot(scope, source)
    temporary = CONTRACT_ROOT / f".publishing-{uuid.uuid4().hex}"
    shutil.copytree(source, temporary, symlinks=False, ignore=copy_ignore)
    os.replace(temporary, destination)
    record = {
        "schema": "duotronic-witness-publish-record/v1",
        "published_at": now(),
        "workspace_ref": f"workspace:{source.name}",
        "published_ref": f"published:{target_name}",
        "corpus_root": prepublish["corpus_root"],
        "authority_activated": False,
        "runtime_connected": False,
    }
    atomic_json(STATE_ROOT / "published" / f"{target_name}.json", record)
    return audit.finish({"state": "published", "contract": inventory_one("published", destination), "publish_record": record, "runtime_connected": False})


def report_is_qualified(report: dict[str, Any], path: Path) -> tuple[bool, list[str]]:
    reasons = []
    if report.get("tested_corpus_path") != str(path.resolve()):
        reasons.append("report_contract_mismatch")
    if report.get("state") != "verified":
        reasons.append("aggregate_not_verified")
    if not report.get("activation_eligible"):
        reasons.append("activation_not_eligible")
    if not report.get("qualification_complete"):
        reasons.append("qualification_incomplete")
    if not report.get("runtime_handoff_eligible"):
        reasons.append("runtime_handoff_ineligible")
    if not (report.get("cleanup") or {}).get("cleaned"):
        reasons.append("sandbox_cleanup_unproven")
    if not (report.get("host_sandbox_controls") or {}).get("passed"):
        reasons.append("sandbox_controls_unproven")
    return not reasons, reasons


def report_path(value: str | None, contract: Path) -> Path | None:
    if value and value != "latest":
        candidate = Path(value).expanduser().resolve(strict=True)
        if LOG_ROOT.resolve() not in candidate.parents or candidate.name != "aggregate-report.json":
            raise ValueError("qualification report must be an aggregate-report.json inside harness/logs")
        return candidate
    for candidate in sorted(LOG_ROOT.glob("*/aggregate-report.json"), reverse=True):
        try:
            report = json.loads(candidate.read_text())
        except Exception:
            continue
        if report.get("tested_corpus_path") == str(contract.resolve()):
            return candidate
    return None


def command_stage(args: argparse.Namespace, audit: Audit) -> int:
    scope, path = resolve_ref(args.version, published_only=True)
    candidate_report = report_path(args.report, path)
    report = json.loads(candidate_report.read_text()) if candidate_report else {}
    qualified, reasons = report_is_qualified(report, path) if candidate_report else (False, ["qualification_report_missing"])
    snap = snapshot(scope, path)
    staged = {
        "schema": "duotronic-witness-runtime-stage/v1",
        "staged_at": now(),
        "contract_ref": f"published:{path.name}",
        "directory_name": path.name,
        "corpus_path": str(path),
        "corpus_root": snap["corpus_root"],
        "qualification_report": str(candidate_report) if candidate_report else None,
        "qualified": qualified,
        "qualification_blockers": reasons,
        "authority_activated": False,
        "runtime_connected": False,
    }
    atomic_json(STAGED_STATE, staged)
    return audit.finish({"state": "staged", "staged": staged, "runtime_connected": False})


def run_fixed(audit: Audit, phase: str, argv: list[str], timeout: int) -> dict[str, Any]:
    audit.emit("command_start", phase=phase, argv=argv, timeout=timeout)
    started = time.monotonic()
    try:
        done = subprocess.run(argv, cwd=RUNTIME_ROOT, text=True, capture_output=True, timeout=timeout, check=False)
        result = {"exit_code": done.returncode, "stdout": done.stdout[-500000:], "stderr": done.stderr[-500000:], "timed_out": False}
    except subprocess.TimeoutExpired as error:
        result = {"exit_code": 124, "stdout": str(error.stdout or "")[-500000:], "stderr": str(error.stderr or "")[-500000:], "timed_out": True}
    result["elapsed_seconds"] = round(time.monotonic() - started, 6)
    (audit.directory / f"{phase}.stdout.log").write_text(result["stdout"], encoding="utf-8")
    (audit.directory / f"{phase}.stderr.log").write_text(result["stderr"], encoding="utf-8")
    audit.emit("command_finish", phase=phase, exit_code=result["exit_code"], elapsed_seconds=result["elapsed_seconds"])
    return result


def restart_and_health(audit: Audit) -> dict[str, Any]:
    build = run_fixed(
        audit,
        "runtime-image-build",
        ["podman", "--remote=false", "build", "--pull=never", "--file", "Containerfile", "--tag", "localhost/duotronic-srnn-runtime-host:latest", "."],
        1800,
    )
    if build["exit_code"] != 0:
        return {"passed": False, "build": build, "restart": None, "health": None, "health_payload": None}
    restart = run_fixed(audit, "runtime-restart", ["bash", str(RESTART_HELPER)], 600)
    health = run_fixed(audit, "runtime-health", ["podman", "--remote=false", "exec", "duotronic-runtime", "curl", "-fsS", "--max-time", "15", "http://127.0.0.1:8080/health"], 30)
    payload = None
    if health["exit_code"] == 0:
        try:
            payload = json.loads(health["stdout"])
        except json.JSONDecodeError:
            payload = None
    return {"passed": restart["exit_code"] == 0 and health["exit_code"] == 0, "build": build, "restart": restart, "health": health, "health_payload": payload}


def command_activate(args: argparse.Namespace, audit: Audit) -> int:
    _scope, path = resolve_ref(args.version, published_only=True)
    if not STAGED_STATE.is_file():
        raise ValueError("no contract is staged")
    staged = json.loads(STAGED_STATE.read_text())
    if staged.get("directory_name") != path.name:
        raise ValueError("staged contract does not match requested activation")
    if args.mode == "qualified":
        if not staged.get("qualified"):
            raise ValueError("qualified activation is blocked: " + ",".join(staged.get("qualification_blockers") or []))
    elif args.confirmation != DEVELOPMENT_CONFIRMATION:
        raise ValueError("development activation requires the exact non-authoritative confirmation token")

    previous = json.loads(ACTIVE_STATE.read_text()) if ACTIVE_STATE.is_file() else None
    active = {
        "schema": "duotronic-active-witness-contract/v1",
        "directory_name": path.name,
        "contract_ref": f"published:{path.name}",
        "corpus_path": str(path),
        "corpus_root": staged.get("corpus_root"),
        "activation_mode": args.mode,
        "qualification_report": staged.get("qualification_report"),
        "activated_at": now(),
        "activated_via": "xavi-ops-mcp",
        "non_authoritative": args.mode == "development",
        "previous": previous,
    }
    atomic_json(ACTIVE_STATE, active)
    audit.emit("active_state_written", contract_ref=active["contract_ref"], mode=args.mode)
    outcome = restart_and_health(audit)
    if not outcome["passed"]:
        if previous is None:
            ACTIVE_STATE.unlink(missing_ok=True)
        else:
            atomic_json(ACTIVE_STATE, previous)
        rollback = (
            {"passed": True, "reason": "build_failed_before_runtime_restart"}
            if outcome.get("restart") is None
            else restart_and_health(audit)
        )
        return audit.finish({
            "state": "activation_failed_rolled_back",
            "requested": active,
            "rollback_runtime": rollback,
            "runtime": outcome,
            "runtime_connected": True,
        }, 1)
    return audit.finish({"state": "active", "active": active, "runtime": outcome, "runtime_connected": True})


def command_rollback(args: argparse.Namespace, audit: Audit) -> int:
    if args.confirmation != ROLLBACK_CONFIRMATION:
        raise ValueError("rollback requires the exact confirmation token")
    if not ACTIVE_STATE.is_file():
        raise ValueError("no active contract state exists")
    current = json.loads(ACTIVE_STATE.read_text())
    previous = current.get("previous")
    if not isinstance(previous, dict):
        raise ValueError("no previous active contract is recorded")
    atomic_json(ACTIVE_STATE, previous)
    outcome = restart_and_health(audit)
    if not outcome["passed"]:
        atomic_json(ACTIVE_STATE, current)
        recovery = (
            {"passed": True, "reason": "build_failed_before_runtime_restart"}
            if outcome.get("restart") is None
            else restart_and_health(audit)
        )
        return audit.finish({"state": "rollback_failed_recovered_current", "runtime": outcome, "recovery": recovery, "runtime_connected": True}, 1)
    return audit.finish({"state": "rolled_back", "from": current.get("contract_ref"), "active": previous, "runtime": outcome, "runtime_connected": True})


def command_runtime_status(_args: argparse.Namespace, audit: Audit) -> int:
    active = json.loads(ACTIVE_STATE.read_text()) if ACTIVE_STATE.is_file() else None
    container = run_fixed(audit, "runtime-container-status", ["podman", "--remote=false", "inspect", "duotronic-runtime"], 30)
    container_state: dict[str, Any] = {}
    if container["exit_code"] == 0:
        try:
            inspected = json.loads(container["stdout"])
            item = inspected[0] if isinstance(inspected, list) else inspected
            container_state = {
                "running": bool((item.get("State") or {}).get("Running")),
                "status": (item.get("State") or {}).get("Status"),
                "health": ((item.get("State") or {}).get("Health") or {}).get("Status"),
                "image": item.get("ImageName"),
            }
        except Exception:
            container_state = {"parse_error": True}
    health = run_fixed(audit, "runtime-health", ["podman", "--remote=false", "exec", "duotronic-runtime", "curl", "-fsS", "--max-time", "10", "http://127.0.0.1:8080/health"], 20)
    healthy = bool(container_state.get("running")) and health["exit_code"] == 0
    return audit.finish({
        "state": "ok" if healthy else "degraded",
        "active": active,
        "fallback_contract": "published:v1.6 - Draft 5.3.16" if active is None else None,
        "container_inspect_exit_code": container["exit_code"],
        "container": container_state,
        "health_exit_code": health["exit_code"],
        "health_body": health["stdout"][-20000:],
        "runtime_connected": True,
    }, 0 if healthy else 1)


def command_discard(args: argparse.Namespace, audit: Audit) -> int:
    if args.confirmation != DISCARD_CONFIRMATION:
        raise ValueError("discard requires the exact confirmation token")
    scope, path = resolve_ref(args.version)
    if scope != "workspace":
        raise ValueError("published contracts cannot be discarded by this controller")
    removed = str(path)
    shutil.rmtree(path)
    (STATE_ROOT / "workspaces" / f"{path.name}.json").unlink(missing_ok=True)
    return audit.finish({"state": "discarded", "workspace": removed, "recoverable": False, "runtime_connected": False})


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="MCP-controlled witness-contract lifecycle")
    sub = result.add_subparsers(dest="action", required=True)
    sub.add_parser("list")
    for name in ("status", "snapshot", "diff"):
        item = sub.add_parser(name)
        item.add_argument("--version", required=True)
    create = sub.add_parser("create")
    create.add_argument("--version", required=True)
    create.add_argument("--parent", required=True)
    sandbox = sub.add_parser("sandbox")
    sandbox.add_argument("--version", required=True)
    sandbox.add_argument("--gate")
    sandbox.add_argument("--timeout", type=int, default=3600)
    publish = sub.add_parser("publish")
    publish.add_argument("--version", required=True)
    publish.add_argument("--as-version")
    stage = sub.add_parser("stage")
    stage.add_argument("--version", required=True)
    stage.add_argument("--report", default="latest")
    activate = sub.add_parser("activate")
    activate.add_argument("--version", required=True)
    activate.add_argument("--mode", choices=("qualified", "development"), default="qualified")
    activate.add_argument("--confirmation", default="")
    rollback = sub.add_parser("rollback")
    rollback.add_argument("--confirmation", default="")
    sub.add_parser("runtime-status")
    discard = sub.add_parser("discard")
    discard.add_argument("--version", required=True)
    discard.add_argument("--confirmation", default="")
    return result


def main() -> int:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_ROOT.mkdir(parents=True, exist_ok=True)
    args = parser().parse_args()
    audit = Audit(args.action)
    commands = {
        "list": command_list, "create": command_create, "status": command_status,
        "snapshot": command_snapshot, "diff": command_diff, "sandbox": command_sandbox,
        "publish": command_publish, "stage": command_stage, "activate": command_activate,
        "rollback": command_rollback, "runtime-status": command_runtime_status,
        "discard": command_discard,
    }
    try:
        return commands[args.action](args, audit)
    except Exception as error:
        audit.emit("error", error=repr(error))
        return audit.finish({"state": "error", "error": str(error), "runtime_connected": args.action in {"activate", "rollback", "runtime-status"}}, 1)


if __name__ == "__main__":
    raise SystemExit(main())
