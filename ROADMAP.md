# Duotronics Program Roadmap

This roadmap tracks the **Duotronics program** (witness-runtime + distributed-systems specification stack), not any one runtime implementation.

The phases below replace earlier polygon-only "binary engine → quantum compatibility → cross-backend → hardware" framing. That framing is preserved as a **long-horizon research track** (track L) but is no longer the spine of the program.

For program scope and authority, see `build_docs/witness_contract/v1.5 - Draft 2/duotronic_program_charter_v1_0.md`. For corpus reading order, see `v1_5_draft_2_reading_guide.md`. For the implementation-target decision (currently TBD), see `duotronic_canonical_implementation_target_v0_1.md`.

---

## Status legend

- **Done** — owned document is documentation-complete for its declared scope.
- **In progress** — partial coverage, active editing or active prototyping.
- **Planned** — committed for the active corpus, not yet started.
- **Deferred** — recorded in the corpus but blocked on the canonical-target decision.

---

## Phase A — Specification finalization (active corpus)

**Goal:** Bring the v1.5 Draft 2 corpus to internal consistency and review-ready quality.

- [x] DPFC v5.15 documentation-complete.
- [x] Witness Contract v10.16 documentation-complete.
- [x] Distributed self-governing recurrent network addendum v1.5 documentation-complete.
- [x] WG-RNN contract v1.0 documentation-complete.
- [x] Auto-profile learning contract v1.3, profile synthesis registry v1.2, normalizer profiles v1.3, representation bridge contract v1.1, schema registry v1.10, family registry v1.4 documentation-complete.
- [x] Policy shield guide v1.8, evidence purge contract v1.0, human review and escalation protocol v1.0, model diversity adjudication v1.1, migration guide v1.3, retention diagnostics v1.4 documentation-complete.
- [x] Program charter v1.0, canonical-target decision note v0.1, and reading guide added.
- [ ] Source architecture overview v1.7 → v1.8 renumber (when the next material rewrite happens).
- [ ] Corpus index v1.13 → next minor revision after the next set of edits.

**Exit:** A reviewer can read `duotronic_program_charter_v1_0.md` → `v1_5_draft_2_reading_guide.md` → core three documents and arrive at an unambiguous architectural picture without consulting external context.

## Phase B — Conformance harness

**Goal:** Make the corpus testable end-to-end with deterministic, replayable fixtures.

- [x] Cluster conformance fixtures (`refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md`) documented.
- [ ] Harness skeleton committed (`harness/` already scaffolded).
- [ ] Replay harness for `MemoryUpdateRecord`, `MetaDiagnostics`, `TaskOutcomeWitness`.
- [ ] WG-RNN replay-identity vectors committed under `refs/examples/`.
- [ ] Schema-registry conformance suite (versioned IDs, compatibility checks).

**Exit:** A research-prototype implementation can run the corpus's conformance fixtures and report pass/fail per spec.

## Phase C — WG-RNN research prototype

**Goal:** A research prototype of the witness-gated recurrent cell suitable for replay-identity validation.

- [x] PyTorch skeleton (`refs/examples/duotronic_wgrnn_pytorch_skeleton_v1_0.md`) authored.
- [ ] Skeleton runs `run_prototype_v1_loop()` against committed sample events.
- [ ] Slot lifecycle (write / decay / quarantine / promote) instrumented with replay records.
- [ ] Policy clamp veto path validated against shield runtime stub.
- [ ] Replay-identity stability test against fixture vectors.

**Status note:** Prototype runs as research code only until the canonical implementation target is decided.

## Phase D — Distributed cluster prototype

**Goal:** A six-machine distributed prototype matching `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md` and `refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md`.

- [ ] DBP v2 S2 full-duplex inter-node lanes operational.
- [ ] `NodeHello` / `NodeAccept` / heartbeat / revocation cycle observed end-to-end.
- [ ] Canonical resource witnesses published and consumed.
- [ ] Policy-gated task delegation with `TaskOutcomeWitness` emission.
- [ ] Container/Docker node lifecycle validated against `refs/duotronic_container_deployment_and_node_lifecycle_reference_v1_0.md`.

**Status note:** Substrate (Docker + SSH + Redis bus vs dedicated DBP daemon vs gRPC/QUIC framing) is one of the open canonical-target decisions.

## Phase E — Canonical implementation-target decision

**Goal:** Record the canonical implementation target.

- [ ] Open decisions in `duotronic_canonical_implementation_target_v0_1.md` settled (language, storage, federation substrate, public surface, operator).
- [ ] Decision recorded as `## 8. Decision record` in that document.
- [ ] Corpus review note explaining the choice.
- [ ] Repository-level documents updated to reference the chosen target.

**Exit:** The program has a named, owned, versioned reference runtime.

## Phase F — Production-grade runtime

**Goal:** First production deployment of the canonical implementation target.

- [ ] Reference runtime ships under the chosen target with versioned releases pinned to numbered Witness Contract / DPFC / WG-RNN revisions.
- [ ] Audit log export, identity and key management, rate-limiting, and quota model committed.
- [ ] Operator response procedures (revocation, purge attestation, human-review escalation) operational.
- [ ] Migration runner deployed.

**Status note:** Phase F cannot start until Phase E is complete.

## Track L — Long-horizon research

These tracks remain on the program but are no longer the spine. Each maps to a bounded research profile and may be promoted to a normative spec only via the auto-profile learning + profile synthesis registry lifecycle.

- L1 **Polygon atomic-model workbook** — Chapters 1–23 material; informs the polygon family research profile. Source files at the repository root.
- L2 **Quantum-compatible representation surface** — historical "Phase 3" target; remains a research interest but is gated on a bounded research profile, not part of the active spine.
- L3 **Cross-backend representation portability** — historical "Phase 4" target; folded into the bridge contract and DPFC export/import policy.
- L4 **Hardware acceleration / specialized backends** — historical "Phase 5" target; deferred until at least Phase F is operational.

---

## Change management

Roadmap changes that re-order phases or move items between Phase A–F and Track L require:

1. a corpus review note in `build_docs/witness_contract/v1.5 - Draft 2/`;
2. an updated entry in this file;
3. consistency check against the program charter.

Roadmap changes that only update the status of an existing checkbox do not require a corpus review note.
