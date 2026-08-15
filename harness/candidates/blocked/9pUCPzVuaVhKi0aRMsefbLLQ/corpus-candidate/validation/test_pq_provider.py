#!/usr/bin/env python3
"""Executable round-trip tests for the standardized 5.3.17 provider adapter."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executable" / "runtime"))

from pq_provider import (  # noqa: E402
    MLDSA87PrivateKey,
    MLKEM1024KeyPair,
    decrypt_payload,
    derive_payload_key,
    encrypt_payload,
)


class PostQuantumProviderTests(unittest.TestCase):
    def test_signature_private_envelope_and_verification(self) -> None:
        private = MLDSA87PrivateKey.generate()
        restored = MLDSA87PrivateKey.from_private_bytes(private.private_bytes())
        payload = b"duotronic-witness-contract-5.3.17"
        signature = restored.sign(payload)
        self.assertEqual(len(signature), 4627)
        restored.public_key().verify(signature, payload)

    def test_kem_kdf_and_aead_round_trip(self) -> None:
        recipient = MLKEM1024KeyPair.generate()
        ciphertext, sender_secret = recipient.encapsulate()
        recipient_secret = recipient.decapsulate(ciphertext)
        self.assertEqual(sender_secret, recipient_secret)
        context = b"DUOTRONIC/ENVELOPE/test/v1"
        key = derive_payload_key(sender_secret, context)
        nonce = b"\x01" * 12
        protected = encrypt_payload(key, nonce, b"witness-payload", context)
        self.assertEqual(decrypt_payload(key, nonce, protected, context), b"witness-payload")


if __name__ == "__main__":
    unittest.main()
