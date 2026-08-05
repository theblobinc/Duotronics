# Duotronic Witness Contract v1.6 — Draft 5.3.2

**Status:** active corrective development corpus; **not frozen**  
**Date:** 2026-07-31  
**Canonical descriptor:** `CANONICAL_CORPUS_v1_6_draft_5_3_2.json`  
**Primary contract:** `duotronic_witness_contract_v1_6_draft_5_3_2.md`

Draft 5.3.2 corrects the theorem-authority and verifier-lifecycle defects reproduced against Draft 5.3.1 while preserving the complete earlier corpus as historical material. The central change is simple but consequential: a passing build is authoritative only when Lean compiles a machine-generated target that imports the submitted artifact and checks the named theorem at the claimed type, followed by complete compiled axiom inspection.

The corpus remains deliberately not frozen. Strict Lean and TLC evidence has not been manufactured when those independently controlled toolchains are unavailable.

## Start here

1. Read `START_HERE.md`.
2. Run `python3 executable/validators/validate_draft5_3_2_corpus.py`.
3. Read the primary contract and `CORPUS_INDEX_v1_6_draft_5_3_2.md`.
4. Apply the SQL migrations in the descriptor's declared order.
5. Treat pre-5.3.2 compiler/proof/gate records as historical evidence unless they are reverified through the new exact-binding and signature path.

## Corrective changes

- Explicit compiled theorem-to-statement binding; claimed `False` cannot reuse a compiled `True` theorem.
- Comment-only theorem names cannot satisfy the generated import/type-check target.
- Lean-aware axiom inspection rejects `exact sorry`, `have := sorry`, and attributed unauthorized axioms.
- The generated module is the exact target and is included in signed build inputs.
- The compiler executable is absolute-path configured and independently hash-pinned; PATH spoofing is outside the authority path.
- Proofs outside the source tree, symlinked Lean sources, and non-importable modules fail closed.
- Verifier-key public bytes, validity windows, append-only status events, current-validity view, and effective revocation/supersession are executable SQL concepts.
- Compiler and proof signatures are checked over exact canonical payloads before a gate can be created.
- Descriptor-required phases are reconciled one-for-one with executed result identifiers; required missing/failed/skipped sets are computed.
- The active strict TLA manifest includes `ProofAuthorityV2` and the new lifecycle-aware `ProofAuthorityV3` model.
- AJV validation is self-contained through hash-covered vendored runtime dependencies.
- Fourteen proof-authority regressions and SQL lifecycle/signature adversarial tests close the reported gaps.

## Mathematical work

The positive-baseline, bijective-numeration, parity-domain, recursive polygonal-cell, and gap-aggregate work remains integrated through the mathematical profile, schemas, evaluator, and tests. It produces computational evidence and does not bypass theorem promotion.

## Historical preservation

The exact Draft 5.2.2 and Draft 5.3.1 ZIPs are retained under `history/source_packages/`. Checksums detect change relative to a trusted copy; this unsigned corpus still has no external trust root.
