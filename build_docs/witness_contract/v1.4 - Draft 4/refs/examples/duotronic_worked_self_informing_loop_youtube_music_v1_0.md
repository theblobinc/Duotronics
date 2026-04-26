# Worked Example: Self-Informing YouTube Music Loop v1.0

**Status:** Reference implementation trace  
**Version:** worked-self-informing-youtube-music@v1.0  
**Document kind:** Worked example and implementation trace  
**Primary purpose:** Show an end-to-end Duotronic self-informing loop in concrete terms: ingest a chronological media stream, derive preference witnesses, create a decision context, let a planner propose a search action, policy-gate the action, execute it, record outcomes, and update lookup memory without treating raw personal history, model output, or search results as truth.

---

## 1. Scenario

A Duotronic instance is allowed to use a private, restricted YouTube-like watch-history export for internal decision support.

Goal:

```text
Find new songs the actor is likely to enjoy based on recent chronological listening behavior,
without posting externally, modifying accounts, or treating a model prediction as truth.
```

The loop is internal and restricted. It may search. It may not subscribe, like, comment, post, or update external accounts.

---

## 2. Policies in force

```yaml
LearningPolicy:
  learning_policy_id: lp-youtube-music-restricted-001
  learning_mode: sandbox
  allowed_source_types:
    - personal_history
    - youtube_like_media_history
    - search_result
  allowed_model_ids:
    - topic-model-local-v1
    - llm-general-lowtemp-v1
    - rule-based-genre-parser-v1
  max_privacy_class: restricted
  outbound_model_calls_allowed: false
  search_expansion_allowed: true
  social_feed_expansion_allowed: false
  profile_candidate_creation_allowed: true
  sandbox_runtime_allowed: true
  requires_human_review: false
```

```yaml
SelfModelPolicy:
  self_model_policy_id: smp-actor-music-internal-001
  allowed_stream_ids:
    - ces-youtube-watch-history-2026-04
  excluded_stream_ids: []
  max_privacy_class: restricted
  allowed_derived_witnesses:
    - PreferenceWitness
    - HabitWitness
    - LikelyActionWitness
  allowed_runtime_modes:
    - audit_only
    - sandbox
    - restricted
  allowed_action_classes:
    - query_memory
    - search
    - call_model
    - recommend
  outbound_use_allowed: false
  model_training_allowed: false
  profile_learning_allowed: true
  deletion_propagation_required: true
```

```yaml
ModelDiversityPolicy:
  model_diversity_policy_id: mdp-music-preference-001
  required_for:
    - action_execution
    - claim_support
    - profile_promotion
  minimum_model_count: 2
  minimum_independence_class: medium
  require_falsifier: true
  homogeneous_agreement_action: down_weight
  shared_failure_action: preserve_uncertainty
```

---

## 3. Step 1: Ingest chronological evidence

Raw source: exported watch-history items.

Each raw item becomes an `EvidenceBundle`.

```yaml
EvidenceBundle:
  evidence_id: eb-yt-0001
  source_type: social_feed
  source_system: youtube_like_export
  source_ref: watch-history:item:0001
  capture_time: 2026-04-26T10:00:00-07:00
  capture_node_id: node-intake-local-01
  raw_payload_hash: sha256:...
  payload_mime_type: application/json
  payload_size: 2048
  modality: mixed
  transport_status: valid
  source_integrity:
    content_hash: sha256:...
    metadata_hash: sha256:...
    connector_version: youtube-history-importer@0.1.0
    retrieval_policy: local_file_import_restricted
  provenance:
    author_or_origin: actor:self
    platform_account_hash: actorhash:...
    thread_or_context_hash: null
    parent_evidence_ids: []
  privacy_class: restricted
  trust_status: raw
```

The evidence is then wrapped as a personal-history source record.

```yaml
PersonalHistorySourceRecord:
  personal_history_record_id: phsr-yt-0001
  evidence_bundle_id: eb-yt-0001
  actor_ref: actor:self:hashed
  actor_ref_policy: hashed
  platform: youtube
  event_type: watch
  source_event_time: 2026-04-20T21:13:42-07:00
  capture_time: 2026-04-26T10:00:00-07:00
  parent_record_ids: []
  content_hash: sha256:...
  metadata_hash: sha256:...
  context_hash: sha256:...
  privacy_class: restricted
  evidence_status: candidate
```

