#!/usr/bin/env python3
"""Hermetic, governed Lean proof authority for Witness Contract Draft 5.3.3.

The request-facing method accepts a compiler-profile identifier, never an
executable path, digest, environment, or authority timestamp.  A protected
service configuration loads a governance-signed compiler registry and a
server-controlled signing key.  Verification copies accepted Lean sources to
an immutable snapshot, rejects prebuilt/native artifacts, uses a deterministic
term-binding module, and requires a canonical machine-readable verifier result
from a pinned execution image.  Human-readable compiler output is diagnostic
only and can never authorize a theorem.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


LEAN_IDENTIFIER = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_']*\.)*[A-Za-z_][A-Za-z0-9_']*$")
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
IMAGE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
DEFAULT_AUTHORIZED_AXIOMS = frozenset({"propext", "Quot.sound", "Classical.choice"})
SOURCE_METADATA = frozenset({"lean-toolchain", "lakefile.lean", "lake-manifest.json"})
FORBIDDEN_BUILD_SUFFIXES = frozenset({
    ".olean", ".ilean", ".so", ".dll", ".dylib", ".a", ".o", ".obj",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".sh", ".bash", ".exe",
})
MINIMAL_HOST_ENV_KEYS = ("PATH", "SYSTEMROOT", "WINDIR")
CONTAINER_ENV = {
    "HOME": "/nonexistent",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "TZ": "UTC",
    "SOURCE_DATE_EPOCH": "0",
    "LEAN_ABORT_ON_PANIC": "1",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_text(value: Any) -> str:
    return canonical_bytes(value).decode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def load_private_key(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("configured verifier key is not Ed25519")
    return key


def load_public_key(path: Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("configured governance key is not Ed25519")
    return key


def public_key_raw_b64url(key: Ed25519PublicKey) -> str:
    raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return _b64url(raw)


def public_key_fingerprint(key: Ed25519PublicKey) -> str:
    raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return sha256_bytes(raw)


def signed_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in {"signed_payload_sha256", "signature"}}


def signed_payload_canonical_json(record: dict[str, Any]) -> str:
    return canonical_text(signed_payload(record))


def sign_record(record: dict[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    unsigned = signed_payload(record)
    payload = canonical_bytes(unsigned)
    result = dict(unsigned)
    result["signed_payload_sha256"] = sha256_bytes(payload)
    result["signature"] = _b64url(private_key.sign(payload))
    return result


def verify_record(record: dict[str, Any], public_key: Ed25519PublicKey) -> bool:
    try:
        payload = canonical_bytes(signed_payload(record))
        if record.get("signed_payload_sha256") != sha256_bytes(payload):
            return False
        public_key.verify(_b64url_decode(record["signature"]), payload)
        return True
    except (InvalidSignature, KeyError, TypeError, ValueError):
        return False


def register_sqlite_crypto_functions(connection: sqlite3.Connection) -> None:
    """Register fail-closed canonicalization and Ed25519 SQL functions."""

    def sql_sha256(value: Any) -> str | None:
        return sha256_bytes(value.encode("utf-8")) if isinstance(value, str) else None

    def sql_key_fingerprint(public_key_b64url: Any) -> str | None:
        try:
            return sha256_bytes(_b64url_decode(str(public_key_b64url)))
        except (TypeError, ValueError):
            return None

    def sql_ed25519_verify(public_key_b64url: Any, payload: Any, signature: Any) -> int:
        try:
            key = Ed25519PublicKey.from_public_bytes(_b64url_decode(str(public_key_b64url)))
            key.verify(_b64url_decode(str(signature)), str(payload).encode("utf-8"))
            return 1
        except (InvalidSignature, TypeError, ValueError):
            return 0

    def sql_is_canonical_json(value: Any) -> int:
        try:
            text = str(value)
            return int(canonical_text(json.loads(text)) == text)
        except (TypeError, ValueError, json.JSONDecodeError):
            return 0

    connection.create_function("wc_sha256", 1, sql_sha256, deterministic=True)
    connection.create_function("wc_public_key_fingerprint", 1, sql_key_fingerprint, deterministic=True)
    connection.create_function("wc_ed25519_verify", 3, sql_ed25519_verify, deterministic=True)
    connection.create_function("wc_is_canonical_json", 1, sql_is_canonical_json, deterministic=True)


@dataclass(frozen=True)
class CompilerProfile:
    compiler_profile_id: str
    toolchain: str
    image_reference: str
    execution_image_digest: str
    lake_executable_sha256: str
    lean_executable_sha256: str
    lean_stdlib_tree_sha256: str
    dependency_closure_sha256: str
    verifier_binary_sha256: str
    sandbox_policy_sha256: str
    authorized_axioms: frozenset[str]
    valid_from: str
    valid_until: str | None

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "CompilerProfile":
        digest_fields = (
            "lake_executable_sha256", "lean_executable_sha256",
            "lean_stdlib_tree_sha256", "dependency_closure_sha256",
            "verifier_binary_sha256", "sandbox_policy_sha256",
        )
        if any(not SHA256_HEX.fullmatch(str(record.get(name, ""))) for name in digest_fields):
            raise ValueError("compiler profile contains an invalid SHA-256 digest")
        if not IMAGE_DIGEST.fullmatch(str(record.get("execution_image_digest", ""))):
            raise ValueError("compiler profile execution image is not digest-pinned")
        return cls(
            compiler_profile_id=record["compiler_profile_id"],
            toolchain=record["toolchain"],
            image_reference=record["image_reference"],
            execution_image_digest=record["execution_image_digest"],
            lake_executable_sha256=record["lake_executable_sha256"],
            lean_executable_sha256=record["lean_executable_sha256"],
            lean_stdlib_tree_sha256=record["lean_stdlib_tree_sha256"],
            dependency_closure_sha256=record["dependency_closure_sha256"],
            verifier_binary_sha256=record["verifier_binary_sha256"],
            sandbox_policy_sha256=record["sandbox_policy_sha256"],
            authorized_axioms=frozenset(record.get("authorized_axioms", [])),
            valid_from=record["valid_from"],
            valid_until=record.get("valid_until"),
        )


@dataclass(frozen=True)
class SandboxExecution:
    returncode: int | None
    structured_result: dict[str, Any] | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    command: tuple[str, ...] = ()


class SandboxRunner(Protocol):
    def run(
        self,
        *,
        profile: CompilerProfile,
        snapshot_root: Path,
        generated_module: Path,
        request: dict[str, Any],
        timeout_seconds: int,
    ) -> SandboxExecution: ...


class OciSandboxRunner:
    """Execute only a preconfigured OCI runtime with a digest-pinned image."""

    def __init__(self, runtime_executable: Path, expected_runtime_sha256: str):
        runtime = runtime_executable.resolve()
        if not runtime.is_absolute() or not runtime.is_file() or not os.access(runtime, os.X_OK):
            raise ValueError("configured OCI runtime must be an absolute executable file")
        if not SHA256_HEX.fullmatch(expected_runtime_sha256) or sha256_file(runtime) != expected_runtime_sha256:
            raise ValueError("configured OCI runtime does not match its protected digest")
        self.runtime = runtime
        self.runtime_sha256 = expected_runtime_sha256

    def run(
        self,
        *,
        profile: CompilerProfile,
        snapshot_root: Path,
        generated_module: Path,
        request: dict[str, Any],
        timeout_seconds: int,
    ) -> SandboxExecution:
        with tempfile.TemporaryDirectory(prefix="wc-authority-control-") as control_name, tempfile.TemporaryDirectory(prefix="wc-authority-output-") as output_name:
            control = Path(control_name)
            output = Path(output_name)
            request_path = control / "request.json"
            request_path.write_bytes(canonical_bytes(request) + b"\n")
            request_path.chmod(0o444)
            control.chmod(0o555)
            output.chmod(0o777)
            image = f"{profile.image_reference}@{profile.execution_image_digest}"
            command = (
                str(self.runtime), "run", "--rm", "--pull=never", "--network=none",
                "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "--pids-limit=128", "--memory=2g", "--cpus=2", "--user=65534:65534",
                "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=512m", "--tmpfs=/work:rw,nosuid,nodev,size=1g",
                f"--volume={snapshot_root}:/input/source:ro",
                f"--volume={generated_module.parents[1]}:/input/generated:ro",
                f"--volume={control}:/input/control:ro", f"--volume={output}:/output:rw",
                "--env=HOME=/nonexistent", "--env=LANG=C.UTF-8", "--env=LC_ALL=C.UTF-8",
                "--env=TZ=UTC", "--env=SOURCE_DATE_EPOCH=0", "--env=LEAN_ABORT_ON_PANIC=1",
                image, "/opt/witness-authority/bin/verify-lean",
                "--request", "/input/control/request.json", "--result", "/output/verifier-result.json",
            )
            host_env = {key: os.environ[key] for key in MINIMAL_HOST_ENV_KEYS if key in os.environ}
            try:
                completed = subprocess.run(
                    command,
                    text=True,
                    capture_output=True,
                    timeout=timeout_seconds,
                    env=host_env,
                )
            except subprocess.TimeoutExpired as error:
                return SandboxExecution(None, None, error.stdout or "", error.stderr or "", True, command)
            result_path = output / "verifier-result.json"
            structured: dict[str, Any] | None = None
            if result_path.is_file():
                try:
                    raw = result_path.read_text(encoding="utf-8")
                    value = json.loads(raw)
                    if isinstance(value, dict) and canonical_text(value) == raw.strip():
                        structured = value
                except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                    structured = None
            return SandboxExecution(completed.returncode, structured, completed.stdout, completed.stderr, False, command)


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("authority time must include a timezone")
    return parsed.astimezone(timezone.utc)


def verify_governed_registry(record: dict[str, Any], governance_key: Ed25519PublicKey) -> dict[str, CompilerProfile]:
    if record.get("schema_version") != "governed_compiler_registry/v1" or not verify_record(record, governance_key):
        raise ValueError("compiler registry is not validly governance-signed")
    profiles = [CompilerProfile.from_record(item) for item in record.get("profiles", [])]
    by_id = {profile.compiler_profile_id: profile for profile in profiles}
    if not profiles or len(by_id) != len(profiles):
        raise ValueError("compiler registry profile identifiers must be nonempty and unique")
    return by_id


def _source_paths(source_root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in source_root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symbolic links are forbidden: {path.relative_to(source_root)}")
        if not path.is_file():
            continue
        if path.suffix.lower() in FORBIDDEN_BUILD_SUFFIXES:
            raise ValueError(f"prebuilt, native, or executable artifact is forbidden: {path.relative_to(source_root)}")
        if path.suffix == ".lean" or path.name in SOURCE_METADATA:
            paths.append(path)
        elif path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            raise ValueError(f"executable source-tree file is forbidden: {path.relative_to(source_root)}")
    return sorted(paths, key=lambda item: item.relative_to(source_root).as_posix())


def content_tree_sha256(source_root: Path) -> str:
    digest = hashlib.sha256()
    for path in _source_paths(source_root):
        relative = path.relative_to(source_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def _copy_immutable_snapshot(source_root: Path, destination: Path) -> tuple[str, str]:
    before = content_tree_sha256(source_root)
    for source in _source_paths(source_root):
        relative = source.relative_to(source_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    after = content_tree_sha256(source_root)
    snapshot = content_tree_sha256(destination)
    if before != after or before != snapshot:
        raise RuntimeError("source changed while the immutable snapshot was created")
    for path in sorted(destination.rglob("*"), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    destination.chmod(0o555)
    return before, snapshot


def _proof_module(source_root: Path, proof_artifact: Path) -> str:
    relative = proof_artifact.relative_to(source_root)
    if relative.suffix != ".lean":
        raise ValueError("proof artifact must be a .lean source file")
    parts = (*relative.parts[:-1], relative.stem)
    if not parts or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", part) for part in parts):
        raise ValueError("proof artifact path is not an importable Lean module")
    return ".".join(parts)


def _validate_statement(statement: str) -> None:
    if not statement or len(statement.encode("utf-8")) > 65536:
        raise ValueError("claimed theorem statement is empty or exceeds 65536 bytes")
    forbidden = ("\u2028", "\u2029", "--", "/-", "-/")
    if any(ord(character) < 0x20 for character in statement) or any(token in statement for token in forbidden):
        raise ValueError("claimed theorem statement must be one comment-free Lean term")


def generated_witness_module(*, proof_module: str, theorem_statement: str, theorem_name: str) -> str:
    _validate_statement(theorem_statement)
    if not LEAN_IDENTIFIER.fullmatch(theorem_name):
        raise ValueError("theorem_name is not a valid fully qualified Lean identifier")
    return (
        f"import {proof_module}\n"
        "set_option autoImplicit false\n"
        "set_option warningAsError true\n"
        f"example : ({theorem_statement}) := {theorem_name}\n"
    )


class ProofAuthorityService:
    """Protected authority service; request data cannot redefine its trust root."""

    def __init__(
        self,
        *,
        governed_registry: dict[str, Any],
        governance_public_key: Ed25519PublicKey,
        verifier_principal_id: str,
        key_id: str,
        signing_key: Ed25519PrivateKey,
        runner: SandboxRunner,
        clock: Callable[[], datetime] | None = None,
        timestamp_source: str = "authority_service_clock",
    ):
        self.profiles = verify_governed_registry(governed_registry, governance_public_key)
        self.registry_sha256 = sha256_bytes(canonical_bytes(governed_registry))
        self.verifier_principal_id = verifier_principal_id
        self.key_id = key_id
        self.signing_key = signing_key
        self.runner = runner
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.timestamp_source = timestamp_source

    def verify(
        self,
        *,
        compiler_profile_id: str,
        claim_id: str,
        canonical_claim: dict[str, Any],
        theorem_statement: str,
        theorem_name: str,
        proof_artifact: Path,
        source_root: Path,
        timeout_seconds: int = 600,
    ) -> dict[str, Any]:
        profile = self.profiles.get(compiler_profile_id)
        if profile is None:
            raise ValueError("compiler profile is not present in the governed registry")
        now = self.clock().astimezone(timezone.utc)
        if now < _parse_time(profile.valid_from) or (profile.valid_until and now > _parse_time(profile.valid_until)):
            raise ValueError("compiler profile is outside its governed validity interval")
        source_root = source_root.resolve()
        proof_artifact = proof_artifact.resolve()
        if not source_root.is_dir() or not proof_artifact.is_file():
            raise ValueError("source root and proof artifact must exist")
        try:
            relative_artifact = proof_artifact.relative_to(source_root)
        except ValueError as error:
            raise ValueError("proof artifact is outside source root") from error
        proof_module = _proof_module(source_root, proof_artifact)
        _validate_statement(theorem_statement)
        if not LEAN_IDENTIFIER.fullmatch(theorem_name):
            raise ValueError("invalid theorem identifier")
        toolchain_file = source_root / "lean-toolchain"
        if not toolchain_file.is_file() or toolchain_file.read_text(encoding="utf-8").strip() != profile.toolchain:
            raise ValueError("submitted toolchain does not match the governed compiler profile")

        claim_hash = sha256_bytes(canonical_bytes(canonical_claim))
        theorem_hash = sha256_bytes(theorem_statement.encode("utf-8"))
        artifact_hash = sha256_file(proof_artifact)
        lakefile_hash = sha256_file(source_root / "lakefile.lean") if (source_root / "lakefile.lean").is_file() else sha256_bytes(b"")

        with tempfile.TemporaryDirectory(prefix="wc-authority-snapshot-") as snapshot_name, tempfile.TemporaryDirectory(prefix="wc-authority-generated-") as generated_name:
            snapshot_root = Path(snapshot_name)
            original_hash, snapshot_hash = _copy_immutable_snapshot(source_root, snapshot_root)
            descriptor_hash = sha256_bytes(canonical_bytes({
                "claim": claim_hash,
                "theorem": theorem_hash,
                "artifact": artifact_hash,
                "snapshot": snapshot_hash,
                "profile": compiler_profile_id,
            }))
            generated_relative = f".witness_authority/Check_{descriptor_hash[:32]}.lean"
            generated_path = Path(generated_name) / generated_relative
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.write_text(generated_witness_module(
                proof_module=proof_module,
                theorem_statement=theorem_statement,
                theorem_name=theorem_name,
            ), encoding="utf-8")
            generated_hash = sha256_file(generated_path)
            generated_path.chmod(0o444)
            generated_path.parent.chmod(0o555)
            request = {
                "schema_version": "wc_lean_verifier_request/v1",
                "compiler_profile_id": compiler_profile_id,
                "claim_content_sha256": claim_hash,
                "theorem_statement_sha256": theorem_hash,
                "proof_artifact_sha256": artifact_hash,
                "proof_artifact_relative_path": relative_artifact.as_posix(),
                "proof_module": proof_module,
                "theorem_name": theorem_name,
                "original_source_tree_sha256": original_hash,
                "immutable_snapshot_sha256": snapshot_hash,
                "generated_witness_module_sha256": generated_hash,
                "generated_witness_module_path": generated_relative,
                "authorized_axioms": sorted(profile.authorized_axioms),
            }
            request_hash = sha256_bytes(canonical_bytes(request))
            execution = self.runner.run(
                profile=profile,
                snapshot_root=snapshot_root,
                generated_module=generated_path,
                request=request,
                timeout_seconds=timeout_seconds,
            )

        structured = execution.structured_result
        structured_valid = self._structured_result_valid(structured, request, request_hash, profile)
        axioms = sorted(set(structured.get("axiom_dependencies", []))) if structured_valid and structured else []
        contains_sorry = any(item == "sorryAx" or item.endswith(".sorryAx") for item in axioms)
        unauthorized = sorted(set(axioms) - set(profile.authorized_axioms))
        passed = bool(
            execution.returncode == 0 and not execution.timed_out and structured_valid and structured
            and structured.get("status") == "passed"
            and structured.get("declaration_found") is True
            and structured.get("declaration_type_matches") is True
            and structured.get("build_from_source") is True
            and structured.get("prebuilt_artifacts_used") is False
            and structured.get("warnings_as_errors") is True
            and not contains_sorry and not unauthorized
        )
        result = "passed" if passed else ("toolchain_unavailable" if execution.returncode is None and not execution.timed_out else "failed_lake_build")
        theorem_status = "proved" if passed else ("sorry_stub" if contains_sorry else "axiom_dependent" if unauthorized else "failed")
        structured_hash = sha256_bytes(canonical_bytes(structured)) if structured is not None else sha256_bytes(b"")
        diagnostic_hash = sha256_bytes(canonical_bytes({
            "returncode": execution.returncode,
            "timed_out": execution.timed_out,
            "stdout": execution.stdout,
            "stderr": execution.stderr,
        }))
        witness_id = "lean:" + sha256_bytes(canonical_bytes({
            "claim": claim_hash, "theorem": theorem_hash, "artifact": artifact_hash,
            "snapshot": snapshot_hash, "generated": generated_hash,
            "profile": compiler_profile_id, "registry": self.registry_sha256,
            "structured": structured_hash,
        }))[:32]
        unsigned = {
            "schema_version": "lean_compiler_witness/v2",
            "lean_compiler_witness_id": witness_id,
            "claim_id": claim_id,
            "claim_content_sha256": claim_hash,
            "theorem_statement_sha256": theorem_hash,
            "proof_artifact_sha256": artifact_hash,
            "proof_artifact_relative_path": relative_artifact.as_posix(),
            "proof_module": proof_module,
            "source_tree_sha256": snapshot_hash,
            "original_source_tree_sha256": original_hash,
            "immutable_snapshot_sha256": snapshot_hash,
            "lakefile_sha256": lakefile_hash,
            "generated_witness_module_sha256": generated_hash,
            "generated_witness_module_path": generated_relative,
            "exact_build_target": generated_relative,
            "compiler_profile_id": compiler_profile_id,
            "compiler_registry_sha256": self.registry_sha256,
            "lake_executable_sha256": profile.lake_executable_sha256,
            "lean_executable_sha256": profile.lean_executable_sha256,
            "lean_stdlib_tree_sha256": profile.lean_stdlib_tree_sha256,
            "dependency_closure_sha256": profile.dependency_closure_sha256,
            "execution_image_digest": profile.execution_image_digest,
            "sandbox_policy_sha256": profile.sandbox_policy_sha256,
            "verifier_binary_sha256": profile.verifier_binary_sha256,
            "compiler_executable_sha256": profile.lean_executable_sha256,
            "structured_result_sha256": structured_hash,
            "build_output_sha256": diagnostic_hash,
            "toolchain": profile.toolchain,
            "command": list(execution.command) if execution.command else ["governed-oci-profile", compiler_profile_id],
            "execution_mode": "strict",
            "result": result,
            "contains_sorry": contains_sorry,
            "contains_admit": contains_sorry,
            "unapproved_axiom_count": len(unauthorized),
            "axiom_dependencies": axioms,
            "axiom_inspection_complete": structured_valid,
            "statement_binding_confirmed": bool(structured_valid and structured and structured.get("declaration_type_matches") is True),
            "warnings_as_errors": bool(structured_valid and structured and structured.get("warnings_as_errors") is True),
            "snapshot_verified_immutable": True,
            "clean_source_build": bool(structured_valid and structured and structured.get("build_from_source") is True),
            "prebuilt_artifacts_rejected": True,
            "hermetic_environment": isinstance(self.runner, OciSandboxRunner),
            "network_disabled": isinstance(self.runner, OciSandboxRunner),
            "resource_limits_enforced": isinstance(self.runner, OciSandboxRunner),
            "structured_inspection_complete": structured_valid,
            "theorem_name": theorem_name,
            "theorem_status": theorem_status,
            "verifier_principal_id": self.verifier_principal_id,
            "key_id": self.key_id,
            "signature_algorithm": "Ed25519",
            "trusted_timestamp_source": self.timestamp_source,
            "created_at": now.isoformat(),
        }
        return sign_record(unsigned, self.signing_key)

    @staticmethod
    def _structured_result_valid(
        result: dict[str, Any] | None,
        request: dict[str, Any],
        request_hash: str,
        profile: CompilerProfile,
    ) -> bool:
        if not isinstance(result, dict) or result.get("schema_version") != "wc_lean_verifier_result/v1":
            return False
        exact = {
            "request_sha256": request_hash,
            "compiler_profile_id": profile.compiler_profile_id,
            "claim_content_sha256": request["claim_content_sha256"],
            "theorem_statement_sha256": request["theorem_statement_sha256"],
            "proof_artifact_sha256": request["proof_artifact_sha256"],
            "immutable_snapshot_sha256": request["immutable_snapshot_sha256"],
            "generated_witness_module_sha256": request["generated_witness_module_sha256"],
            "lake_executable_sha256": profile.lake_executable_sha256,
            "lean_executable_sha256": profile.lean_executable_sha256,
            "lean_stdlib_tree_sha256": profile.lean_stdlib_tree_sha256,
            "dependency_closure_sha256": profile.dependency_closure_sha256,
            "execution_image_digest": profile.execution_image_digest,
            "verifier_binary_sha256": profile.verifier_binary_sha256,
        }
        if any(result.get(key) != value for key, value in exact.items()):
            return False
        axioms = result.get("axiom_dependencies")
        return isinstance(axioms, list) and all(isinstance(item, str) and item for item in axioms) and len(axioms) == len(set(axioms))


def load_production_authority_service(config_root: Path = Path("/etc/witness-authority")) -> ProofAuthorityService:
    """Load protected startup configuration; never call this with request data."""
    root = config_root.resolve()
    config_path = root / "service-config.json"
    if not config_path.is_file() or config_path.is_symlink() or root.stat().st_mode & stat.S_IWOTH:
        raise RuntimeError("protected authority service configuration is unavailable or unsafe")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    registry = json.loads((root / config["compiler_registry_file"]).read_text(encoding="utf-8"))
    governance_key = load_public_key(root / config["governance_public_key_file"])
    signing_key = load_private_key(root / config["verifier_private_key_file"])
    runner = OciSandboxRunner(
        root / config["oci_runtime_file"],
        config["oci_runtime_sha256"],
    )
    return ProofAuthorityService(
        governed_registry=registry,
        governance_public_key=governance_key,
        verifier_principal_id=config["verifier_principal_id"],
        key_id=config["key_id"],
        signing_key=signing_key,
        runner=runner,
    )


__all__ = [
    "CompilerProfile", "OciSandboxRunner", "ProofAuthorityService", "SandboxExecution",
    "canonical_bytes", "canonical_text", "content_tree_sha256", "generated_witness_module",
    "load_production_authority_service", "public_key_fingerprint", "public_key_raw_b64url",
    "register_sqlite_crypto_functions", "sha256_bytes", "sign_record", "signed_payload_canonical_json",
    "verify_governed_registry", "verify_record",
]
