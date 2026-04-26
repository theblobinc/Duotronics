# Duotronic v1.5 Draft 2 — Closure and Next Steps

**Status:** Internal closure note  
**Version:** v1.5-draft-2-closure  
**Document kind:** Closure summary and implementation roadmap  
**Primary purpose:** Summarize what v1.5 Draft 2 accomplished, confirm what is complete, and provide a concrete implementation roadmap for the user as the next phase of work.

---

## 1. What v1.5 Draft 2 achieved

### 1.1 v1.5 (Draft 1) layer

v1.5 added the distributed cluster layer on top of the v1.4 Draft 5 trust model:

- nodes publish resources as canonical witnesses;
- task delegation is policy-gated, not metric-gated;
- DBP v2 S2 full-duplex inter-node lanes;
- Docker-native auto-federation;
- coordinator/worker heartbeat and stale invalidation;
- cluster-wide learning mode;
- `TaskOutcomeWitness` as the feedback channel for recurrent update;
- conformance fixtures for a six-machine prototype.

### 1.2 v1.5 Draft 2 layer

Draft 2 added the Witness-Gated Recurrent Cell research profile:

- `WG-RNN`: an LSTM-style recurrent cell whose persistent memory is governed by canonical witness features, not raw inputs;
- four explicit memory-control gates: write, decay, quarantine, promote;
- hard policy clamps that override any learned gate value;
- slot-based memory bank with candidate/quarantined/stable/deprecated/tombstoned states;
- `SlotPromotionRequest` governed by replay, retention diagnostics, and policy;
- `MemoryUpdateRecord` for every persistent memory change;
- `WGRNNReplayIdentity` binding all inputs deterministically;
- purge cascade behavior for memory slots;
- human review hooks for high-novelty and high-risk memory;
- eight conformance fixtures;
- a worked chronological music-preference memory example;
- a PyTorch implementation skeleton.

### 1.3 Core invariant of v1.5 Draft 2

```text
Fast recurrent state is computation.
Persistent memory authority requires witness features, replay, and policy.
```

---

## 2. What is confirmed complete

| Area | Status |
|---|---|
| v1.5 distributed cluster spec | Complete (Draft 1) |
| DBP inter-node full-duplex profile | Complete |
| Node federation protocol | Complete |
| Task delegation and resource witness contract | Complete |
| Container deployment and node lifecycle reference | Complete |
| v1.5 cluster conformance fixtures | Complete |
| WG-RNN normative contract v1.0 | Complete (Draft 2) |
| WitnessFeatureVector schema | Complete |
| MemorySlot schema | Complete |
| MemoryUpdateRecord schema | Complete |
| WitnessGatedRecurrentCellProfile schema | Complete |
| WitnessGatedRecurrentCellPolicy schema | Complete |
| WGRNNReplayIdentity schema | Complete |
| MemoryPurgeImpactRecord schema | Complete |
| SlotSplitRecord schema | Complete |
| SlotConsolidationRecord schema | Complete |
| MemorySlotPruneRecord schema | Complete |
| SlotPromotionRequest schema | Complete |
| Worked music-preference memory example | Complete |
| PyTorch implementation skeleton | Complete |
| Corpus index updated | Complete |
| Release manifest | Complete |
| Glossary updated | Complete |

---

## 3. WG-RNN promotion path

WG-RNN v1.0 is a **research profile**. It is not normative until promoted.

Promotion requirements:

1. **Fixture evidence** — all eight contract fixtures must pass on the prototype implementation;
2. **Replay traces** — at least one end-to-end memory update sequence must be deterministically reproducible;
3. **Retention diagnostics** — stability scores and slot lifetimes must be measured and pass retention thresholds;
4. **Purge cascade tests** — tombstone and demote behaviors must be tested;
5. **Contradiction tests** — `SlotSplitRecord` behavior under contradiction threshold must be validated;
6. **Human review tests** — `g_write` upper bound and `g_promote = 0` under `human_review_required` must be verified;
7. **Policy approval** — `WitnessGatedRecurrentCellPolicy` must be formally approved for target runtime mode;
8. **Family Registry handoff** — if promoted beyond research profile status.

Until promotion, the WG-RNN may only be used in:

- `audit_only` mode;
- `sandbox` mode;
- `restricted` mode with explicit policy.

---

## 4. Recommended next steps for implementation

### Step 1 — Run the PyTorch skeleton (Prototype v1)

Start with `refs/examples/duotronic_wgrnn_pytorch_skeleton_v1_0.md`.

> **Implementation-target note.** The canonical implementation target is currently undecided. See `duotronic_canonical_implementation_target_v0_1.md`. Until a target is recorded, the skeleton runs as a research prototype, not as a normative reference runtime.

Actions:

1. Copy the skeleton into a research prototype repository or working directory consistent with the canonical-target status note.
2. Run `run_prototype_v1_loop()` with the four sample events.
3. Confirm fixture behaviors A, B, C, and G from the WG-RNN contract:
   - Fixture A: valid candidate write;
   - Fixture B: write blocked by invalidation;
   - Fixture C: quarantine under high novelty / low confidence;
   - Fixture G: transport failure zeroes authority.
