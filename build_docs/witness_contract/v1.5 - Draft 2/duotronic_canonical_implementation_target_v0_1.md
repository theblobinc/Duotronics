# Duotronic Canonical Implementation Target v0.1

**Status:** Open decision — deferred
**Version:** canonical-implementation-target@v0.1
**Document kind:** Decision-pending status note
**Primary purpose:** Make the "where does the canonical Duotronic implementation live" question explicit, list current candidate surfaces, list the criteria that will be used to choose, and stop the corpus from implying that any one repository is already the authoritative target.

---

## 1. Current status

The canonical implementation target for Duotronics is **not yet decided**.

The v1.5 Draft 2 corpus is specification-complete for its declared research and normative scope, but it does not name an authoritative runtime repository, language, build system, deployment substrate, or operator.

References in other documents to "your implementation repo," "the implementation," or "the runtime" should be read as **deferred to this document** until the decision is recorded here.

Pending the decision, all in-flight prototypes (PyTorch WG-RNN skeleton, six-machine cluster fixtures, Docker-native federation reference, etc.) are treated as **research prototypes**, not as the canonical implementation.

## 2. What "canonical implementation target" means

The canonical implementation target is the repository, runtime, and operational owner that:

1. ships the **reference runtime** for the Witness Contract, DPFC bridge boundary, lookup memory, and recurrent state;
2. owns the **conformance harness** that runs `refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md` and the WG-RNN fixtures;
3. owns the **federation reference** (DBP v2 S2 cluster lanes, `NodeHello` / `NodeAccept`, heartbeat, revocation);
4. owns the **policy shield** runtime and emits the audited `MetaDiagnostics`, `MemoryUpdateRecord`, and `TaskOutcomeWitness` records the corpus requires;
5. owns the **migration runner** and replay harness;
6. publishes versioned releases pinned to a numbered Witness Contract / DPFC / WG-RNN revision.

A research prototype that satisfies a subset of the above is a candidate, not the canonical target.

## 3. Candidate surfaces under consideration

This list is descriptive. None of these are committed.

| Surface | Current role | Could host | Risks |
|---|---|---|---|
| A new dedicated Duotronic runtime repo | none yet | reference runtime, harness, federation, shield | bootstrap cost; needs naming and ownership |
| `srnn_server` (theblobinc/srnn_server) | active augmented-intelligence runtime; already hosts witness-contract, cognition stack, federation, policy shield drafts | reference runtime, federation, policy shield | scope risk: SRNN includes music/social work that is not Duotronic; needs a clearly carved Duotronic subsystem boundary |
| `duotronic-bus-protocol` (theblobinc/duotronic-bus-protocol) | DBP transport profile and bus reference | inter-node transport reference; DBP v2 S2 lane layout | not a full runtime; only owns transport |
| `Duotronics` (theblobinc/Duotronics) | specification corpus + research workbook | specifications, fixtures, conformance assets, language-agnostic test vectors | should not become the runtime; mixing specs and runtime hurts both |
| `harness/` (top-level harness folder) | conformance harness scaffolding | conformance harness only | needs to be claimed by whichever repo owns runtime |

## 4. Open decisions that block target selection

The following must be settled before a canonical target can be named.

### 4.1 Implementation language

Candidates discussed in adjacent corpora:

- Python (current de-facto reference for SRNN cognition / WG-RNN PyTorch skeleton);
- Rust (long-term control-plane and runtime candidate, raised explicitly in SRNN handoff notes);
- a mixed stack with Python or Rust as authority and other languages as adapters (Julia for math kernels, SBCL for symbolic delegation, etc.).

This document does not pick. It records that:

- specification documents must remain implementation-language-agnostic;
- the Witness Contract portability note is binding: language migration must not change witness semantics.

### 4.2 Storage authority

The corpus assumes:

- **transactional truth**: a relational store (PostgreSQL is the leading candidate);
- **vector / semantic index**: Milvus (already used by SRNN);
- **ephemeral coordination / cache**: Redis;
- **object storage / replay artifacts**: MinIO (S3-compatible).

This is the same shape as the SRNN database migration plan but is not yet committed for Duotronics specifically.

### 4.3 Federation substrate

The v1.5 distributed addendum requires DBP v2 S2 full-duplex inter-node lanes. The substrate is unresolved:

- Docker + SSH tunnels + Redis bus (current SRNN federation pattern);
- a new dedicated DBP daemon;
- gRPC or QUIC framing inside DBP;
- ATProto / PDS as a public-facing surface, with DBP staying internal.

### 4.4 Public surface

A public surface is out of scope for v1.5 Draft 2 but will be needed before any production deployment:

- API shape (REST, gRPC, ATProto-native);
- identity and key management;
- audit log export format;
- rate-limiting and quota model.

### 4.5 Operator and ownership

A canonical implementation requires a named operator:

- who deploys it;
- who signs releases;
- who responds to a `NodeRevocation` or a `PurgeAttestation`;
- who owns the human-review escalation path defined in `refs/duotronic_human_review_and_escalation_protocol_v1_0.md`.

## 5. Decision criteria

The canonical target will be chosen by these criteria, in priority order.

1. **Specification fidelity.** Can it implement the Witness Contract, DPFC bridge boundary, WG-RNN policy clamps, and L5 shield without diluting any of them?
2. **Replay-stability.** Can it produce deterministic replay traces for `WGRNNReplayIdentity`, `MetaDiagnostics`, and cluster delegation records?
3. **Portability.** Does it preserve the language- and storage-agnostic posture the corpus requires?
4. **Federation realism.** Can it actually run a six-machine prototype matching `refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md`?
5. **Auditability.** Are policy decisions, purge cascades, human review records, and migration events first-class and queryable?
6. **Operational fit.** Does an existing operator already have ownership patterns matching the program's governance needs?
7. **Cost of carving.** How invasive is it to separate Duotronic responsibilities from any unrelated workload in the same repo?

## 6. Interim rule

Until this decision is recorded:

1. The `Duotronics` repository remains the **specification authority** and **conformance asset authority**.
2. Any prototype runs as a research prototype and must not claim normative status.
3. Cross-repo references in the corpus must use the phrase "the canonical implementation target (TBD; see `duotronic_canonical_implementation_target_v0_1.md`)" rather than naming a specific repo.
4. Conformance fixtures, schemas under `refs/schemas/`, and replay vectors must continue to live in the specification corpus so they can move with the eventual target.

## 7. How to record the decision

When the canonical target is chosen, append a section `## 8. Decision record` to this document with:

1. chosen repository and operator;
2. chosen implementation language;
3. chosen storage stack;
4. chosen federation substrate;
5. effective date;
6. version of this document at decision time;
7. a corpus review note in the same draft folder explaining the change.

Until then, this document is intentionally inconclusive and that is the correct state.
