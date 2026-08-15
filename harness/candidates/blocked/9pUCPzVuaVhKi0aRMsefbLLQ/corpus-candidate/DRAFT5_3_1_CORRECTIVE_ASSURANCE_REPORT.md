# Draft 5.3.1 Corrective Assurance Report

## Outcome

Draft 5.3.1 closes the confirmed Draft 5.2.2 executable defects at the canonical schema, SQL, API, runtime, migration, fixture, boot, and documentation layers. It remains not frozen because strict Lake, strict TLC, independent implementation review, and an external release signature are still release evidence—not conditions that can be honestly fabricated inside this build environment.

## Independent executable coverage

- All 46 JSON Schemas compile under AJV Draft 2020-12 with format validation.
- Twelve valid v2 fixtures pass, including an integer claim object.
- Nine adversarial fixtures fail, including `zero -> absence` identity collapse, proof upgrade without proof, passed compiler witness containing `sorry`, empty replay grammar/manifest, pass-with-failed-instruction, invalid parity profile, incomplete proof claim, and contradictory gate result.
- The full carried Draft 5.2 SQL plus the 5.3.1 migration applies to clean SQLite with JSON1 and foreign keys enabled.
- A complete content-bound theorem chain commits and appears in the authoritative-theorem view.
- Mismatched claim hashes, denied non-collapse paths, protected identity collapse, compiler mutation, gate deletion, failed replay instructions, and unsatisfied replay assumptions are rejected.
- Eight positive-baseline runtime tests cover bijective round trips, contraction invariance, mixed baselines, absence versus zero, parity assertions, cycle rejection, derived-codeword mismatch, and unknown operators.
- ML-DSA-87 runtime tests verify that signed authority records reject content or digest tampering and that unavailable/failed strict compilation cannot silently become `proved`.
- The exact retained Draft 5.2.2 source ZIP passes decompression and matches SHAKE256-512 `437395d28c452f0a20937eaf562020afae2214edf01a8df2fe6dadd062201c22` with 492 files.

## Assurance boundary

The SQL validates exact reference conjunctions but does not itself implement public-key cryptography. `executable/runtime/proof_authority.py` performs the content hashing, strict-build execution, ML-DSA-87 signing, and signature verification expected at the controlled service boundary. A production adapter must verify the signature before inserting v2 compiler/proof rows and must keep the private key outside the corpus.

The new Lean and TLA+ files model the strengthened conjunction and append-only state transition. Without actual toolchain execution they are reviewable formal source, not authoritative proof evidence.

## Residual freeze blockers

1. Strict `lake build` for the active Lean tree.
2. Strict TLC exploration of the active TLA+ profiles.
3. Independent review of a concrete deployed authority service and key-management boundary.
4. External signature over the final descriptor/checksum closure.
5. Governance-principal and human release approval.
6. A deliberate licensing decision if rights holders want redistribution beyond review.
