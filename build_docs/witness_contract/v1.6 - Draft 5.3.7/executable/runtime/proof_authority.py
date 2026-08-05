#!/usr/bin/env python3
"""Fail-closed Lean proof authority for Witness Contract Draft 5.3.7.

Authority inputs are derived from a sealed source snapshot.  Submitted Lean is
compiled in a domain that cannot see the verifier request or final result
directory.  A second, trusted verifier domain inspects the compiled Lean
environment and signs a canonical result.  Only an authorized signed result can
become a server-signed compiler witness.

The portable corpus exercises these boundaries without claiming that a real
governed OCI image, Lean toolchain, or external trust root is present.
"""

from __future__ import annotations

import base64
import ctypes
import errno
import hashlib
import json
import os
import re
import selectors
import signal
import shutil
import sqlite3
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Protocol

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
MAX_SOURCE_FILE_BYTES = 64 * 1024 * 1024
MAX_SOURCE_TOTAL_BYTES = 512 * 1024 * 1024
MAX_SOURCE_FILES = 4096
MAX_SOURCE_DIRECTORIES = 1024
MAX_SOURCE_DEPTH = 32
MAX_SOURCE_PATH_BYTES = 1024
MAX_DIRECTORY_ENTRIES = 4096
MAX_SNAPSHOT_SECONDS = 30.0
MAX_RESULT_BYTES = 1024 * 1024
MAX_INSPECTION_BYTES = 4 * 1024 * 1024
MAX_COMPILER_ARTIFACT_BYTES = 128 * 1024 * 1024
MAX_HANDOFF_TOTAL_BYTES = 512 * 1024 * 1024
MAX_STDOUT_BYTES = 1024 * 1024
MAX_STDERR_BYTES = 1024 * 1024
MAX_COMBINED_OUTPUT_BYTES = 2 * 1024 * 1024
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)


ACTIVE_SCHEMA_FILES = {
    "verifier_request": "lean_verifier_request_v4.schema.json",
    "inspector_result": "lean_inspector_result_v1.schema.json",
    "handoff_manifest": "lean_compile_handoff_v2.schema.json",
    "sandbox_invocation": "effective_sandbox_invocation_v4.schema.json",
    "verifier_result": "lean_verifier_result_v5.schema.json",
    "compiler_witness": "lean_compiler_witness_v6.schema.json",
    "proof_check_request": "proof_check_request_v1.schema.json",
    "proof_check_result": "proof_check_result_v5.schema.json",
    "compiler_registry": "governed_compiler_registry_v2.schema.json",
    "proof_policy_registry": "proof_policy_registry_v1.schema.json",
    "platform_capability": "platform_capability_probe_v1.schema.json",
    "trusted_artifact_registry": "trusted_artifact_attestation_registry_v1.schema.json",
}


ERROR_CODES = frozenset({
    "snapshot_creation_failed", "snapshot_mutation_detected", "artifact_digest_mismatch",
    "generated_module_digest_mismatch", "compiler_profile_inactive", "runtime_digest_mismatch",
    "sandbox_policy_mismatch", "verifier_result_missing", "verifier_result_invalid",
    "verifier_result_signature_invalid", "theorem_declaration_missing", "theorem_type_mismatch",
    "forbidden_axiom_present", "sorry_axiom_present", "unsafe_dependency_present",
    "resource_limit_exceeded", "verification_timeout", "authority_snapshot_invalid",
    "ledger_cutoff_mismatch", "governance_authorization_invalid", "toolchain_unavailable",
    "policy_decision_invalid", "runtime_version_mismatch", "root_execution_forbidden",
    "sandbox_control_unsupported", "output_limit_exceeded",
})


class AuthorityFailure(RuntimeError):
    def __init__(self, code: str, message: str):
        if code not in ERROR_CODES:
            raise ValueError(f"unknown authority error code: {code}")
        super().__init__(message)
        self.code = code


