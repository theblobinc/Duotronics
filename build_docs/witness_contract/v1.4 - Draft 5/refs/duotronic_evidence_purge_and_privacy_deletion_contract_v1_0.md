# Duotronic Evidence Purge and Privacy Deletion Contract v1.0

**Status:** Source-spec baseline candidate  
**Version:** evidence-purge-privacy-deletion@v1.0  
**Document kind:** Normative purge, privacy deletion, right-to-be-forgotten, and derived-record cascade contract  
**Primary purpose:** Define how Duotronic systems permanently remove, tombstone, quarantine, or render unusable evidence and all dependent witnesses, lookup records, self-models, profile candidates, replay traces, planner records, action records, and derived artifacts when privacy, policy, legal, consent, or governance rules require stronger action than ordinary invalidation.

---

## 1. Scope

This contract covers permanent or policy-enforced deletion of:

1. raw evidence bundles;
2. source evidence records;
3. personal-history records;
4. chronological streams;
5. timeline witnesses;
6. preference, habit, and likely-action witnesses;
7. self-model snapshots;
8. lookup memory records;
9. model witnesses;
10. candidate witnesses;
11. auto-profile candidates;
12. profile synthesis records;
13. bridge results;
14. action candidate witnesses;
15. action execution records;
16. action outcome witnesses;
17. replay traces;
18. high-speed loop indexes;
19. vector, graph, time-series, and cache entries;
20. lab fixtures derived from purged evidence.

It applies when invalidation is not strong enough.

Invalidation means “do not rely on this until refreshed.”  
Purge means “remove, tombstone, or cryptographically/operationally render unusable according to policy.”

---

## 2. Central rule

> **Status tag:** normative

A purge request is stronger than invalidation.

If policy requires purge, the system must not merely mark records stale. It must identify dependent records, remove or tombstone them according to purge class, and prevent future runtime use.

```text
purge request
-> dependency discovery
-> purge authorization
-> purge execution
-> cascade to derived artifacts
-> lookup/cache invalidation
-> profile/witness demotion
-> replay impact record
-> purge completion record
```

---

## 3. Purge classes

| Purge class | Meaning | Expected behavior |
|---|---|---|
| `soft_tombstone` | keep a minimal tombstone but remove payload authority | replace payload with tombstone, block runtime use |
| `hard_delete` | remove payload and derived private records where possible | delete or irreversibly redact according to policy |
| `cryptographic_erasure` | destroy keys required to read encrypted content | remove/deauthorize key material |
| `derived_only_purge` | remove derived witnesses but retain raw source under policy | delete derived records, keep source |
| `source_only_purge` | remove source payload but preserve non-sensitive aggregate if allowed | remove source, re-evaluate aggregates |
| `legal_hold_exception` | purge requested but legal/policy hold applies | quarantine, restrict, and record hold |
| `audit_tombstone_only` | keep only proof that purge happened | retain minimal non-content tombstone |

A purge class must be declared for every purge event.

---

## 4. Evidence purge request

```yaml
EvidencePurgeRequest:
  purge_request_id: string
  requested_by:
    kind: human | policy | system | legal | privacy | actor | administrator | custom
    ref: string
  request_time: string
  target_refs: []
  target_kind: evidence_bundle | source_record | actor_scope | stream | witness | profile_candidate | lookup_record | replay_trace | action_record | custom
  purge_reason: privacy_request | consent_withdrawal | source_deletion | legal_request | policy_change | actor_scope_removal | safety | data_retention_expiry | manual | custom
  requested_purge_class: soft_tombstone | hard_delete | cryptographic_erasure | derived_only_purge | source_only_purge | audit_tombstone_only
  max_privacy_class: public | internal | restricted | sensitive | mixed
  requested_scope:
    include_raw_evidence: true | false
    include_derived_witnesses: true | false
    include_lookup_memory: true | false
    include_profile_candidates: true | false
    include_replay_traces: true | false
    include_action_records: true | false
    include_lab_fixtures: true | false
  required_policy_gate: string
  status: requested | authorized | rejected | executing | completed | partially_completed | held
```

---

## 5. Purge authorization

A purge must pass through L5 or an approved privacy/legal policy path.

```yaml
EvidencePurgeAuthorization:
  purge_authorization_id: string
  purge_request_id: string
  policy_decision_id: string
  authorized_purge_class: soft_tombstone | hard_delete | cryptographic_erasure | derived_only_purge | source_only_purge | audit_tombstone_only | legal_hold_exception
  authorization_time: string
  authority_ref: string
  constraints: []
  legal_hold_refs: []
  expiry_or_review_time: string | null
```

If a legal hold or governance exception prevents deletion, the record must be quarantined and marked unavailable for ordinary runtime use.

---

## 6. Dependency discovery

Before purge execution, the system must construct a dependency graph.

