# Duotronic Policy Shield Guide v1.8

**Status:** Source-spec baseline candidate  
**Version:** policy-shield-guide@v1.8  
**Supersedes:** policy-shield-guide@v1.7  
**Supersedes:** policy-shield-guide@v1.6  
**Supersedes:** policy-shield-guide@v1.5  
**Supersedes:** policy-shield-guide@v1.4  
**Supersedes:** policy-shield-guide@v1.3  
**Document kind:** Normative L5 policy guide plus runtime mode matrix  
**Primary purpose:** Define how L5 shields runtime operation by enforcing feasibility, bypass modes, rollback authority, source governance, model-gating rules, profile promotion boundaries, and safe degradation.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

The Policy Shield is the L5 safety authority.

It governs:

1. source and transport failures;
2. canonicalization failures;
3. lookup failures;
4. model witness risks;
5. search/social evidence risks;
6. learned profile staging;
7. ML model gating;
8. profile promotion;
9. migration;
10. rollback.

---

## 2. Hard rules

L5 must enforce:

1. normal-form-before-trust;
2. transport/source validation before semantics;
3. no silent family reinterpretation;
4. no schema promotion without migration when semantic behavior changes;
5. bypass as valid behavior;
6. failed canonicalization as a first-class state;
7. replay mismatch blocks promotion;
8. metrics require baselines before authority;
9. raw model output cannot directly control authority;
10. search/social evidence cannot directly establish truth;
11. candidate profiles default to audit-only;
12. privacy class constrains model and node routing.

---

## 3. Runtime modes

| Mode | Meaning | Lookup | Recurrence | ML gating | Promotion |
|---|---|---|---|---|---|
| `normal` | all required checks pass | allowed | allowed | allowed | allowed by policy |
| `restricted` | safe but constrained | limited | conservative | limited | limited |
| `sandbox` | experimental isolated path | sandbox only | sandbox only | sandbox only | blocked except sandbox |
| `audit_only` | observe but do not affect authority | observe | no authority | no gate authority | blocked |
| `degraded` | warning state | limited | conservative | limited | blocked or limited |
| `family_bypass` | family-sensitive path disabled | generic only | conservative | blocked if family-dependent | blocked |
| `transport_bypass` | source or transport failed | blocked for failed path | no semantic update | blocked | blocked |
| `lookup_bypass` | lookup unavailable or unsafe | disabled | allowed without lookup | limited | blocked if dependent |
| `profile_bypass` | learned profile unsafe or unapproved | disabled | no profile use | blocked | blocked |
| `full_bypass` | unsafe semantic path | blocked | blocked or minimal | blocked | blocked |

---

## 4. Decision matrix

| Condition | Default mode | Required action |
|---|---|---|
| transport integrity failed | `transport_bypass` | reject semantic decode |
| source hash missing | `transport_bypass` | block source authority |
| absence-zero collision | `full_bypass` | reject decoder/profile |
| family registry missing | `family_bypass` | generic handling only |
| normalizer timeout | `degraded` | bypass affected path |
| replay identity mismatch | `full_bypass` | block promotion and rollback |
| retention metric lacks baseline | `audit_only` | observe only |
| migration plan missing | `degraded` | block L4 promotion |
| lookup p99 over ceiling | `lookup_bypass` | disable lookup enrichment |
| model disagreement high | `audit_only` | preserve uncertainty |
| search sources conflict | `audit_only` | create contradiction witness |
| learned profile has no fixtures | `audit_only` | block runtime use |
| learned profile passes sandbox only | `sandbox` | isolate runtime path |
| privacy class blocks model route | `transport_bypass` | block outbound inference |

---

## 5. ML gating policy

Witnesses may gate machine-learning models only under policy.

Gate classes:

1. input route;
2. model selection;
3. memory retrieval;
4. prompt or task profile selection;
5. search expansion;
6. tool access;
7. profile candidate generation;
8. output confidence handling;
9. safety review.

Gate authority requires:

