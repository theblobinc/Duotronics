from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROFILE_NAME = "duotronic-pq-2026.1"
IDENTIFIER_PREFIX = "duoid:shake256-512:"
DOMAIN_FORMAT = "length-prefixed-utf8-v1"

try:
    from Cryptodome.Hash import KMAC256
    from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV
    from pqcrypto.kem import ml_kem_1024
    from pqcrypto.sign import ml_dsa_87
    PROVIDER_IMPORT_ERROR: str | None = None
except Exception as exc:
    KMAC256 = AESGCMSIV = ml_kem_1024 = ml_dsa_87 = None
    PROVIDER_IMPORT_ERROR = repr(exc)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def frame(domain: str, *parts: bytes) -> bytes:
    values = [domain.encode("utf-8"), *parts]
    out = bytearray()
    for value in values:
        out.extend(len(value).to_bytes(8, "big"))
        out.extend(value)
    return bytes(out)


def shake256_512(domain: str, *parts: bytes) -> bytes:
    return hashlib.shake_256(frame(domain, *parts)).digest(64)


def duoid(domain: str, value: Any) -> str:
    raw = shake256_512(domain, canonical_bytes(value))
    return IDENTIFIER_PREFIX + base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def kmac256(key: bytes, domain: str, *parts: bytes, output_bytes: int = 64) -> bytes:
    require_providers()
    if len(key) < 32:
        raise ValueError("KMAC256 key must contain at least 256 bits")
    custom = ("DUOTRONIC/" + domain).encode("utf-8")
    return KMAC256.new(
        key=key, data=frame(domain, *parts), mac_len=output_bytes, custom=custom
    ).digest()


def registry_identity(registry: dict[str, Any]) -> str:
    return duoid("DUOTRONIC/CRYPTOGRAPHIC-PROFILE-REGISTRY/v1", registry)


def load_registry(path: Path) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("schema") != "duotronic-cryptographic-profile-registry/v1":
        raise ValueError("unsupported cryptographic profile registry")
    active = registry.get("active_profile")
    if active != PROFILE_NAME or active not in registry.get("profiles", {}):
        raise ValueError("required active cryptographic profile is unavailable")
    return registry


def require_providers() -> None:
    if PROVIDER_IMPORT_ERROR:
        raise RuntimeError("post-quantum provider unavailable: " + PROVIDER_IMPORT_ERROR)


def provider_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for package in ("pqcrypto", "pycryptodomex", "cryptography"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = None
    return result


@dataclass(frozen=True)
class PublicKeyRecord:
    key_id: str
    purpose: str
    algorithm: str
    public_key_base64url: str
    state: str
    created_at: str
    predecessor_key_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "key_id": self.key_id,
            "purpose": self.purpose,
            "algorithm": self.algorithm,
            "public_key_base64url": self.public_key_base64url,
            "state": self.state,
            "created_at": self.created_at,
            "predecessor_key_id": self.predecessor_key_id,
        }


def generate_signing_key(
    purpose: str, predecessor_key_id: str | None = None
) -> tuple[PublicKeyRecord, bytes]:
    require_providers()
    public_key, secret_key = ml_dsa_87.generate_keypair()
    created_at = datetime.now(timezone.utc).isoformat()
    key_id = duoid(
        "DUOTRONIC/ML-DSA-87/PUBLIC-KEY/v1",
        {
            "purpose": purpose,
            "public_key": b64(public_key),
            "predecessor_key_id": predecessor_key_id,
        },
    )
    return (
        PublicKeyRecord(
            key_id=key_id,
            purpose=purpose,
            algorithm="ML-DSA-87",
            public_key_base64url=b64(public_key),
            state="active",
            created_at=created_at,
            predecessor_key_id=predecessor_key_id,
        ),
        secret_key,
    )


def sign_envelope(
    payload: dict[str, Any], record: PublicKeyRecord, secret_key: bytes, *, purpose: str
) -> dict[str, Any]:
    require_providers()
    if record.state != "active" or record.purpose != purpose:
        raise ValueError("signing key is not active for the requested purpose")
    unsigned = {
        "schema": "duotronic-ml-dsa-signed-envelope/v1",
        "profile": PROFILE_NAME,
        "purpose": purpose,
        "key_id": record.key_id,
        "payload": payload,
        "payload_id": duoid("DUOTRONIC/SIGNED-PAYLOAD/v1/" + purpose, payload),
    }
    signature = ml_dsa_87.sign(secret_key, canonical_bytes(unsigned))
    return {
        **unsigned,
        "signature_suite": "ML-DSA-87",
        "signature_base64url": b64(signature),
    }


