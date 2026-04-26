# Duotronic Witness Contract v10.16

**Status:** Research specification draft  
**Version:** 10.16-standalone-revision  
**Supersedes:** Duotronic Witness Contract v10.15
**Prior supersedes:** Duotronic Witness Contract v10.14
**Prior supersedes:** Duotronic Witness Contract v10.13
**Prior supersedes:** Duotronic Witness Contract v10.12
**Prior supersedes:** Duotronic Witness Contract v10.11
**Document kind:** Normative runtime trust contract plus reference schemas, diagnostics, auto-profile learning integration, and distributed model witness rules  
**Primary purpose:** Define how Duotronic evidence, witnesses, learned profile candidates, canonical objects, model outputs, search/social sources, lookup memory, recurrent state, replay, migration, and policy decisions become trusted, degraded, bypassed, rejected, or promoted.

---

## 1. Executive summary

> **Status tag:** reference

The Witness Contract defines the runtime trust discipline for Duotronic systems.

The core rule remains:

```text
A witness fact is not trusted because it is observed.
It becomes trusted only after declared validation, canonicalization,
replay-stable identity checks, and policy gating.
```

v10.12 extends the contract to support automatic profile learning across multiple models, multiple nodes, internal search, external search, social feeds, video transcripts, documents, glyphic or visual inputs, and natural-language streams.

The new rule is:

```text
A learned profile is not trusted because a model discovered it.
It becomes usable only after its witnesses, normalizer, bridge,
canonical identity, replay behavior, preservation claims, and policy boundaries are tested.
```

The Witness Contract is therefore the gate between:

1. raw information and evidence bundles;
2. evidence bundles and witness candidates;
3. witness candidates and profile candidates;
4. profile candidates and registry staging;
5. registry staging and runtime use;
6. runtime use and long-term authority.

---

## 2. Scope

> **Status tag:** normative

This contract governs:

1. evidence intake;
2. transport validation;
3. source validation;
4. modality decode;
5. L1 witness extraction;
6. candidate witness creation;
7. learned profile candidate creation;
8. model witness records;
9. distributed node witness records;
10. canonical normal-form construction;
11. lookup-backed witness memory;
12. recurrent witness state;
13. cross-model adjudication;
14. external search and social evidence ingestion;
15. profile synthesis;
16. policy shielding and bypass modes;
17. replay identity;
18. retention diagnostics;
19. migration and rollback;
20. conformance testing;
21. promotion, demotion, pruning, and rejection.

This contract does not define DPFC arithmetic. It uses DPFC and registry documents as lower-layer semantic sources.

---

## 2A. Draft 2 terminology integration

> **Status tag:** normative

v10.13 adopts `refs/duotronic_glossary_v1_0.md` as the terminology authority for shared corpus terms.

The term `CanonicalWitnessFact` is now explicitly defined:

```yaml
CanonicalWitnessFact:
  canonical_witness_fact_id: string
  source_candidate_witness_ids: []
  evidence_bundle_ids: []
  profile_id: string
  profile_version: string
  schema_id: string
  normalizer_id: string
  bridge_result_ids: []
  canonical_identity_hash: string
  canonical_payload_ref: string
  replay_identity_ref: string
  policy_decision_id: string
  runtime_mode: normal | restricted | sandbox | audit_only | degraded
  authority_scope: representation_identity | runtime_gate | lookup_fact | claim_support | profile_support | custom
  truth_status: not_applicable | unknown | supported | contradicted | disputed | policy_accepted
```

A `CanonicalWitnessFact` is canonical with respect to representation and policy scope. It is not automatically true about the external world.

Allowed witness `trust_status` values are:

```text
raw
candidate
canonicalized
audit_only
rejected
deprecated
```

Documents and examples should use these values consistently unless a profile declares a stricter local subset.

## 3. Runtime levels

> **Status tag:** normative

The witness system is organized into five runtime levels plus one memory layer and two v1.4 learning overlays.