1. canonical witness or approved sandbox witness;
2. runtime mode permitting gate use;
3. replay record;
4. rollback path;
5. audit log.

---

## 6. Profile promotion policy

Profile promotion requires:

1. profile candidate record;
2. evidence lineage;
3. model witness lineage;
4. fixture pack;
5. replay trace set;
6. retention metrics with baselines;
7. bridge preservation report;
8. normalizer stability report;
9. migration plan if semantic behavior changes;
10. rollback plan;
11. privacy review where source data is involved;
12. L5 decision record.

---

## 7. Policy decision schema

```yaml
PolicyDecision:
  policy_decision_id: string
  target_ref: string
  target_kind: evidence | witness | profile | bridge | normalizer | migration | model_gate | source
  input_status: string
  decision: allow | audit_only | restrict | sandbox | degrade | bypass | reject | rollback | human_review
  runtime_mode: normal | restricted | sandbox | audit_only | degraded | family_bypass | transport_bypass | lookup_bypass | profile_bypass | full_bypass
  reasons: []
  required_followup: []
  rollback_ref: string | null
  policy_snapshot_id: string
```

---

## 8. Non-claims

L5 policy approval does not prove mathematical truth or external-domain truth. It grants runtime permission under declared constraints.


---

## 9. Learning mode

> **Status tag:** normative

Draft 2 adds a separate policy dimension for the auto-profile learning pipeline.

Runtime mode controls how approved or candidate objects affect operation. Learning mode controls whether the system is allowed to run the profile-learning process at all.

Allowed learning modes:

| Learning mode | Meaning | Allowed actions |
|---|---|---|
| `blocked` | no auto-profile learning | store raw evidence only if permitted |
| `audit_only` | learning may observe and create candidate records | no model/tool expansion beyond approved audit path |
| `sandbox` | learning may invoke approved models and generate candidate profiles in isolation | sandbox fixtures, no runtime authority |
| `active` | learning may continuously propose profiles under policy | still requires promotion before authority |

### 9.1 Learning policy schema

```yaml
LearningPolicy:
  learning_policy_id: string
  learning_mode: blocked | audit_only | sandbox | active
  allowed_source_types: []
  allowed_model_ids: []
  allowed_node_roles: []
  max_privacy_class: public | internal | restricted | sensitive
  outbound_model_calls_allowed: true | false
  search_expansion_allowed: true | false
  social_feed_expansion_allowed: true | false
  profile_candidate_creation_allowed: true | false
  sandbox_runtime_allowed: true | false
  requires_human_review: true | false
```

### 9.2 Learning-mode enforcement

If `learning_mode: blocked`, the system must not create new candidate profiles.

If `learning_mode: audit_only`, the system may create evidence bundles, model witnesses, candidate witnesses, and candidate profiles, but it must not allow those outputs to gate runtime models or modify lookup authority.

If `learning_mode: sandbox`, the system may run isolated learning experiments and sandbox gates.

If `learning_mode: active`, the system may continuously create and test profile candidates, but promotion still requires the Profile Synthesis Registry and L5 policy approval.

### 9.3 Policy decision extension

`PolicyDecision` records must include:

```yaml
learning_mode: blocked | audit_only | sandbox | active | not_applicable
```

when the target relates to auto-profile learning.


---

## 10. Decision action policy

> **Status tag:** normative

Draft 3 adds policy handling for internal decisions and action candidates.

Every action candidate must receive a policy decision before execution.

Action classes and default policy:

| Action class | Default mode | Notes |
|---|---|---|
| `query_memory` | restricted | allowed if privacy and runtime mode permit |
| `search` | sandbox or restricted | query and result ingestion must be logged |
| `call_model` | restricted | must satisfy privacy and model routing policy |
| `update_profile` | sandbox | promotion still requires registry/policy |
| `update_lookup` | restricted or audit_only | depends on canonicality |
| `recommend` | restricted | user-facing recommendations need source scope |
| `create_message` | blocked | external communication requires explicit approval |
| `external_api_call` | blocked | external side effects require explicit approval |
| `promote_profile` | blocked by default | requires promotion request and L5 approval |
| `demote_profile` | restricted | must update dependencies |
| `no_action` | allowed | decision-critical no-action should be logged |

