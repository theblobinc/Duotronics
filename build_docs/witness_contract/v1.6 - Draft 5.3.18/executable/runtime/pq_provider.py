#!/usr/bin/env python3
"""Fail-closed post-quantum provider for Witness Contract 5.3.17.

The provider uses standardized ML-DSA-87 and ML-KEM-1024 implementations from
pqcrypto, KMAC256 from PyCryptodomeX, and AES-256-GCM-SIV from cryptography.
No fallback signature, KEM, KDF, or cipher is accepted.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV

try:
    from pqcrypto.kem import ml_kem_1024
    from pqcrypto.sign import ml_dsa_87
except ImportError as error:  # pragma: no cover - exercised by deployment gates
    ml_kem_1024 = None
    ml_dsa_87 = None
    _PQ_IMPORT_ERROR: Exception | None = error
else:
    _PQ_IMPORT_ERROR = None

try:
    from Cryptodome.Hash import KMAC256
except ImportError as error:  # pragma: no cover - exercised by deployment gates
    KMAC256 = None
    _KMAC_IMPORT_ERROR: Exception | None = error
else:
    _KMAC_IMPORT_ERROR = None


SUITE_ID = "duotronic-pq-v1"
ML_DSA_PUBLIC_KEY_BYTES = 2592
ML_DSA_SECRET_KEY_BYTES = 4896
ML_DSA_SIGNATURE_BYTES = 4627
ML_KEM_PUBLIC_KEY_BYTES = 1568
ML_KEM_SECRET_KEY_BYTES = 3168
ML_KEM_CIPHERTEXT_BYTES = 1568
ML_KEM_SHARED_SECRET_BYTES = 32
AES_KEY_BYTES = 32
AES_NONCE_BYTES = 12
_PRIVATE_ENVELOPE_TYPE = "duotronic_ml_dsa_87_private_key/v1"


def _require_pq() -> None:
    if ml_dsa_87 is None or ml_kem_1024 is None:
        raise RuntimeError("validated ML-DSA-87/ML-KEM-1024 provider is unavailable") from _PQ_IMPORT_ERROR


def _require_kmac() -> None:
    if KMAC256 is None:
        raise RuntimeError("validated KMAC256 provider is unavailable") from _KMAC_IMPORT_ERROR


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@dataclass(frozen=True)
class MLDSA87PublicKey:
    raw: bytes

    def __post_init__(self) -> None:
        if len(self.raw) != ML_DSA_PUBLIC_KEY_BYTES:
            raise ValueError("invalid ML-DSA-87 public-key length")

    @classmethod
    def from_public_bytes(cls, value: bytes) -> "MLDSA87PublicKey":
        return cls(bytes(value))

    def public_bytes(self, *_args: Any, **_kwargs: Any) -> bytes:
        return self.raw

    def verify(self, signature: bytes, message: bytes) -> None:
        _require_pq()
        if len(signature) != ML_DSA_SIGNATURE_BYTES:
            raise InvalidSignature("invalid ML-DSA-87 signature length")
        try:
            valid = ml_dsa_87.verify(self.raw, bytes(message), bytes(signature))
        except Exception as error:
            raise InvalidSignature("ML-DSA-87 verification failed") from error
        if valid is not True:
            raise InvalidSignature("ML-DSA-87 verification failed")


@dataclass(frozen=True)
class MLDSA87PrivateKey:
    secret: bytes
    public: bytes

    def __post_init__(self) -> None:
        if len(self.secret) != ML_DSA_SECRET_KEY_BYTES or len(self.public) != ML_DSA_PUBLIC_KEY_BYTES:
            raise ValueError("invalid ML-DSA-87 private-key envelope")

    @classmethod
    def generate(cls) -> "MLDSA87PrivateKey":
        _require_pq()
        public, secret = ml_dsa_87.generate_keypair()
        return cls(secret=secret, public=public)

    @classmethod
    def from_private_bytes(cls, value: bytes) -> "MLDSA87PrivateKey":
        try:
            envelope = json.loads(value.decode("utf-8"))
            if envelope.get("type") != _PRIVATE_ENVELOPE_TYPE or set(envelope) != {"type", "public_key_base64url", "secret_key_base64url"}:
                raise ValueError("unexpected private-key envelope")
            return cls(secret=_decode(envelope["secret_key_base64url"]), public=_decode(envelope["public_key_base64url"]))
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid ML-DSA-87 private-key envelope") from error

    def private_bytes(self, *_args: Any, **_kwargs: Any) -> bytes:
        envelope = {
            "public_key_base64url": _b64url(self.public),
            "secret_key_base64url": _b64url(self.secret),
            "type": _PRIVATE_ENVELOPE_TYPE,
        }
        return json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def public_key(self) -> MLDSA87PublicKey:
        return MLDSA87PublicKey(self.public)

    def sign(self, message: bytes) -> bytes:
        _require_pq()
        signature = ml_dsa_87.sign(self.secret, bytes(message))
        if len(signature) != ML_DSA_SIGNATURE_BYTES:
            raise RuntimeError("provider emitted an invalid ML-DSA-87 signature length")
        return signature


@dataclass(frozen=True)
class MLKEM1024KeyPair:
    public: bytes
    secret: bytes

    @classmethod
    def generate(cls) -> "MLKEM1024KeyPair":
        _require_pq()
        public, secret = ml_kem_1024.generate_keypair()
        return cls(public=public, secret=secret)

    def encapsulate(self) -> tuple[bytes, bytes]:
        _require_pq()
        ciphertext, shared_secret = ml_kem_1024.encrypt(self.public)
        return ciphertext, shared_secret

    def decapsulate(self, ciphertext: bytes) -> bytes:
        _require_pq()
        if len(ciphertext) != ML_KEM_CIPHERTEXT_BYTES:
            raise ValueError("invalid ML-KEM-1024 ciphertext length")
        return ml_kem_1024.decrypt(self.secret, bytes(ciphertext))


def kmac256(key: bytes, message: bytes, *, customization: bytes, output_bytes: int = 64) -> bytes:
    _require_kmac()
    if len(key) < 32 or not customization or output_bytes < 32:
        raise ValueError("KMAC256 parameters violate the contract profile")
    return KMAC256.new(key=bytes(key), data=bytes(message), custom=bytes(customization), mac_len=output_bytes).digest()


def derive_payload_key(shared_secret: bytes, envelope_context: bytes) -> bytes:
    return kmac256(
        shared_secret,
        envelope_context,
        customization=b"DUOTRONIC/PAYLOAD-KEY/v1",
        output_bytes=AES_KEY_BYTES,
    )


def encrypt_payload(key: bytes, nonce: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
    if len(key) != AES_KEY_BYTES or len(nonce) != AES_NONCE_BYTES:
        raise ValueError("invalid AES-256-GCM-SIV key or nonce length")
    return AESGCMSIV(bytes(key)).encrypt(bytes(nonce), bytes(plaintext), bytes(associated_data))


def decrypt_payload(key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes) -> bytes:
    if len(key) != AES_KEY_BYTES or len(nonce) != AES_NONCE_BYTES:
        raise ValueError("invalid AES-256-GCM-SIV key or nonce length")
    return AESGCMSIV(bytes(key)).decrypt(bytes(nonce), bytes(ciphertext), bytes(associated_data))