| Layer | Symbolic role | Object family | Update cadence | Primary role |
|---|---|---|---|---|
| L1 | extraction | `WitnessSignature`, `CandidateWitness` | per event | extract local evidence and candidate witnesses |
| L2 | recurrent continuity | `RecurrentWitnessState` | per event or batch | maintain bounded continuity over canonical witness state |
| L2M | lookup memory | `WitnessLookupMemory` | query and maintenance cycles | retrieve stable normal-form facts |
| L3 | meta tuning | `MetaRecurrentWitness` | event time or batch | tune bounded policy coordinates |
| L4 | proposal layer | `ArchitecturalWitness`, `ProfileProposal` | maintenance windows | propose schema, profile, architecture, or migration changes |
| L5 | safety authority | `PolicyShield` | fixed or slow-changing | enforce feasibility, bypass, rollback, promotion boundaries |
| L1P | profile learning overlay | `AutoProfileCandidate` | batch or stream | synthesize candidate representation profiles |
| L2A | adjudication overlay | `CrossModelAdjudicationState` | batch or stream | compare model and node witnesses before promotion |

The overlays do not bypass L1-L5. They produce additional witness objects that must still pass the normal trust path.

---

## 4. Hard rules

> **Status tag:** normative

### 4.1 Normal-form-before-trust

Stable witness facts must be represented in canonical normal form before they are trusted, stored, retrieved, compared, replayed, or promoted.

### 4.2 Transport-before-semantics

Source and transport validation must precede semantic interpretation. A failed frame, missing source hash, malformed event, corrupted media segment, invalid transcript, failed parser, or suspicious connector result must not enter authoritative witness memory.

### 4.3 Evidence-before-profile

A candidate profile must identify the evidence bundles, model witnesses, source records, fixture cases, replay traces, and contradiction checks that produced it.

### 4.4 Profile-before-runtime-authority

A learned profile must not influence runtime authority until it is registered, tested, policy-gated, and assigned an allowed runtime mode.

### 4.5 No silent family reinterpretation

A witness family identifier, schema version, bridge version, normalizer version, source profile, or learned profile version must not be silently changed.

### 4.6 Bypass is valid behavior

When validation, canonicalization, lookup, replay, or policy authority fails, the correct behavior may be bypass or audit-only. Unsafe enrichment is worse than no enrichment.

### 4.7 Model output is raw evidence

The output of a machine-learning model is a witness-bearing event, not authority. A model may propose tokens, segments, relations, translations, rules, source scores, or profile candidates. It may not directly promote them.

### 4.8 Search result is raw evidence

A search result, social post, comment thread, feed item, video transcript, or platform metric is source evidence. It may support or contradict a witness, but it is not truth by default.

### 4.9 Profile synthesis is replayable

The system must be able to replay how a candidate profile was created, including source hashes, model versions, node IDs, prompts or inference settings where permitted, fixture generation, adjudication decisions, and policy outputs.

### 4.10 Analogy containment

Analogy profiles must remain analogy or research unless a separate non-analogy bridge, fixture pack, and evidence path support promotion.

---

## 5. Evidence bundle

> **Status tag:** normative

An `EvidenceBundle` is the first-class wrapper for incoming information.

```yaml
EvidenceBundle:
  evidence_id: string
  source_type: user_input | internal_search | web_search | social_feed | video | document | image | audio | code | model_output | node_event | lab_artifact | other
  source_system: string
  source_ref: string
  capture_time: string
  capture_node_id: string
  raw_payload_hash: string
  payload_mime_type: string
  payload_size: integer
  modality: text | image | audio | video | mixed | structured
  transport_status: valid | partial | failed | unknown
  source_integrity:
    content_hash: string
    metadata_hash: string | null
    connector_version: string
    retrieval_policy: string
  provenance:
    author_or_origin: string | null
    platform_account_hash: string | null
    thread_or_context_hash: string | null
    parent_evidence_ids: []
  privacy_class: public | internal | restricted | sensitive | unknown
  trust_status: raw | rejected | audit_only | candidate
```

Evidence bundles must be immutable after creation. Corrections create new bundles that point to prior bundle IDs.

---

## 6. Model witness

> **Status tag:** normative

A `ModelWitness` records what a model or augmented-intelligence component claimed about an evidence bundle.

