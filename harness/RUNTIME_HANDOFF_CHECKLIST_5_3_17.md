# Runtime handoff checklist for Witness Contract v1.6 Draft 5.3.17

The harness is the external-activation and qualification boundary used during contract development. It never connects or activates the live runtime. Runtime work starts only after a complete signed qualification bundle exists.

## Contract-development loop

- Build the pinned sandbox image through the MCP bounded command.
- Run one gate or the complete 12-gate suite through MCP.
- Give the resulting measurement/result ID to the independently authorized attestor.
- Place the returned ML-DSA-87 evidence envelope in `harness/evidence/<gate_id>.json`.
- Rerun the same gate; evidence must bind to the current subject and measurement.
- Run all 12 gates before producing a runtime handoff bundle.
- Preserve `logs/<run-id>/aggregate-report.json`, `sandbox-report.json`, measurements, toolchain inventory, Compose definition, live inspection, and cleanup proof.
- Do not treat a probe pass, missing evidence, stale evidence, or self-issued evidence as activation.

## Current qualification blockers (2026-08-13)

The latest complete 12-gate sandbox run is `logs/20260813T021138Z-run-fc3f400e55`. The portable corpus validator, identity vectors, PQ providers, rootless controls, immutable-input/ephemeral-workspace boundary, and teardown passed. Runtime handoff remains ineligible until all of the following are resolved:

- Strict Lean: `WitnessAuthority/Verifier.lean` does not compile under pinned Lean 4.29.1 (`ToString` instances for `LMVarId`, `FVarId`, `MVarId`, `BinderInfo`, and `Literal`; invalid `levels.toList`; syntax errors near lines 111 and 125). `Duotronic/All.lean` also imports duplicate `Duotronic.HasProofWitness` declarations from `EvidenceSyntax` and `CoreMetaphysics`.
- Strict TLC: `EvidenceClaimGraph` and `ProofAuthorityV5` exceed the current 60-second per-model bound. `NonCollapseAxioms.tla` has four unresolved `p` references at line 33. `ProofAuthorityV2.tla` lacks resolvable `Append`, `Seq`, and `Len` operators.
- Reproducible inspector: both clean builds fail because the same Lean target fails; no inspector binary commitment can be produced yet.
- Committed source provenance: the repository worktree is dirty at commit `7a92ad713892f63fac280a884a4ad1959dc148ac`.
- External evidence: eight locally passing gates remain blocked pending independent, current ML-DSA-87 evidence envelopes. The failed formal/provenance gates also require passing probes before their evidence can verify.

Do not begin runtime integration merely because the harness itself is operational. First fix the contract sources/models, rerun the failed probes, obtain independent evidence, and produce an all-12 verified aggregate.

## Runtime changes required after qualification

1. Add a versioned contract-loader interface that accepts a corpus root, suite registry, schema registry, relation registry, and qualification bundle as one atomic candidate.
2. Require `runtime_handoff_eligible: true`, `authority_activated: false`, the exact 12 verified gate IDs, the image digest, corpus subject ID, and current evidence before staging.
3. Verify restricted canonical JSON, SHAKE256-512 identifiers, ML-DSA-87 signatures, ML-KEM-1024 envelopes, KMAC256 derivation, and AES-256-GCM-SIV records through an approved provider abstraction.
4. Remove Ed25519/SHA-256 write paths. Keep any legacy decoding strictly version-scoped and read-only; never silently reinterpret old identifiers as 5.3.17.
5. Introduce an algorithm/suite registry keyed by contract version so future contracts can add suites without branching throughout the runtime.
6. Implement schema negotiation and unknown-critical-field fail-closed behavior before accepting witness envelopes or meta-object edges.
7. Implement meta-object signature and edge verification with domain-separated semantic-content IDs, edge-content IDs, signer scope, epoch, and replay protection.
8. Add a trust-registry and key-status cache with explicit activation, revocation, expiry, issuer-scope, and nonexportable production-key semantics.
9. Separate candidate staging, shadow verification, governance authorization, key ceremony, activation, and rollback into distinct state transitions.
10. Add an isolated runtime adapter test mode that consumes harness fixtures but has no production database, network, key registry, or release-authority access.
11. Add mixed-version tests for legacy read-only behavior, 5.3.17 native writes, downgrade rejection, unknown critical fields, and rollback that cannot erase authority history.
12. Add encrypted persistence/recovery tests for correct restore, wrong-key rejection, tamper rejection, rollback detection, zero plaintext leakage, and log redaction.
13. Record provenance for corpus root, image digest, verifier artifact, provider build, qualification run, governance decision, and production ceremony in an append-only audit record.
14. Add metrics and structured logs for version negotiation, schema rejection, signature/KEM failures, replay rejection, evidence expiry, shadow mismatches, and rollback operations without emitting secrets.
15. Put activation behind an operator command distinct from qualification. It must require an independently approved governance decision and production key ceremony; MCP harness commands must not call it.
16. Retain the previous runtime/contract image and migration snapshot until post-activation observation and rollback drills pass.
17. Make contract adapters versioned and side-by-side loadable so 5.3.18+ can be qualified in the harness before changing the runtime default.
18. Add CI/MCP policy that rejects any runtime candidate lacking the full harness bundle and exact image/corpus commitments.

## Handoff invariant

A harness report may qualify a candidate for runtime staging. It never grants runtime, theorem, promotion, release, governance, or production-key authority by itself.
