#!/usr/bin/env python3
"""Import public SSH keys from a GitHub account into a libvirt guest via QEMU guest agent.

No private key material is handled. Existing authorized_keys entries are preserved and
GitHub keys are de-duplicated. The helper is intended for Xavi sandbox VM provisioning
and post-provision synchronization.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

USER_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")
KEY_PREFIXES = ("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-", "sk-ssh-ed25519@", "sk-ecdsa-sha2-")


def fetch_github_keys(username: str) -> list[str]:
    if not USER_RE.fullmatch(username):
        raise SystemExit("invalid GitHub username")
    req = urllib.request.Request(
        f"https://github.com/{username}.keys",
        headers={"User-Agent": "Xavi-VM-SSH-Key-Importer/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        text = response.read(256 * 1024).decode("utf-8", "strict")
    keys: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or not line.startswith(KEY_PREFIXES):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        # Keep algorithm + base64 only. GitHub comments are not required for auth.
        normalized = f"{parts[0]} {parts[1]}"
        if normalized not in seen:
            seen.add(normalized)
            keys.append(normalized)
    if not keys:
        raise SystemExit(f"GitHub returned no usable public SSH keys for {username}")
    return keys


def qga(vm: str, payload: dict) -> dict:
    proc = subprocess.run(
        ["virsh", "-c", "qemu:///system", "qemu-agent-command", vm, json.dumps(payload, separators=(",", ":"))],
        text=True,
        capture_output=True,
        timeout=20,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "qemu-agent-command failed")
    return json.loads(proc.stdout)


def guest_exec(vm: str, script: str, timeout: int = 30) -> dict:
    encoded = base64.b64encode(script.encode()).decode()
    command = f"echo {encoded} | base64 -d | /bin/bash"
    started = qga(vm, {"execute": "guest-exec", "arguments": {"path": "/bin/bash", "arg": ["-lc", command], "capture-output": True}})
    pid = int(started.get("return", {}).get("pid", 0))
    if not pid:
        raise RuntimeError("guest-exec did not return a pid")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = qga(vm, {"execute": "guest-exec-status", "arguments": {"pid": pid}}).get("return", {})
        if status.get("exited"):
            def dec(name: str) -> str:
                value = status.get(name) or ""
                return base64.b64decode(value).decode("utf-8", "replace") if value else ""
            return {"exitcode": int(status.get("exitcode", 1)), "stdout": dec("out-data"), "stderr": dec("err-data")}
        time.sleep(0.25)
    raise TimeoutError("guest command timed out")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vm", default="xavi-sandbox-1")
    ap.add_argument("--github-user", default="theblobinc")
    ap.add_argument("--guest-user", default="xavi")
    args = ap.parse_args()

    keys = fetch_github_keys(args.github_user)
    key_blob = "\n".join(keys) + "\n"
    payload = base64.b64encode(key_blob.encode()).decode()
    guest_user = args.guest_user
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", guest_user):
        raise SystemExit("invalid guest user")

    script = f'''set -euo pipefail
U={guest_user!r}
HOME_DIR=$(getent passwd "$U" | cut -d: -f6)
[ -n "$HOME_DIR" ]
install -d -m 700 -o "$U" -g "$U" "$HOME_DIR/.ssh"
AK="$HOME_DIR/.ssh/authorized_keys"
touch "$AK"
chown "$U:$U" "$AK"
chmod 600 "$AK"
TMP=$(mktemp)
base64 -d > "$TMP" <<'KEYDATA'
{payload}
KEYDATA
while IFS= read -r key; do
  [ -n "$key" ] || continue
  grep -Fqx -- "$key" "$AK" || printf '%s\\n' "$key" >> "$AK"
done < "$TMP"
rm -f "$TMP"
chown "$U:$U" "$AK"
chmod 600 "$AK"
printf 'authorized_key_lines=%s\\n' "$(grep -Ec '^(ssh-|ecdsa-|sk-)' "$AK" || true)"
'''
    result = guest_exec(args.vm, script)
    if result["exitcode"] != 0:
        raise SystemExit(result["stderr"] or f"guest exit {result['exitcode']}")

    # Public-key fingerprints only; never print key bodies.
    fps: list[str] = []
    for key in keys:
        proc = subprocess.run(["ssh-keygen", "-lf", "-"], input=key + "\n", text=True, capture_output=True)
        if proc.returncode == 0:
            fields = proc.stdout.strip().split()
            if len(fields) >= 2:
                fps.append(fields[1])
    print(json.dumps({
        "ok": True,
        "vm": args.vm,
        "guest_user": args.guest_user,
        "github_user": args.github_user,
        "github_key_count": len(keys),
        "fingerprints": fps,
        "guest_result": result["stdout"].strip(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