```yaml
ModelWitness:
  model_witness_id: string
  model_id: string
  model_version: string
  node_id: string
  input_evidence_ids: []
  inference_profile_id: string
  output_hash: string
  proposed_segments: []
  proposed_symbols: []
  proposed_relations: []
  proposed_claims: []
  proposed_profile_refs: []
  confidence:
    scalar: number | null
    calibration_profile: string | null
    confidence_kind: model_reported | calibrated | ensemble_derived | absent
  known_failure_modes: []
  reproducibility:
    deterministic: true | false
    seed_or_trace_ref: string | null
    replay_allowed: true | false
  trust_status: raw_model_output | rejected | audit_only | candidate
```

A model witness can support candidate extraction. It cannot directly write authoritative canonical identity.

---

## 7. Candidate witness

> **Status tag:** normative

A `CandidateWitness` is a structured but not-yet-trusted interpretation.

```yaml
CandidateWitness:
  witness_id: string
  candidate_kind: symbol | token | glyph | relation | number | claim | source | contradiction | translation | geometry | bridge | normalizer | profile | other
  source_evidence_ids: []
  model_witness_ids: []
  proposed_object:
    schema_id: string
    payload: object
  proposed_canonicalization:
    normalizer_candidate_id: string | null
    identity_fields: []
    display_only_fields: []
  confidence:
    support_count: integer
    contradiction_count: integer
    model_agreement: number | null
    source_diversity: number | null
  status: observed | candidate | rejected | audit_only | promoted_to_profile_candidate
```

Candidate witnesses may be stored for analysis. They must not be used as trusted identity until canonicalized.

---

## 8. Auto-profile candidate

> **Status tag:** normative

An `AutoProfileCandidate` is a proposed profile synthesized from candidate witnesses and evidence.

```yaml
AutoProfileCandidate:
  profile_candidate_id: string
  proposed_profile_id: string
  kind: symbolic_numeric | natural_language_semantic | glyphic_visual | transport_adapter | graph | matrix | tensor | geometry | search_source | social_source | custom
  source_evidence_ids: []
  model_witness_ids: []
  candidate_witness_ids: []
  proposed_object_space:
    valid_examples: []
    invalid_examples: []
    ambiguity_cases: []
  proposed_symbols_or_units: []
  proposed_relations: []
  proposed_normalizer:
    normalizer_candidate_id: string
    deterministic: true | false
    identity_fields: []
    display_only_fields: []
  proposed_bridge:
    bridge_candidate_id: string
    source_to_core: string | null
    source_to_canonical_object: string | null
    inverse_bridge: string | null
    expected_loss: []
  absence_policy: string
  zero_policy: string
  invalid_state_policy: string
  conformance:
    generated_fixture_pack_id: string
    replay_trace_set: string
    failure_tests: []
  policy:
    requested_runtime_mode: audit_only | sandbox | restricted | normal
    required_gate: string
  status: candidate | research_profile | sandbox_runtime | rejected | deprecated
```

The default status for learned profiles is `candidate`. The default runtime mode is `audit_only`.

---

## 9. Cross-model adjudication

> **Status tag:** normative

When multiple models or nodes process the same or related evidence, the system should create an adjudication record.

```yaml
CrossModelAdjudication:
  adjudication_id: string
  target_candidate_id: string
  compared_model_witness_ids: []
  compared_node_ids: []
  agreement:
    segment_agreement: number | null
    relation_agreement: number | null
    value_agreement: number | null
    claim_agreement: number | null
  disagreement:
    contradiction_count: integer
    incompatible_outputs: []
    unresolved_ambiguities: []
  source_support:
    independent_source_count: integer
    source_diversity_score: number | null
    source_reliability_notes: []
  decision:
    action: continue_observing | generate_fixtures | stage_candidate | reject | bypass | human_review
    rationale: string
```

Agreement does not equal truth. Disagreement does not always equal failure. Disagreement may identify ambiguity that must be preserved.

---

## 10. Trusted runtime path

> **Status tag:** normative

The trusted path for a profiled object is:

```text
EvidenceBundle
-> source/transport validation
-> semantic or modality decode
-> CandidateWitness
-> registry lookup
-> normalizer selection
-> canonicalization
-> CanonicalWitnessFact
-> policy gate
-> L2M lookup enrichment
-> L2 recurrent update
-> retention diagnostics
-> replay record
-> L3/L4/L5 action if permitted
```