---

## 4. Step 2: Build the chronological stream

```yaml
ChronologicalEvidenceStream:
  stream_id: ces-youtube-watch-history-2026-04
  stream_owner_ref: actor:self:hashed
  owner_kind: person
  stream_kind: media_history
  privacy_class: restricted
  ordering_policy:
    primary_time_field: source_created_time
    tie_breaker: ingestion_order
    clock_uncertainty_policy: preserve
  evidence_bundle_ids:
    - eb-yt-0001
    - eb-yt-0002
    - eb-yt-0003
  parent_stream_ids: []
  derived_stream_ids: []
  status: indexed
```

The timeline node emits a timeline witness.

```yaml
TimelineWitness:
  timeline_witness_id: tw-youtube-music-2026-04
  stream_id: ces-youtube-watch-history-2026-04
  profile_id: timeline-youtube-media-history@0.1.0
  ordering_policy_id: source_event_time_then_ingestion_order@0.1.0
  canonical_event_refs:
    - phsr-yt-0001
    - phsr-yt-0002
    - phsr-yt-0003
  event_count: 100
  time_range:
    start: 2026-04-01T00:00:00-07:00
    end: 2026-04-26T10:00:00-07:00
  gaps:
    known_gaps: []
    unknown_gap_policy: preserve
  canonical_identity_hash: sha256:...
  trust_status: canonicalized
```

---

## 5. Step 3: Run diverse model witnesses

Three systems inspect the timeline:

1. local topic model;
2. general LLM at low temperature;
3. rule-based genre parser.

Each emits a `ModelWitness`.

```yaml
ModelWitness:
  model_witness_id: mw-topic-0001
  model_id: topic-model-local-v1
  model_version: 1.0.0
  node_id: node-model-local-01
  input_evidence_ids:
    - eb-yt-0001
    - eb-yt-0002
  inference_profile_id: music-topic-inference@0.1.0
  output_hash: sha256:...
  proposed_segments:
    - synthwave
    - ambient electronic
  proposed_symbols: []
  proposed_relations:
    - repeated_genre_cluster
  proposed_claims:
    - actor_recently_watches_synthwave_like_music
  confidence:
    scalar: 0.74
    calibration_profile: topic-calibration@0.1.0
    confidence_kind: calibrated
  known_failure_modes:
    - overweights_recent_items
  trust_status: raw_model_output
```

The model diversity layer records independence and overlap.

```yaml
ModelDiversitySet:
  model_diversity_set_id: mds-music-preference-001
  purpose: action_planning
  model_refs:
    - topic-model-local-v1
    - llm-general-lowtemp-v1
    - rule-based-genre-parser-v1
  diversity_dimensions:
    - architecture
    - rule_based
    - modality
  minimum_independence_requirement: medium
  failure_policy: preserve_uncertainty
```

---

## 6. Step 4: Adjudicate model outputs

```yaml
ModelAdjudicationRecord:
  adjudication_id: mar-music-pref-0001
  target_ref: tw-youtube-music-2026-04
  model_witness_ids:
    - mw-topic-0001
    - mw-llm-0001
    - mw-rules-0001
  model_diversity_set_id: mds-music-preference-001
  agreement_summary:
    agreeing_models:
      - topic-model-local-v1
      - llm-general-lowtemp-v1
    disagreeing_models:
      - rule-based-genre-parser-v1
    agreement_fields:
      - synthwave_cluster
      - instrumental_electronic_cluster
    disagreement_fields:
      - vaporwave_vs_synthwave_label
  independence_assessment:
    likely_independent: true
    training_overlap_notes:
      - llm and topic model may share general web vocabulary
    architecture_overlap_notes:
      - rule-based parser is non-ML
  contradiction_refs: []
  uncertainty_refs:
    - genre_label_boundary_uncertain
  decision:
    action: accept_for_scope
    authority_scope: action_support
  policy_decision_id: pd-adjudication-music-001
```

The result is not truth. It is adequate support for an internal search action under restricted policy.

---

## 7. Step 5: Derive preference witness

