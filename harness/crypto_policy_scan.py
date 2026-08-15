#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ACTIVE_PATTERNS = [
    ("sha256-call", re.compile(r"\bhashlib\.sha256\s*\(", re.I)),
    ("sha256-constructor", re.compile(r"\bhashlib\.new\s*\(\s*['\"]sha256['\"]", re.I)),
    ("hmac-sha256", re.compile(r"\bhmac\.(?:new|digest)\s*\([^\n]*sha256", re.I)),
    ("ed25519", re.compile(r"\bed25519\b", re.I)),
]
LEGACY_IDENTITY_PATTERNS = [
    ("sha256-identifier", re.compile(r"['\"]sha256:", re.I)),
    ("sha256-field", re.compile(r"['\"][A-Za-z0-9_]*sha256[A-Za-z0-9_]*['\"]\s*:", re.I)),
]
ALLOWED_INTEROP = [
    re.compile(r"FileHash-SHA256", re.I),
    re.compile(r"license_sha256", re.I),
    re.compile(r"REFERENCE_SHA256", re.I),
    re.compile(r"external_sha256", re.I),
    re.compile(r"untrusted[_ -]interoperability", re.I),
]
IGNORED_PARTS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", "vendor", "ops_agent-old",
    "data", "models",
}


def ignored(path: Path) -> bool:
    name = path.name.lower()
    return (
        any(part in IGNORED_PARTS for part in path.parts)
        or ".backup" in name
        or ".pre-" in name
        or name.endswith(".pyc")
        or name == "bounded_commands.json"
        or name == "cryptographic_profile_registry_v1.json"
        or name == "crypto_policy_scan.py"
    )


def allowed_interop_line(line: str) -> bool:
    return any(pattern.search(line) for pattern in ALLOWED_INTEROP)


def scan(roots: list[Path]) -> dict[str, Any]:
    active: list[dict[str, Any]] = []
    legacy: list[dict[str, Any]] = []
    interoperability: list[dict[str, Any]] = []
    scanned = 0
    for root in roots:
        if not root.exists():
            active.append({"path": str(root), "line": 0, "kind": "missing-scan-root"})
            continue
        files = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in files:
            if ignored(path) or not path.is_file() or path.is_symlink():
                continue
            if path.suffix.lower() not in {".py", ".json", ".yaml", ".yml", ".toml", ".md", ".txt"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            scanned += 1
            for number, line in enumerate(text.splitlines(), 1):
                for kind, pattern in ACTIVE_PATTERNS:
                    if pattern.search(line):
                        active.append({"path": str(path), "line": number, "kind": kind, "text": line.strip()[:300]})
                for kind, pattern in LEGACY_IDENTITY_PATTERNS:
                    if not pattern.search(line):
                        continue
                    item = {"path": str(path), "line": number, "kind": kind, "text": line.strip()[:300]}
                    if allowed_interop_line(line):
                        item["trust"] = "untrusted-interoperability-only"
                        interoperability.append(item)
                    else:
                        legacy.append(item)
    passed = not active and not legacy
    return {
        "schema": "duotronic-forbidden-active-cryptography-scan/v1",
        "passed": passed,
        "scanned_files": scanned,
        "forbidden_active_count": len(active),
        "legacy_identity_count": len(legacy),
        "untrusted_interoperability_count": len(interoperability),
        "forbidden_active": active,
        "legacy_identity": legacy,
        "untrusted_interoperability": interoperability,
        "rules": {
            "Ed25519": "forbidden-active",
            "SHA-256": "forbidden-active-and-identity",
            "external-SHA-256": "untrusted-interoperability-only",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = scan(args.roots)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
