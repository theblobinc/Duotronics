#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

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

    def _project(self, source: pathlib.Path, proof_text: str) -> tuple[pathlib.Path, pathlib.Path, str]:
        (source / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
        (source / "lean-toolchain").write_text("leanprover/lean4:v4.29.1\n", encoding="utf-8")
        artifact = source / "Proof.lean"
        artifact.write_text(proof_text, encoding="utf-8")
        lake = source / "trusted-lake"
        lake.write_bytes(b"independently pinned test executable")
        lake.chmod(0o700)
        return artifact, lake, hashlib.sha256(lake.read_bytes()).hexdigest()

    def _run(
        self,
        source: pathlib.Path,
        artifact: pathlib.Path,
        lake: pathlib.Path | None,
        lake_hash: str | None,
        *,
        statement: str = "True",
        theorem_name: str = "t",
        returncode: int = 0,
        stdout: str = "'t' does not depend on any axioms\n",
        stderr: str = "",
        side_effect=None,
    ):
        completed = authority.subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)
        patch_kwargs = {"side_effect": side_effect} if side_effect is not None else {"return_value": completed}
        with mock.patch.object(authority.subprocess, "run", **patch_kwargs) as runner:
            witness = authority.run_strict_lake_build(
                claim_id="claim:1",
                canonical_claim={"predicate": "is_true"},
                theorem_statement=statement,
                theorem_name=theorem_name,
                proof_artifact=artifact,
                source_root=source,
                toolchain="leanprover/lean4:v4.29.1",
                verifier_principal_id="verifier:test",
                key_id="key:test",
                private_key=self.private,
                lake_executable=lake,
                expected_lake_sha256=lake_hash,
                created_at="2026-07-31T12:00:00Z",
            )
        self.assertTrue(authority.verify_record(witness, self.public))
        return witness, runner

    def test_signed_record_rejects_tampering(self):
        signed = authority.sign_record({"claim_id": "claim:1", "claim_content_sha256": "a" * 64}, self.private)
        self.assertTrue(authority.verify_record(signed, self.public))
        signed["claim_content_sha256"] = "b" * 64
        self.assertFalse(authority.verify_record(signed, self.public))

    def test_signed_payload_hash_is_checked(self):
        signed = authority.sign_record({"claim_id": "claim:1"}, self.private)
        signed["signed_payload_sha256"] = "0" * 64
        self.assertFalse(authority.verify_record(signed, self.public))

    def test_compiled_true_cannot_authorize_claimed_false(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, lake_hash = self._project(source, "theorem t : True := by trivial\n")
            witness, _ = self._run(source, artifact, lake, lake_hash, statement="False", returncode=1, stderr="type mismatch")
            self.assertNotEqual(witness["result"], "passed")
            self.assertFalse(witness["statement_binding_confirmed"])
            self.assertNotEqual(witness["theorem_status"], "proved")

    def test_comment_only_theorem_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, lake_hash = self._project(source, "/- theorem ghost : False := by contradiction -/\n")
            witness, _ = self._run(source, artifact, lake, lake_hash, statement="False", theorem_name="ghost", returncode=1, stderr="unknown identifier 'ghost'")
            self.assertNotEqual(witness["result"], "passed")

    def test_exact_sorry_is_rejected_from_compiled_axioms(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, lake_hash = self._project(source, "theorem t : True := by\n  exact sorry\n")
            witness, _ = self._run(source, artifact, lake, lake_hash, stdout="'t' depends on axioms: [sorryAx]\n")
            self.assertEqual(witness["theorem_status"], "sorry_stub")
            self.assertTrue(witness["contains_sorry"])
            self.assertNotEqual(witness["result"], "passed")

    def test_have_sorry_is_rejected_from_compiled_axioms(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, lake_hash = self._project(source, "theorem t : True := by\n  have h : True := sorry\n  exact h\n")
            witness, _ = self._run(source, artifact, lake, lake_hash, stdout="'t' depends on axioms: [sorryAx]\n")
            self.assertEqual(witness["unapproved_axiom_count"], 1)
            self.assertNotEqual(witness["result"], "passed")

    def test_attributed_unauthorized_axiom_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, lake_hash = self._project(source, "axiom unsafeWitness : True\ntheorem t : True := unsafeWitness\n")
            witness, _ = self._run(source, artifact, lake, lake_hash, stdout="'t' depends on axioms: [unsafeWitness]\n")
            self.assertEqual(witness["theorem_status"], "axiom_dependent")
            self.assertEqual(witness["axiom_dependencies"], ["unsafeWitness"])
            self.assertNotEqual(witness["result"], "passed")

    def test_missing_axiom_inspection_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, lake_hash = self._project(source, "theorem t : True := by trivial\n")
            witness, _ = self._run(source, artifact, lake, lake_hash, stdout="")
            self.assertFalse(witness["axiom_inspection_complete"])
            self.assertNotEqual(witness["result"], "passed")

    def test_proof_artifact_outside_source_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            source = pathlib.Path(temporary)
            _, lake, lake_hash = self._project(source, "theorem local : True := by trivial\n")
            artifact = pathlib.Path(outside) / "Proof.lean"
            artifact.write_text("theorem t : True := by trivial\n", encoding="utf-8")
            witness, runner = self._run(source, artifact, lake, lake_hash)
            self.assertEqual(witness["result"], "failed_static_scan")
            runner.assert_not_called()

    def test_generated_exact_target_imports_submitted_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, lake_hash = self._project(source, "theorem t : True := by trivial\n")

            def inspect_target(command, **kwargs):
                self.assertEqual(command[1:4], ["env", "lean", "-DwarningAsError=true"])
                target = pathlib.Path(kwargs["cwd"]) / command[4]
                generated = target.read_text(encoding="utf-8")
                self.assertIn("import Proof", generated)
                self.assertIn("example : (True)", generated)
                self.assertIn("exact t", generated)
                self.assertIn("#print axioms t", generated)
                return authority.subprocess.CompletedProcess(command, 0, stdout="'t' does not depend on any axioms\n", stderr="")

            witness, _ = self._run(source, artifact, lake, lake_hash, side_effect=inspect_target)
            self.assertEqual(witness["result"], "passed")
            self.assertTrue(witness["statement_binding_confirmed"])
            self.assertTrue(witness["warnings_as_errors"])
            self.assertEqual(witness["exact_build_target"], witness["generated_witness_module_path"])

    def test_spoofed_lake_on_path_is_never_used(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, _, _ = self._project(source, "theorem t : True := by trivial\n")
            spoof = source / "lake"
            spoof.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            spoof.chmod(0o700)
            with mock.patch.dict(os.environ, {"PATH": f"{source}:{os.environ.get('PATH', '')}"}):
                witness, runner = self._run(source, artifact, None, None)
            self.assertEqual(witness["result"], "toolchain_unavailable")
            runner.assert_not_called()

    def test_wrong_compiler_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, _ = self._project(source, "theorem t : True := by trivial\n")
            witness, runner = self._run(source, artifact, lake, "0" * 64)
            self.assertEqual(witness["result"], "toolchain_unavailable")
            runner.assert_not_called()

    def test_multiline_statement_injection_is_rejected_before_compilation(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary)
            artifact, lake, lake_hash = self._project(source, "theorem t : True := by trivial\n")
            witness, runner = self._run(source, artifact, lake, lake_hash, statement="True\n#check False")
            self.assertEqual(witness["result"], "failed_static_scan")
            runner.assert_not_called()

    def test_sql_crypto_functions_verify_exact_payload(self):
        record = authority.sign_record({"claim_id": "claim:1", "result": "passed"}, self.private)
        payload = authority.signed_payload_canonical_json(record)
        public_b64 = authority.public_key_raw_b64url(self.public)
        connection = sqlite3.connect(":memory:")
        authority.register_sqlite_crypto_functions(connection)
        verified = connection.execute("SELECT wc_ed25519_verify(?,?,?)", (public_b64, payload, record["signature"])).fetchone()[0]
        tampered = connection.execute("SELECT wc_ed25519_verify(?,?,?)", (public_b64, payload + " ", record["signature"])).fetchone()[0]
        self.assertEqual(verified, 1)
        self.assertEqual(tampered, 0)
        self.assertEqual(connection.execute("SELECT wc_sha256(?)", (payload,)).fetchone()[0], record["signed_payload_sha256"])


if __name__ == "__main__":
    unittest.main()