The trusted path for an unprofiled object is:

```text
EvidenceBundle
-> source/transport validation
-> model witnesses
-> candidate witnesses
-> auto-profile candidate
-> fixture generation
-> replay tests
-> policy gate
-> registry staging
-> audit-only or sandbox use
```

The second path does not skip the first. It creates a future candidate for the first path.

---

## 11. Failure states

> **Status tag:** normative

The following failure states are first-class:

```text
malformed_reject
transport_failed_reject
source_integrity_reject
schema_mismatch
registry_mismatch
normalizer_missing
normalizer_timeout
canonicalization_failed
ambiguous_reject
presence_zero_collapse_reject
family_bypass_required
transport_bypass_required
lookup_bypass_required
profile_candidate_only
model_disagreement_audit_only
source_conflict_audit_only
replay_mismatch_reject
migration_required
policy_veto
full_bypass
```

Failure states must be recorded. Silent fallback is not allowed when it changes authority.

---

## 12. Lookup memory

> **Status tag:** normative

L2M lookup memory stores stable normal-form facts. It does not store arbitrary unvalidated model output as authority.

Allowed lookup payloads include:

1. canonical witness facts;
2. registry-pinned profile entries;
3. replay-verified bridge results;
4. retention metrics with baselines;
5. policy-approved source reliability records;
6. contradiction records;
7. audit-only learned candidates.

Lookup enrichment must be bounded. Low normalization confidence, stale registry versions, replay mismatch, or missing policy authority must reduce or block lookup influence.

---

## 13. Recurrent witness state

> **Status tag:** normative

L2 recurrent state may use canonical witness context to maintain continuity. It may not let raw evidence directly select transition matrices, memory-write authority, lookup injection authority, profile promotion, or policy decisions.

For machine-learning model gating, Duotronic witnesses may be used as gates only after they are assigned a runtime mode:

```text
audit_only: observe but do not gate
sandbox: gate inside isolated experiments only
restricted: gate bounded non-authoritative paths
normal: gate approved runtime paths
blocked: no gating use
```

---

## 14. Promotion ladder

> **Status tag:** normative

Learned profiles move through this ladder:

```text
observed_pattern
-> candidate_witness
-> candidate_profile
-> research_profile
-> sandbox_runtime_profile
-> reference_profile
-> normative_profile
```

Promotion requires:

1. object-space declaration;
2. normalizer declaration;
3. bridge declaration;
4. fixture pack;
5. replay trace set;
6. failure tests;
7. expected-loss declaration;
8. retention metrics;
9. migration plan if semantic behavior changes;
10. policy approval.

Demotion and pruning must remain easy. A weak profile should be removed before it becomes institutional memory.

---

## 15. Online and social evidence

> **Status tag:** normative

Search and social evidence are treated as external evidence bundles. The system must record platform, retrieval time, content hash, context hash, author or origin hash where allowed, thread relation, source link, edit/delete status if available, and source reliability profile.

Social agreement is not truth. Search ranking is not truth. Virality is not truth.

Allowed witness types include:

1. claim witness;
2. source witness;
3. contradiction witness;
4. propagation witness;
5. sentiment or stance witness;
6. temporal witness;
7. author-history witness;
8. evidence-span witness;
9. reliability diagnostic.

---

## 16. Non-claims

> **Status tag:** normative

The Witness Contract does not claim that:

1. a model can automatically understand every language;
2. a learned profile is reliable without tests;
3. cross-model agreement proves truth;
4. search results are authoritative;
5. social feeds are authoritative;
6. a canonical claim is a true claim;
7. recurrence memory is a proof system;
8. policy approval is semantic proof;
9. runtime gating is safe without replay and rollback;
10. research profiles are production profiles.


---

## 17. Draft 2 promotion consistency rule

> **Status tag:** normative

The Witness Contract uses the canonical status ladder from the Glossary and Profile Synthesis Registry:

```text
observed_pattern
candidate_witness
candidate_profile
research_profile
sandbox_runtime_profile
reference_profile
normative_profile
deprecated_profile
rejected_profile
```

