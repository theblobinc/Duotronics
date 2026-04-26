# Corpus Review: v1.5 Draft 2 Finalization

**Status:** Internal corpus review and update rationale  
**Version:** corpus-review-v1.5-draft-2-finalization  
**Document kind:** Review-to-spec integration note  
**Primary purpose:** Record the three architectural gap fixes applied to v1.5 Draft 2 based on post-review feedback: WG-RNN contract specificity, cluster scheduling operational detail, and recurrent-state vs persistent-memory contamination prevention.

---

## 1. Review summary

After the initial v1.5 Draft 2 release, three areas were identified as still reading more like an architecture proposal than a fully executable design.

This review resolves all three.

---

## 2. Gap 1 — WG-RNN contract specificity

### 2.1 What was missing

The WG-RNN contract described the concept, gates, and update rules, but did not specify:

1. what criteria make a `MemorySlot` canonical (eligible to become a `CanonicalWitnessFact`);
2. the explicit sequential ordering of purge cascade operations;
3. the precise rules guarding against contamination of the witness-governed memory path.

### 2.2 What was added

**Section 25 — MemorySlot canonicality criteria:**

A table of eight required criteria: `trust_status == stable`, independent canonical witness facts, passing replay trace, retention diagnostics, contradiction score within policy limit, purge lineage cleared, human review satisfied, and policy decision present.

Added `MemorySlotCanonicalRecord` schema with `authority_scope` field (internal / restricted / reference / normative).

Added the list of conditions that permanently block canonical status.

**Section 26 — Purge cascade ordering:**

An eleven-step explicit cascade sequence: receive event, identify affected slots, compute full vs partial purge coverage, apply required action per step, emit `MemoryPurgeImpactRecord`, block writes, process tombstone/demote/quarantine/rebuild operations, lift write blocks, emit `ClusterPurgeCascadeCompletionRecord`.

Added fraction threshold rules for partial-lineage purge (default `high_fraction_threshold: 0.60`).

Added `ClusterPurgeCascadeCompletionRecord` schema.

**Section 27 — Contamination prevention guardrails:**

Five explicit "PROHIBITED / REQUIRED" rules:

1. fast state must not become implicit truth;
2. scheduler feedback must re-enter through full evidence canonicalization;
3. memory slots must not self-confirm beliefs;
4. gate thresholds must not drift autonomously;
5. profile-learning tasks must not rewrite policy indirectly.

Added `MemoryContaminationGuardRecord` schema for policy shield to emit on rule trigger.

---

## 3. Gap 2 — Cluster scheduling operational specificity

### 3.1 What was missing

The distributed task delegation contract said "This contract does not prescribe one scheduler algorithm" but provided no reference default, left transport failure semantics undefined, left retry/timeout/downgrade behavior unspecified, and did not define cluster-wide learning mode precisely.

### 3.2 What was added

**Section 20 — Reference scheduler algorithm:**

Defines the **weighted least-load** reference selector:

```text
scheduler_score(node) =
  (1 - effective_queue_pressure)
  * effective_capacity_score
  * confidence
```

Defines capability filter (task type, hardware class, runtime mode, privacy class, learning mode).

Defines priority tiebreaking: highest priority on least-loaded node, then smallest queue, then lexicographic node ID for determinism.

Adds `TaskClassAffinityRule` and `ClusterSchedulerProfile` schemas.

**Section 21 — Transport failure semantics:**

Defines authority on transport failure: delegation, task outcome, and resource witness authority all go to zero immediately.

Defines `DelegationRetryPolicy` with max-retries, backoff, and conditions (must re-validate resource witnesses on retry).

Defines `DelegationTimeoutPolicy` with accept, execution, and outcome-report timeouts and `heartbeat_timeout_action`.

Defines downgrade rules: S2-to-S1 or S2-to-Open during active task forces `stale_blocked`, node must re-authenticate at S2 before new delegations.

Adds `NodeTransportFailureRecord` schema.

**Section 22 — Cluster-wide learning mode:**

Defines five mode values (`blocked`, `audit_only`, `sandbox`, `active`, `not_applicable`) and their meanings.

Defines `ClusterLearningModePolicy` with `node_override_allowed: false` as the required default.

Defines effective learning mode as the minimum of cluster, node, and task-requested modes.

Adds `ClusterLearningModeTransitionEvent` schema.

States that mode-downgrade must pause or cancel active `start_profile_learning` tasks, not silently continue them.

---

## 4. Gap 3 — Recurrent state vs persistent memory boundary

### 4.1 What was missing

The principle "fast recurrent state is computation; persistent memory authority requires witness features, replay, and policy" was stated but not operationally enforced with anti-drift rules.

### 4.2 What was added

**Section 27 of the WG-RNN contract** (described above) makes the guardrails explicit and machine-checkable.

**README update** added a "Contamination prevention" block listing the five rules and pointing to WG-RNN contract section 27.

**README core principle update** adds two new principle statements:
- `Transport failure zeros delegation authority immediately.`
- `Cluster-wide learning mode is enforced at delegation time, not node time.`

---

## 5. Files changed

1. `refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md` — sections 25, 26, 27, 28 added (renumbered from prior 25 non-claims)
2. `refs/duotronic_distributed_task_delegation_and_resource_witness_contract_v1_0.md` — sections 20, 21, 22 added
3. `README_v1_5_draft_2.md` — core principle block updated; implementation order updated with section references; contamination prevention block added to WG-RNN memory loop section

---

## 6. Status after finalization

v1.5 Draft 2 is now substantially more executable:

- the WG-RNN contract specifies canonicality criteria, purge cascade ordering, and contamination prevention guardrails;
- the distributed scheduling contract specifies a reference scheduler, transport failure semantics, and learning mode enforcement;
- the recurrent-state / persistent-memory boundary is protected by explicit PROHIBITED / REQUIRED rules.

The WG-RNN remains a **research profile** pending fixture evidence, replay diagnostics, and policy promotion.