def verify_envelope(
    envelope: dict[str, Any], record: PublicKeyRecord, revoked_key_ids: set[str] | None = None
) -> bool:
    require_providers()
    revoked_key_ids = revoked_key_ids or set()
    if (
        envelope.get("schema") != "duotronic-ml-dsa-signed-envelope/v1"
        or envelope.get("profile") != PROFILE_NAME
        or envelope.get("signature_suite") != "ML-DSA-87"
        or envelope.get("key_id") != record.key_id
        or record.key_id in revoked_key_ids
        or record.state in {"revoked", "destroyed"}
    ):
        return False
    unsigned = {
        key: envelope[key]
        for key in ("schema", "profile", "purpose", "key_id", "payload", "payload_id")
    }
    expected = duoid(
        "DUOTRONIC/SIGNED-PAYLOAD/v1/" + str(envelope["purpose"]), envelope["payload"]
    )
    if envelope["payload_id"] != expected:
        return False
    try:
        return bool(
            ml_dsa_87.verify(
                unb64(record.public_key_base64url),
                canonical_bytes(unsigned),
                unb64(str(envelope["signature_base64url"])),
            )
        )
    except Exception:
        return False


def generate_kem_keypair() -> tuple[bytes, bytes]:
    require_providers()
    return ml_kem_1024.generate_keypair()


def encrypt_for_recipient(
    recipient_public_key: bytes,
    plaintext: bytes,
    *,
    associated_data: bytes = b"",
    context: str = "EVIDENCE-TRANSPORT/v1",
) -> dict[str, Any]:
    require_providers()
    kem_ciphertext, shared_secret = ml_kem_1024.encrypt(recipient_public_key)
    nonce = os.urandom(12)
    key = kmac256(shared_secret, "ML-KEM-1024/" + context, associated_data, output_bytes=32)
    ciphertext = AESGCMSIV(key).encrypt(nonce, plaintext, associated_data)
    body = {
        "schema": "duotronic-ml-kem-encrypted-envelope/v1",
        "profile": PROFILE_NAME,
        "kem": "ML-KEM-1024",
        "kdf": "KMAC256-256",
        "aead": "AES-256-GCM-SIV",
        "context": context,
        "kem_ciphertext_base64url": b64(kem_ciphertext),
        "nonce_base64url": b64(nonce),
        "ciphertext_base64url": b64(ciphertext),
        "associated_data_id": duoid("DUOTRONIC/ENCRYPTED-AAD/v1", b64(associated_data)),
    }
    body["envelope_id"] = duoid("DUOTRONIC/ENCRYPTED-ENVELOPE/v1", body)
    return body


def decrypt_for_recipient(
    recipient_secret_key: bytes,
    envelope: dict[str, Any],
    *,
    associated_data: bytes = b"",
) -> bytes:
    require_providers()
    if (
        envelope.get("schema") != "duotronic-ml-kem-encrypted-envelope/v1"
        or envelope.get("profile") != PROFILE_NAME
        or envelope.get("kem") != "ML-KEM-1024"
        or envelope.get("kdf") != "KMAC256-256"
        or envelope.get("aead") != "AES-256-GCM-SIV"
    ):
        raise ValueError("unsupported encrypted envelope")
    body = {key: value for key, value in envelope.items() if key != "envelope_id"}
    if envelope.get("envelope_id") != duoid("DUOTRONIC/ENCRYPTED-ENVELOPE/v1", body):
        raise ValueError("encrypted envelope identity mismatch")
    if envelope.get("associated_data_id") != duoid(
        "DUOTRONIC/ENCRYPTED-AAD/v1", b64(associated_data)
    ):
        raise ValueError("associated data mismatch")
    kem_ciphertext = unb64(str(envelope["kem_ciphertext_base64url"]))
    shared_secret = ml_kem_1024.decrypt(recipient_secret_key, kem_ciphertext)
    key = kmac256(
        shared_secret,
        "ML-KEM-1024/" + str(envelope["context"]),
        associated_data,
        output_bytes=32,
    )
    return AESGCMSIV(key).decrypt(
        unb64(str(envelope["nonce_base64url"])),
        unb64(str(envelope["ciphertext_base64url"])),
        associated_data,
    )


class AppendOnlyKeyRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path

    def events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def append(self, event_type: str, body: dict[str, Any]) -> dict[str, Any]:
        if event_type not in {"register", "rotate", "retire", "revoke", "destroy"}:
            raise ValueError("unsupported key lifecycle event")
        prior = self.events()
        previous_event_id = prior[-1]["event_id"] if prior else None
        event = {
            "schema": "duotronic-key-lifecycle-event/v1",
            "ordinal": len(prior) + 1,
            "event_type": event_type,
            "at": datetime.now(timezone.utc).isoformat(),
            "previous_event_id": previous_event_id,
            "body": body,
        }
        event["event_id"] = duoid("DUOTRONIC/KEY-LIFECYCLE-EVENT/v1", event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        return event

    def revoked_key_ids(self) -> set[str]:
        return {
            str(event["body"]["key_id"])
            for event in self.events()
            if event["event_type"] in {"revoke", "destroy"}
        }

    def verify_chain(self) -> bool:
        prior_id = None
        for ordinal, event in enumerate(self.events(), 1):
            if event.get("ordinal") != ordinal or event.get("previous_event_id") != prior_id:
                return False
            unsigned = {key: value for key, value in event.items() if key != "event_id"}
            expected = duoid("DUOTRONIC/KEY-LIFECYCLE-EVENT/v1", unsigned)
            if event.get("event_id") != expected:
                return False
            prior_id = expected
        return True


def self_test() -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "duotronic-cryptographic-self-test/v1",
        "profile": PROFILE_NAME,
        "providers": provider_versions(),
        "provider_import_error": PROVIDER_IMPORT_ERROR,
        "tests": {},
    }
    tests = report["tests"]
    shake_expected = (
        "46b9dd2b0ba88d13233b3feb743eeb243fcd52ea62b81b82b50c27646ed5762f"
        "d75dc4ddd8c0f200cb05019d67b592f6fc821c49479ab48640292eacb3b7c4be"
    )
    tests["shake256_empty_512_kat"] = hashlib.shake_256(b"").hexdigest(64) == shake_expected
    if PROVIDER_IMPORT_ERROR:
        report["passed"] = False
        return report

    key = bytes(range(0x40, 0x60))
    expected_kmac = (
        "20c570c31346f703c9ac36c61c03cb64c3970d0cfc787e9b79599d273a68d2f"
        "7f69d4cc3de9d104a351689f27cf6f5951f0103f33f4f24871024d9c27773a8dd"
    )
    actual_kmac = KMAC256.new(
        key=key,
        data=bytes.fromhex("00010203"),
        mac_len=64,
        custom=b"My Tagged Application",
    ).hexdigest()
    tests["kmac256_nist_sample_3_kat"] = actual_kmac.lower() == expected_kmac

    sign_record, sign_secret = generate_signing_key("self-test")
    signed = sign_envelope({"message": "duotronic-pq-self-test"}, sign_record, sign_secret, purpose="self-test")
    tests["ml_dsa_87_sign_verify"] = verify_envelope(signed, sign_record)
    tampered = json.loads(json.dumps(signed))
    tampered["payload"]["message"] = "tampered"
    tests["ml_dsa_87_tamper_rejected"] = not verify_envelope(tampered, sign_record)
    tests["ml_dsa_87_revocation_rejected"] = not verify_envelope(
        signed, sign_record, {sign_record.key_id}
    )

    kem_public, kem_secret = generate_kem_keypair()
    aad = b"duotronic-self-test-aad"
    encrypted = encrypt_for_recipient(kem_public, b"secret evidence", associated_data=aad)
    tests["ml_kem_1024_hybrid_round_trip"] = (
        decrypt_for_recipient(kem_secret, encrypted, associated_data=aad)
        == b"secret evidence"
    )
    tampered_envelope = json.loads(json.dumps(encrypted))
    raw = bytearray(unb64(tampered_envelope["ciphertext_base64url"]))
    raw[-1] ^= 1
    tampered_envelope["ciphertext_base64url"] = b64(bytes(raw))
    body = {key: value for key, value in tampered_envelope.items() if key != "envelope_id"}
    tampered_envelope["envelope_id"] = duoid("DUOTRONIC/ENCRYPTED-ENVELOPE/v1", body)
    try:
        decrypt_for_recipient(kem_secret, tampered_envelope, associated_data=aad)
        tests["hybrid_ciphertext_tamper_rejected"] = False
    except Exception:
        tests["hybrid_ciphertext_tamper_rejected"] = True
    report["passed"] = all(bool(value) for value in tests.values())
    return report


if __name__ == "__main__":
    result = self_test()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 2)
