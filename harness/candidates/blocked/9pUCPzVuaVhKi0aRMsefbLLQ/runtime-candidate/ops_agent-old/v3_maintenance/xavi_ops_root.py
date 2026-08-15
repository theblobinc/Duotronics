#!/usr/bin/env python3
"""Root-owned privileged boundary for Xavi host operations.

This file is source material. The installed copy must live at
/usr/local/sbin/xavi-ops-root, owned by root:root and mode 0755.

The helper intentionally exposes explicit operations instead of a generic shell.
Every operation is executed with fixed argv and validated arguments.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.0"
IFACE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")
UNIT_RE = re.compile(r"^[A-Za-z0-9_.@:-]{1,160}$")
NETPLAN_NAME_RE = re.compile(r"^[0-9]{2}-xavi-[A-Za-z0-9_.-]+\.ya?ml$")
ALLOWED_NETPLAN_SOURCE_ROOTS = (
    Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/data/privileged_staging"),
    Path("/var/www/xavi/xavi-stack-manager/data/privileged_staging"),
)
ALLOWED_SYSTEMCTL_ACTIONS = {
    "start", "stop", "restart", "reload", "enable", "disable",
    "is-active", "is-enabled", "reset-failed",
}


class UsageError(RuntimeError):
    pass


def fail(message: str, code: int = 2) -> "None":
    print(message, file=sys.stderr)
    raise SystemExit(code)


def run(argv: list[str], *, check: bool = True) -> int:
    # Log only operation argv. This helper accepts no secrets by design.
    try:
        subprocess.run(
            ["/usr/bin/logger", "-t", "xavi-ops-root", "--", json.dumps(argv, separators=(",", ":"))],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    proc = subprocess.run(argv, check=False)
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
    tmp.write_bytes(data)
    os.chown(tmp, 0, 0)
    os.chmod(tmp, 0o600)
    os.replace(tmp, dest)


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

    raise UsageError(f"unknown operation: {op}")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except UsageError as exc:
        fail(str(exc))
