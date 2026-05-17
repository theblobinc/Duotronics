# Corpus Review: v1.5 Draft to v1.5 Draft 2

**Status:** Internal corpus review and update rationale  
**Version:** corpus-review-v1.5-draft-to-v1.5-draft-2  
**Document kind:** Review-to-spec integration note  
**Primary purpose:** Record the addition of the Witness-Gated Recurrent Cell research profile to the v1.5 distributed Duotronic corpus, and the subsequent strengthening pass that added chronological self-training specification, architectural guardrails, reference scheduler algorithm, and recurrent-memory boundary rules.

---

## 1. Review driver

v1.5 added distributed cluster operation: resource witnesses, DBP inter-node profiles, node federation, and task delegation.

Draft 2 adds the next recurrent-memory layer:

```text
Witness-Gated Recurrent Cell
```

The WG-RNN uses canonical witness features as memory-control signals.

---

## 2. New source spec

Added:

```text
refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md
```

---

## 3. Core addition

WG-RNN separates:

1. fast recurrent computation;
2. persistent witness memory;
3. witness-derived gates;
4. hard policy clamps;
5. replayable memory updates;
6. slot promotion;
7. purge-aware memory cascade.

---

## 4. New rule

```text
Fast recurrent state is computation.
Persistent memory authority requires witness features, replay, and policy.
```

---

## 5. Research status

WG-RNN v1.0 is a research profile.

Promotion to normative behavior requires fixture evidence, replay traces, retention diagnostics, purge tests, contradiction tests, and policy approval.

---

## 6. Strengthening pass: new sections added

The following sections were added to strengthen the v1.5 Draft 2 specification.

### 6.1 WG-RNN contract additions

**Section 26: Chronological self-training specification** (new)

Added to `refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md`.

Specifies:

1. what "self-training" means in WG-RNN terms;
2. the step-by-step chronological stream training loop;
3. a comparison table distinguishing WG-RNN self-training from GPU-based training;
4. what the cell may update autonomously per step;
5. what the cell must not update autonomously;
6. chronological ordering requirements and out-of-order evidence policy.

This section directly answers the design question: "What would it look like for the WG-RNN to train itself from chronological data without GPU backpropagation?"

**Section 27: Architectural barriers against unbounded self-modification** (new)

Added to `refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md`.

Provides an explicit barrier table and normative rules addressing: "What stops the cell from continuously writing to its own memory without limit?"

Barriers documented:

1. write gate requires witness features;
2. policy clamps override all gate values;
3. gate threshold lock (section 27.3);
4. authority ceiling formula;
5. rate limits;
6. stable write requires external promotion;
7. contradiction and novelty quarantine;
8. human review blocks promotion;
9. purge blocks conflicting writes;
10. fast state authority boundary (section 27.4);
11. self-confirmation prohibition (section 27.2);
12. scheduler feedback isolation (section 27.5).

### 6.2 Distributed task delegation contract additions

**Section 20: Reference scheduling algorithm** (new)

Added to `refs/duotronic_distributed_task_delegation_and_resource_witness_contract_v1_0.md`.

Defines the capability-filtered least-loaded-first reference strategy:

1. eligible node set construction (ten admission criteria);
2. combined score formula with reference weights;
3. GPU-required task handling;
4. action candidate emission with evidence basis;
5. freshness requirement enforcement;
6. cluster-wide learning mode semantics table;
7. conflict resolution precedence table.

**Section 21: Scheduler retry, timeout, and downgrade semantics** (new)

Added to `refs/duotronic_distributed_task_delegation_and_resource_witness_contract_v1_0.md`.

Covers:

1. transport failure retry with exponential backoff;
2. lease timeout and heartbeat failure handling;
3. node downgrade and revocation thresholds;
4. resource normalization formulas and reference defaults;
5. node identity and authentication implementation expectations.

### 6.3 Addendum addition

**Section 9: Recurrent-memory guardrails** (new)

Added to `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md`.

Provides explicit normative rules for the distributed cluster:

1. fast recurrent state is computation only;
2. persistent memory cannot self-confirm;
3. scheduler feedback must not contaminate evidence quality;
4. task outcomes cannot rewrite policy autonomously;
5. cluster-wide state synchronization boundary.

---

## 7. What was not changed

1. The WG-RNN research profile status is unchanged. It remains research-only until promoted.
2. The v1.4/v1.5 trust model is unchanged: evidence before witness, canonicalization before authority, policy before runtime use.
3. No existing sections were removed or weakened.
4. Existing gate equations, memory update record schema, promotion request schema, and purge cascade rules are unchanged.