```yaml
PreferenceWitness:
  preference_witness_id: pref-synthwave-2026-04
  stream_id: ces-youtube-watch-history-2026-04
  target_actor_ref: actor:self:hashed
  preference_domain: music
  inferred_preference: synthwave / instrumental electronic cluster
  supporting_evidence_ids:
    - eb-yt-0001
    - eb-yt-0002
    - eb-yt-0007
  contradicting_evidence_ids:
    - eb-yt-0019
  time_scope: 2026-04
  stability_diagnostic: recent_cluster_moderate_stability
  confidence: 0.71
  truth_status: supported
  runtime_mode: restricted
```

---

## 8. Step 6: Store in lookup memory

```yaml
LookupMemoryRecord:
  lookup_record_id: lmr-pref-synthwave-2026-04
  memory_class: self_model_index
  key: actor:self:hashed:music:preference:2026-04
  value_ref: pref-synthwave-2026-04
  value_hash: sha256:...
  canonical_fact_ref: cwf-pref-synthwave-2026-04
  source_evidence_refs:
    - eb-yt-0001
    - eb-yt-0002
  profile_id: preference-witness@0.1.0
  profile_version: 0.1.0
  index_profile_id: redis-like-kv-index@0.1.0
  policy_decision_id: pd-lookup-pref-001
  runtime_mode: restricted
  created_at: 2026-04-26T10:01:00-07:00
  expires_at: 2026-05-26T10:01:00-07:00
  invalidation_refs: []
```

This lookup record may be queried quickly. Its authority still comes from the witness and policy chain.

---

## 9. Step 7: Create a self-model snapshot

```yaml
SelfModelSnapshot:
  self_model_snapshot_id: sms-music-self-2026-04-26
  stream_ids:
    - ces-youtube-watch-history-2026-04
  actor_ref: actor:self:hashed
  snapshot_time: 2026-04-26T10:02:00-07:00
  version: 1
  prior_snapshot_id: null
  included_witness_classes:
    - PreferenceWitness
    - HabitWitness
  canonical_fact_refs:
    - cwf-pref-synthwave-2026-04
  audit_only_fact_refs:
    - cwf-genre-boundary-uncertain-001
  policy_decision_id: pd-selfmodel-music-001
  runtime_mode: restricted
```

The snapshot is actor-scoped. It models only the actor referenced by `actor_ref`.

---

## 10. Step 8: Build a decision context

Goal: search for new songs likely to fit the actor’s current preference.

```yaml
DecisionContext:
  decision_context_id: dc-find-new-songs-001
  objective_ref: objective-find-new-music-internal
  actor_ref: actor:self:hashed
  decision_scope: internal_only
  input_canonical_fact_refs:
    - cwf-pref-synthwave-2026-04
  input_audit_fact_refs:
    - cwf-genre-boundary-uncertain-001
  input_self_model_snapshot_refs:
    - sms-music-self-2026-04-26
  input_lookup_query_refs:
    - lq-music-pref-001
  input_model_witness_refs:
    - mw-topic-0001
    - mw-llm-0001
    - mw-rules-0001
  uncertainty_refs:
    - genre_label_boundary_uncertain
  contradiction_refs: []
  privacy_class: restricted
  runtime_mode: restricted
  learning_mode: sandbox
```

---

## 11. Step 9: Planner proposes search action

A planner node proposes a search. The proposal is not executed yet.

```yaml
ActionCandidateWitness:
  action_candidate_id: acw-search-synthwave-001
  decision_context_id: dc-find-new-songs-001
  proposed_by:
    kind: planner
    ref: planner-music-discovery-v0.1
  action_kind: search
  action_payload_ref: query-profile-synthwave-discovery-001
  expected_effect: retrieve candidate songs similar to supported recent preference cluster
  supporting_witness_refs:
    - pref-synthwave-2026-04
    - mar-music-pref-0001
  contradicting_witness_refs: []
  uncertainty_refs:
    - genre_label_boundary_uncertain
  risk_assessment_ref: risk-search-internal-low-001
  reversibility: reversible
  required_policy_gate: policy-search-internal-restricted
  status: candidate
```

---

## 12. Step 10: Policy gate

```yaml
PolicyDecision:
  policy_decision_id: pd-action-search-001
  target_ref: acw-search-synthwave-001
  target_kind: action
  input_status: candidate
  decision: allow
  runtime_mode: restricted
  learning_mode: sandbox
  reasons:
    - internal_only
    - no_external_side_effect
    - restricted_privacy_ok
    - search_expansion_allowed
  required_followup:
    - record_action_execution
    - wrap_search_results_as_evidence
  rollback_ref: null
  policy_snapshot_id: ps-music-internal-2026-04-26
```