```yaml
PurgeDependencyGraph:
  purge_dependency_graph_id: string
  purge_request_id: string
  root_target_refs: []
  affected_evidence_bundle_ids: []
  affected_source_record_ids: []
  affected_personal_history_record_ids: []
  affected_stream_ids: []
  affected_witness_ids: []
  affected_self_model_snapshot_ids: []
  affected_lookup_record_ids: []
  affected_profile_candidate_ids: []
  affected_profile_registry_records: []
  affected_bridge_result_ids: []
  affected_action_record_ids: []
  affected_replay_trace_ids: []
  affected_lab_fixture_ids: []
  affected_external_index_refs: []
  unknown_dependency_notes: []
```

A purge with unknown dependencies must either:

1. proceed conservatively;
2. quarantine affected areas;
3. require human/privacy review.

---

## 7. Purge execution event

```yaml
EvidencePurgeEvent:
  purge_event_id: string
  purge_request_id: string
  purge_authorization_id: string
  purge_dependency_graph_id: string
  purge_class: soft_tombstone | hard_delete | cryptographic_erasure | derived_only_purge | source_only_purge | audit_tombstone_only | legal_hold_exception
  executed_at: string
  executed_by_node_id: string
  affected_refs: []
  successful_refs: []
  failed_refs: []
  tombstone_refs: []
  external_index_invalidations: []
  replay_impact_record_id: string
  status: completed | partially_completed | failed | held
```

---

## 8. Purge tombstone

A tombstone must not preserve sensitive content.

```yaml
PurgeTombstone:
  purge_tombstone_id: string
  original_ref_hash: string
  original_kind: string
  purge_event_id: string
  purge_class: string
  purge_time: string
  reason_class: privacy | legal | policy | retention | manual | custom
  content_removed: true
  runtime_use_allowed: false
  replay_use_allowed: false | policy_exception
```

The tombstone exists only to prevent dangling references and prove that a purge occurred.

---

## 9. Cascade behavior

> **Status tag:** normative

A purge event must cascade to derived records.

Default cascade rules:

| Source affected | Required cascade |
|---|---|
| raw evidence bundle | remove/demote dependent source records, witnesses, lookup records, replay traces |
| personal-history record | rebuild or purge timeline witnesses and self-model snapshots |
| actor scope | purge or quarantine actor-scoped streams, self-models, likely-action witnesses |
| source record | demote claim witnesses and source reliability diagnostics |
| model witness | re-evaluate candidate witnesses and profile candidates |
| profile candidate | demote or remove dependent registry records |
| lookup record | invalidate indexes and high-speed loops |
| self-model snapshot | block dependent action candidates unless policy permits replay-only use |
| action record | purge outcome witnesses and derived learning if payload-sensitive |

---

## 10. Replay impact

Purging can break replay. That is expected and must be explicit.

```yaml
PurgeReplayImpactRecord:
  replay_impact_record_id: string
  purge_event_id: string
  affected_replay_trace_ids: []
  replay_status_after_purge: replay_intact | replay_with_tombstones | replay_blocked | replay_requires_policy_exception
  allowed_replay_mode: none | audit_tombstone_only | privacy_safe_aggregate | legal_hold_only | policy_exception
  notes: string
```

If replay depends on purged content, the replay must either fail closed, use tombstones, or run only under an explicit policy exception.

---

## 11. Profile candidate and learning impact

A profile candidate derived from purged evidence must be re-evaluated.

Default behavior:

1. if purged evidence is nonessential, remove it from lineage and rerun tests;
2. if purged evidence is essential, demote profile to `audit_only`, `candidate_profile`, or `rejected_profile`;
3. if privacy requires complete removal, purge the candidate and dependent fixtures;
4. if an aggregate can remain, it must be privacy-safe and policy-approved.

No profile may hide purged evidence in its lineage.

---

## 12. Action and planner impact

If a planner action, decision context, or action outcome depends on purged evidence, the system must:

1. block replay or use tombstones;
2. mark dependent action records as purge-impacted;
3. prevent future decisions from using the purged evidence;
4. invalidate lookup records;
5. re-evaluate self-model snapshots;
6. emit policy follow-up if external actions were based on purged data.

---

## 13. Non-claims

This contract does not define jurisdiction-specific legal compliance. It defines a technical purge and cascade framework that policy/legal layers can bind to specific requirements.

---

## 14. Purge proof and external audit attestation

> **Status tag:** normative for implementations that expose purge compliance externally

Draft 5 completion adds an optional but standardized proof-of-purge layer.

A purge event proves internal execution to the Duotronic system. A purge attestation packages that evidence into a portable form suitable for internal auditors, external auditors, compliance systems, or cross-node verification.

The attestation must not reveal purged content.

### 14.1 Purge proof boundary

A purge proof may prove that:

1. a purge request existed;
2. an authorization decision existed;
3. a dependency graph was constructed;
4. a purge event ran;
5. affected records were removed, tombstoned, quarantined, or cryptographically erased according to the purge class;
6. external indexes were notified or invalidated;
7. replay impact was recorded;
8. tombstones exist without preserving content.