4. Add a simple logging layer that writes `MemoryUpdateRecord` to a file or in-memory store.

### Step 2 — Wire real witness inputs (Prototype v1 continued)

Replace the random embedding `x_t` with a real input pipeline:

1. Define an `EvidenceBundle` producer from your data source.
2. Implement a `CandidateWitness` extractor.
3. Implement a stub `canonicalize()` function.
4. Implement `WitnessFeatureVector` construction from canonicalized facts.
5. Pass real witness features into the cell.

At this point the cell is running real evidence under real gates.

### Step 3 — Add contradiction branching (Prototype v2)

1. Implement `SlotSplitRecord` logic in the memory update path.
2. Add a contradiction threshold check: if `contradiction_score > split_contradiction_threshold`, allocate a new candidate slot.
3. Test fixture E (contradiction split).
4. Implement candidate vs stable slot partition explicitly.

### Step 4 — Implement replay traces

1. Persist `MemoryUpdateRecord` to a log.
2. Implement a replay function that recomputes a step given:
   - the same input embedding;
   - the same witness feature vector;
   - the same prior memory bank state;
   - the same policy snapshot.
3. Confirm the output matches the logged record.
4. Test fixture D (promotion after stable recurrence) by constructing a `SlotPromotionRequest` with a valid `replay_trace_set_id`.

### Step 5 — Add retention diagnostics

1. Track slot stability scores over time.
2. Implement slot age and recurrence counters.
3. Implement `MemorySlotPruneRecord` for stale candidates.
4. Run retention diagnostic fixtures.

### Step 6 — Connect to v1.5 distributed cluster

When the standalone cell is working:

1. Wrap the cell step in a `DelegatedTaskRecord` payload.
2. Produce a `TaskOutcomeWitness` that includes the `MemoryUpdateRecord` refs.
3. Feed task outcomes back through the recurrent update path on the coordinator.
4. Test that cluster-delivered inputs require DBP S2 transport validation before the cell grants write authority.

### Step 7 — Add local plasticity adapters (Prototype v3, optional)

Only after Prototypes v1 and v2 are stable:

1. Implement the Hebbian-style fast-weight update rule from contract section 17.2.
2. Bound updates by `max_fast_weight_update_norm`.
3. Log every adapter update as a `MemoryUpdateRecord`.
4. Test that adapter updates are reversible on replay failure.
5. Confirm that gate threshold adaptation (`min_replay`, `max_contradiction`, etc.) is blocked.

---

## 5. What to NOT do yet

1. **Do not allow full self-rewrite of core parameters.** The WG-RNN updates memory state and optionally local adapters. It does not modify its own gate matrices through autonomous gradient descent.
2. **Do not skip the policy clamp layer.** Even if gate values look correct, the hard clamps in section 9 of the contract must execute on every step.
3. **Do not promote a slot to stable without a `SlotPromotionRequest`.** Inline stable writes are not permitted.
4. **Do not treat fast recurrent state `h_t` as a canonical fact.** `h_t` is computation, not authority.
5. **Do not bypass transport validation** when feeding inputs from the distributed cluster.

---

## 6. How v1.5 Draft 2 connects to the prior design conversation

The WG-RNN specification in this corpus directly addresses the architecture design described in the conversation:

| Conversation concept | Draft 2 implementation |
|---|---|
| Witnesses as direct gates | `WitnessFeatureVector` drives `g_write`, `g_decay`, `g_quarantine`, `g_promote` |
| Hard policy constraints on gating | Policy clamps in section 9 of the WG-RNN contract |
| Self-training without GPU backprop | Local content adaptation rule (section 17.1), fast-weight rule (section 17.2) |
| Catastrophic instability prevention | `max_content_update_norm`, policy clamps, quarantine gate, replay requirement |
| Replayability of memory updates | `MemoryUpdateRecord` and `WGRNNReplayIdentity` |
| Truth collapse prevention | No raw inputs to persistent memory; all writes require canonical witness features |
| Credit assignment | `MemoryUpdateRecord` logs why each update happened |
| Structural growth management | Slot bank with max slot limits; tombstone/prune records |
| Online self-modification safety | Three-tier memory: candidate, quarantined, stable; promotion requires external approval |
| Contradiction handling | `SlotSplitRecord`; contradiction gate; forced quarantine |

---

## 7. Summary

v1.5 Draft 2 is **documentation-complete** for its research-profile scope.

The specification is ready for:

1. Prototype v1 implementation from the PyTorch skeleton;
2. Conformance fixture testing;
3. Replay trace development;
4. Potential promotion to a sandbox or restricted normative profile after evidence review.

The user's original question — *"what if we wanted a new RNN cell that uses witnesses directly as gates and self-trains from chronological data?"* — is now fully addressed in this corpus as a concrete, bounded, governable design.