class CanonicalSchemaValidator:
    """Dependency-free, fail-closed validator for the corpus schema subset.

    Every active schema is also compiled by the canonical AJV phase.  This
    runtime validator deliberately implements only the JSON Schema keywords
    used by the authority-boundary schemas and rejects unknown keywords there.
    """

    def __init__(self, schema_root: Path):
        root = Path(schema_root)
        if not root.is_dir() or root.is_symlink():
            raise RuntimeError("authority schema root must be a real directory")
        documents: dict[str, dict[str, Any]] = {}
        for path in sorted(root.glob("*.schema.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(document, dict) or document.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                raise RuntimeError(f"invalid authority schema document: {path.name}")
            documents[path.name] = document
        missing = sorted(set(ACTIVE_SCHEMA_FILES.values()) - set(documents))
        if missing:
            raise RuntimeError(f"active authority schemas are missing: {missing}")
        self.root = root
        self.documents = documents

    def validate(self, surface: str, value: Any) -> None:
        filename = ACTIVE_SCHEMA_FILES.get(surface)
        if filename is None:
            raise RuntimeError(f"unknown authority schema surface: {surface}")
        try:
            self._validate_node(self.documents[filename], value, self.documents[filename], filename, ())
        except ValueError as error:
            raise AuthorityFailure("verifier_result_invalid", f"{surface} schema validation failed: {error}") from error

    def _resolve_ref(self, reference: str, document: dict[str, Any], filename: str) -> tuple[dict[str, Any], dict[str, Any], str]:
        if reference.startswith("#/"):
            target: Any = document
            for part in reference[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
            return target, document, filename
        other_name, _, fragment = reference.partition("#")
        if other_name not in self.documents:
            raise ValueError(f"unresolved schema reference {reference}")
        other = self.documents[other_name]
        if fragment:
            target: Any = other
            for part in fragment.lstrip("/").split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
            return target, other, other_name
        return other, other, other_name

    @staticmethod
    def _type_matches(expected: str, value: Any) -> bool:
        return {
            "object": isinstance(value, dict), "array": isinstance(value, list),
            "string": isinstance(value, str), "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": isinstance(value, bool), "null": value is None,
        }.get(expected, False)

    def _conforms(self, schema: dict[str, Any], value: Any, document: dict[str, Any], filename: str) -> bool:
        try:
            self._validate_node(schema, value, document, filename, ())
            return True
        except (ValueError, KeyError, TypeError):
            return False

    def _validate_node(self, schema: dict[str, Any], value: Any, document: dict[str, Any], filename: str, path: tuple[Any, ...]) -> None:
        location = "/".join(map(str, path)) or "<root>"
        supported_keywords = {
            "$schema", "$id", "$ref", "$defs", "title", "description",
            "type", "const", "enum", "required", "properties", "additionalProperties",
            "minItems", "maxItems", "uniqueItems", "items", "contains",
            "minLength", "maxLength", "pattern", "format", "minimum", "maximum",
            "maxProperties", "allOf", "oneOf", "if", "then", "else",
        }
        unknown = sorted(set(schema) - supported_keywords)
        if unknown:
            raise ValueError(f"{location}: unsupported schema keywords {unknown}")
        if "$ref" in schema:
            target, target_document, target_filename = self._resolve_ref(schema["$ref"], document, filename)
            self._validate_node(target, value, target_document, target_filename, path)
            return
        if "const" in schema and value != schema["const"]:
            raise ValueError(f"{location}: value differs from const")
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError(f"{location}: value is outside enum")
        if "type" in schema:
            choices = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
            if not any(self._type_matches(choice, value) for choice in choices):
                raise ValueError(f"{location}: type mismatch; expected {choices}")
        if isinstance(value, dict):
            required = schema.get("required", [])
            missing = [key for key in required if key not in value]
            if missing:
                raise ValueError(f"{location}: missing required properties {missing}")
            properties = schema.get("properties", {})
            if schema.get("additionalProperties") is False:
                extra = sorted(set(value) - set(properties))
                if extra:
                    raise ValueError(f"{location}: additional properties {extra}")
            if "maxProperties" in schema and len(value) > schema["maxProperties"]:
                raise ValueError(f"{location}: too many properties")
            for key, child in properties.items():
                if key in value:
                    self._validate_node(child, value[key], document, filename, (*path, key))
        if isinstance(value, list):
            if len(value) < schema.get("minItems", 0) or ("maxItems" in schema and len(value) > schema["maxItems"]):
                raise ValueError(f"{location}: array length is outside bounds")
            if schema.get("uniqueItems") and len({canonical_text(item) for item in value}) != len(value):
                raise ValueError(f"{location}: array items are not unique")
            if isinstance(schema.get("items"), dict):
                for index, item in enumerate(value):
                    self._validate_node(schema["items"], item, document, filename, (*path, index))
            if "contains" in schema and not any(self._conforms(schema["contains"], item, document, filename) for item in value):
                raise ValueError(f"{location}: array does not satisfy contains")
        if isinstance(value, str):
            if len(value) < schema.get("minLength", 0) or ("maxLength" in schema and len(value) > schema["maxLength"]):
                raise ValueError(f"{location}: string length is outside bounds")
            if "pattern" in schema and re.search(schema["pattern"], value) is None:
                raise ValueError(f"{location}: string does not match pattern")
            if schema.get("format") == "date-time":
                _parse_time(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                raise ValueError(f"{location}: number is below minimum")
            if "maximum" in schema and value > schema["maximum"]:
                raise ValueError(f"{location}: number is above maximum")
        if "allOf" in schema:
            for child in schema["allOf"]:
                self._validate_node(child, value, document, filename, path)
        if "oneOf" in schema:
            matches = sum(self._conforms(child, value, document, filename) for child in schema["oneOf"])
            if matches != 1:
                raise ValueError(f"{location}: oneOf matched {matches} branches")
        if "if" in schema and self._conforms(schema["if"], value, document, filename):
            if "then" in schema:
                self._validate_node(schema["then"], value, document, filename, path)
        elif "else" in schema:
            self._validate_node(schema["else"], value, document, filename, path)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_text(value: Any) -> str:
    return canonical_bytes(value).decode("utf-8")


def canonical_json_loads(text: str) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(text, object_pairs_hook=reject_duplicates)
    if canonical_text(value) != text:
        raise ValueError("JSON is not in canonical form")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def load_private_key(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("configured signing key is not Ed25519")
    return key


def load_public_key(path: Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("configured public key is not Ed25519")
    return key


def _private_key_from_bytes(data: bytes) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(data, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("configured signing key is not Ed25519")
    return key


def _public_key_from_bytes(data: bytes) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(data)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("configured public key is not Ed25519")
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


def authority_event_set_root(events: list[list[Any]] | list[tuple[Any, ...]]) -> str:
    normalized = [[int(sequence), str(payload_hash)] for sequence, payload_hash in events]
    if normalized != sorted(normalized, key=lambda item: item[0]):
        raise ValueError("authority events are not sequence ordered")
    if len({item[0] for item in normalized}) != len(normalized):
        raise ValueError("duplicate authority event sequence")
    if any(not SHA256_HEX.fullmatch(item[1]) for item in normalized):
        raise ValueError("invalid authority event payload digest")
    return sha256_bytes(canonical_bytes(normalized))


def register_sqlite_crypto_functions(connection: sqlite3.Connection) -> None:
    """Register fail-closed canonicalization, event-root, and Ed25519 functions."""

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

    def sql_event_root(value: Any) -> str | None:
        try:
            parsed = json.loads(str(value)) if value is not None else []
            return authority_event_set_root(parsed)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    connection.create_function("wc_sha256", 1, sql_sha256, deterministic=True)
    connection.create_function("wc_public_key_fingerprint", 1, sql_key_fingerprint, deterministic=True)
    connection.create_function("wc_ed25519_verify", 3, sql_ed25519_verify, deterministic=True)
    connection.create_function("wc_is_canonical_json", 1, sql_is_canonical_json, deterministic=True)
    connection.create_function("wc_authority_event_root", 1, sql_event_root, deterministic=True)


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("authority time must include a timezone")
    return parsed.astimezone(timezone.utc)


def _safe_relative_path(value: str, *, expected_suffix: str | None = None) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("path must be a nonempty normalized POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts) or path.as_posix() != value:
        raise ValueError("path traversal or non-normalized relative path is forbidden")
    if expected_suffix and path.suffix != expected_suffix:
        raise ValueError(f"path must end in {expected_suffix}")
    return path


def _check_trusted_stat(info: os.stat_result, *, expected_uid: int, directory: bool, link_count_one: bool = True) -> None:
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected_type(info.st_mode):
        raise RuntimeError("trusted path has the wrong filesystem type")
    if info.st_uid != expected_uid:
        raise RuntimeError("trusted path owner does not match authority policy")
    if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise RuntimeError("trusted path is group- or world-writable")
    if link_count_one and info.st_nlink != 1:
        raise RuntimeError("trusted file has ambiguous hard-link identity")


def secure_read_bytes(root: Path, relative: str, *, expected_uid: int, maximum: int = MAX_SOURCE_FILE_BYTES) -> bytes:
    """Open a trusted-root file component-by-component with O_NOFOLLOW."""
    parts = _safe_relative_path(relative).parts
    root_fd = os.open(root, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    current_fd = root_fd
    try:
        _check_trusted_stat(os.fstat(root_fd), expected_uid=expected_uid, directory=True, link_count_one=False)
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW, dir_fd=current_fd)
            _check_trusted_stat(os.fstat(next_fd), expected_uid=expected_uid, directory=True, link_count_one=False)
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | O_NOFOLLOW, dir_fd=current_fd)
        try:
            before = os.fstat(file_fd)
            _check_trusted_stat(before, expected_uid=expected_uid, directory=False)
            if before.st_size > maximum:
                raise RuntimeError("trusted file exceeds its maximum size")
            chunks: list[bytes] = []
            remaining = maximum + 1
            while remaining:
                chunk = os.read(file_fd, min(1024 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
            after = os.fstat(file_fd)
            identity = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns, item.st_nlink)
            if len(data) > maximum or identity(before) != identity(after):
                raise RuntimeError("trusted file changed while it was read")
            return data
        finally:
            os.close(file_fd)
    finally:
        if current_fd != root_fd:
            os.close(current_fd)
        os.close(root_fd)


def validate_trusted_root_ancestry(root: Path, *, expected_uid: int) -> None:
    """Reject a trust root reachable through a symlink or writable ancestor."""
    if not root.is_absolute():
        raise RuntimeError("trusted root must be absolute")
    current = Path(root.anchor)
    anchor_info = current.lstat()
    if anchor_info.st_uid != expected_uid or anchor_info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise RuntimeError("trusted-root filesystem anchor is unsafe")
    for part in root.parts[1:]:
        current = current / part
        info = current.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise RuntimeError("trusted-root ancestry contains an unsafe component")
        if info.st_uid != expected_uid or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise RuntimeError("trusted-root ancestry has unsafe ownership or write permissions")


@dataclass(frozen=True)
class CompilerProfile:
    compiler_profile_id: str
    toolchain: str
    image_reference: str
    oci_image_digest: str
    oci_runtime_sha256: str
    oci_runtime_version: str
    lake_executable_sha256: str
    lean_executable_sha256: str
    lean_stdlib_tree_sha256: str
    dependency_closure_sha256: str
    verifier_executable_sha256: str
    verifier_source_revision: str
    verifier_build_attestation_id: str
    sandbox_policy_sha256: str
    verifier_result_signer_key_id: str
    verifier_result_public_key_base64url: str
    authorized_axioms: frozenset[str]
    valid_from: str
    valid_until: str | None

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "CompilerProfile":
        digest_fields = (
            "oci_runtime_sha256", "lake_executable_sha256", "lean_executable_sha256",
            "lean_stdlib_tree_sha256", "dependency_closure_sha256",
            "verifier_executable_sha256", "sandbox_policy_sha256",
        )
        if any(not SHA256_HEX.fullmatch(str(record.get(name, ""))) for name in digest_fields):
            raise ValueError("compiler profile contains an invalid SHA-256 digest")
        if not IMAGE_DIGEST.fullmatch(str(record.get("oci_image_digest", ""))):
            raise ValueError("compiler profile OCI image is not digest-pinned")
        public_raw = _b64url_decode(str(record.get("verifier_result_public_key_base64url", "")))
        if len(public_raw) != 32:
            raise ValueError("compiler profile verifier-result key is not Ed25519")
        return cls(
            compiler_profile_id=record["compiler_profile_id"], toolchain=record["toolchain"],
            image_reference=record["image_reference"], oci_image_digest=record["oci_image_digest"],
            oci_runtime_sha256=record["oci_runtime_sha256"], oci_runtime_version=record["oci_runtime_version"],
            lake_executable_sha256=record["lake_executable_sha256"], lean_executable_sha256=record["lean_executable_sha256"],
            lean_stdlib_tree_sha256=record["lean_stdlib_tree_sha256"], dependency_closure_sha256=record["dependency_closure_sha256"],
            verifier_executable_sha256=record["verifier_executable_sha256"], verifier_source_revision=record["verifier_source_revision"],
            verifier_build_attestation_id=record["verifier_build_attestation_id"], sandbox_policy_sha256=record["sandbox_policy_sha256"],
            verifier_result_signer_key_id=record["verifier_result_signer_key_id"],
            verifier_result_public_key_base64url=record["verifier_result_public_key_base64url"],
            authorized_axioms=frozenset(record.get("authorized_axioms", [])),
            valid_from=record["valid_from"], valid_until=record.get("valid_until"),
        )

    @property
    def verifier_result_public_key(self) -> Ed25519PublicKey:
        return Ed25519PublicKey.from_public_bytes(_b64url_decode(self.verifier_result_public_key_base64url))

    def as_verifier_record(self) -> dict[str, Any]:
        """Canonical public profile made available only to the trusted domain."""
        return {
            "compiler_profile_id": self.compiler_profile_id,
            "toolchain": self.toolchain,
            "image_reference": self.image_reference,
            "oci_image_digest": self.oci_image_digest,
            "oci_runtime_sha256": self.oci_runtime_sha256,
            "oci_runtime_version": self.oci_runtime_version,
            "lake_executable_sha256": self.lake_executable_sha256,
            "lean_executable_sha256": self.lean_executable_sha256,
            "lean_stdlib_tree_sha256": self.lean_stdlib_tree_sha256,
            "dependency_closure_sha256": self.dependency_closure_sha256,
            "verifier_executable_sha256": self.verifier_executable_sha256,
            "verifier_source_revision": self.verifier_source_revision,
            "verifier_build_attestation_id": self.verifier_build_attestation_id,
            "sandbox_policy_sha256": self.sandbox_policy_sha256,
            "verifier_result_signer_key_id": self.verifier_result_signer_key_id,
            "verifier_result_public_key_base64url": self.verifier_result_public_key_base64url,
            "authorized_axioms": sorted(self.authorized_axioms),
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
        }


def verify_governed_registry(record: dict[str, Any], governance_key: Ed25519PublicKey) -> dict[str, CompilerProfile]:
    if record.get("schema_version") != "governed_compiler_registry/v2" or not verify_record(record, governance_key):
        raise ValueError("compiler registry is not a valid governance-signed v2 registry")
    profiles = [CompilerProfile.from_record(item) for item in record.get("profiles", [])]
    by_id = {profile.compiler_profile_id: profile for profile in profiles}
    if not profiles or len(by_id) != len(profiles):
        raise ValueError("compiler profile identifiers must be nonempty and unique")
    return by_id


def verify_trusted_artifact_registry(
    record: dict[str, Any], governance_key: Ed25519PublicKey, *,
    trusted_root: Path, expected_uid: int,
) -> str:
    """Verify direct trusted-root files and signed-attestation-only artifacts."""
    if record.get("schema_version") != "trusted_artifact_attestation_registry/v1" or not verify_record(record, governance_key):
        raise RuntimeError("trusted artifact registry is not governance-signed")
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise RuntimeError("trusted artifact registry is empty")
    identifiers: set[str] = set()
    required_roles = {"database_migrations", "trusted_inspector", "oci_image_metadata", "dependency_manifest"}
    observed_roles: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"artifact_id", "role", "verification_mode", "relative_path", "sha256", "attestation_id"}:
            raise RuntimeError("trusted artifact registry entry is not canonical")
        artifact_id = artifact["artifact_id"]
        if not isinstance(artifact_id, str) or not artifact_id or artifact_id in identifiers:
            raise RuntimeError("trusted artifact identifiers are invalid or duplicated")
        identifiers.add(artifact_id); observed_roles.add(artifact["role"])
        if not SHA256_HEX.fullmatch(str(artifact["sha256"])):
            raise RuntimeError("trusted artifact digest is invalid")
        if artifact["verification_mode"] == "direct_trusted_root_file":
            if not isinstance(artifact["relative_path"], str) or artifact["attestation_id"] is not None:
                raise RuntimeError("direct trusted artifact binding is malformed")
            data = secure_read_bytes(trusted_root, artifact["relative_path"], expected_uid=expected_uid)
            if sha256_bytes(data) != artifact["sha256"]:
                raise RuntimeError("direct trusted artifact digest mismatch")
        elif artifact["verification_mode"] == "governance_signed_build_attestation":
            if artifact["relative_path"] is not None or not isinstance(artifact["attestation_id"], str) or not artifact["attestation_id"]:
                raise RuntimeError("attested trusted artifact binding is malformed")
        else:
            raise RuntimeError("unknown trusted artifact verification mode")
    if not required_roles.issubset(observed_roles):
        raise RuntimeError("trusted artifact registry does not cover every claimed role")
    return sha256_bytes(canonical_bytes(record))


@dataclass(frozen=True)
class ResolvedPolicyDecision:
    policy_decision_id: str
    canonical_record: dict[str, Any]
    canonical_record_sha256: str
    maximum_timeout_seconds: int
    maximum_source_bytes: int

    def effective_limits(self) -> "EffectiveResourceLimits":
        return EffectiveResourceLimits(
            timeout_seconds=min(self.maximum_timeout_seconds, 600),
            source_total_bytes=min(self.maximum_source_bytes, MAX_SOURCE_TOTAL_BYTES),
            compiler_artifact_file_bytes=MAX_COMPILER_ARTIFACT_BYTES,
            handoff_total_bytes=MAX_HANDOFF_TOTAL_BYTES,
            inspection_output_bytes=MAX_INSPECTION_BYTES,
            final_result_bytes=MAX_RESULT_BYTES,
            stdout_bytes=MAX_STDOUT_BYTES,
            stderr_bytes=MAX_STDERR_BYTES,
            combined_output_bytes=MAX_COMBINED_OUTPUT_BYTES,
        )


class ProofPolicyResolver:
    """Resolve immutable, governance-signed proof-check policy decisions."""

    def __init__(
        self, registry: dict[str, Any], governance_key: Ed25519PublicKey, *,
        clock: Callable[[], datetime] | None = None,
        schema_validator: CanonicalSchemaValidator | None = None,
    ):
        if schema_validator is not None:
            schema_validator.validate("proof_policy_registry", registry)
        if registry.get("schema_version") != "proof_policy_registry/v1" or not verify_record(registry, governance_key):
            raise ValueError("proof policy registry is not a valid governance-signed v1 registry")
        decisions = registry.get("decisions")
        if not isinstance(decisions, list) or not decisions:
            raise ValueError("proof policy registry must contain decisions")
        indexed: dict[str, dict[str, Any]] = {}
        for decision in decisions:
            decision_id = decision.get("policy_decision_id") if isinstance(decision, dict) else None
            if not isinstance(decision_id, str) or not decision_id or decision_id in indexed:
                raise ValueError("policy decision identifiers must be nonempty and unique")
            canonical_hash = sha256_bytes(canonical_bytes(decision))
            if decision.get("canonical_record_sha256") != canonical_hash:
                # The hash field itself is intentionally excluded to avoid recursion.
                without_hash = {key: value for key, value in decision.items() if key != "canonical_record_sha256"}
                canonical_hash = sha256_bytes(canonical_bytes(without_hash))
                if decision.get("canonical_record_sha256") != canonical_hash:
                    raise ValueError("policy decision canonical hash is invalid")
            indexed[decision_id] = dict(decision)
        self.registry = registry
        self.decisions = indexed
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def resolve(
        self, policy_decision_id: str, *, subject_id: str, operation: str,
        compiler_profile_id: str, source_bundle_id: str,
    ) -> ResolvedPolicyDecision:
        if not isinstance(policy_decision_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", policy_decision_id):
            raise AuthorityFailure("policy_decision_invalid", "policy decision identifier is malformed")
        decision = self.decisions.get(policy_decision_id)
        if decision is None:
            raise AuthorityFailure("policy_decision_invalid", "policy decision is unresolved")
        now = self.clock().astimezone(timezone.utc)
        valid_until = decision.get("valid_until")
        if decision.get("status") != "active" or now < _parse_time(decision["valid_from"]) or (valid_until and now >= _parse_time(valid_until)):
            raise AuthorityFailure("policy_decision_invalid", "policy decision is inactive, revoked, or expired")
        if decision.get("subject_id") not in {subject_id, "*"} or decision.get("operation") != operation:
            raise AuthorityFailure("policy_decision_invalid", "policy decision subject or operation is out of scope")
        if compiler_profile_id not in decision.get("compiler_profile_ids", []):
            raise AuthorityFailure("policy_decision_invalid", "compiler profile is outside policy scope")
        bundle_patterns = decision.get("source_bundle_ids", [])
        if source_bundle_id not in bundle_patterns and "*" not in bundle_patterns:
            raise AuthorityFailure("policy_decision_invalid", "source bundle is outside policy scope")
        without_hash = {key: value for key, value in decision.items() if key != "canonical_record_sha256"}
        observed_hash = sha256_bytes(canonical_bytes(without_hash))
        if observed_hash != decision["canonical_record_sha256"]:
            raise AuthorityFailure("policy_decision_invalid", "policy record changed after registration")
        permissions = decision.get("resource_permissions")
        if not isinstance(permissions, dict):
            raise AuthorityFailure("policy_decision_invalid", "policy resource permissions are absent")
        timeout = permissions.get("maximum_timeout_seconds")
        source_bytes = permissions.get("maximum_source_bytes")
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
            raise AuthorityFailure("policy_decision_invalid", "policy timeout permission is invalid")
        if not isinstance(source_bytes, int) or isinstance(source_bytes, bool) or source_bytes <= 0:
            raise AuthorityFailure("policy_decision_invalid", "policy source-byte permission is invalid")
        return ResolvedPolicyDecision(
            policy_decision_id, dict(decision), observed_hash,
            timeout, source_bytes,
        )


@dataclass(frozen=True)
class EffectiveResourceLimits:
    timeout_seconds: int
    source_total_bytes: int
    compiler_artifact_file_bytes: int
    handoff_total_bytes: int
    inspection_output_bytes: int
    final_result_bytes: int
    stdout_bytes: int
    stderr_bytes: int
    combined_output_bytes: int

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"effective resource limit {name} must be a positive integer")

    def as_dict(self) -> dict[str, int]:
        return dict(self.__dict__)

    @property
    def sha256(self) -> str:
        return sha256_bytes(canonical_bytes(self.as_dict()))


@dataclass(frozen=True)
class SnapshotLimits:
    maximum_files: int = MAX_SOURCE_FILES
    maximum_directories: int = MAX_SOURCE_DIRECTORIES
    maximum_total_bytes: int = MAX_SOURCE_TOTAL_BYTES
    maximum_file_bytes: int = MAX_SOURCE_FILE_BYTES
    maximum_depth: int = MAX_SOURCE_DEPTH
    maximum_path_bytes: int = MAX_SOURCE_PATH_BYTES
    maximum_directory_entries: int = MAX_DIRECTORY_ENTRIES
    maximum_seconds: float = MAX_SNAPSHOT_SECONDS

    def __post_init__(self) -> None:
        values = (
            self.maximum_files, self.maximum_directories, self.maximum_total_bytes,
            self.maximum_file_bytes, self.maximum_depth, self.maximum_path_bytes,
            self.maximum_directory_entries,
        )
        if any(value <= 0 for value in values) or self.maximum_seconds <= 0:
            raise ValueError("snapshot limits must all be positive")


def _source_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns,
        info.st_ctime_ns, info.st_nlink,
    )


def _check_snapshot_deadline(started: float, limits: SnapshotLimits) -> None:
    if time.monotonic() - started > limits.maximum_seconds:
        raise AuthorityFailure("resource_limit_exceeded", "source snapshot exceeded its wall-clock limit")


def _enumerate_source_fd(root_fd: int, limits: SnapshotLimits, started: float) -> list[tuple[PurePosixPath, tuple[int, ...]]]:
    """Enumerate from one retained root FD using no-follow component opens."""
    files: list[tuple[PurePosixPath, tuple[int, ...]]] = []
    directories = 0
    total_bytes = 0
    normalized: set[str] = set()

    def walk(directory_fd: int, prefix: PurePosixPath, depth: int) -> None:
        nonlocal directories, total_bytes
        _check_snapshot_deadline(started, limits)
        directories += 1
        if directories > limits.maximum_directories or depth > limits.maximum_depth:
            raise AuthorityFailure("resource_limit_exceeded", "source directory or depth limit exceeded")
        names = sorted(os.listdir(directory_fd), key=lambda value: value.encode("utf-8", "surrogateescape"))
        if len(names) > limits.maximum_directory_entries:
            raise AuthorityFailure("resource_limit_exceeded", "source directory entry limit exceeded")
        for name in names:
            if name in {"", ".", ".."} or "/" in name or "\x00" in name:
                raise ValueError("source tree contains an unsafe filename")
            relative = prefix / name if prefix.parts else PurePosixPath(name)
            relative_text = relative.as_posix()
            if len(relative_text.encode("utf-8", "surrogateescape")) > limits.maximum_path_bytes:
                raise AuthorityFailure("resource_limit_exceeded", "source path length limit exceeded")
            folded = relative_text.casefold()
            if folded in normalized:
                raise ValueError(f"source contains a normalized/case-colliding path: {relative}")
            normalized.add(folded)
            info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(f"symbolic links are forbidden: {relative}")
            if stat.S_ISDIR(info.st_mode):
                child_fd = os.open(name, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW, dir_fd=directory_fd)
                try:
                    opened = os.fstat(child_fd)
                    if _source_identity(opened) != _source_identity(info):
                        raise AuthorityFailure("snapshot_mutation_detected", f"directory changed during traversal: {relative}")
                    walk(child_fd, relative, depth + 1)
                finally:
                    os.close(child_fd)
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"special filesystem nodes are forbidden: {relative}")
            if info.st_nlink != 1:
                raise ValueError(f"hard-linked source files are forbidden: {relative}")
            if info.st_size > limits.maximum_file_bytes:
                raise AuthorityFailure("resource_limit_exceeded", f"source file exceeds limit: {relative}")
            if info.st_size > 4096 and getattr(info, "st_blocks", 0) * 512 < info.st_size:
                raise ValueError(f"sparse source files are forbidden: {relative}")
            if relative.suffix.lower() in FORBIDDEN_BUILD_SUFFIXES:
                raise ValueError(f"prebuilt, native, or executable artifact is forbidden: {relative}")
            if info.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                raise ValueError(f"executable source-tree file is forbidden: {relative}")
            files.append((relative, _source_identity(info)))
            total_bytes += info.st_size
            if len(files) > limits.maximum_files or total_bytes > limits.maximum_total_bytes:
                raise AuthorityFailure("resource_limit_exceeded", "source file-count or aggregate-byte limit exceeded")

    walk(root_fd, PurePosixPath(), 0)
    return sorted(files, key=lambda item: item[0].as_posix().encode("utf-8", "surrogateescape"))


def _open_relative_file(root_fd: int, relative: PurePosixPath) -> int:
    current_fd = os.dup(root_fd)
    try:
        for part in relative.parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return os.open(relative.parts[-1], os.O_RDONLY | O_NOFOLLOW, dir_fd=current_fd)
    finally:
        os.close(current_fd)


def _source_relatives(source_root: Path, limits: SnapshotLimits | None = None) -> list[PurePosixPath]:
    selected = limits or SnapshotLimits()
    root_fd = os.open(source_root, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    try:
        return [relative for relative, _ in _enumerate_source_fd(root_fd, selected, time.monotonic())]
    finally:
        os.close(root_fd)


def _stable_read_source(source_root: Path, relative: PurePosixPath, limits: SnapshotLimits | None = None) -> tuple[bytes, tuple[int, ...]]:
    """Compatibility helper; authority snapshot copying itself is streaming."""
    selected = limits or SnapshotLimits()
    root_fd = os.open(source_root, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    try:
        file_fd = _open_relative_file(root_fd, relative)
        try:
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > selected.maximum_file_bytes:
                raise ValueError(f"unsafe source identity: {relative}")
            chunks: list[bytes] = []
            remaining = selected.maximum_file_bytes + 1
            while remaining:
                chunk = os.read(file_fd, min(1024 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk); remaining -= len(chunk)
            after = os.fstat(file_fd)
            if _source_identity(before) != _source_identity(after) or remaining == 0:
                raise AuthorityFailure("snapshot_mutation_detected", f"source changed while reading: {relative}")
            return b"".join(chunks), _source_identity(before)
        finally:
            os.close(file_fd)
    finally:
        os.close(root_fd)


def _tree_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise AuthorityFailure("snapshot_mutation_detected", "sealed snapshot contains an unsafe file")
        data = path.read_bytes()
        records.append({
            "path": path.relative_to(root).as_posix(), "size": len(data),
            "sha256": sha256_bytes(data),
            "executable": bool(info.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)),
        })
    return records


def content_tree_sha256(source_root: Path) -> str:
    """Diagnostic helper. Authority execution uses only the sealed snapshot digest."""
    records = []
    for relative in _source_relatives(source_root):
        data, _ = _stable_read_source(source_root, relative)
        records.append({"path": relative.as_posix(), "size": len(data), "sha256": sha256_bytes(data), "executable": False})
    return sha256_bytes(canonical_bytes(records))


@dataclass(frozen=True)
class ImmutableSnapshot:
    root: Path
    snapshot_id: str
    tree_sha256: str
    records: tuple[dict[str, Any], ...]


def create_immutable_snapshot(
    source_root: Path,
    destination: Path,
    *,
    after_file_copy: Callable[[PurePosixPath], None] | None = None,
    limits: SnapshotLimits | None = None,
) -> ImmutableSnapshot:
    selected = limits or SnapshotLimits()
    started = time.monotonic()
    if source_root.is_symlink():
        raise ValueError("source root must not be a symbolic link")
    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise ValueError("source root must be a real directory")
    root_fd = os.open(source_root, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    root_identity = _source_identity(os.fstat(root_fd))
    enumerated = _enumerate_source_fd(root_fd, selected, started)
    if not enumerated:
        os.close(root_fd)
        raise ValueError("source snapshot is empty")
    source_identities = {relative.as_posix(): identity for relative, identity in enumerated}
    source_hashes: dict[str, str] = {}
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        for relative, expected_identity in enumerated:
            _check_snapshot_deadline(started, selected)
            source_fd = _open_relative_file(root_fd, relative)
            try:
                before = os.fstat(source_fd)
                if _source_identity(before) != expected_identity:
                    raise AuthorityFailure("snapshot_mutation_detected", f"source replaced before copy: {relative}")
                target = destination.joinpath(*relative.parts)
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o400)
                digest = hashlib.sha256(); copied = 0
                try:
                    while True:
                        _check_snapshot_deadline(started, selected)
                        chunk = os.read(source_fd, 1024 * 1024)
                        if not chunk:
                            break
                        copied += len(chunk)
                        if copied > selected.maximum_file_bytes:
                            raise AuthorityFailure("resource_limit_exceeded", f"source file grew beyond limit: {relative}")
                        digest.update(chunk)
                        view = memoryview(chunk)
                        while view:
                            written = os.write(target_fd, view); view = view[written:]
                    os.fsync(target_fd)
                finally:
                    os.close(target_fd)
                after = os.fstat(source_fd)
                if _source_identity(before) != _source_identity(after) or copied != before.st_size:
                    raise AuthorityFailure("snapshot_mutation_detected", f"source changed while copying: {relative}")
                source_hashes[relative.as_posix()] = digest.hexdigest()
            finally:
                os.close(source_fd)
            if after_file_copy:
                after_file_copy(relative)

        if _source_identity(os.fstat(root_fd)) != root_identity:
            raise AuthorityFailure("snapshot_mutation_detected", "source root identity changed during snapshot creation")
        repeated = _enumerate_source_fd(root_fd, selected, started)
        if repeated != enumerated:
            raise AuthorityFailure("snapshot_mutation_detected", "source changed: path set or metadata changed during snapshot creation")
        for relative, expected_identity in enumerated:
            file_fd = _open_relative_file(root_fd, relative)
            digest = hashlib.sha256()
            try:
                before = os.fstat(file_fd)
                if _source_identity(before) != expected_identity:
                    raise AuthorityFailure("snapshot_mutation_detected", f"source changed after copy: {relative}")
                while chunk := os.read(file_fd, 1024 * 1024):
                    digest.update(chunk)
                after = os.fstat(file_fd)
            finally:
                os.close(file_fd)
            if _source_identity(before) != _source_identity(after) or digest.hexdigest() != source_hashes[relative.as_posix()]:
                raise AuthorityFailure("snapshot_mutation_detected", f"source changed during snapshot creation: {relative}")
    finally:
        os.close(root_fd)

    for path in sorted(destination.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    destination.chmod(0o555)
    records = _tree_records(destination)
    tree_hash = sha256_bytes(canonical_bytes(records))
    verify_sealed_snapshot(destination, tree_hash)
    return ImmutableSnapshot(destination, f"sha256:{tree_hash}", tree_hash, tuple(records))


def verify_sealed_snapshot(root: Path, expected_tree_sha256: str) -> None:
    if stat.S_IMODE(root.stat().st_mode) != 0o555:
        raise AuthorityFailure("snapshot_mutation_detected", "snapshot root is not sealed")
    for path in root.rglob("*"):
        expected = 0o555 if path.is_dir() else 0o444
        if path.is_symlink() or stat.S_IMODE(path.lstat().st_mode) != expected:
            raise AuthorityFailure("snapshot_mutation_detected", "snapshot permissions or identity changed")
    observed = sha256_bytes(canonical_bytes(_tree_records(root)))
    if observed != expected_tree_sha256:
        raise AuthorityFailure("snapshot_mutation_detected", "sealed snapshot digest changed")


def _proof_module(relative: PurePosixPath) -> str:
    if relative.suffix != ".lean":
        raise ValueError("proof artifact must be a .lean source file")
    parts = (*relative.parts[:-1], relative.stem)
    if not parts or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", part) for part in parts):
        raise ValueError("proof artifact path is not an importable Lean module")
    return ".".join(parts)


def _validate_statement(statement: str) -> None:
    if not isinstance(statement, str) or not statement or len(statement.encode("utf-8")) > 65536:
        raise ValueError("claimed theorem statement is empty or too large")
    if any(ord(character) < 0x20 for character in statement) or any(token in statement for token in ("\u2028", "\u2029", "--", "/-", "-/")):
        raise ValueError("claimed theorem statement must be one comment-free Lean term")


def generated_witness_module(*, proof_module: str, theorem_statement: str, theorem_name: str) -> str:
    _validate_statement(theorem_statement)
    if not LEAN_IDENTIFIER.fullmatch(theorem_name):
        raise ValueError("theorem_name is not a valid fully qualified Lean identifier")
    return (
        f"import {proof_module}\n"
        "set_option autoImplicit false\n"
        "set_option warningAsError true\n"
        "namespace WitnessAuthorityGenerated\n"
        f"theorem BoundClaim : ({theorem_statement}) := {theorem_name}\n"
        "end WitnessAuthorityGenerated\n"
    )


@dataclass(frozen=True)
class EffectiveSandboxInvocation:
    domain: str
    oci_runtime_path: str
    oci_runtime_sha256: str
    oci_runtime_version: str
    oci_runtime_version_output_sha256: str
    image_reference: str
    image_digest: str
    entrypoint: str
    arguments: tuple[str, ...]
    container_uid: int
    container_gid: int
    network_mode: str
    read_only_rootfs: bool
    capability_drop_set: tuple[str, ...]
    security_options: tuple[str, ...]
    seccomp_profile_sha256: str
    seccomp_profile_path: str
    apparmor_profile: str
    selinux_label: str
    user_namespace_mode: str
    pid_limit: int
    memory_limit: str
    cpu_limit: str
    compiler_artifact_file_size_limit: int
    handoff_total_bytes_limit: int
    inspection_output_bytes_limit: int
    final_result_bytes_limit: int
    stdout_bytes_limit: int
    stderr_bytes_limit: int
    combined_output_bytes_limit: int
    open_file_limit: int
    timeout: int
    environment_allowlist: tuple[str, ...]
    mount_manifest: tuple[dict[str, str], ...]
    tmpfs_mounts: tuple[dict[str, str], ...]
    working_directory: str
    requested_controls: tuple[str, ...]
    emitted_controls: tuple[str, ...]
    accepted_controls: tuple[str, ...]
    applied_controls: tuple[str, ...]
    immutable_policy_files: tuple[dict[str, str], ...]

    @property
    def domain_file_size_limit(self) -> int:
        """Return the one RLIMIT_FSIZE value authorized for this domain.

        Booleans are rejected explicitly because ``bool`` is an ``int``
        subclass in Python.  Unknown domains and out-of-policy values never
        receive a fallback.
        """
        selected = {
            "untrusted_compilation": (
                self.compiler_artifact_file_size_limit,
                MAX_COMPILER_ARTIFACT_BYTES,
            ),
            "trusted_inspection": (
                self.inspection_output_bytes_limit,
                MAX_INSPECTION_BYTES,
            ),
        }.get(self.domain)
        if selected is None:
            raise AuthorityFailure(
                "sandbox_policy_mismatch",
                f"unknown sandbox execution domain: {self.domain!r}",
            )
        value, governed_maximum = selected
        if type(value) is not int or value <= 0 or value > governed_maximum:
            raise AuthorityFailure(
                "resource_limit_exceeded",
                "domain-specific RLIMIT_FSIZE is malformed or exceeds policy",
            )
        return value

    def as_dict(self) -> dict[str, Any]:
        record = {key: (list(value) if isinstance(value, tuple) else value) for key, value in self.__dict__.items()}
        record["domain_file_size_limit"] = self.domain_file_size_limit
        argv = list(self.executed_argv)
        record["normalized_executed_argv"] = argv
        record["normalized_executed_argv_sha256"] = sha256_bytes(canonical_bytes(argv))
        return record

    @property
    def executed_argv(self) -> tuple[str, ...]:
        fsize = self.domain_file_size_limit
        command = [
            self.oci_runtime_path, "run", "--rm", "--pull=never", f"--entrypoint={self.entrypoint}",
            f"--workdir={self.working_directory}", f"--network={self.network_mode}", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges",
            f"--security-opt=seccomp={self.seccomp_profile_path}",
        ]
        if self.apparmor_profile:
            command.append(f"--security-opt=apparmor={self.apparmor_profile}")
        if self.selinux_label:
            command.append(f"--security-opt=label=type:{self.selinux_label}")
        command.extend([
            f"--userns={self.user_namespace_mode}", f"--pids-limit={self.pid_limit}",
            f"--memory={self.memory_limit}", f"--cpus={self.cpu_limit}",
            f"--user={self.container_uid}:{self.container_gid}",
            f"--ulimit=fsize={fsize}:{fsize}",
            f"--ulimit=nofile={self.open_file_limit}:{self.open_file_limit}",
        ])
        for item in self.tmpfs_mounts:
            command.append(f"--tmpfs={item['destination']}:{item['options']}")
        for mount in self.mount_manifest:
            command.append(f"--volume={mount['host_path']}:{mount['destination']}:{mount['mode']}")
        for value in self.environment_allowlist:
            command.append(f"--env={value}")
        command.extend([f"{self.image_reference}@{self.image_digest}", *self.arguments])
        return tuple(command)

    @property
    def sha256(self) -> str:
        return sha256_bytes(canonical_bytes(self.as_dict()))


@dataclass(frozen=True)
class SandboxExecution:
    returncode: int | None
    structured_result: dict[str, Any] | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    untrusted_command: tuple[str, ...] = ()
    trusted_command: tuple[str, ...] = ()
    effective_sandbox_invocation_sha256: str = ""
    security_properties: tuple[str, ...] = ()
    requested_controls: tuple[str, ...] = ()
    applied_controls: tuple[str, ...] = ()
    verified_controls: tuple[str, ...] = ()
    output_limit_exceeded: bool = False
    stdout_sha256: str = ""
    stderr_sha256: str = ""
    emitted_controls: tuple[str, ...] = ()
    accepted_controls: tuple[str, ...] = ()
    measured_controls: tuple[str, ...] = ()
    derived_controls: tuple[str, ...] = ()
    control_evidence: tuple[dict[str, Any], ...] = ()
    normalized_executed_argv: tuple[str, ...] = ()
    normalized_executed_argv_sha256: str = ""
    domain_file_size_limit: int = 0


@dataclass(frozen=True)
class BoundedProcessResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    output_limit_exceeded: bool
    stdout_sha256: str
    stderr_sha256: str


def run_bounded_process(
    command: tuple[str, ...] | list[str], *, cwd: str | Path | None = None,
    env: dict[str, str] | None = None, timeout_seconds: float,
    stdout_limit: int = MAX_STDOUT_BYTES, stderr_limit: int = MAX_STDERR_BYTES,
    combined_limit: int = MAX_COMBINED_OUTPUT_BYTES,
) -> BoundedProcessResult:
    """Stream child output under separate/combined quotas and kill descendants."""
    if min(stdout_limit, stderr_limit, combined_limit) <= 0:
        raise ValueError("subprocess output limits must be positive")
    process = subprocess.Popen(
        list(command), cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True,
    )
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    digests = {"stdout": hashlib.sha256(), "stderr": hashlib.sha256()}
    limits = {"stdout": stdout_limit, "stderr": stderr_limit}
    total = 0; timed_out = False; exceeded = False
    deadline = time.monotonic() + timeout_seconds
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True; break
            events = selector.select(min(0.1, remaining))
            if not events and process.poll() is not None:
                # Drain EOF notifications after process completion.
                events = selector.select(0)
                if not events:
                    break
            for key, _ in events:
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj); continue
                stream = key.data
                digests[stream].update(chunk)
                total += len(chunk)
                allowed = limits[stream] - len(buffers[stream])
                if allowed > 0:
                    buffers[stream].extend(chunk[:allowed])
                if len(chunk) > allowed or total > combined_limit:
                    exceeded = True; break
            if exceeded:
                break
        if timed_out or exceeded:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)
    finally:
        selector.close()
        process.stdout.close(); process.stderr.close()
    return BoundedProcessResult(
        process.returncode, buffers["stdout"].decode("utf-8", "replace"),
        buffers["stderr"].decode("utf-8", "replace"), timed_out, exceeded,
        digests["stdout"].hexdigest(), digests["stderr"].hexdigest(),
    )


class SandboxRunner(Protocol):
    def run(self, *, profile: CompilerProfile, snapshot_root: Path, generated_module: Path, request: dict[str, Any], timeout_seconds: int) -> SandboxExecution: ...


class AtomicResultPublisher:
    """Trusted-only canonical result publication using exclusive, no-follow I/O."""

    def __init__(self, directory: Path, *, expected_uid: int | None = None, maximum: int = MAX_RESULT_BYTES, create: bool = True, final_name: str = "verifier-result.json"):
        self.directory = directory
        self.expected_uid = os.getuid() if expected_uid is None else expected_uid
        self.maximum = maximum
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", final_name):
            raise ValueError("result filename is unsafe")
        self.final_name = final_name
        if create:
            directory.mkdir(mode=0o700, parents=True, exist_ok=False)
            directory.chmod(0o700)
        self._validate_directory()

    def _validate_directory(self) -> None:
        info = self.directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != self.expected_uid or stat.S_IMODE(info.st_mode) != 0o700:
            raise RuntimeError("private verifier-result directory is unsafe")

    def publish(self, record: dict[str, Any], signing_key: Ed25519PrivateKey) -> Path:
        self._validate_directory()
        return self.publish_unsigned(sign_record(record, signing_key))

    def publish_unsigned(self, record: dict[str, Any]) -> Path:
        """Publish canonical trusted-domain output; callers decide its authority."""
        self._validate_directory()
        data = canonical_bytes(record)
        if len(data) > self.maximum:
            raise AuthorityFailure("verifier_result_invalid", "verifier result exceeds its maximum size")
        nonce = sha256_bytes(data)[:24]
        temporary = f"{self.final_name}.tmp.{nonce}"
        directory_fd = os.open(self.directory, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600, dir_fd=directory_fd)
            try:
                os.write(fd, data)
                os.fsync(fd)
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
                    raise RuntimeError("temporary result identity is unsafe")
            finally:
                os.close(fd)
            _rename_noreplace(directory_fd, temporary, self.final_name)
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return self.directory / self.final_name


def _rename_noreplace(directory_fd: int, source: str, destination: str) -> None:
    """Atomically publish without replacing a pre-existing result path."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is not None:
        renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        renameat2.restype = ctypes.c_int
        if renameat2(directory_fd, source.encode(), directory_fd, destination.encode(), 1) == 0:
            return
        error = ctypes.get_errno()
        if error not in {errno.ENOSYS, errno.EINVAL}:
            raise FileExistsError(error, os.strerror(error), destination)
    # Portable atomic no-replace fallback: create the final directory entry as a
    # hard link, then immediately remove the private temporary name.
    os.link(source, destination, src_dir_fd=directory_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
    os.unlink(source, dir_fd=directory_fd)


def read_private_result(path: Path, *, expected_uid: int | None = None, maximum: int = MAX_RESULT_BYTES) -> dict[str, Any]:
    expected_uid = os.getuid() if expected_uid is None else expected_uid
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_uid != expected_uid or stat.S_IMODE(before.st_mode) != 0o600:
        raise AuthorityFailure("verifier_result_invalid", "result file identity, owner, or mode is unsafe")
    fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino) or opened.st_size > maximum:
            raise AuthorityFailure("verifier_result_invalid", "result file changed or is oversized")
        data = os.read(fd, maximum + 1)
        after = os.fstat(fd)
        if len(data) > maximum or (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise AuthorityFailure("verifier_result_invalid", "result-file race detected")
    finally:
        os.close(fd)
    try:
        value = canonical_json_loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise AuthorityFailure("verifier_result_invalid", "result is not canonical UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise AuthorityFailure("verifier_result_invalid", "result root must be an object")
    return value


class OciSandboxRunner:
    """Two-domain OCI execution; submitted Lean never receives the result mount."""

    REQUIRED_CONTROLS = frozenset({
        "explicit_entrypoint", "working_directory", "network_none", "read_only_rootfs",
        "capabilities_dropped", "no_new_privileges", "seccomp", "lsm_profile",
        "private_user_namespace", "non_root_user", "pid_limit", "memory_limit", "cpu_limit",
        "rlimit_fsize", "open_file_limit", "environment_allowlist", "mount_manifest",
    })

    def __init__(
        self, runtime_executable: Path, expected_runtime_sha256: str, expected_runtime_version: str, *,
        verifier_result_signing_key: Ed25519PrivateKey, authority_uid: int | None = None,
        authority_gid: int | None = None, seccomp_profile_path: Path | None = None,
        expected_seccomp_profile_sha256: str | None = None,
        apparmor_profile: str = "witness-authority-default", selinux_label: str = "",
        user_namespace_mode: str = "private", supported_controls: frozenset[str] | None = None,
        schema_validator: CanonicalSchemaValidator | None = None,
    ):
        runtime_input = Path(runtime_executable)
        if not runtime_input.is_absolute() or runtime_input.is_symlink():
            raise ValueError("configured OCI runtime must be an absolute non-symlink executable")
        runtime = runtime_input.resolve(strict=True)
        if not runtime.is_file() or not os.access(runtime, os.X_OK):
            raise ValueError("configured OCI runtime must be an absolute non-symlink executable")
        if not SHA256_HEX.fullmatch(expected_runtime_sha256) or sha256_file(runtime) != expected_runtime_sha256:
            raise ValueError("configured OCI runtime does not match its protected digest")
        if runtime.stat().st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise ValueError("configured OCI runtime is group- or world-writable")
        measured = run_bounded_process(
            (str(runtime), "version"), timeout_seconds=5, stdout_limit=65536,
            stderr_limit=65536, combined_limit=131072,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TZ": "UTC"},
        )
        normalized_version = " ".join((measured.stdout + " " + measured.stderr).split())
        expected_normalized = " ".join(expected_runtime_version.split())
        if measured.returncode != 0 or measured.timed_out or measured.output_limit_exceeded or normalized_version != expected_normalized:
            raise AuthorityFailure("runtime_version_mismatch", "measured OCI runtime version differs from the governed identity")
        if authority_uid is None or authority_gid is None or authority_uid == 0 or authority_gid == 0:
            raise AuthorityFailure("root_execution_forbidden", "authority domains require explicit non-root UID and GID")
        if seccomp_profile_path is None or expected_seccomp_profile_sha256 is None:
            raise AuthorityFailure("sandbox_control_unsupported", "a governed seccomp profile is required")
        seccomp = Path(seccomp_profile_path)
        if not seccomp.is_absolute() or seccomp.is_symlink() or not seccomp.is_file():
            raise AuthorityFailure("sandbox_control_unsupported", "seccomp profile must be an immutable absolute regular file")
        if seccomp.stat().st_mode & (stat.S_IWGRP | stat.S_IWOTH) or sha256_file(seccomp) != expected_seccomp_profile_sha256:
            raise AuthorityFailure("sandbox_policy_mismatch", "seccomp profile does not match its governed digest")
        if supported_controls is None:
            raise AuthorityFailure(
                "sandbox_control_unsupported",
                "a governed platform capability probe is required; configured controls are not measurements",
            )
        available = supported_controls
        missing = self.REQUIRED_CONTROLS - available
        if missing:
            raise AuthorityFailure("sandbox_control_unsupported", "OCI runtime adapter lacks required controls: " + ",".join(sorted(missing)))
        self.runtime = runtime
        self.runtime_sha256 = expected_runtime_sha256
        self.runtime_version = normalized_version
        self.runtime_version_output_sha256 = sha256_bytes(normalized_version.encode("utf-8"))
        self.verifier_result_signing_key = verifier_result_signing_key
        self.authority_uid = authority_uid
        self.authority_gid = authority_gid
        self.seccomp_profile_path = seccomp
        self.seccomp_profile_sha256 = expected_seccomp_profile_sha256
        self.apparmor_profile = apparmor_profile
        self.selinux_label = selinux_label
        self.user_namespace_mode = user_namespace_mode
        self.supported_controls = available
        self.schema_validator = schema_validator or CanonicalSchemaValidator(Path(__file__).resolve().parents[2] / "schemas")

    def _invocation(
        self, *, domain: str, profile: CompilerProfile, entrypoint: str,
        arguments: tuple[str, ...], mounts: tuple[dict[str, str], ...],
        limits: EffectiveResourceLimits, uid: int, gid: int,
    ) -> EffectiveSandboxInvocation:
        if uid == 0 or gid == 0:
            raise AuthorityFailure("root_execution_forbidden", "sandbox invocation cannot use UID or GID zero")
        if domain not in {"untrusted_compilation", "trusted_inspection"}:
            raise AuthorityFailure("sandbox_policy_mismatch", f"unknown sandbox execution domain: {domain!r}")
        requested = tuple(sorted(self.REQUIRED_CONTROLS))
        if bool(self.apparmor_profile) == bool(self.selinux_label):
            raise AuthorityFailure("sandbox_control_unsupported", "exactly one governed LSM profile must be selected")
        invocation = EffectiveSandboxInvocation(
            domain=domain, oci_runtime_path=str(self.runtime),
            oci_runtime_sha256=self.runtime_sha256, oci_runtime_version=self.runtime_version,
            oci_runtime_version_output_sha256=self.runtime_version_output_sha256,
            image_reference=profile.image_reference, image_digest=profile.oci_image_digest,
            entrypoint=entrypoint, arguments=arguments, container_uid=uid, container_gid=gid,
            network_mode="none", read_only_rootfs=True, capability_drop_set=("ALL",),
            security_options=("no-new-privileges",), seccomp_profile_sha256=self.seccomp_profile_sha256,
            seccomp_profile_path=str(self.seccomp_profile_path), apparmor_profile=self.apparmor_profile,
            selinux_label=self.selinux_label, user_namespace_mode=self.user_namespace_mode,
            pid_limit=128, memory_limit="2g", cpu_limit="2",
            compiler_artifact_file_size_limit=limits.compiler_artifact_file_bytes,
            handoff_total_bytes_limit=limits.handoff_total_bytes,
            inspection_output_bytes_limit=limits.inspection_output_bytes,
            final_result_bytes_limit=limits.final_result_bytes,
            stdout_bytes_limit=limits.stdout_bytes,
            stderr_bytes_limit=limits.stderr_bytes,
            combined_output_bytes_limit=limits.combined_output_bytes,
            open_file_limit=256, timeout=limits.timeout_seconds,
            environment_allowlist=("HOME=/nonexistent", "LANG=C.UTF-8", "LC_ALL=C.UTF-8", "TZ=UTC", "SOURCE_DATE_EPOCH=0", "LEAN_ABORT_ON_PANIC=1", "PYTHONPATH="),
            mount_manifest=mounts,
            tmpfs_mounts=(
                {"destination": "/tmp", "options": "rw,noexec,nosuid,nodev,size=512m"},
                {"destination": "/work", "options": "rw,nosuid,nodev,size=1g"},
            ),
            working_directory="/work",
            requested_controls=requested, emitted_controls=(),
            accepted_controls=(), applied_controls=(),
            immutable_policy_files=({"path": str(self.seccomp_profile_path), "sha256": self.seccomp_profile_sha256},),
        )
        emitted = self._emitted_controls_from_argv(invocation.executed_argv)
        if set(emitted) != set(requested):
            missing = sorted(set(requested) - set(emitted))
            unexpected = sorted(set(emitted) - set(requested))
            raise AuthorityFailure(
                "sandbox_policy_mismatch",
                f"exact OCI argv control mismatch; missing={missing} unexpected={unexpected}",
            )
        return replace(invocation, emitted_controls=emitted)

    @staticmethod
    def _emitted_controls_from_argv(argv: tuple[str, ...]) -> tuple[str, ...]:
        """Parse control intent only from the exact command that will execute."""
        controls: set[str] = set()
        flags = set(argv)
        prefixes = tuple(argv)
        mappings = {
            "explicit_entrypoint": "--entrypoint=",
            "working_directory": "--workdir=",
            "network_none": "--network=none",
            "read_only_rootfs": "--read-only",
            "capabilities_dropped": "--cap-drop=ALL",
            "no_new_privileges": "--security-opt=no-new-privileges",
            "seccomp": "--security-opt=seccomp=",
            "lsm_profile": "--security-opt=apparmor=",
            "private_user_namespace": "--userns=",
            "non_root_user": "--user=",
            "pid_limit": "--pids-limit=",
            "memory_limit": "--memory=",
            "cpu_limit": "--cpus=",
            "rlimit_fsize": "--ulimit=fsize=",
            "open_file_limit": "--ulimit=nofile=",
            "environment_allowlist": "--env=",
            "mount_manifest": "--volume=",
        }
        for control, token in mappings.items():
            if token in flags or any(value.startswith(token) for value in prefixes):
                controls.add(control)
        if any(value.startswith("--security-opt=label=type:") for value in prefixes):
            controls.add("lsm_profile")
        return tuple(sorted(controls))

    def _command(self, invocation: EffectiveSandboxInvocation) -> tuple[str, ...]:
        command = invocation.executed_argv
        record = invocation.as_dict()
        if record["normalized_executed_argv"] != list(command):
            raise AuthorityFailure("sandbox_policy_mismatch", "executed argv diverges from sealed invocation")
        return command

    def run(self, *, profile: CompilerProfile, snapshot_root: Path, generated_module: Path, request: dict[str, Any], timeout_seconds: int) -> SandboxExecution:
        if profile.oci_runtime_sha256 != self.runtime_sha256 or profile.oci_runtime_version != self.runtime_version:
            raise AuthorityFailure("runtime_digest_mismatch", "runtime identity differs from governed compiler profile")
        if public_key_raw_b64url(self.verifier_result_signing_key.public_key()) != profile.verifier_result_public_key_base64url:
            raise AuthorityFailure("verifier_result_signature_invalid", "protected result-signing key does not match governed profile")
        verify_sealed_snapshot(snapshot_root, request["immutable_snapshot_tree_sha256"])
        generated_root = generated_module.parents[1]
        if stat.S_IMODE(generated_root.stat().st_mode) != 0o555 or stat.S_IMODE(generated_module.stat().st_mode) != 0o444:
            raise AuthorityFailure("generated_module_digest_mismatch", "generated input permissions are not sealed")
        with tempfile.TemporaryDirectory(prefix="wc-handoff-") as handoff_name, tempfile.TemporaryDirectory(prefix="wc-control-") as control_name, tempfile.TemporaryDirectory(prefix="wc-inspection-parent-") as inspection_parent_name, tempfile.TemporaryDirectory(prefix="wc-result-parent-") as result_parent_name:
            handoff = Path(handoff_name); control = Path(control_name); inspection_parent = Path(inspection_parent_name); result_parent = Path(result_parent_name)
            handoff.chmod(0o700)
            request_path = control / "request.json"
            request_path.write_bytes(canonical_bytes(request)); request_path.chmod(0o444)
            inspection_directory = inspection_parent / "private-inspection"
            inspection_directory.mkdir(mode=0o700); inspection_directory.chmod(0o700)
            limits = EffectiveResourceLimits(**request["effective_resource_limits"])
            compile_manifest = (
                {"source": f"snapshot:{request['immutable_snapshot_tree_sha256']}", "host_path": str(snapshot_root), "destination": "/input/source", "mode": "ro", "domain": "untrusted_compilation", "purpose": "sealed_source", "lifecycle": "request"},
                {"source": f"generated:{request['generated_binding_module_sha256']}", "host_path": str(generated_root), "destination": "/input/generated", "mode": "ro", "domain": "untrusted_compilation", "purpose": "generated_type_binding", "lifecycle": "request"},
                {"source": "ephemeral:compile-handoff", "host_path": str(handoff), "destination": "/handoff", "mode": "rw", "domain": "untrusted_compilation", "purpose": "compiled_artifact_handoff", "lifecycle": "request"},
            )
            compile_invocation = self._invocation(
                domain="untrusted_compilation", profile=profile,
                entrypoint="/opt/witness-authority/bin/compile-lean",
                arguments=(
                    "--generated", "/input/generated/WitnessAuthorityGenerated",
                    "--artifact-limit", str(limits.compiler_artifact_file_bytes),
                    "--handoff-limit", str(limits.handoff_total_bytes),
                ), mounts=compile_manifest, limits=limits, uid=65534, gid=65534,
            )
            untrusted_command = self._command(compile_invocation)
            minimal_env = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TZ": "UTC"}
            compiled = run_bounded_process(
                untrusted_command, timeout_seconds=limits.timeout_seconds, env=minimal_env,
                stdout_limit=limits.stdout_bytes, stderr_limit=limits.stderr_bytes,
                combined_limit=limits.combined_output_bytes,
            )
            if compiled.timed_out or compiled.output_limit_exceeded or compiled.returncode != 0:
                return SandboxExecution(
                    compiled.returncode, None, compiled.stdout, compiled.stderr, compiled.timed_out,
                    untrusted_command=untrusted_command,
                    effective_sandbox_invocation_sha256=compile_invocation.sha256,
                    requested_controls=compile_invocation.requested_controls,
                    applied_controls=compile_invocation.applied_controls,
                    output_limit_exceeded=compiled.output_limit_exceeded,
                    stdout_sha256=compiled.stdout_sha256, stderr_sha256=compiled.stderr_sha256,
                    emitted_controls=compile_invocation.emitted_controls,
                    normalized_executed_argv=untrusted_command,
                    normalized_executed_argv_sha256=sha256_bytes(canonical_bytes(list(untrusted_command))),
                    domain_file_size_limit=compile_invocation.domain_file_size_limit,
                )
            verifier_manifest = (
                {"source": f"snapshot:{request['immutable_snapshot_tree_sha256']}", "host_path": str(snapshot_root), "destination": "/input/source", "mode": "ro", "domain": "trusted_inspection", "purpose": "sealed_source", "lifecycle": "request"},
                {"source": f"generated:{request['generated_binding_module_sha256']}", "host_path": str(generated_root), "destination": "/input/generated", "mode": "ro", "domain": "trusted_inspection", "purpose": "generated_type_binding", "lifecycle": "request"},
                {"source": "ephemeral:compile-handoff", "host_path": str(handoff), "destination": "/handoff", "mode": "ro", "domain": "trusted_inspection", "purpose": "compiled_artifact_input", "lifecycle": "request"},
                {"source": f"control:{request['request_id']}", "host_path": str(control), "destination": "/input/control", "mode": "ro", "domain": "trusted_inspection", "purpose": "trusted_verifier_request", "lifecycle": "request"},
                {"source": "ephemeral:trusted-inspection", "host_path": str(inspection_directory), "destination": "/trusted-inspection", "mode": "rw", "domain": "trusted_inspection", "purpose": "private_inspection_output", "lifecycle": "request"},
            )
            verifier_invocation = self._invocation(domain="trusted_inspection", profile=profile, entrypoint="/opt/witness-authority/bin/verify-lean", arguments=("--request", "/input/control/request.json", "--result-dir", "/trusted-inspection"), mounts=verifier_manifest, limits=limits, uid=self.authority_uid, gid=self.authority_gid)
            profile_path = control / "effective-profile.json"
            profile_path.write_bytes(canonical_bytes(profile.as_verifier_record()))
            profile_path.chmod(0o444)
            invocation_path = control / "effective-sandbox-invocation.json"
            invocation_path.write_bytes(canonical_bytes(verifier_invocation.as_dict()))
            invocation_path.chmod(0o444)
            control.chmod(0o555)
            trusted_command = self._command(verifier_invocation)
            verified = run_bounded_process(
                trusted_command, timeout_seconds=limits.timeout_seconds, env=minimal_env,
                stdout_limit=limits.stdout_bytes, stderr_limit=limits.stderr_bytes,
                combined_limit=limits.combined_output_bytes,
            )
            if verified.timed_out or verified.output_limit_exceeded:
                return SandboxExecution(
                    verified.returncode, None, compiled.stdout + verified.stdout, compiled.stderr + verified.stderr,
                    verified.timed_out, untrusted_command, trusted_command, verifier_invocation.sha256,
                    requested_controls=verifier_invocation.requested_controls,
                    applied_controls=verifier_invocation.applied_controls,
                    output_limit_exceeded=verified.output_limit_exceeded,
                    stdout_sha256=verified.stdout_sha256, stderr_sha256=verified.stderr_sha256,
                    emitted_controls=verifier_invocation.emitted_controls,
                    normalized_executed_argv=trusted_command,
                    normalized_executed_argv_sha256=sha256_bytes(canonical_bytes(list(trusted_command))),
                    domain_file_size_limit=verifier_invocation.domain_file_size_limit,
                )
            inspection_path = inspection_directory / "verifier-inspection.json"
            inspection = read_private_result(
                inspection_path, expected_uid=self.authority_uid,
                maximum=limits.inspection_output_bytes,
            ) if inspection_path.exists() else None
            structured = None
            if inspection is not None:
                topology_root = sha256_bytes(canonical_bytes({
                    "compile_argv": list(untrusted_command),
                    "inspection_argv": list(trusted_command),
                    "compile_mounts": list(compile_manifest),
                    "inspection_mounts": list(verifier_manifest),
                }))
                derived_evidence = [
                    {"control": "result_channel_isolated", "status": "derived_pass", "source": "sealed_execution_topology", "observation_sha256": topology_root},
                    {"control": "trusted_inspection_only", "status": "derived_pass", "source": "sealed_execution_topology", "observation_sha256": topology_root},
                ]
                augmented = dict(inspection)
                augmented["derived_controls"] = ["result_channel_isolated", "trusted_inspection_only"]
                augmented["control_evidence"] = sorted(
                    [*inspection.get("control_evidence", []), *derived_evidence],
                    key=lambda item: (item["control"], item["status"], item["source"]),
                )
                candidate = sign_record(augmented, self.verifier_result_signing_key)
                self.schema_validator.validate("verifier_result", candidate)
                final_directory = result_parent / "private-result"
                publisher = AtomicResultPublisher(
                    final_directory, expected_uid=self.authority_uid,
                    maximum=limits.final_result_bytes,
                )
                result_path = publisher.publish_unsigned(candidate)
                structured = read_private_result(
                    result_path, expected_uid=self.authority_uid,
                    maximum=limits.final_result_bytes,
                )
            emitted_controls = tuple(sorted(structured.get("emitted_controls", []))) if structured else ()
            accepted_controls = tuple(sorted(structured.get("accepted_controls", []))) if structured else ()
            applied_controls = tuple(sorted(structured.get("applied_controls", []))) if structured else ()
            measured_controls = tuple(sorted(structured.get("measured_controls", []))) if structured else ()
            derived_controls = tuple(sorted(structured.get("derived_controls", []))) if structured else ()
            security_properties = tuple(sorted(set(measured_controls) | set(derived_controls)))
            return SandboxExecution(
                returncode=verified.returncode, structured_result=structured,
                stdout=compiled.stdout + verified.stdout, stderr=compiled.stderr + verified.stderr,
                timed_out=False, untrusted_command=untrusted_command, trusted_command=trusted_command,
                effective_sandbox_invocation_sha256=verifier_invocation.sha256,
                security_properties=security_properties,
                requested_controls=verifier_invocation.requested_controls,
                applied_controls=applied_controls,
                verified_controls=measured_controls, output_limit_exceeded=False,
                stdout_sha256=sha256_bytes((compiled.stdout + verified.stdout).encode("utf-8")),
                stderr_sha256=sha256_bytes((compiled.stderr + verified.stderr).encode("utf-8")),
                emitted_controls=emitted_controls, accepted_controls=accepted_controls,
                measured_controls=measured_controls, derived_controls=derived_controls,
                control_evidence=tuple(structured.get("control_evidence", [])) if structured else (),
                normalized_executed_argv=trusted_command,
                normalized_executed_argv_sha256=sha256_bytes(canonical_bytes(list(trusted_command))),
                domain_file_size_limit=verifier_invocation.domain_file_size_limit,
            )


class ProofAuthorityService:
    def __init__(
        self, *, governed_registry: dict[str, Any], governance_public_key: Ed25519PublicKey,
        verifier_principal_id: str, key_id: str, signing_key: Ed25519PrivateKey,
        runner: SandboxRunner, clock: Callable[[], datetime] | None = None,
        timestamp_source: str = "authority_service_clock", authority_snapshot_id: str,
        authority_ledger_high_water_sequence: int,
        schema_validator: CanonicalSchemaValidator | None = None,
        trust_root_attestation_registry_sha256: str | None = None,
    ):
        self.profiles = verify_governed_registry(governed_registry, governance_public_key)
        self.registry_sha256 = sha256_bytes(canonical_bytes(governed_registry))
        self.verifier_principal_id = verifier_principal_id; self.key_id = key_id; self.signing_key = signing_key
        self.runner = runner; self.clock = clock or (lambda: datetime.now(timezone.utc)); self.timestamp_source = timestamp_source
        if not authority_snapshot_id or authority_ledger_high_water_sequence < 0:
            raise ValueError("authority service requires a governed ledger-bound authority snapshot")
        self.authority_snapshot_id = authority_snapshot_id
        self.authority_ledger_high_water_sequence = authority_ledger_high_water_sequence
        self.schema_validator = schema_validator or CanonicalSchemaValidator(Path(__file__).resolve().parents[2] / "schemas")
        self.trust_root_attestation_registry_sha256 = trust_root_attestation_registry_sha256 or sha256_bytes(canonical_bytes({"status": "portable_unattested"}))

    def verify(
        self, *, compiler_profile_id: str, claim_id: str, canonical_claim: dict[str, Any],
        theorem_statement: str, theorem_name: str, proof_artifact: Path, source_root: Path,
        policy_decision_id: str, policy_decision_sha256: str,
        timeout_seconds: int = 600,
        effective_resource_limits: EffectiveResourceLimits | None = None,
    ) -> dict[str, Any]:
        if not isinstance(claim_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", claim_id):
            raise ValueError("claim_id must be a canonical string identifier")
        if not isinstance(canonical_claim, dict):
            raise ValueError("canonical_claim must be a JSON object")
        limits = effective_resource_limits or EffectiveResourceLimits(
            timeout_seconds=min(timeout_seconds, 600), source_total_bytes=MAX_SOURCE_TOTAL_BYTES,
            compiler_artifact_file_bytes=MAX_COMPILER_ARTIFACT_BYTES,
            handoff_total_bytes=MAX_HANDOFF_TOTAL_BYTES,
            inspection_output_bytes=MAX_INSPECTION_BYTES, final_result_bytes=MAX_RESULT_BYTES,
            stdout_bytes=MAX_STDOUT_BYTES, stderr_bytes=MAX_STDERR_BYTES,
            combined_output_bytes=MAX_COMBINED_OUTPUT_BYTES,
        )
        profile = self.profiles.get(compiler_profile_id)
        if profile is None:
            raise ValueError("compiler profile is not present in the governed registry")
        now = self.clock().astimezone(timezone.utc)
        if now < _parse_time(profile.valid_from) or (profile.valid_until and now >= _parse_time(profile.valid_until)):
            raise AuthorityFailure("compiler_profile_inactive", "compiler profile is outside its governed validity interval")
        if source_root.is_symlink() or proof_artifact.is_symlink():
            raise ValueError("source root and proof artifact must not be symbolic links")
        source_root = source_root.resolve(); proof_artifact = proof_artifact.resolve()
        if not source_root.is_dir() or not proof_artifact.is_file():
            raise ValueError("source root and proof artifact must exist")
        try:
            submitted_relative = _safe_relative_path(proof_artifact.relative_to(source_root).as_posix(), expected_suffix=".lean")
        except ValueError as error:
            raise ValueError("proof artifact is outside source root or has an unsafe path") from error
        _validate_statement(theorem_statement)
        if not LEAN_IDENTIFIER.fullmatch(theorem_name):
            raise ValueError("invalid theorem identifier")
        if not isinstance(policy_decision_id, str) or not policy_decision_id or not SHA256_HEX.fullmatch(policy_decision_sha256):
            raise AuthorityFailure("policy_decision_invalid", "resolved policy identity and canonical hash are required")
        claim_hash = sha256_bytes(canonical_bytes(canonical_claim)); theorem_hash = sha256_bytes(theorem_statement.encode("utf-8"))

        with tempfile.TemporaryDirectory(prefix="wc-snapshot-parent-") as snapshot_parent_name, tempfile.TemporaryDirectory(prefix="wc-generated-parent-") as generated_parent_name:
            snapshot_limits = SnapshotLimits(maximum_total_bytes=min(limits.source_total_bytes, MAX_SOURCE_TOTAL_BYTES))
            snapshot = create_immutable_snapshot(
                source_root, Path(snapshot_parent_name) / "snapshot", limits=snapshot_limits,
            )
            snapshot_artifact = snapshot.root.joinpath(*submitted_relative.parts)
            if not snapshot_artifact.is_file():
                raise AuthorityFailure("artifact_digest_mismatch", "proof artifact is absent from immutable snapshot")
            proof_module = _proof_module(submitted_relative)
            artifact_hash = sha256_file(snapshot_artifact)
            required_metadata = {name: snapshot.root / name for name in SOURCE_METADATA}
            if any(not path.is_file() for path in required_metadata.values()):
                raise AuthorityFailure("snapshot_creation_failed", "lean-toolchain, lakefile.lean, and lake-manifest.json are required")
            if required_metadata["lean-toolchain"].read_text(encoding="utf-8").strip() != profile.toolchain:
                raise ValueError("snapshot toolchain does not match governed profile")
            metadata_hashes = {name: sha256_file(path) for name, path in required_metadata.items()}

            descriptor_seed = sha256_bytes(canonical_bytes({
                "snapshot": snapshot.tree_sha256, "artifact": artifact_hash, "claim": claim_hash,
                "theorem": theorem_hash, "profile": compiler_profile_id,
                "policy_decision_id": policy_decision_id, "policy_decision_sha256": policy_decision_sha256,
            }))
            generated_relative = f"WitnessAuthorityGenerated/Check_{descriptor_seed[:32]}.lean"
            generated_root = Path(generated_parent_name) / "generated"
            generated_path = generated_root / generated_relative
            generated_path.parent.mkdir(parents=True, mode=0o700)
            generated_path.write_text(generated_witness_module(proof_module=proof_module, theorem_statement=theorem_statement, theorem_name=theorem_name), encoding="utf-8")
            generated_hash = sha256_file(generated_path)
            generated_path.chmod(0o444)
            for directory in sorted((item for item in generated_root.rglob("*") if item.is_dir()), key=lambda item: len(item.parts), reverse=True):
                directory.chmod(0o555)
            generated_root.chmod(0o555)

            sandbox_template = {
                "schema_version": "sandbox_template/v1", "profile": compiler_profile_id,
                "network": "none", "read_only_rootfs": True,
                "untrusted_final_result_mount": False, "trusted_final_result_mount": False,
                "trusted_inspection_mount": True, "runtime_sha256": profile.oci_runtime_sha256,
            }
            request = {
                "schema_version": "wc_lean_verifier_request/v4", "request_id": f"request:{descriptor_seed}",
                "compiler_profile_id": compiler_profile_id, "claim_content_sha256": claim_hash,
                "policy_decision_id": policy_decision_id, "policy_decision_sha256": policy_decision_sha256,
                "theorem_statement_sha256": theorem_hash, "proof_artifact_relative_path": submitted_relative.as_posix(),
                "proof_artifact_sha256": artifact_hash, "proof_module": proof_module, "theorem_name": theorem_name,
                "immutable_snapshot_id": snapshot.snapshot_id, "immutable_snapshot_tree_sha256": snapshot.tree_sha256,
                "lakefile_sha256": metadata_hashes["lakefile.lean"], "lake_manifest_sha256": metadata_hashes["lake-manifest.json"],
                "lean_toolchain_sha256": metadata_hashes["lean-toolchain"],
                "generated_binding_module_sha256": generated_hash, "generated_binding_module_path": generated_relative,
                "generated_binding_declaration": "WitnessAuthorityGenerated.BoundClaim",
                "authorized_axioms": sorted(profile.authorized_axioms), "normalization_policy": "lean_isDefEq_reducibility_regular/v1",
                "sandbox_policy_sha256": profile.sandbox_policy_sha256, "sandbox_template_sha256": sha256_bytes(canonical_bytes(sandbox_template)),
                "effective_resource_limits": limits.as_dict(), "effective_resource_limits_sha256": limits.sha256,
            }
            self.schema_validator.validate("verifier_request", request)
            request_hash = sha256_bytes(canonical_bytes(request))
            verify_sealed_snapshot(snapshot.root, snapshot.tree_sha256)
            execution = self.runner.run(profile=profile, snapshot_root=snapshot.root, generated_module=generated_path, request=request, timeout_seconds=limits.timeout_seconds)
            verify_sealed_snapshot(snapshot.root, snapshot.tree_sha256)

        structured = execution.structured_result
        structured_valid, result_error = self._structured_result_valid(structured, request, request_hash, profile, execution)
        axioms = sorted(set(structured.get("axiom_set", []))) if structured_valid and structured else []
        forbidden_axioms = sorted(set(structured.get("forbidden_axiom_set", []))) if structured_valid and structured else []
        contains_sorry = bool(structured_valid and structured and structured.get("sorry_ax_present"))
        unsafe_dependency = bool(structured_valid and structured and structured.get("unsafe_dependency_present"))
        unauthorized = sorted((set(axioms) - set(profile.authorized_axioms)) | set(forbidden_axioms))
        required_verified_controls = {
            "working_directory", "network_none", "read_only_rootfs", "capabilities_dropped",
            "no_new_privileges", "seccomp", "lsm_profile", "private_user_namespace",
            "non_root_user", "pid_limit", "memory_limit", "cpu_limit", "rlimit_fsize",
            "open_file_limit", "mount_manifest",
        }
        emitted = set(execution.emitted_controls)
        accepted = set(execution.accepted_controls)
        applied = set(execution.applied_controls)
        measured = set(execution.measured_controls)
        exact_controls = (
            set(execution.requested_controls) == emitted == accepted
            and applied.issubset(measured)
            and required_verified_controls.issubset(measured)
        )
        passed = bool(
            execution.returncode == 0 and not execution.timed_out and not execution.output_limit_exceeded and structured_valid and structured
            and structured.get("status") == "passed" and structured.get("declaration_found") is True
            and structured.get("declaration_type_matches") is True
            and structured.get("build_from_source") is True and structured.get("prebuilt_artifacts_used") is False
            and structured.get("warnings_as_errors") is True and structured.get("opaque_dependency_policy_result") == "passed"
            and not contains_sorry and not unsafe_dependency and not unauthorized
            and exact_controls and "result_channel_isolated" in execution.security_properties
        )
        if passed:
            result = "passed"; theorem_status = "proved"; failure_code = None
        else:
            if execution.timed_out: failure_code = "verification_timeout"
            elif execution.output_limit_exceeded: failure_code = "output_limit_exceeded"
            elif result_error: failure_code = result_error
            elif contains_sorry: failure_code = "sorry_axiom_present"
            elif unsafe_dependency: failure_code = "unsafe_dependency_present"
            elif unauthorized: failure_code = "forbidden_axiom_present"
            elif structured and structured.get("declaration_found") is False: failure_code = "theorem_declaration_missing"
            elif structured and structured.get("declaration_type_matches") is False: failure_code = "theorem_type_mismatch"
            else: failure_code = "verifier_result_invalid"
            result = "toolchain_unavailable" if execution.returncode is None and not execution.timed_out else "failed"
            theorem_status = "sorry_stub" if contains_sorry else "axiom_dependent" if unauthorized else "failed"
        structured_payload_hash = structured.get("signed_payload_sha256", sha256_bytes(canonical_bytes({}))) if structured else sha256_bytes(canonical_bytes({}))
        diagnostic_hash = sha256_bytes(canonical_bytes({"returncode": execution.returncode, "timed_out": execution.timed_out, "stdout": execution.stdout, "stderr": execution.stderr}))
        semantic_result = {
            key: structured.get(key) if structured else None
            for key in (
                "status", "compiler_profile_id", "claim_content_sha256", "theorem_statement_sha256",
                "policy_decision_id", "policy_decision_sha256",
                "proof_artifact_sha256", "immutable_snapshot_id", "immutable_snapshot_tree_sha256",
                "generated_binding_module_sha256", "theorem_declaration", "declaration_found",
                "declaration_type_matches", "expected_type_expression_hash", "actual_type_expression_hash",
                "expected_type_expression_fingerprint", "actual_type_expression_fingerprint",
                "normalization_policy", "direct_dependencies", "dependency_closure", "transitive_dependencies_root", "axiom_set",
                "axiom_set_sha256", "forbidden_axiom_set", "sorry_ax_present", "unsafe_dependency_present",
                "opaque_dependency_policy_result", "build_from_source", "prebuilt_artifacts_used", "warnings_as_errors",
                "exit_status", "timeout_status", "effective_sandbox_invocation_sha256",
                "normalized_executed_argv_sha256", "handoff_manifest_sha256",
                "effective_resource_limits", "effective_resource_limits_sha256",
                "domain_file_size_limit", "requested_controls", "emitted_controls", "accepted_controls", "applied_controls", "measured_controls", "derived_controls",
                "control_evidence", "oci_runtime_version_output_sha256",
            )
        }
        semantic = {
            "claim": claim_hash, "theorem": theorem_hash, "artifact": artifact_hash, "snapshot": snapshot.tree_sha256,
            "generated": generated_hash, "request": request_hash, "profile": compiler_profile_id,
            "policy_decision_id": policy_decision_id, "policy_decision_sha256": policy_decision_sha256,
            "registry": self.registry_sha256,
            "semantic_result_sha256": sha256_bytes(canonical_bytes(semantic_result)),
        }
        semantic_id = "lean-semantic:" + sha256_bytes(canonical_bytes(semantic))
        unsigned = {
            "schema_version": "lean_compiler_witness/v6", "lean_compiler_witness_id": "lean:" + sha256_bytes(canonical_bytes(semantic))[:32],
            "semantic_witness_content_id": semantic_id, "claim_id": claim_id, "claim_content_sha256": claim_hash,
            "theorem_statement_sha256": theorem_hash, "submitted_source_locator": "caller-bundle-redacted",
            "policy_decision_id": policy_decision_id, "policy_decision_sha256": policy_decision_sha256,
            "immutable_snapshot_id": snapshot.snapshot_id, "immutable_snapshot_tree_sha256": snapshot.tree_sha256,
            "proof_artifact_relative_path": submitted_relative.as_posix(), "proof_artifact_sha256": artifact_hash,
            "lakefile_sha256": metadata_hashes["lakefile.lean"], "lake_manifest_sha256": metadata_hashes["lake-manifest.json"],
            "lean_toolchain_sha256": metadata_hashes["lean-toolchain"], "generated_binding_module_sha256": generated_hash,
            "generated_binding_request_sha256": request_hash, "generated_binding_module_path": generated_relative,
            "compiler_profile_id": compiler_profile_id, "compiler_registry_sha256": self.registry_sha256,
            "verifier_executable_sha256": profile.verifier_executable_sha256, "lean_executable_sha256": profile.lean_executable_sha256,
            "lake_executable_sha256": profile.lake_executable_sha256, "lean_stdlib_tree_sha256": profile.lean_stdlib_tree_sha256,
            "dependency_closure_sha256": profile.dependency_closure_sha256, "oci_image_digest": profile.oci_image_digest,
            "oci_runtime_sha256": profile.oci_runtime_sha256, "oci_runtime_version": profile.oci_runtime_version,
            "oci_runtime_version_output_sha256": structured.get("oci_runtime_version_output_sha256", sha256_bytes(b"")) if structured else sha256_bytes(b""),
            "sandbox_policy_sha256": profile.sandbox_policy_sha256,
            "sandbox_template_sha256": request["sandbox_template_sha256"],
            "effective_sandbox_invocation_sha256": execution.effective_sandbox_invocation_sha256,
            "normalized_executed_argv_sha256": structured.get("normalized_executed_argv_sha256", sha256_bytes(canonical_bytes([]))) if structured else sha256_bytes(canonical_bytes([])),
            "handoff_manifest_sha256": structured.get("handoff_manifest_sha256", sha256_bytes(canonical_bytes({}))) if structured else sha256_bytes(canonical_bytes({})),
            "effective_resource_limits": limits.as_dict(), "effective_resource_limits_sha256": limits.sha256,
            "domain_file_size_limit": execution.domain_file_size_limit,
            "trust_root_attestation_registry_sha256": self.trust_root_attestation_registry_sha256,
            "verifier_result_payload_sha256": structured_payload_hash,
            "verifier_result_signer_key_id": profile.verifier_result_signer_key_id,
            "verifier_result_signed_payload_canonical_json": signed_payload_canonical_json(structured) if structured else "{}",
            "verifier_result_signature": structured.get("signature", "") if structured else "",
            "expected_type_expression_hash": structured.get("expected_type_expression_hash", sha256_bytes(b"")) if structured else sha256_bytes(b""),
            "actual_type_expression_hash": structured.get("actual_type_expression_hash", sha256_bytes(b"")) if structured else sha256_bytes(b""),
            "expected_type_expression_fingerprint": structured.get("expected_type_expression_fingerprint", "") if structured else "",
            "actual_type_expression_fingerprint": structured.get("actual_type_expression_fingerprint", "") if structured else "",
            "normalization_policy": "lean_isDefEq_reducibility_regular/v1", "axiom_set": axioms,
            "axiom_set_sha256": sha256_bytes(canonical_bytes(axioms)), "direct_dependencies": structured.get("direct_dependencies", []) if structured_valid and structured else [],
            "dependency_closure": structured.get("dependency_closure", []) if structured_valid and structured else [],
            "transitive_dependencies_root": structured.get("transitive_dependencies_root", sha256_bytes(b"")) if structured_valid and structured else sha256_bytes(b""),
            "forbidden_axiom_set": forbidden_axioms, "sorry_ax_present": contains_sorry, "unsafe_dependency_present": unsafe_dependency,
            "opaque_dependency_policy_result": structured.get("opaque_dependency_policy_result", "not_evaluated") if structured_valid and structured else "not_evaluated",
            "build_output_sha256": diagnostic_hash, "stdout_sha256": execution.stdout_sha256 or sha256_bytes(execution.stdout.encode("utf-8")),
            "stderr_sha256": execution.stderr_sha256 or sha256_bytes(execution.stderr.encode("utf-8")),
            "output_limit_exceeded": execution.output_limit_exceeded, "result": result, "failure_code": failure_code,
            "theorem_name": theorem_name, "theorem_status": theorem_status,
            "statement_binding_confirmed": bool(passed), "snapshot_verified_immutable": True,
            "result_channel_isolated": "result_channel_isolated" in execution.security_properties,
            "requested_controls": sorted(execution.requested_controls),
            "emitted_controls": sorted(execution.emitted_controls),
            "accepted_controls": sorted(execution.accepted_controls),
            "applied_controls": sorted(execution.applied_controls),
            "measured_controls": sorted(execution.measured_controls),
            "derived_controls": sorted(execution.derived_controls),
            "control_evidence": list(execution.control_evidence),
            "authority_snapshot_id": self.authority_snapshot_id,
            "authority_ledger_high_water_sequence": self.authority_ledger_high_water_sequence,
            "verifier_principal_id": self.verifier_principal_id, "key_id": self.key_id,
            "signature_algorithm": "Ed25519", "trusted_timestamp_source": self.timestamp_source, "created_at": now.isoformat(),
        }
        signed_witness = sign_record(unsigned, self.signing_key)
        self.schema_validator.validate("compiler_witness", signed_witness)
        return signed_witness

    def _structured_result_valid(self, result: dict[str, Any] | None, request: dict[str, Any], request_hash: str, profile: CompilerProfile, execution: SandboxExecution) -> tuple[bool, str | None]:
        if not isinstance(result, dict) or result.get("schema_version") != "wc_lean_verifier_result/v5":
            return False, "verifier_result_invalid"
        if result.get("verifier_result_signer_key_id") != profile.verifier_result_signer_key_id or not verify_record(result, profile.verifier_result_public_key):
            return False, "verifier_result_signature_invalid"
        try:
            self.schema_validator.validate("verifier_result", result)
        except (AuthorityFailure, ValueError):
            return False, "verifier_result_invalid"
        exact = {
            "request_id": request["request_id"], "request_sha256": request_hash,
            "compiler_profile_id": profile.compiler_profile_id, "claim_content_sha256": request["claim_content_sha256"],
            "policy_decision_id": request["policy_decision_id"], "policy_decision_sha256": request["policy_decision_sha256"],
            "theorem_statement_sha256": request["theorem_statement_sha256"], "proof_artifact_sha256": request["proof_artifact_sha256"],
            "immutable_snapshot_id": request["immutable_snapshot_id"], "immutable_snapshot_tree_sha256": request["immutable_snapshot_tree_sha256"],
            "generated_binding_module_sha256": request["generated_binding_module_sha256"],
            "lake_executable_sha256": profile.lake_executable_sha256, "lean_executable_sha256": profile.lean_executable_sha256,
            "lean_stdlib_tree_sha256": profile.lean_stdlib_tree_sha256, "dependency_closure_sha256": profile.dependency_closure_sha256,
            "oci_image_digest": profile.oci_image_digest, "oci_runtime_sha256": profile.oci_runtime_sha256,
            "oci_runtime_version": profile.oci_runtime_version, "verifier_executable_sha256": profile.verifier_executable_sha256,
            "sandbox_policy_sha256": profile.sandbox_policy_sha256,
            "effective_sandbox_invocation_sha256": execution.effective_sandbox_invocation_sha256,
            "normalized_executed_argv_sha256": execution.normalized_executed_argv_sha256,
            "effective_resource_limits_sha256": request["effective_resource_limits_sha256"],
            "domain_file_size_limit": execution.domain_file_size_limit,
        }
        if any(result.get(key) != value for key, value in exact.items()):
            return False, "verifier_result_invalid"
        for field in ("expected_type_expression_hash", "actual_type_expression_hash", "transitive_dependencies_root", "axiom_set_sha256", "normalized_executed_argv_sha256", "handoff_manifest_sha256"):
            if not SHA256_HEX.fullmatch(str(result.get(field, ""))):
                return False, "verifier_result_invalid"
        for field in ("direct_dependencies", "dependency_closure", "axiom_set", "forbidden_axiom_set", "requested_controls", "emitted_controls", "accepted_controls", "applied_controls", "measured_controls", "derived_controls"):
            values = result.get(field)
            if not isinstance(values, list) or values != sorted(set(values)) or not all(isinstance(item, str) and item for item in values):
                return False, "verifier_result_invalid"
        if result["axiom_set_sha256"] != sha256_bytes(canonical_bytes(result["axiom_set"])):
            return False, "verifier_result_invalid"
        if result["requested_controls"] != sorted(execution.requested_controls) or result["emitted_controls"] != sorted(execution.emitted_controls):
            return False, "verifier_result_invalid"
        if result["accepted_controls"] != sorted(execution.accepted_controls):
            return False, "verifier_result_invalid"
        if result["applied_controls"] != sorted(execution.applied_controls):
            return False, "verifier_result_invalid"
        if result["measured_controls"] != sorted(execution.measured_controls):
            return False, "verifier_result_invalid"
        if result.get("effective_resource_limits") != request["effective_resource_limits"]:
            return False, "verifier_result_invalid"
        if result.get("opaque_dependency_policy_result") not in {"passed", "failed", "not_evaluated"}:
            return False, "verifier_result_invalid"
        return True, None


def load_production_authority_service(config_root: Path = Path("/etc/witness-authority")) -> ProofAuthorityService:
    """Load every trust-root file through descriptor-relative, no-follow I/O."""
    root = config_root
    expected_uid = os.getuid()
    validate_trusted_root_ancestry(root, expected_uid=expected_uid)
    config = json.loads(secure_read_bytes(root, "service-config.json", expected_uid=expected_uid).decode("utf-8"))
    allowed = {
        "compiler_registry_file", "governance_public_key_file", "verifier_private_key_file", "verifier_result_private_key_file", "oci_runtime_file",
        "oci_runtime_sha256", "oci_runtime_version", "verifier_principal_id", "key_id", "authority_snapshot_id",
        "authority_ledger_high_water_sequence", "artifact_store_root", "policy_registry_file",
        "seccomp_profile_file", "seccomp_profile_sha256", "authority_uid", "authority_gid",
        "platform_capability_file", "trusted_artifact_registry_file", "schema_root",
        "idempotency_database", "idempotency_retention_seconds", "idempotency_lease_seconds",
        "idempotency_maximum_completed_rows",
    }
    if set(config) != allowed:
        raise RuntimeError("authority service configuration fields are not canonical")
    registry = json.loads(secure_read_bytes(root, config["compiler_registry_file"], expected_uid=expected_uid).decode("utf-8"))
    governance_key = _public_key_from_bytes(secure_read_bytes(root, config["governance_public_key_file"], expected_uid=expected_uid))
    signing_key = _private_key_from_bytes(secure_read_bytes(root, config["verifier_private_key_file"], expected_uid=expected_uid))
    result_signing_key = _private_key_from_bytes(secure_read_bytes(root, config["verifier_result_private_key_file"], expected_uid=expected_uid))
    schema_relative = _safe_relative_path(config["schema_root"])
    schema_root = root.joinpath(*schema_relative.parts)
    validate_trusted_root_ancestry(schema_root, expected_uid=expected_uid)
    schema_validator = CanonicalSchemaValidator(schema_root)
    schema_validator.validate("compiler_registry", registry)
    trusted_artifact_registry = json.loads(secure_read_bytes(root, config["trusted_artifact_registry_file"], expected_uid=expected_uid).decode("utf-8"))
    schema_validator.validate("trusted_artifact_registry", trusted_artifact_registry)
    trust_registry_sha256 = verify_trusted_artifact_registry(
        trusted_artifact_registry, governance_key, trusted_root=root, expected_uid=expected_uid,
    )
    platform = json.loads(secure_read_bytes(root, config["platform_capability_file"], expected_uid=expected_uid).decode("utf-8"))
    schema_validator.validate("platform_capability", platform)
    if platform.get("schema_version") != "platform_capability_probe/v1" or platform.get("probe_status") != "measured":
        raise RuntimeError("platform capability evidence is absent or configured-only")
    supported_controls = frozenset(platform.get("supported_controls", []))
    lsm = platform.get("lsm") if isinstance(platform.get("lsm"), dict) else {}
    runtime_relative = _safe_relative_path(config["oci_runtime_file"])
    runtime_path = root.joinpath(*runtime_relative.parts)
    secure_read_bytes(root, config["oci_runtime_file"], expected_uid=expected_uid)
    secure_read_bytes(root, config["seccomp_profile_file"], expected_uid=expected_uid)
    runner = OciSandboxRunner(
        runtime_path, config["oci_runtime_sha256"], config["oci_runtime_version"],
        verifier_result_signing_key=result_signing_key,
        authority_uid=int(config["authority_uid"]), authority_gid=int(config["authority_gid"]),
        seccomp_profile_path=root.joinpath(*_safe_relative_path(config["seccomp_profile_file"]).parts),
        expected_seccomp_profile_sha256=config["seccomp_profile_sha256"],
        apparmor_profile=lsm.get("profile", "") if lsm.get("kind") == "apparmor" else "",
        selinux_label=lsm.get("profile", "") if lsm.get("kind") == "selinux" else "",
        supported_controls=supported_controls,
        schema_validator=schema_validator,
    )
    return ProofAuthorityService(
        governed_registry=registry, governance_public_key=governance_key,
        verifier_principal_id=config["verifier_principal_id"], key_id=config["key_id"],
        signing_key=signing_key, runner=runner, authority_snapshot_id=config["authority_snapshot_id"],
        authority_ledger_high_water_sequence=int(config["authority_ledger_high_water_sequence"]),
        schema_validator=schema_validator,
        trust_root_attestation_registry_sha256=trust_registry_sha256,
    )


__all__ = [
    "AtomicResultPublisher", "AuthorityFailure", "BoundedProcessResult", "CanonicalSchemaValidator", "CompilerProfile",
    "EffectiveResourceLimits", "EffectiveSandboxInvocation",
    "ImmutableSnapshot", "OciSandboxRunner", "ProofAuthorityService", "ProofPolicyResolver",
    "ResolvedPolicyDecision", "SandboxExecution", "SnapshotLimits",
    "authority_event_set_root", "canonical_bytes", "canonical_json_loads", "canonical_text",
    "content_tree_sha256", "create_immutable_snapshot", "generated_witness_module",
    "load_production_authority_service", "public_key_fingerprint", "public_key_raw_b64url",
    "read_private_result", "register_sqlite_crypto_functions", "secure_read_bytes", "sha256_bytes",
    "run_bounded_process", "sign_record", "signed_payload_canonical_json", "verify_governed_registry", "verify_record",
    "validate_trusted_root_ancestry", "verify_sealed_snapshot", "verify_trusted_artifact_registry",
]
