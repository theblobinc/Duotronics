# Duotronic Glossary v1.0

**Status:** Source-spec baseline candidate  
**Version:** glossary@v1.0  
**Document kind:** Normative terminology and ontology reference  
**Primary purpose:** Provide one canonical terminology source for Duotronic documents so that core concepts such as absence, zero, canonical identity, evidence, witness, profile, bridge, replay, policy, and promotion do not drift across documents.

---

## 1. Scope

This glossary defines terms used across the v1.4 Draft 2 corpus.

A document may repeat a short definition locally for readability, but if the local definition conflicts with this glossary, the glossary controls unless the local document explicitly declares a narrower profile-specific meaning.

This glossary is intentionally written for both human reviewers and machine-learning / augmented-intelligence systems that need stable terminology when reading, generating, validating, or modifying Duotronic source documents.

---

## 2. Authority rule

> **Status tag:** normative

The glossary is a terminology authority, not a semantic authority for every subsystem.

It defines shared terms. It does not override the owning documents for subsystem behavior:

| Term class | Owning document |
|---|---|
| DPFC core magnitude, family word, export/import behavior | DPFC |
| runtime trust, witness state, policy gates | Witness Contract |
| representation bridge behavior | Representation Bridge Contract |
| auto-profile lifecycle | Auto-Profile Learning Contract |
| source/social/search wrappers | Search and Social Evidence Ingestion |
| distributed node events | Distributed Model Node Protocol |
| profile staging and promotion records | Profile Synthesis Registry |
| family/profile registry entries | Family Registry |
| runtime modes and L5 decisions | Policy Shield Guide |
| migration and replay versioning | Migration Guide |

---

## 3. Core separation terms

### 3.1 Structural absence

Structural absence means that no object is present in a location, slot, field, relation, or container.

Structural absence is not ordinary numeric zero, not a failed parse, not an unknown value, not an inactive transport row unless declared, and not a model’s low confidence.

### 3.2 Ordinary numeric zero

Ordinary numeric zero is the conventional zero used by external arithmetic systems, host languages, transport protocols, and mathematical formats.

In Duotronic profiles, ordinary zero may appear only where a profile declares an import/export policy or external adapter behavior.

### 3.3 Origin role

Origin role is a coordinate or scalar-line role. It may be represented by a native label in a specific profile, but it is not automatically structural absence.

### 3.4 Least realized magnitude

Least realized magnitude is the first present positive core magnitude in the DPFC core.

It is not absence.

### 3.5 Token-free absence

Token-free absence is a transport/source encoding state where no active token is present.

It is not numeric zero. It is not a malformed payload. It is not unknown. It is valid only where a transport or source profile declares it.

### 3.6 Invalid payload

An invalid payload is information that fails validation. It is neither absence nor zero.

### 3.7 Unknown present value

An unknown present value is a state where an object is present but its value is not known or not resolved.

Unknown present value is not absence.

---

## 4. Evidence and witness terms

### 4.1 Raw information

Raw information is untrusted incoming content before it has been wrapped as an evidence bundle.

### 4.2 Evidence bundle

An evidence bundle is the first-class source wrapper for incoming information. It records source type, source reference, capture time, payload hash, modality, provenance, privacy class, and trust status.

An evidence bundle is not itself a trusted semantic object.

### 4.3 Source evidence record

A source evidence record is a structured record for search, social, document, transcript, or platform-derived content.

A source evidence record is not truth by default.

### 4.4 Model witness

A model witness records what a machine-learning model or augmented-intelligence component claimed about an evidence bundle.

A model witness is raw or candidate evidence unless canonicalized and policy-approved.

### 4.5 Candidate witness

A candidate witness is a structured hypothesis extracted from evidence and/or model output.

A candidate witness may be useful for learning, clustering, and fixture generation. It is not canonical authority.

### 4.6 Canonical witness fact

A canonical witness fact is a witness object that has passed declared validation, deterministic canonicalization, registry/version pinning, and policy gating for its allowed runtime mode.

A canonical witness fact may still have limited authority depending on policy mode. It is canonical with respect to representation, not necessarily true about the external world.

### 4.7 Witness history

Witness history is the retained provenance, evidence, model output, construction path, confidence, contradiction, and replay information behind a witness.

Witness history may be richer than canonical identity.

---

## 5. Canonicalization and identity terms

### 5.1 Canonical identity

Canonical identity is the stable versioned normal form used for equality, hashing, signing, storage, replay, conversion, and promotion.

Canonical identity is not truth. It is identity under declared rules.

### 5.2 Normalizer

A normalizer is a deterministic procedure or profile that maps valid inputs into canonical identity.

A normalizer must declare its identity fields, display-only fields, uncertainty policy, expected-loss fields, and failure states.

### 5.3 Serializer

A serializer emits byte-stable or otherwise replay-stable representation of a canonical object.

### 5.4 Replay identity

