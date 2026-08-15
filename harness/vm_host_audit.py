#!/usr/bin/env python3
"""Read-only host capability audit for the witness-harness libvirt VM."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any

TOOLS = (
    "virsh",
    "virt-install",
    "virt-host-validate",
    "qemu-img",
    "qemu-system-x86_64",
    "cloud-localds",
    "ssh",
    "scp",
    "rsync",
)
SERVICES = ("libvirtd.service", "virtqemud.service", "virtlogd.service")
DOMAIN = "duotronic-witness-harness"


def capture(argv: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "argv": argv,
            "exit_code": result.returncode,
            "stdout": result.stdout[-12000:],
            "stderr": result.stderr[-12000:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": argv, "exit_code": 127, "error": str(exc)}


def device(path: str) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"path": path, "exists": False}
    mode = target.stat().st_mode
    return {
        "path": path,
        "exists": True,
        "readable": os.access(path, os.R_OK),
        "writable": os.access(path, os.W_OK),
        "character_device": stat.S_ISCHR(mode),
    }


def main() -> int:
    tools = {name: shutil.which(name) for name in TOOLS}
    report: dict[str, Any] = {
        "schema": "duotronic-witness-harness-vm-host-audit/v1",
        "uid": os.geteuid(),
        "gid": os.getegid(),
        "groups": os.getgroups(),
        "tools": tools,
        "devices": {path: device(path) for path in ("/dev/kvm", "/dev/vhost-net")},
        "cpu": capture(["lscpu"]),
        "memory": capture(["free", "-h"]),
        "filesystems": capture(["df", "-h", "/", "/var/www/xavi", "/datastore2"]),
        "services": {
            name: capture(["systemctl", "is-active", name], timeout=10)
            for name in SERVICES
        },
    }
    if tools["virt-host-validate"]:
        report["virt_host_validate"] = capture(["virt-host-validate", "qemu"])
    if tools["virsh"]:
        report["libvirt_version"] = capture(["virsh", "-c", "qemu:///system", "version"])
        report["domains"] = capture(["virsh", "-c", "qemu:///system", "list", "--all", "--name"])
        report["domain_info"] = capture(
            ["virsh", "-c", "qemu:///system", "dominfo", DOMAIN]
        )
        report["networks"] = capture(["virsh", "-c", "qemu:///system", "net-list", "--all"])
    missing = [name for name, path in tools.items() if path is None]
    system_libvirt = report.get("libvirt_version", {}).get("exit_code") == 0
    report["ready"] = (
        not missing
        and report["devices"]["/dev/kvm"]["readable"]
        and report["devices"]["/dev/kvm"]["writable"]
        and system_libvirt
    )
    report["missing_tools"] = missing
    report["system_libvirt_access"] = system_libvirt
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
