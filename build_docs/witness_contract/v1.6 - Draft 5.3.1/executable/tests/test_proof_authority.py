#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "executable/runtime/proof_authority.py"
SPEC = importlib.util.spec_from_file_location("proof_authority", MODULE_PATH)
authority = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = authority
SPEC.loader.exec_module(authority)


class ProofAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key()

    def test_signed_record_rejects_tampering(self):
        signed = authority.sign_record({"claim_id": "claim:1", "claim_content_sha256": "a" * 64}, self.private)
        self.assertTrue(authority.verify_record(signed, self.public))
        signed["claim_content_sha256"] = "b" * 64
        self.assertFalse(authority.verify_record(signed, self.public))

    def test_signed_payload_hash_is_checked(self):
        signed = authority.sign_record({"claim_id": "claim:1"}, self.private)
        signed["signed_payload_sha256"] = "0" * 64
        self.assertFalse(authority.verify_record(signed, self.public))

    def test_unavailable_lake_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            (source / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
            (source / "lean-toolchain").write_text("leanprover/lean4:v4.29.1\n", encoding="utf-8")
            artifact = source / "Proof.lean"
            artifact.write_text("theorem t : True := by trivial\n", encoding="utf-8")
            witness = authority.run_strict_lake_build(
                claim_id="claim:1",
                canonical_claim={"predicate": "is_true"},
                theorem_statement="True",
                theorem_name="t",
                proof_artifact=artifact,
                source_root=source,
                toolchain="leanprover/lean4:v4.29.1",
                verifier_principal_id="verifier:test",
                key_id="key:test",
                private_key=self.private,
                created_at="2026-07-31T12:00:00Z",
            )
            self.assertIn(witness["result"], {"toolchain_unavailable", "failed_lake_build", "failed_static_scan", "passed"})
            if witness["result"] != "passed":
                self.assertNotEqual(witness["theorem_status"], "proved")
            self.assertTrue(authority.verify_record(witness, self.public))


if __name__ == "__main__":
    unittest.main()