The Witness Contract does not promote profiles directly. It emits canonical witness facts, replay records, failure records, and policy inputs that the Profile Synthesis Registry and Policy Shield use for promotion decisions.

Promotion to `reference_profile` or `normative_profile` must create a Family Registry handoff record.


---

## 18. Chronological self-evidence integration

> **Status tag:** normative

v10.14 recognizes chronological self-evidence streams as first-class evidence structures.

A chronological self-evidence stream may support:

1. timeline witnesses;
2. preference witnesses;
3. habit witnesses;
4. likely-action witnesses;
5. self-model snapshots;
6. source reliability trends;
7. contradiction trends;
8. decision-support facts;
9. model-gating evidence;
10. planner context.

The owning document is `refs/duotronic_chronological_self_evidence_contract_v1_2.md`.

### 18.1 Self-evidence trust boundary

Chronological evidence about an actor is not the actor.

A self-model snapshot is a canonicalized, policy-scoped representation of selected evidence. It must declare:

1. included streams;
2. excluded streams where relevant;
3. time window;
4. privacy class;
5. runtime mode;
6. authority scope;
7. policy decision.

### 18.2 Personal history as evidence

Personal history sources such as watch history, playlist order, search history, posts, comments, clicks, likes, saves, and edits may enter the Witness Contract only as evidence bundles or source evidence records.

A derived claim such as “this actor prefers X” requires a derived witness with support, contradiction, time scope, stability diagnostics, and policy mode.

---

## 19. Internal decision and action witnesses

> **Status tag:** normative

The Witness Contract now recognizes decision and action objects as witness-bearing objects.

An internal planner, model, rule engine, heuristic, reinforcement learner, or human-in-the-loop workflow that proposes an action must emit an `ActionCandidateWitness`.

An action candidate is not executed merely because it is proposed.

```text
decision context
-> action candidate witness
-> risk and reversibility assessment
-> policy gate
-> action execution record
-> action outcome witness
```

Allowed decision objects include:

1. `DecisionContext`;
2. `ActionCandidateWitness`;
3. `ActionExecutionRecord`;
4. `ActionOutcomeWitness`;
5. `DecisionSupportFact`.

The owning document is `refs/duotronic_internal_decision_and_planning_contract_v1_2.md`.

### 19.1 Internal-only decisions

A Duotronic system may make internal decisions for itself without producing user-facing text.

Internal-only decisions still require:

1. evidence references;
2. authority scope;
3. runtime mode;
4. policy decision;
5. outcome witness if executed.

### 19.2 External actions

External actions such as posting, messaging, API calls, purchases, file writes, public claims, or irreversible workflow steps require explicit L5 approval unless a narrower policy document grants authority.

---

## 20. Lookup memory and replay integration

> **Status tag:** normative

L2M lookup memory may be backed by high-speed databases, Redis-like key-value stores, vector stores, graph stores, time-series stores, or event logs.

Implementation speed does not grant authority.

Any lookup result that influences runtime must link back to one of:

1. canonical witness fact;
2. policy decision;
3. source evidence record;
4. bridge result;
5. profile registry record;
6. replay identity;
7. explicit audit-only candidate.

The owning document is `refs/duotronic_lookup_memory_and_replay_profile_v1_2.md`.

### 20.1 Runtime query vs replay query

Runtime queries may use caches and approximations if policy permits.

Replay queries must pin versions, source hashes, model versions, index profiles, and policy snapshots.

Promotion requires replay or a policy-approved replay-equivalence path.

---

## 21. Model diversity and oracle-risk governance

> **Status tag:** normative

v10.14 recognizes model diversity and oracle-risk records as required governance inputs when multiple models are used for witness extraction, profile synthesis, translation, claim extraction, planning, or adjudication.

A cross-model agreement record must not treat agreement as strong support unless model independence is assessed.

The owning document is `refs/duotronic_model_diversity_and_adjudication_governance_v1_1.md`.

### 21.1 No single oracle

No model output may be treated as authority by default.

A model witness can support a canonical witness fact only under declared authority scope and policy.

### 21.2 Homogeneous-model agreement

If multiple models share high training-data overlap, architecture similarity, provider dependence, or known shared failure modes, their agreement must be down-weighted or treated as weak support unless policy allows otherwise.

