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
import argparse
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
WARNING_AS_ERROR_OPTION = "-DwarningAsError=true"
WARNING_MARKERS = ("warning:", "warning ")
COMMAND_RECONSTRUCTION_POLICY = "lean_compile_command_reconstruction/v1"


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


def artifact_record(path: Path) -> dict:
    info = path.lstat()
    if path.is_symlink() or not path.is_file() or info.st_nlink != 1:
        raise RuntimeError("unsafe compiler handoff artifact")
    return {
        "path": path.relative_to(HANDOFF).as_posix(),
        "size_bytes": info.st_size,
        "sha256": digest(path),
        "mode": format(info.st_mode & 0o777, "04o"),
    }


def compile_command(source: Path, target: Path) -> list[str]:
    """Return the one governed command form used for every Lean source."""
    return [str(LEAN), WARNING_AS_ERROR_OPTION, "-o", str(target), str(source)]


def compilation_environment(output: Path) -> dict[str, str]:
    return {
        "HOME": "/nonexistent", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        "TZ": "UTC", "SOURCE_DATE_EPOCH": "0", "LEAN_ABORT_ON_PANIC": "1",
        "LEAN_PATH": str(output),
    }


def warning_diagnostic_present(value: str) -> bool:
    normalized = value.casefold()
    return any(marker in normalized for marker in WARNING_MARKERS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", required=True)
    parser.add_argument("--artifact-limit", required=True, type=int)
    parser.add_argument("--handoff-limit", required=True, type=int)
    args = parser.parse_args()
    if args.artifact_limit <= 0 or args.handoff_limit <= 0:
        return 64
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
    output.mkdir(mode=0o750)
    environment = compilation_environment(output)
    pending = [WORK / path.relative_to(SOURCE) for path in sources]
    compiled = []
    compilation_commands = []
    diagnostics = []
    for _ in range(max(1, len(pending))):
        progress = False
        for source in list(pending):
            relative = source.relative_to(WORK)
            target = output / relative.with_suffix(".olean")
            target.parent.mkdir(parents=True, exist_ok=True)
            command = compile_command(source, target)
            process = run_bounded(command, cwd=WORK, env=environment, timeout=300)
            if process.timed_out:
                return 124
            if process.output_limit_exceeded:
                return 73
            diagnostic = process.stdout + process.stderr
            if process.returncode == 0 and not warning_diagnostic_present(diagnostic):
                if target.stat().st_size > args.artifact_limit:
                    return 74
                pending.remove(source); progress = True
                module = relative.with_suffix("").as_posix().replace("/", ".")
                compiled.append({"module": module, "role": "submitted_source", "source_sha256": digest(source), "olean_path": target.relative_to(HANDOFF).as_posix(), "olean_sha256": digest(target)})
                compilation_commands.append({"module": module, "role": "submitted_source", "argv_sha256": hashlib.sha256(canonical(command)).hexdigest()})
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
    binding_command = compile_command(binding, binding_target)
    process = run_bounded(binding_command, cwd=WORK, env=environment, timeout=300)
    if process.timed_out:
        return 124
    if process.output_limit_exceeded:
        return 73
    if process.returncode != 0 or warning_diagnostic_present(process.stdout + process.stderr):
        return 1
    if binding_target.stat().st_size > args.artifact_limit:
        return 74
    binding_relative = binding.relative_to(WORK)
    binding_module = binding_relative.with_suffix("").as_posix().replace("/", ".")
    compiled.append({
        "module": binding_module,
        "role": "generated_binding",
        "source_sha256": digest(binding),
        "olean_path": binding_target.relative_to(HANDOFF).as_posix(),
        "olean_sha256": digest(binding_target),
    })
    compilation_commands.append({
        "module": binding_module,
        "role": "generated_binding",
        "argv_sha256": hashlib.sha256(canonical(binding_command)).hexdigest(),
    })
    for path in sorted(output.rglob("*.olean"), key=lambda item: item.relative_to(HANDOFF).as_posix()):
        path.chmod(0o440)
    for directory in sorted((path for path in output.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True):
        directory.chmod(0o550)
    output.chmod(0o550)
    artifacts = [artifact_record(path) for path in sorted(output.rglob("*.olean"), key=lambda item: item.relative_to(HANDOFF).as_posix())]
    total_handoff_bytes = sum(item["size_bytes"] for item in artifacts)
    if total_handoff_bytes > args.handoff_limit:
        return 75
    manifest = {
        "schema_version": "lean_compile_handoff/v3",
        "compiled_modules": sorted(compiled, key=lambda item: item["module"]),
        "compilation_commands": sorted(compilation_commands, key=lambda item: item["module"]),
        "warnings_as_errors": True,
        "warning_as_error_cli_option": WARNING_AS_ERROR_OPTION,
        "command_reconstruction_policy": COMMAND_RECONSTRUCTION_POLICY,
        "lean_executable_path": str(LEAN),
        "lean_executable_sha256": digest(LEAN),
        "working_directory": str(WORK),
        "compilation_environment_sha256": hashlib.sha256(canonical(environment)).hexdigest(),
        "binding_module_sha256": digest(binding),
        "binding_olean_path": binding_target.relative_to(HANDOFF).as_posix(),
        "binding_olean_sha256": digest(binding_target),
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "total_handoff_bytes": total_handoff_bytes,
        "maximum_artifact_bytes": args.artifact_limit,
        "maximum_handoff_bytes": args.handoff_limit,
    }
    data = canonical(manifest)
    if len(data) > MAX_DIAGNOSTIC_BYTES:
        return 72
    path = HANDOFF / "compile-manifest.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o640)
    try:
        os.write(fd, data); os.fsync(fd)
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
