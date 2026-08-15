from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .crypto_profile import PROFILE_NAME, duoid, load_registry, registry_identity

INTERFACE_SCHEMA = "duotronic-runtime-interface/v1"
MANIFEST_SCHEMA = "duotronic-corpus-manifest/1.0"
BINDING_SCHEMA = "duotronic-paired-runtime-binding/v1"


class CompatibilityError(ValueError):
    pass


@dataclass(frozen=True)
class NegotiationResult:
    compatible: bool
    mode: str
    reasons: tuple[str, ...]
    preserved_unknown_fields: dict[str, Any]
    required_capabilities: tuple[str, ...]
    provided_capabilities: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "mode": self.mode,
            "reasons": list(self.reasons),
            "preserved_unknown_fields": self.preserved_unknown_fields,
            "required_capabilities": list(self.required_capabilities),
            "provided_capabilities": list(self.provided_capabilities),
        }


def load_interface(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != INTERFACE_SCHEMA:
        raise CompatibilityError("unsupported runtime interface schema")
    return value


def adapt_manifest(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CompatibilityError("corpus manifest must be an object")
    original = json.loads(json.dumps(value))
    schema = str(value.get("schema") or value.get("manifest_schema") or "")
    known = {
        "schema", "manifest_schema", "contract_version", "active_version", "corpus_root_id",
        "digest", "cryptographic_profile", "required_capabilities", "critical_extensions",
        "extensions", "api_version", "authority",
    }
    unknown = {key: child for key, child in original.items() if key not in known}
    if schema in {"", "legacy", "duotronic-corpus-manifest/v0"}:
        adapted = {
            "schema": MANIFEST_SCHEMA,
            "contract_version": str(
                value.get("contract_version") or value.get("active_version") or "legacy-unversioned"
            ),
            "corpus_root_id": str(
                value.get("corpus_root_id") or value.get("digest") or "unresolved"
            ),
            "cryptographic_profile": str(
                value.get("cryptographic_profile") or "legacy-read-only"
            ),
            "required_capabilities": list(value.get("required_capabilities") or []),
            "critical_extensions": list(value.get("critical_extensions") or []),
            "extensions": dict(value.get("extensions") or {}),
            "preserved_unknown_fields": unknown,
            "migration": {
                "adapter": "legacy-unversioned-to-v1-read-only",
                "source_schema": schema or "unversioned",
                "read_only": True,
            },
        }
        return adapted
    if schema in {MANIFEST_SCHEMA, "duotronic-corpus-manifest/v1"}:
        adapted = dict(original)
        adapted["schema"] = MANIFEST_SCHEMA
        adapted["preserved_unknown_fields"] = unknown
        adapted["migration"] = {
            "adapter": "v1-forward-preserving",
            "source_schema": schema,
            "read_only": bool(value.get("critical_extensions")),
        }
        return adapted
    raise CompatibilityError("unsupported corpus manifest schema: " + schema)


def negotiate(
    manifest: dict[str, Any],
    interface: dict[str, Any],
    provided_capabilities: set[str] | list[str] | tuple[str, ...],
) -> NegotiationResult:
    adapted = adapt_manifest(manifest)
    provided = set(map(str, provided_capabilities))
    required = set(map(str, adapted.get("required_capabilities") or []))
    runtime_required = set(map(str, interface.get("required_capabilities") or []))
    reasons: list[str] = []
    missing = sorted(required - provided)
    if missing:
        reasons.append("missing capabilities: " + ", ".join(missing))
    profile = str(adapted.get("cryptographic_profile") or "")
    if profile not in {PROFILE_NAME, "legacy-read-only"}:
        reasons.append("cryptographic profile mismatch")
    critical = adapted.get("critical_extensions") or []
    mode = "native"
    if adapted.get("migration", {}).get("read_only") or critical or profile == "legacy-read-only":
        mode = "read-only"
    if critical:
        reasons.append("unknown critical extensions force read-only mode")
    if not runtime_required.issubset(provided):
        reasons.append(
            "runtime capability set incomplete: "
            + ", ".join(sorted(runtime_required - provided))
        )
    compatible = not missing and runtime_required.issubset(provided)
    return NegotiationResult(
        compatible=compatible,
        mode=mode if compatible else "rejected",
        reasons=tuple(reasons),
        preserved_unknown_fields=dict(adapted.get("preserved_unknown_fields") or {}),
        required_capabilities=tuple(sorted(required)),
        provided_capabilities=tuple(sorted(provided)),
    )


def verify_pair_binding(
    binding: dict[str, Any],
    *,
    corpus_root_id: str,
    profile_registry: dict[str, Any],
    runtime_source_id: str | None = None,
) -> dict[str, Any]:
    checks = {
        "schema": binding.get("schema") == BINDING_SCHEMA,
        "corpus_root": binding.get("corpus_root_id") == corpus_root_id,
        "profile": binding.get("cryptographic_profile") == PROFILE_NAME,
        "profile_registry": binding.get("profile_registry_id")
        == registry_identity(profile_registry),
        "runtime_source": runtime_source_id is None
        or binding.get("runtime_source_id") == runtime_source_id,
        "partial_upgrade_forbidden": binding.get("partial_upgrade_allowed") is False,
    }
    if not all(checks.values()):
        raise CompatibilityError(
            "mixed or partially upgraded corpus/runtime pair rejected: "
            + ", ".join(key for key, passed in checks.items() if not passed)
        )
    return {
        "schema": "duotronic-pair-binding-verification/v1",
        "passed": True,
        "checks": checks,
        "binding_id": binding.get("binding_id"),
    }


def make_binding(
    *,
    corpus_root_id: str,
    runtime_source_id: str,
    profile_registry: dict[str, Any],
    api_version: str,
    manifest_schema: str,
) -> dict[str, Any]:
    body = {
        "schema": BINDING_SCHEMA,
        "corpus_root_id": corpus_root_id,
        "runtime_source_id": runtime_source_id,
        "cryptographic_profile": PROFILE_NAME,
        "profile_registry_id": registry_identity(profile_registry),
        "api_version": api_version,
        "manifest_schema": manifest_schema,
        "partial_upgrade_allowed": False,
        "unknown_noncritical_fields": "preserve",
        "unknown_critical_fields": "read-only",
    }
    body["binding_id"] = duoid("DUOTRONIC/PAIRED-RUNTIME-BINDING/v1", body)
    return body


def verify_mounted_pair(
    *,
    config_root: Path = Path("/runtime/config"),
    pair_root: Path = Path("/runtime/corpus-history"),
) -> dict[str, Any]:
    binding = json.loads((config_root / "paired_binding.json").read_text(encoding="utf-8"))
    registry = load_registry(config_root / "cryptographic_profile_registry_v1.json")
    manifest = json.loads((pair_root / "paired-candidate.json").read_text(encoding="utf-8"))
    candidate = manifest.get("candidate", {})
    checks = {
        "binding_schema": binding.get("schema") == BINDING_SCHEMA,
        "pair_schema": manifest.get("schema") == "duotronic-paired-candidate/v1",
        "corpus_identity": binding.get("corpus_root_id") == candidate.get("corpus_id"),
        "profile_registry": binding.get("profile_registry_id") == registry_identity(registry),
        "profile": binding.get("cryptographic_profile") == PROFILE_NAME,
        "partial_upgrade_forbidden": binding.get("partial_upgrade_allowed") is False,
        "env_corpus": os.environ.get("DUOTRONIC_CORPUS_ROOT_ID") == binding.get("corpus_root_id"),
        "env_profile": os.environ.get("DUOTRONIC_CRYPTO_PROFILE") == PROFILE_NAME,
        "env_profile_registry": os.environ.get("DUOTRONIC_PROFILE_REGISTRY_ID")
        == binding.get("profile_registry_id"),
        "sandbox_mode": os.environ.get("WG_RNN_RUNTIME_MODE") == "sandbox",
    }
    if not all(checks.values()):
        raise CompatibilityError(
            "mounted pair rejected: "
            + ", ".join(key for key, passed in checks.items() if not passed)
        )
    return {
        "schema": "duotronic-mounted-pair-verification/v1",
        "passed": True,
        "checks": checks,
        "binding_id": binding.get("binding_id"),
        "pair_id": manifest.get("pair_id"),
    }