Replay identity is the pinned set of versions, inputs, evidence hashes, models, node events, profiles, normalizers, bridge versions, policy snapshots, and fixture packs required to reproduce or audit a result.

---

## 6. Profile and registry terms

### 6.1 Profile

A profile is a declared object-space and behavior specification. It may define validation, normalization, bridges, absence policy, zero policy, invalid states, fixtures, and promotion requirements.

### 6.2 Learned profile

A learned profile is a profile proposed from evidence, model witnesses, source data, fixtures, and/or distributed node observations.

A learned profile begins as a candidate and must pass the promotion ladder before runtime authority.

### 6.3 Hand-authored profile

A hand-authored profile is written by a human or directly specified by a trusted internal author.

Hand-authored profiles still require promotion evidence before influencing runtime authority. Human authorship is not a bypass.

### 6.4 Candidate profile

A candidate profile is a proposed profile that has not yet passed the required fixtures, replay checks, preservation tests, migration checks, and policy gates.

### 6.5 Family Registry

The Family Registry records declared families and promoted profile-backed object spaces that may be referenced by runtime systems.

### 6.6 Profile Synthesis Registry

The Profile Synthesis Registry records the pre-promotion and promotion lifecycle for candidate, research, sandbox, reference, normative, deprecated, and rejected profiles.

---

## 7. Bridge terms

### 7.1 Representation bridge

A representation bridge maps a source representation into a canonical Duotronic object, DPFC core object, or target representation through declared validation, canonicalization, preservation, expected-loss, replay, and policy rules.

### 7.2 Total bridge

A total bridge is declared for all valid source objects in the source profile.

### 7.3 Partial bridge

A partial bridge is declared only for a subset of valid source objects.

Partial bridges require explicit domain declarations and may not be used as normal authority unless promoted with complete policy justification.

### 7.4 Lossy bridge

A lossy bridge intentionally discards declared information.

Lossy bridges must declare expected loss. Unexpected loss is a failure condition.

### 7.5 Expected loss

Expected loss is information loss explicitly declared by a bridge, normalizer, source adapter, or profile.

### 7.6 Prohibited loss

Prohibited loss is information that must not be lost if the result is to remain valid for the requested authority level.

---

## 8. Runtime and policy terms

### 8.1 Runtime mode

Runtime mode controls how a witness, profile, bridge, or source may affect operation.

Common modes include `normal`, `restricted`, `sandbox`, `audit_only`, `degraded`, `family_bypass`, `transport_bypass`, `lookup_bypass`, `profile_bypass`, and `full_bypass`.

### 8.2 Learning mode

Learning mode controls whether the auto-profile learning pipeline is allowed to run and what authority it has.

Allowed learning modes are `blocked`, `audit_only`, `sandbox`, and `active`.

### 8.3 Policy gate

A policy gate is an L5 decision point that allows, restricts, degrades, sandboxes, bypasses, rejects, or rolls back a path.

### 8.4 Promotion

Promotion is the controlled movement of a profile, bridge, normalizer, metric, or source profile to a higher authority status.

Promotion requires evidence lineage, fixtures, replay, retention diagnostics where applicable, migration/rollback support where applicable, and L5 policy approval.

### 8.5 Demotion

Demotion reduces a profile, witness, bridge, normalizer, metric, or source record to a lower authority state because of replay failure, policy change, source deletion, contradiction, normalizer instability, migration failure, or other governance reason.

---

## 9. Source and online terms

### 9.1 Search result

A search result is a retrieved source candidate. Search rank does not prove truth.

### 9.2 Social source

A social source is a post, comment, thread, message, video comment, community item, or similar platform-derived record.

Social agreement, virality, likes, reposts, and comments are diagnostics, not proof.

### 9.3 Deleted source

A deleted source is a previously captured source record that is later marked deleted, unavailable, removed, or inaccessible.

Deletion requires re-evaluation of dependent claim witnesses according to policy.

### 9.4 Source reliability diagnostic

A source reliability diagnostic is a measured or assessed signal about a source’s reliability for a specific context. It requires baselines before it can affect authority.

---

## 10. Status names

The canonical v1.4 Draft 2 status ladder is:

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

Short aliases may be used in local contexts only if mapped explicitly:

| Alias | Canonical status |
|---|---|
| `sketch` | `observed_pattern` |
| `candidate` | `candidate_profile` when referring to profiles |
| `experimental` | `research_profile` |
| `research_valid` | `research_profile` |
| `sandbox_runtime` | `sandbox_runtime_profile` |
| `reference` | `reference_profile` |
| `normative` | `normative_profile` |
| `deprecated` | `deprecated_profile` |
| `rejected` | `rejected_profile` |

For machine-readable records, canonical status names are preferred.

---

## 11. Draft 3 self-informing and decision terms

### 11.1 Chronological evidence stream

A chronological evidence stream is an ordered set of evidence bundles tied to an actor, agent, project, organization, model, or system over time.

### 11.2 Self-evidence

