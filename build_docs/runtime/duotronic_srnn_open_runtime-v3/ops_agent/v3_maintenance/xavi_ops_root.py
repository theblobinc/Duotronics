#!/usr/bin/env python3
"""Root-owned privileged boundary for Xavi host operations.

This file is source material. The installed copy must live at
/usr/local/sbin/xavi-ops-root, owned by root:root and mode 0755.

The helper intentionally exposes explicit operations instead of a generic shell.
Every operation is executed with fixed argv and validated arguments.
"""
from __future__ import annotations

import fcntl
import hashlib
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

VERSION = "1.3.0"
EVIDENCE_ROOT = Path("/var/lib/xavi-ops-root/evidence")
EVIDENCE_LOG = EVIDENCE_ROOT / "evidence.jsonl"
EVIDENCE_HEAD = EVIDENCE_ROOT / "head.shake256_512"
ROLLBACK_ROOT = Path("/var/backups/xavi-ops-root/rollback")
_CURRENT_OP_ID = ""
IFACE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")
UNIT_RE = re.compile(r"^[A-Za-z0-9_.@:-]{1,160}$")
NETPLAN_NAME_RE = re.compile(r"^[0-9]{2}-xavi-[A-Za-z0-9_.-]+\.ya?ml$")
ALLOWED_NETPLAN_SOURCE_ROOTS = (
    Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/data/privileged_staging"),
    Path("/var/www/xavi/xavi-stack-manager/data/privileged_staging"),
)
ALLOWED_NGINX_SOURCE_ROOTS = (
    Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/data/privileged_staging/nginx"),
    Path("/var/www/xavi/updates/privileged_staging/nginx"),
)
NGINX_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,180}$")
NGINX_ALLOWED_DIRS = {"sites-available", "conf.d", "snippets"}
ACL_SPEC_RE = re.compile(r"^(?:u|user|g|group):[A-Za-z0-9_.@:-]{1,160}:[rwx-]{3}$")
OP_ID_RE = re.compile(r"^[0-9a-f]{32}$")
ALLOWED_SYSTEMCTL_ACTIONS = {
    "start", "stop", "restart", "reload", "enable", "disable",
    "is-active", "is-enabled", "reset-failed",
}


class UsageError(RuntimeError):
    pass


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_evidence(event: dict) -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    os.chown(EVIDENCE_ROOT, 0, 0)
    os.chmod(EVIDENCE_ROOT, 0o750)
    fd = os.open(EVIDENCE_LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o640)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        prev_hash = EVIDENCE_HEAD.read_text().strip() if EVIDENCE_HEAD.exists() else "0" * 128
        event = dict(event)
        event.setdefault("ts", _utc_now())
        event.setdefault("operation_id", _CURRENT_OP_ID)
        event["prev_hash"] = prev_hash
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
        entry_hash = hashlib.shake_256(canonical).hexdigest(64)
        event["entry_hash"] = entry_hash
        line = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
        tmp = EVIDENCE_HEAD.with_suffix(".tmp")
        tmp.write_text(entry_hash + "\n")
        os.chown(tmp, 0, 0)
        os.chmod(tmp, 0o640)
        os.replace(tmp, EVIDENCE_HEAD)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    os.chown(EVIDENCE_LOG, 0, 0)
    os.chmod(EVIDENCE_LOG, 0o640)


def _rollback_hint(op: str, args: list[str]) -> dict:
    inverse = {
        "ip-link-up": "ip-link-down",
        "ip-link-down": "ip-link-up",
        "ip-addr-add": "ip-addr-del",
        "ip-addr-del": "ip-addr-add",
    }
    if op in inverse:
        return {"type": "inverse", "operation": inverse[op], "args": args}
    if op == "systemctl" and len(args) == 2:
        action, unit_name = args
        inv = {"start": "stop", "stop": "start", "enable": "disable", "disable": "enable"}.get(action)
        if inv:
            return {"type": "inverse", "operation": "systemctl", "args": [inv, unit_name]}
    return {}


def _audit_artifact(kind: str, **fields) -> None:
    global _CURRENT_OP_ID
    if not _CURRENT_OP_ID:
        _CURRENT_OP_ID = uuid.uuid4().hex
    _append_evidence({"phase": "artifact", "kind": kind, **fields})


def fail(message: str, code: int = 2) -> "None":
    print(message, file=sys.stderr)
    raise SystemExit(code)