A purge proof must not reveal:

1. purged raw content;
2. sensitive actor identity unless policy permits;
3. private source payload;
4. derived sensitive features;
5. vector payloads or embeddings if they are within purge scope.

### 14.2 Purge attestation package

```yaml
PurgeAttestation:
  purge_attestation_id: string
  purge_event_id: string
  purge_request_hash: string
  purge_authorization_hash: string
  purge_dependency_graph_hash: string
  purge_tombstone_hashes: []
  purge_replay_impact_hash: string
  external_index_invalidation_hashes: []
  generated_at: string
  generated_by_node_id: string
  attestation_profile_id: string
  disclosure_class: internal_only | auditor_safe | external_safe | legal_hold_only | custom
  signature:
    signature_alg: string | null
    signer_ref: string | null
    signature_value: string | null
  hash_chain:
    prior_attestation_hash: string | null
    attestation_hash: string
  verification_instructions_ref: string | null
```

The `attestation_hash` must be computed over the canonical attestation payload.

### 14.3 External notarization record

External notarization is optional. If used, it must be recorded.

```yaml
ExternalPurgeNotarization:
  external_purge_notarization_id: string
  purge_attestation_id: string
  notarization_kind: transparency_log | timestamp_authority | external_audit_system | blockchain | signed_manifest | custom
  external_ref: string
  submitted_at: string
  accepted_at: string | null
  notarization_payload_hash: string
  notarization_receipt_hash: string | null
  disclosure_class: internal_only | auditor_safe | external_safe | legal_hold_only | custom
  status: submitted | accepted | rejected | unavailable | revoked
```

External notarization must not upload purged content unless policy explicitly permits and the content is not within purge scope.

### 14.4 Verification result

```yaml
PurgeAttestationVerification:
  purge_attestation_verification_id: string
  purge_attestation_id: string
  verified_by:
    kind: system | human | auditor | external_service | custom
    ref: string
  verified_at: string
  checks:
    request_hash_valid: true | false
    authorization_hash_valid: true | false
    dependency_graph_hash_valid: true | false
    tombstone_hashes_valid: true | false
    replay_impact_hash_valid: true | false
    external_index_invalidations_valid: true | false
    signature_valid: true | false | null
    notarization_valid: true | false | null
  result: verified | failed | partial | unverifiable
  notes: string
```

### 14.5 Policy statement

For internal prototypes, purge events and tombstones are sufficient.

For external compliance, regulated environments, or cross-organization audit, systems should emit `PurgeAttestation` and may emit `ExternalPurgeNotarization`.

---

## 15. Standardized external index invalidation

> **Status tag:** normative for purge-aware external indexes

External indexes include vector stores, graph stores, time-series stores, search indexes, caches, embedding stores, feature stores, analytic warehouses, and derived materialized views.

A purge cascade must communicate to these systems through a standard invalidation request and result record even if the underlying implementation API differs.

### 15.1 External index target

```yaml
ExternalIndexTarget:
  external_index_target_id: string
  index_kind: vector_store | graph_store | search_index | cache | time_series | feature_store | analytics_store | document_store | custom
  index_ref: string
  owner_node_id: string | null
  index_profile_id: string
  supports_delete: true | false
  supports_tombstone: true | false
  supports_rebuild: true | false
  supports_proof: true | false
  privacy_class: public | internal | restricted | sensitive | mixed
```

### 15.2 External index invalidation request

```yaml
ExternalIndexInvalidationRequest:
  external_index_invalidation_request_id: string
  purge_event_id: string
  target_index_ref: string
  affected_keys: []
  affected_vector_ids: []
  affected_graph_node_ids: []
  affected_graph_edge_ids: []
  affected_time_ranges: []
  affected_document_ids: []
  required_action: delete | tombstone | remove_edges | remove_vectors | rebuild_partition | expire_cache | quarantine | custom
  deadline: string | null
  requested_at: string
  requested_by_node_id: string
  policy_decision_id: string
```

### 15.3 External index invalidation result

```yaml
ExternalIndexInvalidationResult:
  external_index_invalidation_result_id: string
  external_index_invalidation_request_id: string
  target_index_ref: string
  completed_at: string | null
  status: completed | partially_completed | failed | unsupported | pending | held
  completed_actions: []
  failed_actions: []
  residual_risk:
    residual_vectors_possible: true | false | unknown
    residual_edges_possible: true | false | unknown
    stale_cache_possible: true | false | unknown
  proof_ref: string | null
  notes: string
```

### 15.4 Failure policy

If an external index cannot confirm invalidation:

1. dependent lookup records must be blocked or demoted;
2. high-speed loops using that index must stop or enter audit-only mode;
3. runtime actions depending on that index must be re-gated;
4. the purge attestation must record the partial or failed invalidation;
5. human/privacy review may be required.
