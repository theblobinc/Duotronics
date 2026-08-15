# Release Notes — Duotronic Witness Contract v1.6 Draft 5.3.2

**Date:** 2026-07-31  
**Status:** complete corrective development corpus; not frozen

Draft 5.3.2 preserves Draft 5.3.1 as an exact historical source archive and closes the reproduced theorem-authority, verifier-lifecycle, validation-accounting, and TLA-manifest defects.

## Authority corrections

- The proof runtime compiles an exact generated target that imports the submitted artifact and checks `example : <claimed statement> := <theorem name>`.
- The generated module, proof-module path, exact build target, pinned Lake executable digest, and build output are content-bound and signed.
- Plain source regexes no longer decide theorem existence or proof safety.
- Lean's compiled axiom report must complete, excludes `sorryAx`, and rejects every non-authorized axiom.
- Warnings are fatal for the exact generated target.
- Proofs outside the source root, non-importable proof modules, symlinked Lean sources, unsafe statement injection, missing compiler pins, and PATH-only compiler resolution fail closed.
- Fourteen proof-authority regression tests cover statement mismatch, comment-only names, `exact sorry`, `have := sorry`, attributed axioms, missing axiom inspection, external artifacts, exact imports, statement injection, PATH spoofing, binary-digest mismatch, payload tampering, and SQL signature verification.

## Verifier lifecycle and SQL authority

- Public verifier-key bytes are registered append-only and matched to their fingerprints.
- Activation, revocation, retirement, and supersession are effective-dated append-only events.
- `wc_currently_valid_verifiers_v3` evaluates validity windows, latest status, and principal supersession.
- Compiler and proof signatures must verify over canonical JSON that exactly matches every stored authority field.
- Gate creation requires both verified signature bindings, exact statement binding, complete axiom inspection, fatal warnings, a currently effective key, and gate/execution times within the key window.
- Expired, revoked, superseded, wrong-key, and tampered-signature cases are adversarial validation cases.
- Later key revocation removes historical gates from the current authoritative-theorem view without mutating the historical gate.

## Validator and formal-toolchain corrections

- Required phases use the exact canonical identifiers declared by the descriptor.
- Missing, failed, and skipped sets are computed from descriptor-versus-result reconciliation; `required_skipped` is derived.
- AJV and its runtime dependencies are vendored and hash-covered for offline/restricted schema validation.
- `ProofAuthorityV2.tla` and its configuration are in the active strict TLA manifest.
- A new `ProofAuthorityV3` model covers statement binding, clean axioms, verified signatures, active keys, persistent gate history, and loss of current authority after revocation/supersession.
- Strict Lake and TLC execution remain freeze blockers when their independently controlled toolchains are unavailable.

## Preserved work

The full positive-baseline, bijective-numeration, recursive polygonal-cell integration remains unchanged in authority class: its results are computational evidence until separately promoted through the proof path.

The exact Draft 5.3.1 ZIP and Draft 5.2.2 ZIP are retained under `history/source_packages/` with independently checked SHAKE256-512 digests.
