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
