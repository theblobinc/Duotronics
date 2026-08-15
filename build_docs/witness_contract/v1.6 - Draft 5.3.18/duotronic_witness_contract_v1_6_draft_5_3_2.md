# Duotronic Witness Contract v1.6 — Draft 5.3.2

**Author:** Hugh Armstrong, TBI Contracting Inc  
**Date:** July 31, 2026  
**Status:** active corrective specification; complete draft; not frozen

## 1. Scope

Draft 5.3.2 carries the complete v1.6 corpus forward and repairs the theorem-authority bindings found incomplete in Draft 5.3.1. Draft 5.2 remains the conceptual language-of-evidence foundation, and Draft 5.3.1 remains historical design evidence. Draft 5.3.2 requires a compiled theorem-to-statement check, Lean-aware axiom inspection, pinned compiler identity, effective-dated verifier keys, cryptographically verified database signature bindings, descriptor-driven phase accounting, and strict-manifest coverage of the active proof-authority TLA+ models. It retains the optional positive-baseline polygonal-computation profile.

This document is the active delta contract. Earlier documents remain necessary for definitions not superseded here.

## 2. Version and authority

`CANONICAL_CORPUS_v1_6_draft_5_3_2.json` is the only root selector for active boot artifacts. Filenames, directory names, historical manifests, or prose banners must not override it. If the descriptor is missing, malformed, hash-inconsistent, or selects unavailable artifacts, boot fails closed.

The move from 5.3.1 to 5.3.2 is a corrective draft change that hardens authority semantics and changes conformance behavior. It is not a wording-only patch.

## 3. Evidence and authority separation

The following distinctions are permanent:

- a claim is content;
- a proof artifact is evidence about a mathematical statement;
- a compiler execution is evidence that a named toolchain processed particular bytes;
- a proof witness binds the claim, theorem statement, proof artifact, compiler execution, policy, and verifier;
- a policy decision authorizes an action but does not make the claim true;
- a non-collapse transition records the permitted epistemic change;
- a promotion gate records that the required conjunction matched;
- an external signature anchors a release outside the package it signs.

No one object may self-certify the existence or validity of another.

## 4. Canonical content binding

Every proof-backed claim uses deterministic canonical JSON: UTF-8, sorted object keys, no insignificant whitespace, arrays preserved in order, and numbers restricted to the schema's canonical numeric domain. The authority service computes:

```text
claim_content_shake256_512
theorem_statement_shake256_512
proof_artifact_shake256_512
source_tree_shake256_512
generated_witness_module_shake256_512
compiler_executable_shake256_512
build_output_shake256_512
```

The compiler witness includes every listed digest, the exact generated target, proof-module import, toolchain, pinned compiler executable, command vector, compiled axiom set, result, verifier principal, key identifier, signature algorithm, and signature. A proof witness repeats the claim, theorem, artifact, verifier, and key bindings and references exactly one compiler witness. Mismatched bytes produce a different identity and cannot reuse the old gate.

The controlled verifier generates and compiles a module equivalent to:

```lean
import Submitted.Proof.Module
set_option warningAsError true
example : (<claimed theorem statement>) := by
  exact <fully qualified theorem name>
#print axioms <fully qualified theorem name>
```

The generated module is part of the hashed source tree and is the exact compiler target. A declaration name found only in a comment cannot satisfy this check. A theorem whose actual type differs from the claimed statement cannot satisfy the `example`. Source-text searches are non-authoritative: the compiled axiom report must complete successfully, must not contain `sorryAx`, and may contain only the explicitly authorized axiom set. Missing or unparsable axiom output fails closed.

## 5. Server-produced proof authority

Clients may submit a proof-check request containing claim and artifact references. They may not POST compiler conclusions, proof witnesses, non-collapse approvals, or promotion gates to canonical endpoints. The authority service performs the check in a controlled execution boundary, calculates the digests, signs the result, persists append-only records, and returns references.

An implementation must authenticate the requesting principal and the verifier principal separately. A verifier key must be active at execution and gate time, both times must fall within its validity interval, and the latest effective lifecycle event must be `active`. Revoked, retired, superseded, expired, not-yet-valid, or generically superseded principals are non-authoritative. Private material must not be supplied in an API request.

Key registration and lifecycle are append-only. Activation, revocation, retirement, and supersession are separate effective-dated events. The canonical currently-valid-verifier view evaluates the validity window, latest event, and supersession state at query time. An old gate remains in the historical log after later revocation, but it disappears from the current authoritative-theorems view.

## 6. Theorem-promotion conjunction

An allowed theorem gate exists only when all of the following refer to the same claim and policy:

1. an immutable claim with matching canonical claim and theorem-statement hashes;
2. an `allow` policy decision scoped to `theorem_promotion`;
3. a passing compiler witness whose exact generated target compiled the named theorem at the claimed statement, with warnings fatal, complete compiled axiom inspection, no `sorryAx`, and no unapproved axioms;
4. a proved proof witness with matching claim, theorem, artifact, compiler witness, policy, verifier, key, and signature binding;
5. an allowed `proof_upgrade` non-collapse transition from `conjectural` to `theorem` for that claim and proof;
6. an allowed status event from `conjecture` to `theorem` containing the same proof, compiler, non-collapse, and policy references; and
7. cryptographic verification of the exact canonical compiler-witness and proof-witness payloads against the effective ML-DSA-87 public key; and
8. the gate's own exact reference, verifier-key, validity-window, and lifecycle match.

The SQL migration enforces this conjunction at insertion. A foreign key alone is insufficient.

## 7. Immutability and correction

Claims, policies, compiler witnesses, proof witnesses, non-collapse transitions, status events, gates, verifier records, and verification results are append-only after insertion. Update and delete operations fail. A correction creates a new record and an immutable supersession edge stating the old record, replacement, reason, principal, and time. Supersession does not erase the original evidence.

## 8. Non-collapse

An identity transition between distinct protected primitive categories is invalid. In particular, the following pairs cannot be asserted as allowed identity transitions:

```text
zero / absence
unknown / invalid
empty / null
computational_evidence / theorem
conjectural / theorem
self_trained / authoritative
audit_only / active
observation / proof
explanation / fact
policy_approval / fact
```

Transitions that legitimately change epistemic or authority state must name the transition kind, claim, policy, and required external or proof witness. An allowed theorem upgrade is relevant only when it is `conjectural -> theorem`, `proof_upgrade`, and bound to the same claim, proof, and policy as the gate.

## 9. Replay non-vacuity

A verification grammar contains at least one instruction and ends with `return_status`. A deep-time assumption manifest contains at least one assumption and at least one required assumption. Every required identifier resolves to a listed assumption whose status is `satisfied` for a `pass`. A `pass` result contains a non-null manifest, at least one executed instruction, no failed/error/skipped required instruction, and a result entry for every grammar instruction.

Unknown, unverifiable, waived, or absent required assumptions yield `inconclusive`, `fail`, or `error` according to policy; never `pass`.

## 10. Positive-baseline polygonal computation

Draft 5.3.2 retains `positive-baseline-polygonal/v1` as an optional evidence-producing computation profile. Its central boundary rule is:

```text
parent_input = child_codeword - child_baseline
```

The normalized codeword `1` may represent payload zero when `tau = 1`, but the integer one is not declared equal to zero. Absence, invalidity, unknown state, and hardware failure remain separate statuses. The `even-payload-1` invariant is legal only with exact-integer construction, deserialization, child-boundary, and output assertions and with a domain-closed operator or recorded postcondition.

Computed cell results are `computational_evidence`. They do not become theorem, fact, authority, or proof without the ordinary promotion path.

## 11. Legacy generations

Draft 5.2.2 v1 schemas, SQL tables, API, fixtures, proofs, and reports remain readable for replay. They are not canonical for new writes. Existing rows are not silently upgraded because their original records lack the content and signature bindings required by v2. Migration records them as legacy-untrusted-for-promotion and requires re-verification to enter the v2 authority path.

## 12. Formal assurance claims

The Lean and TLA+ models state abstract invariants. They do not prove the runtime, SQL engine, API implementation, cryptographic library, operating system, or deployment correct. The strict TLA manifest includes both `formal/draft5_3_1/ProofAuthorityV2.tla` and `formal/draft5_3_2/ProofAuthorityV3.tla` with their configurations. Advisory static checks demonstrate manifest/configuration coverage only. Strict tool execution is release evidence only when its bytes and output are bound into a compiler or model-check witness.

## 13. Validation-phase closure

Every required validation phase has one canonical identifier in the descriptor and one result with the same identifier in the report. The validator derives `missing`, `failed`, and `skipped` sets from that descriptor. Adding a required phase without implementing and executing it therefore fails validation. Required skips are never hard-coded and never acceptable for a passing corpus report.

Vendored AJV runtime dependencies are part of the checksum closure so schema and fixture phases do not depend on an online package mirror. Their inclusion does not make Lean or TLC self-contained.

## 14. Freeze conditions

Draft 5.3.2 remains not frozen until all of the following exist:

- a successful canonical validator report with zero required skips;
- strict Lake build evidence for the active Lean tree;
- strict TLC evidence for the active TLA+ models;
- independent review of the SQL and API implementation;
- an external release signature from a configured governance principal;
- an explicit rights-holder licensing decision if distribution beyond review is intended; and
- human approval recorded under the governance contract.
