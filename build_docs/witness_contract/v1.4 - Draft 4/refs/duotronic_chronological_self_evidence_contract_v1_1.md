# Duotronic Chronological Self-Evidence Contract v1.1

**Status:** Source-spec baseline candidate  
**Version:** chronological-self-evidence-contract@v1.1  
**Supersedes:** chronological-self-evidence-contract@v1.0  
**Document kind:** Normative self-referential evidence and personal-history ingestion contract plus reference schemas  
**Primary purpose:** Define how chronologically ordered personal, organizational, social, behavioral, media, and self-referential evidence streams enter Duotronic as evidence bundles, become canonical witness facts, support internal reasoning, and feed recurrent/lookup memory without being treated as automatic truth or identity.

---

## 1. Scope

This contract applies when the Duotronic system ingests evidence that represents an actor, organization, project, user, community, agent, or system over time.

Examples include:

1. YouTube watch history;
2. YouTube likes, playlists, subscriptions, comments, descriptions, captions, and transcripts;
3. social-media posts and replies;
4. Reddit posts, comments, saved items, and voting patterns where available;
5. Bluesky-like, Facebook-like, Discord-like, and forum-like activity;
6. browser or search history where policy permits;
7. self-authored notes and documents;
8. code commits, issues, comments, pull requests, and review activity;
9. email or message threads where policy permits;
10. audio, video, image, and mixed-media artifacts;
11. prior Duotronic decisions and policy snapshots;
12. model-output histories;
13. recurrent-state snapshots;
14. manually imported autobiographical or organizational timelines.

The contract is not limited to personal data. It also applies to project memory, agent memory, organization memory, product memory, or any chronologically ordered self-referential corpus.

---

## 2. Central rule

> **Status tag:** normative

Chronological self-evidence is evidence, not essence.

A chronological stream can help the system infer preferences, habits, priorities, contradictions, goals, decision tendencies, source reliability, and likely next actions. It does not become an authoritative identity model without witness extraction, canonicalization, replay, retention diagnostics, and policy gating.

The system may ask:

```text
What did this actor tend to watch, write, choose, reject, search, build, or correct over time?
```

The system must not silently answer:

```text
This is what the actor is, wants, or will do.
```

unless the claim is explicitly scoped, supported, and policy-approved.

---

## 3. Chronological evidence stream

A chronological stream is an ordered collection of evidence bundles.

```yaml
ChronologicalEvidenceStream:
  stream_id: string
  stream_owner_ref: string
  owner_kind: person | agent | organization | project | community | model | system | custom
  stream_kind: personal_history | project_history | social_history | media_history | decision_history | mixed
  privacy_class: public | internal | restricted | sensitive | mixed
  ordering_policy:
    primary_time_field: capture_time | source_created_time | source_updated_time | event_time | custom
    tie_breaker: source_ref | ingestion_order | hash_order | custom
    clock_uncertainty_policy: preserve | bucket | reject | custom
  evidence_bundle_ids: []
  parent_stream_ids: []
  derived_stream_ids: []
  status: raw | indexed | canonicalized | audit_only | restricted | deprecated
```

A stream must preserve the difference between:

1. source event time;
2. capture time;
3. ingestion time;
4. modified time;
5. replay time;
6. model-inference time.

---

## 4. Self-reference rule

> **Status tag:** normative

A stream is self-referential when later evidence refers to, modifies, quotes, contradicts, repeats, interprets, deletes, revises, or depends on earlier evidence.

Self-reference must be explicit.

```yaml
SelfReferenceEdge:
  edge_id: string
  from_evidence_id: string
  to_evidence_id: string
  relation: replies_to | quotes | contradicts | revises | repeats | summarizes | deletes | explains | predicts | caused_by | derived_from | custom
  relation_confidence: number | null
  extracted_by_model_witness_ids: []
  trust_status: raw | candidate | canonicalized | audit_only | rejected
```

Self-reference is not automatically semantic agreement. A reply may support, mock, reject, reinterpret, or derail an earlier item.

---

## 5. Personal-history source record

For personal or actor-specific streams, the system may use a specialized source record:

```yaml
PersonalHistorySourceRecord:
  personal_history_record_id: string
  evidence_bundle_id: string
  actor_ref: string
  actor_ref_policy: direct | hashed | pseudonymous | group | unknown
  platform: youtube | reddit | bluesky | facebook | discord | web | notes | code | search | custom
  event_type: watch | like | dislike | save | share | post | comment | reply | edit | delete | subscribe | search | click | dwell | skip | commit | review | decision | custom
  source_event_time: string | null
  capture_time: string
  parent_record_ids: []
  content_hash: string
  metadata_hash: string | null
  context_hash: string | null
  privacy_class: public | internal | restricted | sensitive | unknown
  evidence_status: raw | candidate | canonicalized | audit_only | restricted | rejected
```

The actor reference must respect privacy and access policy. Direct identity is not required when a hashed or pseudonymous identity is sufficient.

---

## 6. Timeline canonicalization

A chronological stream may be canonicalized into a timeline witness.

```yaml
TimelineWitness:
  timeline_witness_id: string
  stream_id: string
  profile_id: string
  ordering_policy_id: string
  canonical_event_refs: []
  event_count: integer
  time_range:
    start: string | null
    end: string | null
  gaps:
    known_gaps: []
    unknown_gap_policy: preserve | ignore | reject | custom
  canonical_identity_hash: string
  trust_status: candidate | canonicalized | audit_only | rejected
```

A timeline witness is canonical with respect to ordering and evidence references. It is not automatically a psychological, preference, or intention model.

---

## 7. Preference, habit, and tendency witnesses

Chronological evidence may support derived witnesses.

Examples:

```yaml
PreferenceWitness:
  preference_witness_id: string
  stream_id: string
  target_actor_ref: string
  preference_domain: music | video | topic | community | action | style | product | custom
  inferred_preference: string
  supporting_evidence_ids: []
  contradicting_evidence_ids: []
  time_scope: string
  stability_diagnostic: string | null
  confidence: number | null
  truth_status: unknown | supported | disputed | contradicted | policy_accepted
  runtime_mode: audit_only | sandbox | restricted | normal
```

```yaml
HabitWitness:
  habit_witness_id: string
  stream_id: string
  habit_description: string
  recurrence_pattern: string
  supporting_evidence_ids: []
  exception_evidence_ids: []
  time_scope: string
  confidence: number | null
  trust_status: candidate | canonicalized | audit_only | rejected
```

```yaml
LikelyActionWitness:
  likely_action_witness_id: string
  stream_id: string
  situation_profile_id: string
  proposed_action: string
  based_on_patterns: []
  supporting_evidence_ids: []
  contradicting_evidence_ids: []
  confidence: number | null
  authority_scope: internal_decision_support | sandbox_prediction | user_facing_claim | custom
  policy_decision_id: string
```

A likely-action witness is not a command. It is input to the decision layer.

---

## 8. High-speed self-query path

> **Status tag:** normative

A chronological stream may be queried many times per second for internal reasoning, simulation, or model gating. That is an implementation path, not a semantic shortcut.

High-speed self-query is allowed only when:

1. the backing records are canonical or explicitly audit-only;
2. the lookup index records its profile and version;
3. privacy class permits the query;
4. runtime mode permits internal use;
5. replay requirements are understood;
6. source deletion or demotion events propagate to derived indexes.

The system may use Redis, key-value stores, vector stores, time-series stores, graph stores, or custom indexes as backing implementations. The contract does not require a specific database.

---

## 9. Self-model boundary

A self-model is a set of derived witnesses about an actor or system.

```yaml
SelfModelSnapshot:
  self_model_snapshot_id: string
  stream_ids: []
  actor_ref: string
  snapshot_time: string
  included_witness_classes:
    - preference
    - habit
    - likely_action
    - contradiction
    - source_reliability
    - topic
    - goal
  canonical_fact_refs: []
  audit_only_fact_refs: []
  policy_decision_id: string
  runtime_mode: audit_only | sandbox | restricted | normal
```

A self-model snapshot must declare:

1. whose evidence it models;
2. which streams it includes;
3. which streams it excludes;
4. what time window it covers;
5. what authority it has;
6. what actions it may influence.

---

## 10. Privacy and consent boundary

Chronological self-evidence often contains sensitive data.

A conforming implementation must:

1. label privacy class at ingestion;
2. prevent unauthorized cross-node sharing;
3. prevent unauthorized outbound model calls;
4. record whether personal data can be used for profile learning;
5. record whether personal data can be used for model training;
6. propagate deletion/unavailability events;
7. separate internal decision support from user-facing claims;
8. support restricted and audit-only modes.