### 10.1 External side-effect boundary

External side effects include:

1. posting online;
2. sending a message;
3. writing to an external file;
4. making a purchase;
5. modifying a third-party system;
6. calling a public API with side effects;
7. publishing a claim;
8. deleting or altering evidence.

External side effects require explicit policy permission.

---

## 11. Self-evidence and self-model policy

> **Status tag:** normative

Chronological self-evidence and self-model snapshots require policy controls.

A self-model policy must declare:

```yaml
SelfModelPolicy:
  self_model_policy_id: string
  allowed_stream_ids: []
  excluded_stream_ids: []
  max_privacy_class: public | internal | restricted | sensitive
  allowed_derived_witnesses: []
  allowed_runtime_modes: []
  allowed_action_classes: []
  outbound_use_allowed: true | false
  model_training_allowed: true | false
  profile_learning_allowed: true | false
  deletion_propagation_required: true
```

A self-model must not be used for external action unless the policy explicitly permits external use.

---

## 12. Oracle-risk and diversity policy

> **Status tag:** normative

When model outputs support a profile, claim, translation, action, or gate, L5 may require a model diversity set.

Minimum policy fields:

```yaml
ModelDiversityPolicy:
  model_diversity_policy_id: string
  required_for:
    - profile_promotion
    - claim_support
    - action_execution
    - translation
    - glyphic_reading
    - source_reliability
  minimum_model_count: integer
  minimum_independence_class: low | medium | high | policy_specific
  require_falsifier: true | false
  homogeneous_agreement_action: allow | down_weight | audit_only | reject
  shared_failure_action: preserve_uncertainty | require_more_evidence | reject | human_review
```

A policy may permit one model for low-risk audit-only tasks. A policy should require diversity for promotion, external action, and high-authority decisions.

---

## 13. High-speed loop policy

> **Status tag:** normative

High-speed memory/replay loops must declare:

1. loop profile;
2. source streams;
3. memory classes;
4. model calls allowed;
5. runtime mode;
6. learning mode;
7. replay requirement;
8. invalidation policy;
9. allowed actions.

A high-speed loop running many times per second may support internal reasoning, but it must not bypass policy when creating, promoting, or executing actions.


---

## 14. Policy change governance

> **Status tag:** normative

Policy changes are governed actions.

A system component may propose a policy change. It may not silently apply it.

### 14.1 PolicyChangeProposal handling

Every policy change proposal must be evaluated by L5 or a stricter configured approval workflow.

Required evaluation:

1. prior policy snapshot;
2. proposed policy snapshot;
3. authority increase or decrease classification;
4. reversibility;
5. privacy impact;
6. source impact;
7. model-routing impact;
8. external side-effect impact;
9. rollback plan;
10. conflict with existing policy.

### 14.2 Authority changes

| Change type | Default requirement |
|---|---|
| reducing authority | L5 approval or configured automatic safe-decrease rule |
| increasing learning mode | L5 approval |
| increasing runtime mode | L5 approval |
| adding new model | L5 approval if model sees restricted/sensitive data |
| adding external search source | L5 approval |
| allowing external side effects | explicit L5 approval and optional human review |
| relaxing privacy class | explicit L5 approval and human review if configured |
| changing rollback behavior | L5 approval |

### 14.3 Active policy snapshot rule

Only an approved policy snapshot is active.

A pending policy change proposal must not influence runtime unless policy explicitly allows simulation or shadow evaluation.

---

## 15. Action conflict policy

> **Status tag:** normative

When action candidates conflict:

1. the most restrictive applicable policy wins by default;
2. if restriction cannot be determined, choose `no_action`, `audit_only`, or `human_review`;
3. external side effects are blocked unless explicitly approved;
4. profile promotion is blocked until conflict is resolved;
5. policy escalation must be recorded.

