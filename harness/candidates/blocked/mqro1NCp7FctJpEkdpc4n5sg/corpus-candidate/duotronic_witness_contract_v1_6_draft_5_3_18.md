# Duotronic Witness Contract v1.6 — Draft 5.3.18

Status: mutable development contract; complete standalone corpus; production authority disabled.

## 1. Revision purpose

Draft 5.3.18 turns the twelve external activation gates into an executable, domain-separated evidence protocol. It retains the complete 5.3.17 corpus and all earlier mathematics, formal work, history, schemas, vectors, and explanatory material. Where this document conflicts with an earlier retained draft, this document governs only the 5.3.18 development workspace.

The revision incorporates lessons produced by the isolated QEMU/libvirt harness:

1. a development contract can fully activate inside a sandbox authority domain without acquiring production authority;
2. the exact first probe measurement and a later successful revalidation are different facts and must not be collapsed;
3. volatile tool output is not evidence failure when the declared stable semantic projection revalidates;
4. evidence relationships must be explicit signed objects rather than inferred graph proximity;
5. expensive signatures should be reserved for authority boundaries while content-addressed edges and Merkle checkpoints carry eligible high-volume evidence.

## 2. Non-collapse invariants

The following remain independently addressable and independently verifiable:

- semantic content;
- witness envelope;
- attestation;
- authority domain;
- trust-registry snapshot;
- original probe measurement;
- fresh revalidation measurement;
- evidence graph edge;
- gate result;
- aggregate result;
- activation record;
- chronology and supersession.

Similarity, reachability, recurrence, reservoir state, visual proximity, tensor adjacency, or model confidence never create authority. They may propose candidate relations. Only a registered deterministic rule, its declared inputs, policy, verifier witness, and valid authority-domain signatures can make an authoritative derived edge.

## 3. Authority domains

Every authority-bearing object MUST bind:

- `authority_namespace`;
- `authority_profile`;
- `evidence_environment`;
- `production_eligible`;
- `trust_registry_snapshot_id`;
- `cryptographic_suite_id`.

The `sandbox-test-only` profile MAY exercise all twelve gates and MAY produce an active activation record inside a sandbox namespace. It MUST set `production_eligible=false`. No sandbox signature, aggregate, activation record, key, namespace, registry, or evidence object can be promoted or re-labeled as production evidence.

Production activation requires a new production-domain challenge, new external measurements, production trust roots, production policy, and a distinct aggregate. Copying a passing sandbox graph is useful regression input but is not evidence.

## 4. Measurement semantics

A probe declares one stability class:

- `semantic-deterministic`: the normalized semantic projection must match on revalidation;
- `artifact-reproducible`: the declared artifact bytes and their identifiers must match;
- `execution-volatile`: timestamps, process identifiers, scheduling, temporary paths, ordering of independent diagnostics, and other declared telemetry may differ; a registered semantic predicate must still pass.

`AttestedProbeMeasurement/v1` preserves the exact original invocation, result, normalized projection, volatile-field declaration, timing, toolchain identity, environment identity, and subject identifiers.

`RevalidationMeasurement/v1` records a fresh run. It references rather than overwrites the original measurement. A verifier MUST evaluate the registered comparison policy for the stability class. It MUST NOT replace the original result digest with the fresh result digest.

This rule resolves a real harness finding: Lean, TLC, build, and reproducibility probes can produce successful fresh runs whose incidental output bytes differ. Such a run is valid only when its declared stable projection satisfies policy.

## 5. Twelve-gate evidence graph

The normative graph path is:

`contract subject → probe challenge → original measurement → external attestation → fresh revalidation → gate result → aggregate → domain activation`.

Each arrow is a typed `EvidenceGraphEdge/v1`. Required registered relations include:

- `measured_by` / `measures`;
- `attested_by` / `attests_measurement`;
- `revalidated_by` / `revalidates_measurement`;
- `satisfies_gate` / `satisfied_by`;
- `aggregated_by` / `aggregates_gate`;
- `activated_by` / `activates_domain`;
- `bound_to_registry` / `binds_evidence`.

