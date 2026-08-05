#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import pathlib
import sqlite3
import sys
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "executable/runtime/proof_authority.py"
SPEC = importlib.util.spec_from_file_location("proof_authority_sql", MODULE_PATH)
authority = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = authority
SPEC.loader.exec_module(authority)


def expect_integrity_error(testcase: unittest.TestCase, action) -> None:
    with testcase.assertRaises(sqlite3.IntegrityError):
        action()


class AuthorityDatabase:
    def __init__(self):
        self.connection = sqlite3.connect(":memory:", isolation_level=None)
        authority.register_sqlite_crypto_functions(self.connection)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript((ROOT / "executable/sql/draft5_2_schema_additions.sql").read_text(encoding="utf-8"))
        self.connection.executescript((ROOT / "migration/draft5_2_2_to_draft5_3_1.sql").read_text(encoding="utf-8"))
        self.connection.executescript((ROOT / "migration/draft5_3_1_to_draft5_3_2.sql").read_text(encoding="utf-8"))
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key()
        self.claim_hash = "a" * 64
        self.theorem_hash = "b" * 64
        self.artifact_hash = "c" * 64
        self.base_time = "2026-07-31T12:00:00Z"
        self.proof_time = "2026-07-31T12:01:00Z"
        self.binding_time = "2026-07-31T12:02:00Z"
        self.gate_time = "2026-07-31T12:04:00Z"

    def close(self):
        connection = getattr(self, "connection", None)
        if connection is not None:
            connection.close(); self.connection = None

    def __enter__(self): return self
    def __exit__(self, *_): self.close()
    def __del__(self): self.close()

    def register_key(
        self,
        *,
        suffix: str = "1",
        private: Ed25519PrivateKey | None = None,
        valid_from: str = "2020-01-01T00:00:00Z",
        valid_until: str | None = "2099-01-01T00:00:00Z",
    ) -> tuple[str, str, Ed25519PrivateKey]:
        private = private or self.private
        public = private.public_key()
        verifier_id = f"verifier:{suffix}"
        key_id = f"key:{suffix}"
        fingerprint = authority.public_key_fingerprint(public)
        self.connection.execute(
            "INSERT INTO wc_verifier_principals_v2 VALUES (?,?,?,?,?,?,?,?,?)",
            (verifier_id, "verifier_principal/v2", key_id, "Ed25519", fingerprint, "active", valid_from, valid_until, valid_from),
        )
        self.connection.execute(
            "INSERT INTO wc_verifier_keys_v3 VALUES (?,?,?,?,?,?,?,?,?)",
            (key_id, "verifier_key/v3", verifier_id, "Ed25519", authority.public_key_raw_b64url(public), fingerprint, valid_from, valid_until, valid_from),
        )
        self.connection.execute(
            "INSERT INTO wc_verifier_key_status_events_v1 VALUES (?,?,?,?,?,?,?,?,?)",
            (f"key-event:{suffix}:active", "verifier_key_status_event/v1", key_id, "active", None, "initial activation", valid_from, valid_from, "principal:governance"),
        )
        return verifier_id, key_id, private

    def insert_chain_before_gate(self, *, hardening: bool = True, insert_bindings: bool = True) -> None:
        verifier_id, key_id, private = self.register_key()
        c = self.connection
        c.execute(
            "INSERT INTO wc_claims_v2 VALUES (?,?,?,?,?,?,?,?,?)",
            ("claim:proof", "evidence_claim/v2", "proof_claim", '{"statement":"P"}', self.claim_hash, "theorem P", self.theorem_hash, "principal:hugh", self.base_time),
        )
        c.execute(
            "INSERT INTO wc_policy_decisions_v2 VALUES (?,?,?,?,?,?,?,?)",
            ("policy:allow", "policy_decision/v2", "claim:proof", "allow", "theorem_promotion", "principal:governance", "approved for strict check", self.base_time),
        )

        compiler_unsigned = {
            "schema_version": "lean_compiler_witness/v2",
            "lean_compiler_witness_id": "lean:valid",
            "claim_id": "claim:proof",
            "claim_content_sha256": self.claim_hash,
            "theorem_statement_sha256": self.theorem_hash,
            "proof_artifact_sha256": self.artifact_hash,
            "proof_artifact_relative_path": "Proof.lean",
            "proof_module": "Proof",
            "source_tree_sha256": "d" * 64,
            "lakefile_sha256": "e" * 64,
            "generated_witness_module_sha256": "9" * 64,
            "generated_witness_module_path": ".witness_authority/Check_valid.lean",
            "exact_build_target": ".witness_authority/Check_valid.lean",
            "compiler_executable_sha256": "8" * 64,
            "build_output_sha256": "f" * 64,
            "toolchain": "leanprover/lean4:v4.29.1",
            "command": ["/trusted/lake", "env", "lean", "-DwarningAsError=true", ".witness_authority/Check_valid.lean"],
            "execution_mode": "strict",
            "result": "passed",
            "contains_sorry": False,
            "contains_admit": False,
            "unapproved_axiom_count": 0,
            "axiom_dependencies": ["Classical.choice"],
            "axiom_inspection_complete": hardening,
            "statement_binding_confirmed": hardening,
            "warnings_as_errors": hardening,
            "theorem_name": "promotion_sound",
            "theorem_status": "proved",
            "verifier_principal_id": verifier_id,
            "key_id": key_id,
            "signature_algorithm": "Ed25519",
            "created_at": self.base_time,
        }
        compiler = authority.sign_record(compiler_unsigned, private)
        c.execute(
            """INSERT INTO wc_lean_compiler_witnesses_v2 (
              lean_compiler_witness_id,schema_version,claim_id,claim_content_sha256,theorem_statement_sha256,
              proof_artifact_sha256,source_tree_sha256,lakefile_sha256,build_output_sha256,toolchain,command_json,
              execution_mode,result,contains_sorry,contains_admit,unapproved_axiom_count,theorem_name,theorem_status,
              verifier_principal_id,key_id,signature_algorithm,signed_payload_sha256,signature,created_at,
              proof_artifact_relative_path,proof_module,generated_witness_module_sha256,generated_witness_module_path,
              exact_build_target,compiler_executable_sha256,axiom_dependencies_json,axiom_inspection_complete,
              statement_binding_confirmed,warnings_as_errors
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                compiler["lean_compiler_witness_id"], compiler["schema_version"], compiler["claim_id"], compiler["claim_content_sha256"], compiler["theorem_statement_sha256"],
                compiler["proof_artifact_sha256"], compiler["source_tree_sha256"], compiler["lakefile_sha256"], compiler["build_output_sha256"], compiler["toolchain"], json.dumps(compiler["command"], separators=(",", ":")),
                compiler["execution_mode"], compiler["result"], int(compiler["contains_sorry"]), int(compiler["contains_admit"]), compiler["unapproved_axiom_count"], compiler["theorem_name"], compiler["theorem_status"],
                compiler["verifier_principal_id"], compiler["key_id"], compiler["signature_algorithm"], compiler["signed_payload_sha256"], compiler["signature"], compiler["created_at"],
                compiler["proof_artifact_relative_path"], compiler["proof_module"], compiler["generated_witness_module_sha256"], compiler["generated_witness_module_path"],
                compiler["exact_build_target"], compiler["compiler_executable_sha256"], json.dumps(compiler["axiom_dependencies"], separators=(",", ":")), int(compiler["axiom_inspection_complete"]),
                int(compiler["statement_binding_confirmed"]), int(compiler["warnings_as_errors"]),
            ),
        )
        if insert_bindings:
            c.execute(
                "INSERT INTO wc_authority_signature_bindings_v1 VALUES (?,?,?,?,?,?,?,?)",
                ("sigbind:lean", "authority_signature_binding/v1", "lean_compiler_witness", "lean:valid", key_id, authority.signed_payload_canonical_json(compiler), compiler["signed_payload_sha256"], self.binding_time),
            )

        proof_unsigned = {
            "schema_version": "proof_witness/v2",
            "proof_witness_id": "proof:valid",
            "claim_id": "claim:proof",
            "claim_content_sha256": self.claim_hash,
            "theorem_statement_sha256": self.theorem_hash,
            "proof_artifact_sha256": self.artifact_hash,
            "lean_compiler_witness_id": "lean:valid",
            "theorem_name": "promotion_sound",
            "theorem_status": "proved",
            "policy_decision_id": "policy:allow",
            "verifier_principal_id": verifier_id,
            "key_id": key_id,
            "created_at": self.proof_time,
        }
        proof = authority.sign_record(proof_unsigned, private)
        c.execute(
            """INSERT INTO wc_proof_witnesses_v2 (
              proof_witness_id,schema_version,claim_id,claim_content_sha256,theorem_statement_sha256,
              proof_artifact_sha256,lean_compiler_witness_id,theorem_name,theorem_status,policy_decision_id,
              verifier_principal_id,signed_payload_sha256,signature,created_at,key_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                proof["proof_witness_id"], proof["schema_version"], proof["claim_id"], proof["claim_content_sha256"], proof["theorem_statement_sha256"],
                proof["proof_artifact_sha256"], proof["lean_compiler_witness_id"], proof["theorem_name"], proof["theorem_status"], proof["policy_decision_id"],
                proof["verifier_principal_id"], proof["signed_payload_sha256"], proof["signature"], proof["created_at"], proof["key_id"],
            ),
        )
        if insert_bindings:
            c.execute(
                "INSERT INTO wc_authority_signature_bindings_v1 VALUES (?,?,?,?,?,?,?,?)",
                ("sigbind:proof", "authority_signature_binding/v1", "proof_witness", "proof:valid", key_id, authority.signed_payload_canonical_json(proof), proof["signed_payload_sha256"], self.binding_time),
            )
        c.execute(
            "INSERT INTO wc_non_collapse_transitions_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("nc:valid", "non_collapse_transition/v2", "claim:proof", "conjectural", "theorem", "proof_upgrade", "allowed", None, "proof:valid", "policy:allow", "strict proof upgrade", self.proof_time),
        )
        c.execute(
            "INSERT INTO wc_claim_status_events_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("status:valid", "claim_status_event/v2", "claim:proof", "conjecture", "theorem", "prove", 1, "policy:allow", "proof:valid", "lean:valid", "nc:valid", self.proof_time),
        )

    def insert_gate(self, gate_id: str = "gate:valid") -> None:
        self.connection.execute(
            """INSERT INTO wc_theorem_promotion_gates_v2 (
              theorem_promotion_gate_id,schema_version,claim_id,claim_content_sha256,theorem_statement_sha256,
              status_event_id,proof_witness_id,lean_compiler_witness_id,non_collapse_transition_id,
              policy_decision_id,verifier_principal_id,allowed,rejection_reason,created_at,key_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (gate_id, "theorem_promotion_gate/v2", "claim:proof", self.claim_hash, self.theorem_hash, "status:valid", "proof:valid", "lean:valid", "nc:valid", "policy:allow", "verifier:1", 1, None, self.gate_time, "key:1"),
        )


class SqlAuthorityLifecycleTests(unittest.TestCase):
    def database(self):
        database = AuthorityDatabase()
        self.addCleanup(database.close)
        return database

    def test_happy_chain_is_currently_authoritative(self):
        db = self.database()
        db.insert_chain_before_gate()
        db.insert_gate()
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_authoritative_theorems_v2").fetchone()[0], 1)

    def test_expired_key_cannot_create_gate(self):
        db = self.database()
        original = db.register_key

        def expired_register_key(**kwargs):
            return original(valid_from="2019-01-01T00:00:00Z", valid_until="2020-01-01T00:00:00Z", **kwargs)

        db.register_key = expired_register_key
        db.insert_chain_before_gate()
        expect_integrity_error(self, db.insert_gate)

    def test_revoked_key_cannot_create_gate(self):
        db = self.database()
        db.insert_chain_before_gate()
        db.connection.execute(
            "INSERT INTO wc_verifier_key_status_events_v1 VALUES (?,?,?,?,?,?,?,?,?)",
            ("key-event:1:revoked", "verifier_key_status_event/v1", "key:1", "revoked", None, "compromise", "2026-07-31T12:03:00Z", "2026-07-31T12:03:00Z", "principal:governance"),
        )
        expect_integrity_error(self, db.insert_gate)

    def test_superseded_key_cannot_create_gate(self):
        db = self.database()
        db.insert_chain_before_gate()
        replacement = Ed25519PrivateKey.generate()
        db.register_key(suffix="2", private=replacement)
        db.connection.execute(
            "INSERT INTO wc_verifier_key_status_events_v1 VALUES (?,?,?,?,?,?,?,?,?)",
            ("key-event:1:superseded", "verifier_key_status_event/v1", "key:1", "superseded", "key:2", "rotation", "2026-07-31T12:03:00Z", "2026-07-31T12:03:00Z", "principal:governance"),
        )
        expect_integrity_error(self, db.insert_gate)

    def test_later_revocation_removes_gate_from_current_view(self):
        db = self.database()
        db.insert_chain_before_gate()
        db.insert_gate()
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_authoritative_theorems_v2").fetchone()[0], 1)
        db.connection.execute(
            "INSERT INTO wc_verifier_key_status_events_v1 VALUES (?,?,?,?,?,?,?,?,?)",
            ("key-event:1:revoked", "verifier_key_status_event/v1", "key:1", "revoked", None, "post-gate compromise", "2026-07-31T12:05:00Z", "2026-07-31T12:05:00Z", "principal:governance"),
        )
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_authoritative_theorems_v2").fetchone()[0], 0)
        self.assertEqual(db.connection.execute("SELECT count(*) FROM wc_theorem_promotion_gates_v2 WHERE allowed=1").fetchone()[0], 1)

    def test_missing_signature_bindings_cannot_create_gate(self):
        db = self.database()
        db.insert_chain_before_gate(insert_bindings=False)
        expect_integrity_error(self, db.insert_gate)

    def test_wrong_claim_hash_cannot_create_gate(self):
        db = self.database()
        db.insert_chain_before_gate()
        expect_integrity_error(
            self,
            lambda: db.connection.execute(
                """INSERT INTO wc_theorem_promotion_gates_v2 (
                  theorem_promotion_gate_id,schema_version,claim_id,claim_content_sha256,theorem_statement_sha256,
                  status_event_id,proof_witness_id,lean_compiler_witness_id,non_collapse_transition_id,
                  policy_decision_id,verifier_principal_id,allowed,rejection_reason,created_at,key_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("gate:wrong-hash", "theorem_promotion_gate/v2", "claim:proof", "0" * 64, db.theorem_hash, "status:valid", "proof:valid", "lean:valid", "nc:valid", "policy:allow", "verifier:1", 1, None, db.gate_time, "key:1"),
            ),
        )

    def test_denied_noncollapse_path_cannot_create_gate(self):
        db = self.database()
        db.insert_chain_before_gate()
        db.connection.execute(
            "INSERT INTO wc_non_collapse_transitions_v2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("nc:denied", "non_collapse_transition/v2", "claim:proof", "conjectural", "theorem", "proof_upgrade", "denied", None, "proof:valid", "policy:allow", "denied path", db.proof_time),
        )
        expect_integrity_error(
            self,
            lambda: db.connection.execute(
                """INSERT INTO wc_theorem_promotion_gates_v2 (
                  theorem_promotion_gate_id,schema_version,claim_id,claim_content_sha256,theorem_statement_sha256,
                  status_event_id,proof_witness_id,lean_compiler_witness_id,non_collapse_transition_id,
                  policy_decision_id,verifier_principal_id,allowed,rejection_reason,created_at,key_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("gate:denied", "theorem_promotion_gate/v2", "claim:proof", db.claim_hash, db.theorem_hash, "status:valid", "proof:valid", "lean:valid", "nc:denied", "policy:allow", "verifier:1", 1, None, db.gate_time, "key:1"),
            ),
        )

    def test_incomplete_statement_binding_cannot_create_gate(self):
        db = self.database()
        db.insert_chain_before_gate(hardening=False)
        expect_integrity_error(self, db.insert_gate)

    def test_tampered_canonical_payload_is_rejected(self):
        db = self.database()
        verifier_id, key_id, private = db.register_key()
        db.connection.execute(
            "INSERT INTO wc_claims_v2 VALUES (?,?,?,?,?,?,?,?,?)",
            ("claim:proof", "evidence_claim/v2", "proof_claim", '{"statement":"P"}', db.claim_hash, "theorem P", db.theorem_hash, "principal:hugh", db.base_time),
        )
        record = authority.sign_record({"schema_version": "lean_compiler_witness/v2", "lean_compiler_witness_id": "not-stored"}, private)
        expect_integrity_error(
            self,
            lambda: db.connection.execute(
                "INSERT INTO wc_authority_signature_bindings_v1 VALUES (?,?,?,?,?,?,?,?)",
                ("sigbind:bad", "authority_signature_binding/v1", "lean_compiler_witness", "not-stored", key_id, authority.signed_payload_canonical_json(record) + " ", record["signed_payload_sha256"], db.binding_time),
            ),
        )

    def test_key_lifecycle_tables_are_append_only(self):
        db = self.database()
        db.register_key()
        expect_integrity_error(self, lambda: db.connection.execute("UPDATE wc_verifier_keys_v3 SET valid_until=NULL WHERE key_id='key:1'"))
        expect_integrity_error(self, lambda: db.connection.execute("DELETE FROM wc_verifier_key_status_events_v1 WHERE key_id='key:1'"))

    def test_compiler_proof_and_gate_are_append_only(self):
        db = self.database()
        db.insert_chain_before_gate()
        db.insert_gate()
        expect_integrity_error(self, lambda: db.connection.execute("UPDATE wc_lean_compiler_witnesses_v2 SET result='failed' WHERE lean_compiler_witness_id='lean:valid'"))
        expect_integrity_error(self, lambda: db.connection.execute("DELETE FROM wc_proof_witnesses_v2 WHERE proof_witness_id='proof:valid'"))
        expect_integrity_error(self, lambda: db.connection.execute("DELETE FROM wc_theorem_promotion_gates_v2 WHERE theorem_promotion_gate_id='gate:valid'"))


if __name__ == "__main__":
    unittest.main()
