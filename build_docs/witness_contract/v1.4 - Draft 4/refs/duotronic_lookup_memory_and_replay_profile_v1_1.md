# Duotronic Lookup Memory and Replay Profile v1.1

**Status:** Source-spec baseline candidate  
**Version:** lookup-memory-and-replay-profile@v1.1  
**Supersedes:** lookup-memory-and-replay-profile@v1.0  
**Document kind:** Normative L2M lookup, high-speed memory, cache, replay, and implementation-profile contract  
**Primary purpose:** Define how Duotronic systems may use fast databases, Redis-like key-value stores, time-series indexes, graph stores, vector stores, and replay logs to support high-speed internal reasoning while preserving canonical identity, evidence lineage, demotion, deletion, policy mode, and replay boundaries.

---

## 1. Scope

This profile governs implementation choices for L2M lookup memory and replayable evidence stores.

It applies to:

1. Redis-like key-value stores;
2. embedded key-value stores;
3. SQL and document databases;
4. graph databases;
5. vector stores;
6. time-series stores;
7. event logs;
8. streaming queues;
9. replay trace stores;
10. local node caches;
11. distributed cache layers.

The contract does not require any specific storage technology. It defines the witness and authority requirements storage systems must preserve.

---

## 2. Core rule

> **Status tag:** normative

Fast memory is not authority.

A fast lookup result may influence runtime only if it points back to canonical witness facts, policy decisions, source records, replay identities, or explicitly audit-only candidates.

A cache hit without provenance must be treated as untrusted implementation detail.

---

## 3. L2M memory classes

| Memory class | Use | Authority |
|---|---|---|
| `canonical_fact_index` | retrieve canonical witness facts | authority according to fact policy |
| `audit_candidate_index` | retrieve candidate witnesses/profile candidates | audit-only |
| `timeline_index` | chronological stream query | according to timeline witness policy |
| `self_model_index` | actor/system self-model lookup | restricted by self-model policy |
| `bridge_result_index` | conversion/bridge result lookup | according to BridgeResult policy |
| `source_record_index` | source evidence lookup | evidence only |
| `contradiction_index` | contradiction retrieval | diagnostic and policy input |
| `model_witness_index` | model output lineage lookup | raw/candidate only |
| `feature_cache` | derived feature acceleration | no authority unless linked |
| `vector_similarity_index` | approximate retrieval | candidate/search only unless policy-approved |

---

## 4. Lookup record schema

```yaml
LookupMemoryRecord:
  lookup_record_id: string
  memory_class: canonical_fact_index | audit_candidate_index | timeline_index | self_model_index | bridge_result_index | source_record_index | contradiction_index | model_witness_index | feature_cache | vector_similarity_index | custom
  key: string
  value_ref: string
  value_hash: string
  canonical_fact_ref: string | null
  source_evidence_refs: []
  profile_id: string
  profile_version: string
  index_profile_id: string
  policy_decision_id: string
  runtime_mode: normal | restricted | sandbox | audit_only | degraded | bypass
  created_at: string
  expires_at: string | null
  invalidation_refs: []
```

A lookup record must never contain authority without a canonical or policy reference.

---

## 5. Redis-like implementation profile

A Redis-like key-value store may be used for high-speed lookup.

Recommended key classes:

```text
cf:<canonical_fact_id>
timeline:<stream_id>:<bucket>
selfmodel:<actor_ref>:<snapshot_id>
bridge:<bridge_result_id>
claim:<claim_hash>
source:<source_record_id>
contradiction:<claim_hash>
candidate:<candidate_id>
```

Required metadata must be available either inline or via dereference:

1. value hash;
2. profile version;
3. policy mode;
4. source or canonical fact reference;
5. invalidation version;
6. privacy class;
7. replay relevance.

Redis should not be the only source of replay truth unless configured as a durable event log with policy-approved persistence.

---

## 6. High-speed loop profiles

The system may run chronological or recurrent loops many times per second.

Loop types:

| Loop type | Purpose | Required mode |
|---|---|---|
| `audit_replay_loop` | inspect historical patterns | audit_only |
| `sandbox_simulation_loop` | simulate behavior or profile changes | sandbox |
| `restricted_decision_loop` | internal bounded decision support | restricted |
| `normal_runtime_loop` | approved production path | normal |
| `training_feature_loop` | feature generation for models | policy-specific |

A high-speed loop must declare:

```yaml
HighSpeedLoopProfile:
  loop_profile_id: string
  loop_type: audit_replay_loop | sandbox_simulation_loop | restricted_decision_loop | normal_runtime_loop | training_feature_loop
  input_memory_classes: []
  output_witness_classes: []
  max_privacy_class: public | internal | restricted | sensitive
  replay_required: true | false
  deterministic_required: true | false
  allowed_models: []
  allowed_actions: []
  invalidation_policy: string
```

---

## 7. Replay vs runtime query

The system distinguishes two modes:

### 7.1 Runtime query

A runtime query may prioritize latency. It may use indexes, caches, approximations, and recent snapshots if policy permits.

### 7.2 Replay query

A replay query prioritizes reproducibility. It must pin exact versions, inputs, source hashes, model versions, index profiles, and policy snapshots.

Runtime query output may support immediate internal action only within its policy mode. Promotion requires replay or a policy-approved replay equivalence profile.

---

## 8. Derived pattern storage

Derived patterns may be stored as witness facts.

Examples:

1. transition probability witness;
2. repeated-topic witness;
3. preference witness;
4. habit witness;
5. contradiction trend witness;
6. source reliability trend witness;
7. likely-action witness;
8. planner-state witness;
9. self-model snapshot.

Derived patterns must record:

1. source time window;
2. evidence bundle IDs;
3. extractor/profile version;
4. retention metric IDs;
5. invalidation triggers;
6. runtime mode.

---

## 9. Invalidation and demotion propagation

If a source is deleted, a profile is demoted, a bridge fails replay, a normalizer changes, or a policy mode changes, dependent lookup records must be invalidated or downgraded.

```yaml
LookupInvalidationEvent:
  invalidation_event_id: string
  trigger_kind: source_deleted | profile_demoted | bridge_failed | normalizer_changed | policy_changed | privacy_changed | replay_failed | manual
  trigger_ref: string
  affected_lookup_record_ids: []
  required_action: expire | demote_to_audit | remove | rebuild | human_review
  event_time: string
```

---

## 10. Vector and approximate retrieval

Approximate retrieval is useful but dangerous.

A vector similarity result may propose candidate witnesses, search expansions, or likely related facts. It must not be treated as canonical identity.

Any vector result used in restricted or normal runtime must point to canonical witness facts and preserve the difference between:

1. similar;
2. same;
3. supports;
4. contradicts;
5. derived from;
6. source-equivalent.

---

## 11. Non-claims

This profile does not prescribe Redis or any database. It specifies how fast memory can be used without becoming an ungoverned oracle.


---

## 12. Resource limits for high-speed loops

> **Status tag:** normative

High-speed loops must declare resource budgets.

A loop that runs many times per second can starve other processes, amplify stale memory, or create runaway model calls. Resource controls are therefore part of the profile, not merely deployment configuration.

Updated `HighSpeedLoopProfile` resource fields:

```yaml
HighSpeedLoopProfile:
  loop_profile_id: string
  loop_type: audit_replay_loop | sandbox_simulation_loop | restricted_decision_loop | normal_runtime_loop | training_feature_loop
  input_memory_classes: []
  output_witness_classes: []
  max_privacy_class: public | internal | restricted | sensitive
  replay_required: true | false
  deterministic_required: true | false
  allowed_models: []
  allowed_actions: []
  invalidation_policy: string

  resource_budget:
    max_cpu_percent: number | null
    max_memory_bytes: integer | null
    max_storage_bytes: integer | null
    max_network_bytes_per_minute: integer | null
    max_concurrent_loops: integer | null
    max_iterations_per_second: number | null
    max_model_calls_per_minute: integer | null
    max_search_calls_per_minute: integer | null
    max_runtime_seconds: number | null

  overload_policy:
    on_cpu_exceeded: throttle | pause | degrade | stop | policy_review
    on_memory_exceeded: throttle | pause | degrade | stop | policy_review
    on_model_call_exceeded: pause | degrade | stop | policy_review
    on_search_call_exceeded: pause | degrade | stop | policy_review
```

### 12.1 Resource violation event

```yaml
LoopResourceViolationEvent:
  loop_resource_violation_event_id: string
  loop_profile_id: string
  violation_kind: cpu | memory | storage | network | concurrency | iterations | model_calls | search_calls | runtime | custom
  observed_value: number
  limit_value: number
  event_time: string
  required_action: throttle | pause | degrade | stop | policy_review
```

A resource violation must not be silently ignored if the loop influences runtime decisions, lookup memory, profile learning, or action candidates.