The Policy Shield must emit a `PolicyDecision` for the conflict outcome.

---

## 16. Self-model invalidation policy

> **Status tag:** normative

If a self-model invalidation event affects a decision context, lookup memory record, likely-action witness, or action candidate, L5 must decide whether to:

1. continue;
2. demote to audit-only;
3. rebuild snapshot;
4. invalidate action candidate;
5. block action execution;
6. require human review.

Default behavior for stale self-models in restricted or normal runtime:

```text
block action execution until refreshed or policy accepts staleness
```

---

## 17. Resource-budget policy

> **Status tag:** normative

A high-speed loop with no resource budget may run only in `audit_only` mode.

A high-speed loop in `sandbox`, `restricted`, or `normal` mode must declare resource limits and overload policy.

Resource violations must be routed to L5 when they affect runtime actions, profile learning, lookup memory authority, or external calls.


---

## 18. Evidence purge policy

> **Status tag:** normative

L5 governs evidence purge requests unless a stricter privacy/legal governance path is configured.

Purge handling requires:

1. purge request;
2. dependency graph;
3. authorization decision;
4. purge execution event;
5. tombstones or deletion records;
6. replay impact record;
7. lookup/cache invalidation;
8. derived witness/profile/action cascade.

Default purge policy:

| Target | Default action |
|---|---|
| raw evidence with privacy purge | hard delete or cryptographic erasure if possible |
| derived witness | tombstone or remove, depending on purge class |
| lookup record | remove or demote to tombstone |
| self-model snapshot | invalidate and rebuild without purged evidence |
| profile candidate | demote, rebuild lineage, or purge |
| replay trace | block or replay with tombstones |
| action record | purge sensitive payloads and mark purge-impacted |

A purge must not leave hidden data inside model features, profile lineage, vector stores, indexes, or lab fixtures.

---

## 19. Human review policy

> **Status tag:** normative

When policy routes to human review, the system must create a `HumanReviewRequest`.

Human review is required by default for:

1. external side effects when not pre-approved;
2. policy authority increases beyond configured automatic limits;
3. ambiguous actor scope in restricted or normal runtime;
4. purge requests involving sensitive data, legal hold, or multi-party rights;
5. action conflicts where most restrictive policy cannot be determined;
6. profile promotion with unresolved major contradictions;
7. replay with purged data under policy exception.

If human review expires, high-authority actions default to no-action, reject, audit-only, or most restrictive policy.

---

## 20. Planner-triggered learning promotion override

> **Status tag:** normative

The Policy Shield must ignore or reject `promotion_requested: true` in any planner-triggered profile-learning payload.

Only the Profile Synthesis Registry may create a `ProfilePromotionRequest`.

If a planner-triggered learning run attempts to request direct promotion, L5 must:

1. override `promotion_requested` to `false`; or
2. reject the action payload; and
3. record a policy reason.

---

## 21. Cross-version replay and stale self-model policy

> **Status tag:** normative

Old decision contexts may be replayed if replay identity records:

1. self-model snapshot ID;
2. self-model version;
3. staleness state at decision time;
4. current invalidation state;
5. policy snapshot;
6. action candidate status.

Default authority:

| Replay case | Allowed use |
|---|---|
| exact historical replay with stale snapshot | audit-only |
| stale snapshot used for new action | blocked unless policy permits |
| lazy/deferred action after snapshot invalidation | must be re-gated |
| replay with purged evidence | blocked or tombstone-only unless policy exception |

---

## 22. Diversity-weighted score policy

> **Status tag:** normative

A `DiversityWeightedAgreement` score is observe-only unless calibrated.

Promotion beyond observe-only requires:

1. calibration dataset;
2. threshold definitions;
3. known failure modes;
4. model independence assessment;
5. policy-approved allowed use;
6. retention diagnostic baseline.

Uncalibrated diversity scores may support analysis, but must not directly promote profiles, execute actions, or assert truth.

---

## 23. Completion-pass purge proof policy

> **Status tag:** normative

