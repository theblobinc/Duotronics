#!/usr/bin/env python3
"""Untrusted-domain clean-source Lean compiler for the governed OCI image.

This program intentionally has no verifier request, result directory, signing
key, registry, database, network, or host configuration input.  It emits only
bounded `.olean` handoff artifacts and a content manifest.  The trusted
verifier independently inspects those artifacts and never accepts a result
object from this domain.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from bounded_subprocess import run_bounded

SOURCE = Path("/input/source")
GENERATED = Path("/input/generated")
WORK = Path("/work/project")
HANDOFF = Path("/handoff")
LEAN = Path("/opt/lean/bin/lean")
MAX_DIAGNOSTIC_BYTES = 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def safe_sources(root: Path) -> list[Path]:
    result = []
    for path in root.rglob("*"):
        info = path.lstat()
        if path.is_symlink() or (path.is_file() and info.st_nlink != 1):
            raise RuntimeError("unsafe source identity")
        if path.is_file() and path.suffix == ".lean":
            result.append(path)
        elif path.is_file() and path.suffix in {".olean", ".ilean", ".so", ".dll", ".dylib", ".o", ".a"}:
            raise RuntimeError("prebuilt or native input is forbidden")
    return sorted(result, key=lambda item: item.relative_to(root).as_posix())


def main() -> int:
    if not LEAN.is_file() or not SOURCE.is_dir() or not GENERATED.is_dir() or not HANDOFF.is_dir():
        return 70
    WORK.mkdir(parents=True, exist_ok=False)
    sources = safe_sources(SOURCE)
    for source in sources:
        relative = source.relative_to(SOURCE)
        target = WORK / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target, follow_symlinks=False)
    generated_sources = safe_sources(GENERATED)
    for source in generated_sources:
        relative = source.relative_to(GENERATED)
        target = WORK / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target, follow_symlinks=False)
    output = HANDOFF / "olean"
    output.mkdir(mode=0o700)
    environment = {"HOME": "/nonexistent", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "SOURCE_DATE_EPOCH": "0", "LEAN_ABORT_ON_PANIC": "1", "LEAN_PATH": str(output)}
    pending = [WORK / path.relative_to(SOURCE) for path in sources]
    compiled = []
    diagnostics = []
    for _ in range(max(1, len(pending))):
        progress = False
        for source in list(pending):
            relative = source.relative_to(WORK)
            target = output / relative.with_suffix(".olean")
            target.parent.mkdir(parents=True, exist_ok=True)
            process = run_bounded([str(LEAN), "-o", str(target), str(source)], cwd=WORK, env=environment, timeout=300)
            if process.timed_out:
                return 124
            if process.output_limit_exceeded:
                return 73
            diagnostic = process.stdout + process.stderr
            if process.returncode == 0:
                pending.remove(source); progress = True
                compiled.append({"module": relative.with_suffix("").as_posix().replace("/", "."), "source_sha256": digest(source), "olean_sha256": digest(target)})
            else:
                diagnostics.append({"module": relative.as_posix(), "sha256": hashlib.sha256(diagnostic.encode()).hexdigest()})
        if not pending or not progress:
            break
    if pending:
        return 1
    generated = [WORK / path.relative_to(GENERATED) for path in generated_sources]
    if len(generated) != 1:
        return 71
    binding = generated[0]
    binding_target = output / binding.relative_to(WORK).with_suffix(".olean")
    binding_target.parent.mkdir(parents=True, exist_ok=True)
    process = run_bounded([str(LEAN), "-o", str(binding_target), str(binding)], cwd=WORK, env=environment, timeout=300)
    if process.timed_out:
        return 124
    if process.output_limit_exceeded:
        return 73
    if process.returncode != 0:
        return 1
    manifest = {"schema_version": "lean_compile_handoff/v1", "compiled_modules": sorted(compiled, key=lambda item: item["module"]), "binding_module_sha256": digest(binding), "binding_olean_sha256": digest(binding_target)}
    data = canonical(manifest)
    if len(data) > MAX_DIAGNOSTIC_BYTES:
        return 72
    path = HANDOFF / "compile-manifest.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        os.write(fd, data); os.fsync(fd)
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
