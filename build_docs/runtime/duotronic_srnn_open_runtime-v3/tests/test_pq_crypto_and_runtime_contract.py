from __future__ import annotations

import json
from pathlib import Path

import pytest

from duotronic_runtime.crypto_profile import (
    AppendOnlyKeyRegistry,
    PROFILE_NAME,
    decrypt_for_recipient,
    encrypt_for_recipient,
    generate_kem_keypair,
    generate_signing_key,
    load_registry,
    self_test,
    sign_envelope,
    verify_envelope,
)
from duotronic_runtime.runtime_contract import (
    CompatibilityError,
    adapt_manifest,
    load_interface,
    make_binding,
    negotiate,
    verify_pair_binding,
)


ROOT = Path(__file__).resolve().parents[1]


def test_full_post_quantum_provider_self_test() -> None:
    report = self_test()
    assert report["passed"], report
    assert all(report["tests"].values())


def test_ml_dsa_rotation_and_revocation(tmp_path: Path) -> None:
    registry = AppendOnlyKeyRegistry(tmp_path / "key-events.jsonl")
    first, first_secret = generate_signing_key("witness")
    registry.append("register", first.as_dict())
    envelope = sign_envelope({"ordinal": 1}, first, first_secret, purpose="witness")
    assert verify_envelope(envelope, first, registry.revoked_key_ids())

    second, second_secret = generate_signing_key("witness", first.key_id)
    registry.append(
        "rotate",
        {
            "key_id": second.key_id,
            "predecessor_key_id": first.key_id,
            "public_record": second.as_dict(),
        },
    )
    registry.append("revoke", {"key_id": first.key_id, "reason": "rotation-complete"})
    assert registry.verify_chain()
    assert not verify_envelope(envelope, first, registry.revoked_key_ids())
    successor = sign_envelope({"ordinal": 2}, second, second_secret, purpose="witness")
    assert verify_envelope(successor, second, registry.revoked_key_ids())


def test_ml_kem_hybrid_transport_rejects_wrong_aad() -> None:
    public_key, secret_key = generate_kem_keypair()
    envelope = encrypt_for_recipient(
        public_key, b"gate evidence", associated_data=b"pair-A"
    )
    assert (
        decrypt_for_recipient(secret_key, envelope, associated_data=b"pair-A")
        == b"gate evidence"
    )
    with pytest.raises(Exception):
        decrypt_for_recipient(secret_key, envelope, associated_data=b"pair-B")


def test_forward_fields_are_preserved_and_critical_fields_force_read_only() -> None:
    interface = load_interface(ROOT / "config/runtime_interface_v1.json")
    manifest = {
        "schema": "duotronic-corpus-manifest/1.0",
        "contract_version": "v1.6-draft-5.3.18",
        "corpus_root_id": "duoid:shake256-512:test",
        "cryptographic_profile": PROFILE_NAME,
        "required_capabilities": ["shake256-512-identities"],
        "critical_extensions": ["future-authority-rule"],
        "future_field": {"must_survive": True},
    }
    result = negotiate(
        manifest, interface, set(interface["required_capabilities"])
    )
    assert result.compatible
    assert result.mode == "read-only"
    assert result.preserved_unknown_fields["future_field"]["must_survive"] is True


def test_legacy_manifest_adapter_is_read_only() -> None:
    adapted = adapt_manifest(
        {"active_version": "v1.6-draft-5.3.17", "digest": "legacy", "extra": 7}
    )
    assert adapted["migration"]["read_only"] is True
    assert adapted["preserved_unknown_fields"]["extra"] == 7


def test_pair_binding_rejects_mixed_corpus() -> None:
    profile_registry = load_registry(
        ROOT / "config/cryptographic_profile_registry_v1.json"
    )
    interface = load_interface(ROOT / "config/runtime_interface_v1.json")
    binding = make_binding(
        corpus_root_id="duoid:shake256-512:corpus-A",
        runtime_source_id="duoid:shake256-512:runtime-A",
        profile_registry=profile_registry,
        api_version=interface["api_version"],
        manifest_schema=interface["manifest_schema"],
    )
    assert verify_pair_binding(
        binding,
        corpus_root_id="duoid:shake256-512:corpus-A",
        profile_registry=profile_registry,
        runtime_source_id="duoid:shake256-512:runtime-A",
    )["passed"]
    with pytest.raises(CompatibilityError):
        verify_pair_binding(
            binding,
            corpus_root_id="duoid:shake256-512:corpus-B",
            profile_registry=profile_registry,
            runtime_source_id="duoid:shake256-512:runtime-A",
        )