### 21.3 Falsifier and red-team role

A model diversity set should include at least one falsifier or counterexample role before a learned profile or action policy is promoted beyond sandbox, unless policy explicitly waives that requirement.

---

## 22. Draft 3 authority summary

> **Status tag:** reference

Draft 3 adds one major principle:

```text
The system can use evidence to inform itself,
but self-informing loops are still witness-gated.
```

Chronological personal or organizational history, high-speed memory, internal planners, and diverse model ensembles are all allowed. None are authority by themselves.


---

## 23. Draft 4 conflict, policy-change, and invalidation objects

> **Status tag:** normative

v10.15 recognizes these additional witness-bearing objects:

1. `ActorScope`;
2. `SelfModelInvalidationEvent`;
3. `LikelyActionToActionLink`;
4. `LoopResourceViolationEvent`;
5. `ProfileLearningActionPayload`;
6. `PlannerTriggeredLearningRun`;
7. `PolicyChangeProposal`;
8. `ActionConflictRecord`.

These objects may affect runtime behavior only through policy decisions.

### 23.1 Conflict is a witness condition

Contradictory action candidates are not resolved silently.

An action conflict must be represented as `ActionConflictRecord` and routed to Policy Shield. The default resolution is most restrictive policy wins, no-action, audit-only, or human review.

### 23.2 Policy change is not self-executing

A `PolicyChangeProposal` is a candidate, not an active policy. Only an approved policy snapshot can govern runtime.

### 23.3 Stale self-models block authority

If a `SelfModelInvalidationEvent` marks a self-model stale, any dependent restricted or normal runtime action must be blocked, refreshed, or explicitly allowed by policy under a staleness exception.

### 23.4 Resource violations reduce authority

A `LoopResourceViolationEvent` affecting a high-speed loop must reduce runtime authority or trigger policy review when it affects lookup memory, action candidates, model calls, search, or profile learning.


---

## 24. Draft 5 purge and human-review objects

> **Status tag:** normative

v10.16 recognizes evidence purge and human-review records as first-class governance objects.

New purge-related objects:

1. `EvidencePurgeRequest`;
2. `EvidencePurgeAuthorization`;
3. `PurgeDependencyGraph`;
4. `EvidencePurgeEvent`;
5. `PurgeTombstone`;
6. `PurgeReplayImpactRecord`.

New human-review objects:

1. `HumanReviewRequest`;
2. `HumanReviewPacket`;
3. `HumanReviewDecision`;
4. `HumanReviewFeedbackRecord`;
5. `MultiPartyReviewRule`.

The owning documents are:

1. `refs/duotronic_evidence_purge_and_privacy_deletion_contract_v1_0.md`;
2. `refs/duotronic_human_review_and_escalation_protocol_v1_0.md`.

### 24.1 Purge is stronger than invalidation

Invalidation marks a record stale or unsafe to use. Purge removes, tombstones, quarantines, or cryptographically erases a record and cascades to derived artifacts according to policy.

If a purge affects evidence used by a canonical witness fact, that witness fact must be demoted, tombstoned, rebuilt, or blocked according to the purge decision.

### 24.2 Human review is witness-bearing

A human review decision is an evidence event and must be recorded. It may influence policy, profile promotion, action conflict resolution, purge authorization, or source annotation only through declared authority scope.

Human review must not be an undocumented side channel.

### 24.3 Planner promotion guard

A planner-triggered learning run must not promote a profile.

If a planner-provided payload contains `promotion_requested: true`, the Witness Contract must treat that field as invalid or override it to `false`.

Profile promotion may occur only through the Profile Synthesis Registry and its promotion request / Family Registry handoff path.

### 24.4 Replay with stale self-models and lazy actions

Old decision contexts may be replayed with stale self-model snapshots if replay identity pins the exact self-model snapshot version and staleness state.

Default rule:

```text
replay allowed for audit;
runtime reuse blocked unless policy permits stale replay use.
```

Lazy or deferred actions that were proposed under a now-stale self-model must be re-gated before execution.

### 24.5 Diversity score authority

`DiversityWeightedAgreement` scores are observe-only unless the model-diversity governance profile declares calibration data, thresholds, and policy authority.
