#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

import paired_candidate as pc


class PairedCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.corpus = self.root / "corpus"
        self.runtime = self.root / "runtime"
        (self.corpus / "tests").mkdir(parents=True)
        (self.runtime / "app").mkdir(parents=True)
        (self.runtime / "tests").mkdir(parents=True)
        (self.corpus / "README.md").write_text("corpus\n")
        (self.runtime / "README.md").write_text("runtime\n")
        (self.runtime / "app" / "main.py").write_text("VALUE = 1\n")
        self.policy = self.root / "policy.json"
        source = Path(__file__).with_name("paired_candidate_policy_v1.json")
        self.policy.write_text(source.read_text())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_pair_materialization_is_non_authoritative(self) -> None:
        proposal = self.root / "proposal.json"
        proposal.write_text(json.dumps({
            "schema": pc.PROPOSAL_SCHEMA,
            "changes": [{"target": "runtime", "action": "replace_text", "path": "app/main.py", "old": "VALUE = 1", "content": "VALUE = 2"}],
        }))
        out = self.root / "out"
        manifest = pc.materialize(Namespace(parent_corpus=self.corpus, parent_runtime=self.runtime, output=out, policy=self.policy, external_data=None, proposal=proposal))
        self.assertFalse(manifest["authority"]["production_eligible"])
        self.assertEqual("VALUE = 2\n", (out / "runtime-candidate/app/main.py").read_text())
        self.assertEqual("VALUE = 1\n", (self.runtime / "app/main.py").read_text())
        self.assertTrue(manifest["pair_id"].startswith("duoid:shake256-512:"))

    def test_traversal_is_rejected(self) -> None:
        policy = json.loads(self.policy.read_text())
        with self.assertRaises(ValueError):
            pc.apply_proposal({"schema": pc.PROPOSAL_SCHEMA, "changes": [{"target": "runtime", "action": "write_text", "path": "../escape", "content": "x"}]}, self.corpus, self.runtime, policy)

    def test_external_credentials_are_rejected(self) -> None:
        external = self.root / "external"
        external.mkdir()
        (external / "bad.env").write_text("API_KEY=do-not-copy\n")
        with self.assertRaises(ValueError):
            pc.snapshot_external(external, json.loads(self.policy.read_text()))

    def test_recurrent_state_is_only_proposal_evidence(self) -> None:
        one = {"corpus": pc.tree_identity(self.corpus, "P-C"), "runtime": pc.tree_identity(self.runtime, "P-R")}
        two = {"corpus": pc.tree_identity(self.corpus, "C-C"), "runtime": pc.tree_identity(self.runtime, "C-R")}
        witness = pc.recurrent_witness(one, two, {"snapshot_id": "x", "files": 0, "bytes": 0}, 0)
        self.assertFalse(witness["authority_created"])
        self.assertEqual("candidate-proposal-and-diagnostic-only", witness["role"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