---

## 11. Non-claims

This contract does not claim that chronological personal data fully captures a person, intention, identity, or future behavior.

It specifies how such data can be used as governed evidence for internal reasoning.


---

## 12. Multi-actor scoping

> **Status tag:** normative

A Duotronic instance may model multiple actors, agents, users, organizations, projects, communities, models, or systems.

Self-informing does not imply a single global self.

Every self-evidence object must be actor-scoped or system-scoped.

Required actor-scope fields:

```yaml
ActorScope:
  actor_scope_id: string
  actor_ref: string
  actor_kind: person | agent | organization | project | community | model | system | group | custom
  actor_ref_policy: direct | hashed | pseudonymous | group | unknown
  allowed_stream_ids: []
  excluded_stream_ids: []
  scope_purpose: internal_decision_support | profile_learning | project_memory | model_governance | custom
  privacy_class: public | internal | restricted | sensitive | mixed
```

A self-model snapshot must not mix actors unless it explicitly declares `actor_kind: group` or `actor_kind: organization` and records member/source boundaries.

### 12.1 Actor selection rule

When multiple actors are present, a decision context must declare which actor or group it models.

If actor selection is ambiguous, the system must use `audit_only`, request disambiguation, or choose the most restrictive policy.

---

## 13. Self-model versioning

> **Status tag:** normative

A `SelfModelSnapshot` is versioned.

Updated schema:

```yaml
SelfModelSnapshot:
  self_model_snapshot_id: string
  actor_scope_id: string
  stream_ids: []
  actor_ref: string
  snapshot_time: string
  version: integer
  prior_snapshot_id: string | null
  supersedes_snapshot_ids: []
  included_witness_classes: []
  canonical_fact_refs: []
  audit_only_fact_refs: []
  policy_decision_id: string
  runtime_mode: audit_only | sandbox | restricted | normal
  staleness_policy:
    max_age_seconds: integer | null
    invalidate_on_new_evidence: true | false
    invalidate_on_source_delete: true | false
    invalidate_on_policy_change: true | false
    invalidate_on_profile_demotion: true | false
```

A self-model snapshot must not be updated in place. New evidence, changed policy, source deletion, or profile demotion creates a new snapshot or invalidation event.

---

## 14. Self-model invalidation

> **Status tag:** normative

A self-model snapshot becomes stale or invalid when its underlying streams, witnesses, policies, profiles, lookup records, or privacy constraints change.

```yaml
SelfModelInvalidationEvent:
  self_model_invalidation_event_id: string
  self_model_snapshot_id: string
  actor_scope_id: string
  actor_ref: string
  trigger_kind: new_evidence_arrived | source_deleted | source_unavailable | source_edited | policy_changed | profile_demoted | witness_retracted | lookup_invalidated | privacy_changed | manual | custom
  trigger_refs: []
  affected_lookup_record_ids: []
  affected_decision_context_ids: []
  required_action: mark_stale | rebuild_snapshot | demote_to_audit | remove_from_lookup | human_review
  prior_snapshot_version: integer
  next_snapshot_policy: increment_version | rebuild_from_scratch | block_until_review
  event_time: string
```

### 14.1 Invalidation propagation

Invalidation must propagate to:

1. lookup memory records;
2. high-speed loop profiles;
3. decision contexts;
4. action candidate witnesses;
5. likely-action witnesses;
6. preference/habit witnesses where affected;
7. model-gating paths;
8. profile-learning runs that depended on the stale snapshot.

---

## 15. Likely action is prediction, not proposal

> **Status tag:** normative

A `LikelyActionWitness` predicts or estimates what an actor may do or prefer.

It is not an executable proposal.

A `LikelyActionWitness` may inform a `DecisionContext`. It may not be automatically converted into an `ActionCandidateWitness`.

Conversion requires:

1. a planner or policy component to create a separate `ActionCandidateWitness`;
2. an explicit link to the likely-action witness as support;
3. risk and reversibility assessment;
4. policy gate.

```yaml
LikelyActionToActionLink:
  link_id: string
  likely_action_witness_id: string
  action_candidate_id: string
  conversion_author: planner | policy | human | hybrid
  conversion_reason: string
  policy_decision_id: string
```

No link means no executable action.