Self-evidence is evidence about an actor, agent, project, organization, or system that can be used to model its own history, tendencies, preferences, contradictions, decisions, and likely actions.

Self-evidence is not identity or essence.

### 11.3 Self-model snapshot

A self-model snapshot is a policy-scoped set of derived witnesses about an actor or system at a point in time.

### 11.4 Lookup memory

Lookup memory is fast retrieval infrastructure for canonical facts, audit candidates, timelines, self-models, bridge results, source records, contradictions, model witnesses, and derived features.

Fast lookup is not authority.

### 11.5 High-speed loop

A high-speed loop is an implementation profile that repeatedly queries or replays memory many times per second for audit, sandbox simulation, restricted decision support, or normal runtime paths.

### 11.6 Decision context

A decision context is the structured set of objectives, evidence, witnesses, uncertainty, contradictions, memory records, privacy constraints, and runtime mode for a proposed decision.

### 11.7 Action candidate witness

An action candidate witness is a proposed action wrapped as a witness candidate before execution.

### 11.8 Action execution record

An action execution record records whether a policy-approved action ran, failed, partially completed, was blocked, or was rolled back.

### 11.9 Action outcome witness

An action outcome witness records the observed result of an executed action and becomes evidence for future decisions.

### 11.10 Oracle risk

Oracle risk is the risk that a model, search system, source, heuristic, or homogeneous model group is treated as authority without sufficient evidence, diversity, replay, and policy.

### 11.11 Model diversity set

A model diversity set is a declared group of models or reasoning systems used together to reduce single-oracle dependence and expose disagreement.

---

## 12. Draft 4 implementation-hardening terms

### 12.1 Actor scope

Actor scope defines which person, agent, organization, project, community, group, model, or system a self-model or decision context is about.

### 12.2 Self-model invalidation

Self-model invalidation is the process of marking a self-model snapshot stale, demoted, or unusable because source evidence, policy, lookup memory, profile status, or privacy constraints changed.

### 12.3 Profile-learning action

A profile-learning action is a planner-proposed action that requests a profile-learning run. It produces candidate profile material only and does not imply promotion.

### 12.4 Policy change proposal

A policy change proposal is a witness-wrapped proposed change to a policy snapshot. It is not active policy until approved by the required governance path.

### 12.5 Action conflict

An action conflict occurs when two or more action candidates for the same decision context cannot all be safely executed together, or when one candidate blocks another.

### 12.6 Loop resource budget

A loop resource budget defines CPU, memory, storage, network, concurrency, model-call, search-call, and runtime limits for high-speed loops.

### 12.7 Likely action to action link

A likely action to action link records an explicit, policy-aware conversion from a prediction witness into an action proposal.

---

## 13. Draft 5 purge, review, replay, and calibration terms

### 13.1 Purge

Purge is a privacy, policy, legal, consent, or governance operation that removes, tombstones, quarantines, or cryptographically erases evidence and derived records. Purge is stronger than invalidation.

### 13.2 Evidence purge event

An evidence purge event records execution of an authorized purge and its affected objects, tombstones, failures, and replay impact.

### 13.3 Purge tombstone

A purge tombstone is a non-content record that preserves the fact that a purge occurred without preserving sensitive payload.

### 13.4 Human review request

A human review request is a governed request for a human or role-bearing reviewer to decide, classify, approve, reject, annotate, or escalate a target.

### 13.5 Human review decision

A human review decision is a recorded decision from a reviewer. It is evidence and may feed policy, fixtures, profile promotion, action resolution, or purge authorization.

### 13.6 Lazy action

A lazy action is an action candidate created at one time but executed later. It must be revalidated if relevant self-model, policy, source, lookup, or purge state changes.

### 13.7 Stale replay

Stale replay is replay of a historical decision context whose self-model or dependencies are now stale. Stale replay is audit-only by default.

### 13.8 Diversity calibration

Diversity calibration is the process of grounding a diversity-weighted agreement score in fixtures, thresholds, known failure modes, and policy-approved allowed use.

---

## 14. Draft 5 completion-pass terms

### 14.1 Purge attestation

A purge attestation is a portable, content-safe proof object showing that a purge request, authorization, dependency graph, event, tombstones, replay impact, and external index invalidations were recorded.

### 14.2 External purge notarization

External purge notarization records that a purge attestation or signed manifest was submitted to an external timestamp, audit, compliance, transparency, or notarization system.

### 14.3 External index invalidation

External index invalidation is the standardized process for deleting, tombstoning, rebuilding, or quarantining content in vector stores, graph stores, caches, search indexes, and other indexes outside the core evidence store.

### 14.4 Human review timeout policy

A human review timeout policy defines default deadlines and expiration behavior when a review request does not specify its own deadline.

### 14.5 Human review expiration event

A human review expiration event records that a human review request expired and which default behavior was applied.

### 14.6 Meta replay governance state

Meta replay governance state records purge, stale self-model, human review, and diversity calibration context for meta-runtime replay.