def run(argv: list[str], *, check: bool = True) -> int:
    global _CURRENT_OP_ID
    if not _CURRENT_OP_ID:
        _CURRENT_OP_ID = uuid.uuid4().hex
    started = time.monotonic()
    _append_evidence({"phase": "exec-start", "argv": argv})
    try:
        subprocess.run(
            ["/usr/bin/logger", "-t", "xavi-ops-root", "--", json.dumps({"operation_id": _CURRENT_OP_ID, "argv": argv}, separators=(",", ":"))],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    proc = subprocess.run(argv, check=False)
    _append_evidence({"phase": "exec-finish", "argv": argv, "returncode": proc.returncode, "elapsed_ms": int((time.monotonic() - started) * 1000)})
    if check and proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc.returncode


def require_root() -> None:
    if os.geteuid() != 0:
        fail("xavi-ops-root must run as root (normally through sudo -n)")


def iface(value: str) -> str:
    if not IFACE_RE.fullmatch(value):
        raise UsageError(f"invalid interface name: {value!r}")
    if not Path("/sys/class/net", value).exists():
        raise UsageError(f"interface does not exist: {value}")
    return value


def cidr(value: str) -> str:
    if "/" not in value:
        raise UsageError(f"CIDR prefix is required: {value!r}")
    try:
        return str(ipaddress.ip_interface(value))
    except ValueError as exc:
        raise UsageError(f"invalid CIDR: {value!r}") from exc


def unit(value: str) -> str:
    if not UNIT_RE.fullmatch(value):
        raise UsageError(f"invalid unit name: {value!r}")
    return value


def netplan_source(value: str) -> Path:
    p = Path(value).resolve(strict=True)
    if not p.is_file():
        raise UsageError("netplan source must be a regular file")
    allowed = False
    for root in ALLOWED_NETPLAN_SOURCE_ROOTS:
        rr = root.resolve()
        try:
            p.relative_to(rr)
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        raise UsageError(f"netplan source outside privileged staging roots: {p}")
    return p


def install_netplan(src_raw: str, dest_name: str) -> None:
    src = netplan_source(src_raw)
    if not NETPLAN_NAME_RE.fullmatch(dest_name):
        raise UsageError("destination must match NN-xavi-*.yaml")
    dest = Path("/etc/netplan") / dest_name
    tmp = dest.with_name(dest.name + ".tmp-xavi")
    data = src.read_bytes()
    if len(data) > 256 * 1024:
        raise UsageError("netplan file exceeds 256 KiB")
    global _CURRENT_OP_ID
    if not _CURRENT_OP_ID:
        _CURRENT_OP_ID = uuid.uuid4().hex
    rollback_dir = ROLLBACK_ROOT / _CURRENT_OP_ID
    rollback_dir.mkdir(parents=True, exist_ok=True)
    os.chown(rollback_dir, 0, 0)
    os.chmod(rollback_dir, 0o700)
    existed = dest.exists()
    backup = rollback_dir / dest.name
    if existed:
        shutil.copy2(dest, backup)
        os.chown(backup, 0, 0)
        os.chmod(backup, 0o600)
    tmp.write_bytes(data)
    os.chown(tmp, 0, 0)
    os.chmod(tmp, 0o600)
    os.replace(tmp, dest)
    _audit_artifact("netplan-backup", target=str(dest), backup=str(backup) if existed else "", existed=existed, rollback={"type": "file-backup", "target": str(dest), "backup": str(backup) if existed else ""})


def acl_path(value: str) -> Path:
    if not value.startswith("/") or "\x00" in value:
        raise UsageError("ACL path must be absolute")
    return Path(value).resolve(strict=True)


def acl_spec(value: str) -> str:
    if not ACL_SPEC_RE.fullmatch(value):
        raise UsageError("ACL spec must look like u:NAME:rwx or g:NAME:r-x")
    return value


def acl_set(path_raw: str, spec_raw: str) -> None:
    global _CURRENT_OP_ID
    path = acl_path(path_raw)
    spec = acl_spec(spec_raw)
    op_id = _CURRENT_OP_ID or uuid.uuid4().hex
    _CURRENT_OP_ID = op_id
    rollback_dir = ROLLBACK_ROOT / op_id
    rollback_dir.mkdir(parents=True, exist_ok=True)
    os.chown(rollback_dir, 0, 0)
    os.chmod(rollback_dir, 0o700)
    backup = rollback_dir / "acl.before"
    with backup.open("wb") as fh:
        proc = subprocess.run(["/usr/bin/getfacl", "-p", str(path)], stdout=fh, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        backup.unlink(missing_ok=True)
        raise SystemExit(proc.returncode)
    os.chown(backup, 0, 0)
    os.chmod(backup, 0o600)
    run(["/usr/bin/setfacl", "-m", spec, str(path)])
    _audit_artifact("acl-snapshot", path=str(path), spec=spec, backup=str(backup), rollback={"operation": "acl-restore", "args": [op_id]})
    print(json.dumps({"ok": True, "operation": "acl-set", "operation_id": op_id, "path": str(path), "spec": spec, "rollback_operation": "acl-restore", "rollback_args": [op_id]}, separators=(",", ":")))


def acl_restore(op_id: str) -> None:
    if not OP_ID_RE.fullmatch(op_id):
        raise UsageError("invalid operation id")
    backup = ROLLBACK_ROOT / op_id / "acl.before"
    if not backup.is_file():
        raise UsageError(f"ACL rollback snapshot not found for {op_id}")
    run(["/usr/bin/setfacl", f"--restore={backup}"])
    _audit_artifact("acl-restore", restored_from_operation_id=op_id, backup=str(backup))
    print(json.dumps({"ok": True, "operation": "acl-restore", "restored_from_operation_id": op_id, "backup": str(backup)}, separators=(",", ":")))


def evidence_tail(limit_raw: str = "50") -> None:
    try:
        limit = max(1, min(int(limit_raw), 500))
    except ValueError as exc:
        raise UsageError("evidence-tail limit must be an integer") from exc
    if not EVIDENCE_LOG.exists():
        return
    print("\n".join(EVIDENCE_LOG.read_text(errors="replace").splitlines()[-limit:]))


def nginx_source(value: str) -> Path:
    p = Path(value).resolve(strict=True)
    if not p.is_file():
        raise UsageError("nginx source must be a regular file")
    if p.stat().st_size > 2 * 1024 * 1024:
        raise UsageError("nginx source exceeds 2 MiB")
    for root in ALLOWED_NGINX_SOURCE_ROOTS:
        rr = root.resolve()
        try:
            p.relative_to(rr)
            return p
        except ValueError:
            continue
    raise UsageError(f"nginx source outside privileged staging roots: {p}")


def nginx_target(value: str) -> Path:
    raw = value.strip()
    if raw == "nginx.conf":
        return Path("/etc/nginx/nginx.conf")
    rel = Path(raw)
    if rel.is_absolute() or ".." in rel.parts or len(rel.parts) != 2:
        raise UsageError("nginx target must be nginx.conf or DIR/BASENAME")
    directory, name = rel.parts
    if directory not in NGINX_ALLOWED_DIRS:
        raise UsageError(f"nginx target directory not allowed: {directory}")
    if not NGINX_NAME_RE.fullmatch(name):
        raise UsageError(f"invalid nginx target basename: {name!r}")
    if directory in {"conf.d", "snippets"} and not name.endswith(".conf"):
        raise UsageError(f"{directory} targets must end in .conf")
    return Path("/etc/nginx") / directory / name


def install_nginx_config(src_raw: str, target_raw: str) -> None:
    src = nginx_source(src_raw)
    dest = nginx_target(target_raw)
    if dest.is_symlink():
        raise UsageError("refusing to replace nginx symlink; edit its sites-available target instead")
    dest.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup_root = Path("/var/backups/xavi-ops-root/nginx") / stamp
    backup = backup_root / target_raw
    backup.parent.mkdir(parents=True, exist_ok=True)
    existed = dest.exists()
    if existed:
        shutil.copy2(dest, backup)
    data = src.read_bytes()
    digest = hashlib.shake_256(data).hexdigest(64)
    tmp = dest.with_name(dest.name + f".tmp-xavi-{os.getpid()}")
    tmp.write_bytes(data)
    os.chown(tmp, 0, 0)
    os.chmod(tmp, 0o644)
    os.replace(tmp, dest)

    def rollback() -> None:
        if existed:
            shutil.copy2(backup, dest)
            os.chown(dest, 0, 0)
            os.chmod(dest, 0o644)
        else:
            dest.unlink(missing_ok=True)
        run(["/usr/sbin/nginx", "-t"], check=False)

    if run(["/usr/sbin/nginx", "-t"], check=False) != 0:
        rollback()
        raise SystemExit(1)
    if run(["/usr/bin/systemctl", "reload", "nginx.service"], check=False) != 0:
        rollback()
        run(["/usr/bin/systemctl", "reload", "nginx.service"], check=False)
        raise SystemExit(1)
    _audit_artifact(
        "nginx-config-backup",
        source=str(src),
        target=str(dest),
        shake256_512=digest,
        backup=str(backup) if existed else "",
        rollback={"type": "file-backup", "target": str(dest), "backup": str(backup) if existed else ""},
    )
    print(json.dumps({
        "ok": True,
        "operation": "nginx-config-install",
        "operation_id": _CURRENT_OP_ID,
        "source": str(src),
        "target": str(dest),
        "shake256_512": digest,
        "backup": str(backup) if existed else "",
    }, separators=(",", ":")))


def usage() -> str:
    return """Usage: xavi-ops-root OPERATION [ARGS...]

Operations:
  probe
  ip-link-up IFACE
  ip-link-down IFACE
  ip-addr-add CIDR IFACE
  ip-addr-del CIDR IFACE
  netplan-install SOURCE_PATH DEST_BASENAME
  netplan-generate
  netplan-apply
  systemctl ACTION UNIT
  systemctl-daemon-reload
  nginx-test
  nginx-reload
  nginx-config-install SOURCE_PATH TARGET
  acl-set PATH SPEC
  acl-restore OPERATION_ID
  evidence-tail [LIMIT]
"""


def main(argv: list[str]) -> int:
    require_root()
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(usage())
        return 0

    op, *args = argv

    if op == "probe":
        if args:
            raise UsageError("probe takes no arguments")
        print(json.dumps({"ok": True, "version": VERSION, "euid": os.geteuid()}))
        return 0

    if op == "ip-link-up":
        if len(args) != 1:
            raise UsageError("ip-link-up requires IFACE")
        return run(["/usr/sbin/ip", "link", "set", "dev", iface(args[0]), "up"])

    if op == "ip-link-down":
        if len(args) != 1:
            raise UsageError("ip-link-down requires IFACE")
        return run(["/usr/sbin/ip", "link", "set", "dev", iface(args[0]), "down"])

    if op == "ip-addr-add":
        if len(args) != 2:
            raise UsageError("ip-addr-add requires CIDR IFACE")
        return run(["/usr/sbin/ip", "addr", "add", cidr(args[0]), "dev", iface(args[1])])

    if op == "ip-addr-del":
        if len(args) != 2:
            raise UsageError("ip-addr-del requires CIDR IFACE")
        return run(["/usr/sbin/ip", "addr", "del", cidr(args[0]), "dev", iface(args[1])])

    if op == "netplan-install":
        if len(args) != 2:
            raise UsageError("netplan-install requires SOURCE_PATH DEST_BASENAME")
        install_netplan(args[0], args[1])
        return 0

    if op == "netplan-generate":
        if args:
            raise UsageError("netplan-generate takes no arguments")
        return run(["/usr/sbin/netplan", "generate"])

    if op == "netplan-apply":
        if args:
            raise UsageError("netplan-apply takes no arguments")
        return run(["/usr/sbin/netplan", "apply"])

    if op == "systemctl":
        if len(args) != 2:
            raise UsageError("systemctl requires ACTION UNIT")
        action, unit_name = args
        if action not in ALLOWED_SYSTEMCTL_ACTIONS:
            raise UsageError(f"systemctl action not allowed: {action}")
        return run(["/usr/bin/systemctl", action, unit(unit_name)])

    if op == "systemctl-daemon-reload":
        if args:
            raise UsageError("systemctl-daemon-reload takes no arguments")
        return run(["/usr/bin/systemctl", "daemon-reload"])

    if op == "nginx-test":
        if args:
            raise UsageError("nginx-test takes no arguments")
        return run(["/usr/sbin/nginx", "-t"])

    if op == "nginx-reload":
        if args:
            raise UsageError("nginx-reload takes no arguments")
        run(["/usr/sbin/nginx", "-t"])
        return run(["/usr/bin/systemctl", "reload", "nginx.service"])

    if op == "nginx-config-install":
        if len(args) != 2:
            raise UsageError("nginx-config-install requires SOURCE_PATH TARGET")
        install_nginx_config(args[0], args[1])
        return 0

    if op == "acl-set":
        if len(args) != 2:
            raise UsageError("acl-set requires PATH SPEC")
        acl_set(args[0], args[1])
        return 0

    if op == "acl-restore":
        if len(args) != 1:
            raise UsageError("acl-restore requires OPERATION_ID")
        acl_restore(args[0])
        return 0

    if op == "evidence-tail":
        if len(args) > 1:
            raise UsageError("evidence-tail accepts at most LIMIT")
        evidence_tail(args[0] if args else "50")
        return 0

    raise UsageError(f"unknown operation: {op}")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except UsageError as exc:
        fail(str(exc))