An edge binds both endpoints, relation type, authority domain, registry snapshot, policy, chronology, and any superseded edge. Graph structure alone is never proof. An activation is valid only when all twelve distinct gate identifiers are present, verified, fresh, policy-compatible, and in the same authority domain.

## 6. Cryptographic profile and performance

The 5.3.17 post-quantum profile remains normative:

- authority identifiers: SHAKE256 with 512-bit output and framed domain separation;
- signatures: ML-DSA-87;
- key establishment: ML-KEM-1024;
- key derivation and keyed commitments: KMAC256;
- authenticated encryption: AES-256-GCM-SIV.

Duotronic mathematics does not substitute for public cryptanalysis or standard primitives. It informs positive-domain state representation, candidate traversal, visualization, scheduling, and test generation.

Eligible high-volume evidence edges MAY use SHAKE256 Merkle segments. One ML-DSA-87 checkpoint signature can bind a segment root, ordered leaf count, authority domain, registry snapshot, policy, and chronology. Individual signatures remain mandatory for release governance, trust-registry changes, key ceremonies, aggregate activation, revocation, recovery, and cross-domain operations. This contract does not claim standardized batch verification for ML-DSA.

Implementations SHOULD parallelize canonicalization, identifier calculation, independent signature verification, graph checks, and Merkle proof verification. Cached provider or public-key state must be keyed by suite and registry snapshot and invalidated on policy, registry, or key-state change.

## 7. Duotronics-derived state views

A non-authoritative `ActivationStateVector/v1` may expose the twelve gate states as a positive ordinal vector suitable for the zero-free tensor and hexagonal-grid work. It may include freshness, contradiction pressure, replay status, revalidation status, and graph completeness. This vector is a perceptual and scheduling interface only; it cannot grant authority.

The symbolic-state abstraction described in the augmented-intelligence work motivates separating the normative graph from its rendering. The dual-fluid reservoir work motivates a separate candidate/discovery channel and deterministic readout. Accordingly:

- heuristic, analog, neural, or reservoir processes may propose probes, relations, schedules, and counterexamples;
- a deterministic verifier maps those candidates into accepted or rejected evidence;
- only accepted typed objects enter the authority graph.

## 8. Activation algorithm

A conforming verifier:

1. loads the exact 5.3.18 canonical descriptor and cryptographic suite;
2. verifies the corpus manifest and schema registry;
3. verifies authority-domain and trust-registry bindings;
4. validates each original measurement and external attestation;
5. performs or verifies a fresh revalidation under the declared stability policy;
6. verifies typed graph edges and rejects cross-domain edges;
7. requires exactly the registered twelve gates with no duplicate substitution;
8. verifies freshness, revocation, chronology, policy, and checkpoint proofs;
9. creates a domain-bound aggregate;
10. signs a domain-bound activation record.

The portable development corpus always defaults to authority disabled. Sandbox activation is an external runtime event and never mutates the portable corpus into a production-authoritative artifact.

## 9. Failure rules

Fail closed on unknown schemas, relations, suites, policy identifiers, domains, registry snapshots, keys, gates, or stability classes. Reject missing external evidence, invalid signatures, stale evidence, cross-domain edges, undeclared volatile fields, graph cycles prohibited by policy, duplicate gate substitution, sandbox-to-production relabeling, and heuristic-only proof claims.

Conflicts are retained as typed objects. Supersession adds chronology; it does not erase prior evidence.

## 10. Complete-corpus rule

The complete 5.3.17 parent corpus is retained byte-for-byte at workspace creation. Draft 5.3.18 adds executable authority-domain, measurement, evidence-graph, benchmark, formal, migration, and runtime materials. Standalone validation MUST demonstrate that the inherited 1,968-file historical baseline remains present and that the current 5.3.18 manifest covers the entire workspace.

## 11. Development lifecycle

This revision is deliberately mutable. Harness results, counterexamples, performance measurements, and formal failures may change its files. Publication, production connection, and production activation are separate explicitly authorized lifecycle operations.