Internal prototypes may treat `EvidencePurgeEvent` plus tombstones as sufficient proof of purge.

If a deployment requires external audit, compliance export, cross-organization verification, or regulated deletion evidence, L5 must require `PurgeAttestation`.

L5 may also require `ExternalPurgeNotarization` when:

1. policy requires externally verifiable timestamping;
2. auditors require a signed manifest;
3. cross-node deletion must be proven;
4. external index invalidation must be attested;
5. legal or compliance workflows require independent receipt.

A purge proof must not disclose purged content.

### 23.1 Purge proof decision

```yaml
PurgeProofPolicy:
  purge_proof_policy_id: string
  require_attestation_for:
    - sensitive_purge
    - external_audit
    - legal_request
    - cross_node_purge
    - external_index_invalidation
  require_notarization_for: []
  allowed_disclosure_classes:
    - internal_only
    - auditor_safe
    - external_safe
    - legal_hold_only
  signature_required: true | false
  policy_decision_id: string
```

---

## 24. Completion-pass human timeout policy

> **Status tag:** normative

Every deployment that uses human review must define or inherit a `HumanReviewTimeoutPolicy`.

If a `HumanReviewRequest` has no deadline, L5 must compute one from the global timeout policy.

If a review expires, L5 must emit or reference a `HumanReviewExpirationEvent`.

High-authority actions must fail closed if no timeout policy is available.

---

## 25. Completion-pass external index invalidation policy

> **Status tag:** normative

External indexes must be represented as `ExternalIndexTarget` records when used by purge-aware paths.

A purge affecting external indexes must emit `ExternalIndexInvalidationRequest` and record `ExternalIndexInvalidationResult`.

If an external index returns `failed`, `unsupported`, `pending` past deadline, or `partially_completed`, L5 must:

1. block dependent runtime paths; or
2. demote them to audit-only; or
3. require human/privacy review; and
4. record residual risk in purge attestation.
---

## 26. v1.5 cluster resource delegation policy

> **Status tag:** normative

v1.5 adds policy controls for resource-aware distributed task delegation.

A coordinator or distributed planner may propose delegation. L5 decides whether it is allowed.

### 26.1 Delegation policy schema

```yaml
ClusterDelegationPolicy:
  cluster_delegation_policy_id: string
  cluster_id: string
  allowed_coordinator_node_ids: []
  allowed_worker_node_ids: []
  allowed_task_types:
    - run_model_inference
    - start_profile_learning
    - execute_search
    - replay_trace
    - purge_cascade
    - resource_probe
    - custom
  allowed_privacy_classes:
    - public
    - internal
    - restricted
  require_fresh_resource_witness: true
  max_resource_staleness_seconds: 30
  require_task_queue_witness: true | false
  min_effective_capacity_score: number
  max_queue_pressure: number
  require_resource_lease: true
  overcommit_policy: reject | queue | least_loaded_node | human_review
  policy_decision_id: string
```

### 26.2 Delegation gate

A `delegate_task` action may proceed only if:

1. target node is admitted and not revoked;
2. target node DBP session uses S2;
3. resource witness is canonicalized and fresh;
4. self-model snapshot is fresh;
5. task queue witness is fresh or policy permits missing queue data;
6. target node capacity meets required resource claims;
7. node privacy permission includes the task privacy class;
8. cluster learning mode permits learning tasks;
9. local node policy does not reject the task;
10. lane layout supports the task payload and task result;
11. replay identity includes transport profile, lane layout, and direction;
12. no purge, legal hold, human review block, or policy conflict applies.

If any required check fails:

```text
delegation_authority = 0
```

### 26.3 Capacity comparison rule

For initial implementation:

```text
allowed = effective_capacity_score >= min_effective_capacity_score
```

and task-specific resources must be satisfied:

```text
cpu_available_cores >= required.cpu_cores
ram_free_bytes >= required.ram_bytes
gpu_free_bytes >= required.gpu_bytes
containers_running + required.containers <= max_containers
```

Task-specific profiles may add disk and network constraints.

---

## 27. v1.5 node admission policy

