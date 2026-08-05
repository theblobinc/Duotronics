# Duotronic Witness Contract v1.6 — Draft 5.3.1

**Status:** active development corpus; complete corrective build; **not frozen**  
**Date:** 2026-07-31  
**Canonical descriptor:** `CANONICAL_CORPUS_v1_6_draft_5_3_1.json`  
**Primary contract:** `duotronic_witness_contract_v1_6_draft_5_3_1.md`

Draft 5.3.1 is the canonical working revision of the v1.6 Witness Contract. It carries forward the complete Draft 5.2.2 corpus and replaces its self-attested proof-authority path with a server-produced, content-bound, append-only authority profile. It also integrates the positive-baseline, bijective-numeration, and recursive polygonal-cell work as an optional computation profile without claiming that zero has been removed from mathematics.

The corpus is deliberately not frozen. Strict Lean and TLC evidence is authoritative only when the declared toolchains actually run and their signed output is bound to this corpus. The included advisory checks never promote a theorem.

## Start here

1. Read `START_HERE.md`.
2. Install the locked validation dependencies with `python3 -m pip install -r requirements-validation.txt` and `npm ci`, then run `python3 executable/validators/validate_draft5_3_1_corpus.py`.
3. Read the primary contract and `CORPUS_INDEX_v1_6_draft_5_3_1.md`.
4. Apply `executable/sql/draft5_2_schema_additions.sql`, then `migration/draft5_2_2_to_draft5_3_1.sql` for a new database. Existing installations must follow `migration/draft5_2_2_to_draft5_3_1_migration_runbook.md`.
5. Treat the Draft 5.2.2 proof/compiler/gate rows as legacy evidence, never as Draft 5.3.1 authority.

## Corrective changes

- A single machine-readable descriptor now selects the active version, manifest, inventory, checksums, schema registry, validator, SQL migration, and API.
- Proof authority is bound to the canonical claim hash, theorem-statement hash, proof-artifact hash, source-tree hash, build-output digest, verifier identity, key identifier, and signature.
- The controlled reference runtime performs strict `lake build`, deterministic content hashing, Ed25519 signing, and signature verification; missing or failed toolchains produce non-passing witnesses.
- Compiler witnesses, proof witnesses, policies, status events, non-collapse transitions, and promotion gates are append-only. Corrections use explicit supersession records.
- The theorem gate enforces one claim, one policy, one compiler execution, one proof, and one relevant allowed `conjectural -> theorem` non-collapse path.
- Caller-supplied compiler conclusions, proof witnesses, and gates were removed from the canonical API. Clients request checks; the authority service emits results.
- Deep-time `pass` results require a nonempty grammar, a nonempty assumption manifest, every required assumption satisfied, and every executed instruction passed.
- The evidence-claim v2 scalar union accepts integers exactly once.
- The validator fails closed when AJV, YAML parsing, SQLite JSON1, or a required test phase is unavailable, and reports pass/fail/skipped counts.
- A real 5.2.2-to-5.3.1 database migration creates new v2 authority tables rather than pretending `CREATE TABLE IF NOT EXISTS` can harden old tables.
- Positive-baseline polygonal computation is integrated through a normative profile, schema, executable evaluator, and conformance tests.
- `LICENSE.md` now states an explicit all-rights-reserved posture pending a deliberate licensing decision.

## Historical preservation

All files from Draft 5.2.2 remain present. The exact uploaded Draft 5.2.2 ZIP is retained at `history/source_packages/v1.6 - Draft 5.2.2.zip` and its digest is recorded in the 5.3.1 inventory. Earlier manifests and reports are historical and do not select active behavior.

## Trust boundary

Checksums detect accidental or unauthorized change relative to a trusted copy; they are not an external trust root. This unfrozen package is unsigned. `refs/trust/TRUST_ROOT_POLICY_v1_0.md` defines how a future release can add an externally held signing key without rewriting the corpus.