---

## 13. Step 11: Execute search

```yaml
ActionExecutionRecord:
  action_execution_id: aer-search-synthwave-001
  action_candidate_id: acw-search-synthwave-001
  policy_decision_id: pd-action-search-001
  execution_node_id: node-search-local-01
  executed_at: 2026-04-26T10:03:00-07:00
  execution_status: success
  output_evidence_bundle_ids:
    - eb-search-song-0001
    - eb-search-song-0002
  resulting_witness_ids:
    - sw-search-result-set-001
  rollback_ref: null
```

Search results become evidence, not recommendations yet.

---

## 14. Step 12: Record outcome

```yaml
ActionOutcomeWitness:
  action_outcome_witness_id: aow-search-synthwave-001
  action_execution_id: aer-search-synthwave-001
  expected_effect: retrieve candidate songs similar to supported recent preference cluster
  observed_effect: retrieved 25 candidate songs, 9 high-similarity, 3 contradicted by skip-history
  success_metric_refs:
    - metric-music-candidate-relevance-001
  unexpected_effects:
    - query broadened into adjacent genre label
  source_evidence_ids:
    - eb-search-song-0001
    - eb-search-song-0002
  policy_followup: audit
```

The outcome can update lookup memory and future decision contexts.

---

## 15. Step 13: Optional profile-learning trigger

The planner notices that several search results contain an unknown microgenre label.

It may propose profile learning, but only as another action candidate:

```yaml
ActionCandidateWitness:
  action_candidate_id: acw-profile-learn-microgenre-001
  decision_context_id: dc-find-new-songs-001
  proposed_by:
    kind: planner
    ref: planner-music-discovery-v0.1
  action_kind: start_profile_learning
  action_payload_ref: profile-learning-request-microgenre-001
  expected_effect: create candidate profile for unknown microgenre label and relation to existing preference cluster
  supporting_witness_refs:
    - aow-search-synthwave-001
  contradicting_witness_refs: []
  uncertainty_refs:
    - unknown_microgenre_label
  reversibility: reversible
  required_policy_gate: policy-profile-learning-sandbox
  status: candidate
```

Policy may approve sandbox learning or reject it. The planner does not directly create a promoted profile.

---

## 16. Failure and conflict examples

### 16.1 Conflicting planner actions

Planner A proposes search. Planner B proposes no search due to privacy. The system creates an action conflict record and the stricter policy wins.

```yaml
ActionConflictRecord:
  action_conflict_id: acr-search-vs-privacy-001
  decision_context_id: dc-find-new-songs-001
  action_candidate_ids:
    - acw-search-synthwave-001
    - acw-no-search-privacy-001
  conflict_type: execute_vs_block
  default_resolution: most_restrictive_policy_wins
  resolved_action: human_review
```

### 16.2 Stale self-model

A new batch of watch history arrives. The self-model snapshot is now stale.

```yaml
SelfModelInvalidationEvent:
  self_model_invalidation_event_id: smie-music-2026-04-26-001
  self_model_snapshot_id: sms-music-self-2026-04-26
  actor_ref: actor:self:hashed
  trigger_kind: new_evidence_arrived
  trigger_refs:
    - eb-yt-0101
  affected_lookup_record_ids:
    - lmr-pref-synthwave-2026-04
  required_action: rebuild_snapshot
  prior_snapshot_version: 1
  next_snapshot_policy: increment_version
  event_time: 2026-04-26T11:00:00-07:00
```

---

## 17. Implementation notes

A minimal implementation can build this example with:

1. local JSON watch-history import;
2. evidence bundle store;
3. timeline sorter;
4. two models plus one rule-based parser;
5. model adjudication record;
6. preference witness generator;
7. Redis-like lookup memory;
8. simple planner;
9. policy gate;
10. action execution recorder.

The first implementation does not need external side effects. It can produce an internal ranked candidate list only.

---

## 18. Key boundary

```text
Personal history is evidence.
Model outputs are evidence.
Planner proposals are evidence.
Search results are evidence.
Actions require policy.
Outcomes become new evidence.
```

This is the self-informing loop without turning memory, models, or planners into oracles.