> **Status tag:** normative

Node admission is policy-gated.

```yaml
NodeAdmissionPolicy:
  node_admission_policy_id: string
  cluster_id: string
  allowed_bootstrap_modes:
    - dbp_hs1
    - psk_s2
    - mtls
  require_s2: true
  allowed_image_digests: []
  allowed_daemon_versions: []
  allowed_dbp_stack_versions: []
  allowed_node_roles:
    - worker
    - model_worker
    - search_worker
    - profile_worker
    - replay_worker
    - purge_worker
    - hybrid
  allowed_capabilities: []
  max_privacy_class_by_role:
    worker: internal
    model_worker: restricted
    search_worker: internal
    profile_worker: restricted
    replay_worker: restricted
    purge_worker: sensitive
  registry_hash_policy: exact_match | sync_allowed | sandbox_on_mismatch | reject_on_mismatch
  self_signed_identity_policy: audit_only | sandbox | restricted | reject
  policy_decision_id: string
```

A node with only self-signed identity must not receive sensitive tasks unless policy explicitly permits it.

---

## 28. v1.5 cluster-wide learning mode

> **Status tag:** normative

Cluster learning mode constrains distributed profile learning.

```yaml
ClusterLearningPolicy:
  cluster_learning_policy_id: string
  cluster_id: string
  cluster_learning_mode: blocked | audit_only | sandbox | active
  allowed_learning_nodes: []
  allowed_source_classes: []
  allowed_model_nodes: []
  allowed_privacy_classes: []
  allow_planner_triggered_learning: true | false
  max_concurrent_learning_tasks: integer
  require_human_review_for_promotion: true | false
  policy_decision_id: string
```

If cluster learning mode is lower than task requirement, delegation must be blocked.

```text
start_profile_learning requires cluster_learning_mode in {sandbox, active}
authority-bearing promotion still requires Profile Synthesis Registry
```

Planner-triggered learning remains unable to promote directly.

---

## 29. v1.5 node revocation and quarantine policy

> **Status tag:** normative

L5 may revoke or quarantine nodes.

```yaml
NodeQuarantinePolicy:
  node_quarantine_policy_id: string
  triggers:
    - s2_auth_failure
    - repeated_task_failure
    - stale_heartbeat
    - policy_violation
    - suspicious_output
    - purge_failure
    - human_review_required
  default_action: block_new_tasks | cancel_tasks | quarantine_outputs | revoke_node | human_review
  output_handling:
    allow_existing_outputs: true | false
    demote_outputs_to_audit: true | false
    require_replay: true | false
  policy_decision_id: string
```

Revoked nodes:

1. receive no new tasks;
2. cannot publish authority-bearing witnesses;
3. may have prior outputs demoted until replayed or reviewed;
4. may require purge if compromised.

---

## 30. v1.5 DBP cluster transport policy

> **Status tag:** normative

Authority-bearing inter-node traffic must use:

```yaml
transport_profile_id: dbp-cluster-full-duplex-v1
security_mode: S2
```

L5 must reject authority-bearing DBP payloads if:

1. security mode is Open or S1;
2. semantic descriptor is missing;
3. lane layout is missing or mismatched;
4. lane direction is invalid;
5. replay identity omits direction;
6. registry hash mismatch is unresolved;
7. session is revoked;
8. S2 authentication fails.

---

## 31. v1.5 resource conflict policy

> **Status tag:** normative

Task conflict resolution defaults:

| Conflict | Default resolution |
|---|---|
| privacy conflict | most restrictive policy wins |
| security conflict | reject or quarantine |
| stale resource witness | no delegation |
| overcommit CPU/RAM/GPU | least-loaded node if policy-equivalent, otherwise queue |
| duplicate task | deduplicate or no-action |
| urgent vs normal task | priority may win only if policy permits |
| purge/legal hold | block task |
| unknown conflict | no-action or human review |

If conflict resolution selects `least_loaded_node_gets_task`, nodes must be policy-equivalent for privacy, security, and task type.
