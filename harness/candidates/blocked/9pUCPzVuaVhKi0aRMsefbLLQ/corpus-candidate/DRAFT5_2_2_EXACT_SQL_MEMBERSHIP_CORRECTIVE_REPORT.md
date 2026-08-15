# Draft 5.2.2 Exact SQL Membership Corrective Report

This corrective pass closes the remaining 5.2.2 freeze blockers identified after the first SQL hardening pass.

## Fixed

1. `START_HERE.md` no longer contains the stale "TLA+-only formal layer" wording.
2. `START_HERE.md` now points to `executable/validators/validate_draft5_2_2_corpus.py`.
3. `PACKAGE_METADATA_v1_6_draft_5_2_2.json` now carries Draft 5.2.2 values for version, validator, and inventory.
4. `CORPUS_INDEX_v1_6_draft_5_2_2.md` has been added.
5. SQL theorem-promotion hardening now checks exact JSON witness-ID membership, not merely non-empty arrays.

## SQL rule strengthened

An allowed theorem-promotion gate now requires:

- its `proof_witness_id` to appear in the claim `proof_witness_refs_json` array;
- its `lean_compiler_witness_id` to appear in the claim `lean_compiler_witness_refs_json` array;
- its `proof_witness_id` to appear in the transition `proof_witness_refs_json` array;
- its `lean_compiler_witness_id` to appear in the transition `lean_compiler_witness_refs_json` array;
- its proof, Lean, and gate IDs to appear in the transition `required_witness_refs_json` array.

The validator includes a mismatched transaction test where the gate uses `proof:valid` / `lean:valid` while the claim and transition arrays use `proof:other` / `lean:other`; that transaction must fail.

## Still not frozen

Strict freeze still requires running `lake build` and strict TLA/TLC model checking in CI or another environment with the required toolchains installed.
