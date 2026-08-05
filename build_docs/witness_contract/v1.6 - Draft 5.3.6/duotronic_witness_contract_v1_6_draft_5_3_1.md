# Duotronic Witness Contract v1.6 — Draft 5.3.1

**Author:** Hugh Armstrong, TBI Contracting Inc  
**Date:** July 31, 2026  
**Status:** active corrective specification; complete draft; not frozen

## 1. Scope

Draft 5.3.1 carries the complete v1.6 corpus forward and changes the canonical assurance path. Draft 5.2 remains the conceptual language-of-evidence foundation. Draft 5.3.1 makes its strongest executable claims non-self-attesting, append-only, content-bound, and testable. It also introduces an optional positive-baseline polygonal-computation profile.

This document is the active delta contract. Earlier documents remain necessary for definitions not superseded here.

## 2. Version and authority

`CANONICAL_CORPUS_v1_6_draft_5_3_1.json` is the only root selector for active boot artifacts. Filenames, directory names, historical manifests, or prose banners must not override it. If the descriptor is missing, malformed, hash-inconsistent, or selects unavailable artifacts, boot fails closed.

The move from 5.2.2 to 5.3.1 is a minor draft change under the corpus governance rule because it adds object generations and changes conformance behavior. It is not a wording-only patch.

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
claim_content_sha256
theorem_statement_sha256
proof_artifact_sha256
source_tree_sha256
build_output_sha256
```

The compiler witness includes all five relevant digests, the exact toolchain, command vector, result, verifier principal, key identifier, signature algorithm, and signature. A proof witness repeats the claim, theorem, and artifact digests and references exactly one compiler witness. Mismatched bytes produce a different identity and cannot reuse the old gate.

## 5. Server-produced proof authority

Clients may submit a proof-check request containing claim and artifact references. They may not POST compiler conclusions, proof witnesses, non-collapse approvals, or promotion gates to canonical endpoints. The authority service performs the check in a controlled execution boundary, calculates the digests, signs the result, persists append-only records, and returns references.

An implementation must authenticate the requesting principal and the verifier principal separately. A verifier key must be active at execution time and its private material must not be supplied in an API request.

## 6. Theorem-promotion conjunction

An allowed theorem gate exists only when all of the following refer to the same claim and policy:

1. an immutable claim with matching canonical claim and theorem-statement hashes;
2. an `allow` policy decision scoped to `theorem_promotion`;
3. a passing compiler witness with no `sorry`, no `admit`, and no unapproved axioms;
4. a proved proof witness with matching claim, theorem, artifact, compiler witness, policy, verifier, and signature binding;
5. an allowed `proof_upgrade` non-collapse transition from `conjectural` to `theorem` for that claim and proof;
6. an allowed status event from `conjecture` to `theorem` containing the same proof, compiler, non-collapse, and policy references; and
7. the gate's own exact reference match.

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

Draft 5.3.1 recognizes `positive-baseline-polygonal/v1` as an optional evidence-producing computation profile. Its central boundary rule is:

```text
parent_input = child_codeword - child_baseline
```

The normalized codeword `1` may represent payload zero when `tau = 1`, but the integer one is not declared equal to zero. Absence, invalidity, unknown state, and hardware failure remain separate statuses. The `even-payload-1` invariant is legal only with exact-integer construction, deserialization, child-boundary, and output assertions and with a domain-closed operator or recorded postcondition.

Computed cell results are `computational_evidence`. They do not become theorem, fact, authority, or proof without the ordinary promotion path.

## 11. Legacy generations

Draft 5.2.2 v1 schemas, SQL tables, API, fixtures, proofs, and reports remain readable for replay. They are not canonical for new writes. Existing rows are not silently upgraded because their original records lack the content and signature bindings required by v2. Migration records them as legacy-untrusted-for-promotion and requires re-verification to enter the v2 authority path.

## 12. Formal assurance claims

The Lean and TLA+ models state abstract invariants. They do not prove the runtime, SQL engine, API implementation, cryptographic library, operating system, or deployment correct. Advisory static scans demonstrate only that the scanned source lacks selected forbidden markers. Strict tool execution is release evidence only when its bytes and output are bound into a compiler or model-check witness.

## 13. Freeze conditions

Draft 5.3.1 remains not frozen until all of the following exist:

- a successful canonical validator report with zero required skips;
- strict Lake build evidence for the active Lean tree;
- strict TLC evidence for the active TLA+ models;
- independent review of the SQL and API implementation;
- an external release signature from a configured governance principal;
- an explicit rights-holder licensing decision if distribution beyond review is intended; and
- human approval recorded under the governance contract.
