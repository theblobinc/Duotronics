# Duotronic Source Architecture Overview v1.7

**Status:** Internal source architecture draft  
**Version:** 1.7-source-overview  
**Document kind:** Reference architecture and reading guide  
**Primary purpose:** Explain the current v1.4 Duotronic source-spec stack, including DPFC, the Witness Contract, representation bridges, auto-profile learning, distributed model nodes, search/social evidence ingestion, and policy-gated profile promotion.

---

## 1. What Duotronics is in v1.4

Duotronics is a presence-first, witness-gated, representation-bridging and profile-learning framework.

It is designed to take many forms of information, including mathematical notation, scripts, language, images, documents, social feeds, search results, and machine-learning model outputs, and route them through explicit witness and canonicalization paths.

The system is not built around a single universal parser. It is built around profiles.

A profile declares:

1. what kind of object exists;
2. how to validate it;
3. how to distinguish absence, zero, invalidity, and unknown;
4. how to normalize it;
5. how to serialize it;
6. how to bridge it into the DPFC core or another canonical object layer;
7. how to test it;
8. how to govern its authority.

The v1.4 addition is that profiles may be learned or proposed automatically, but they still require validation, replay, retention diagnostics, registry staging, and policy approval.

---

## 2. The source-spec stack

```text
Source Architecture
|
|-- DPFC Core
|   |-- realized magnitudes
|   |-- family-native values
|   |-- canonical identity
|   |-- bridge boundaries
|   |-- export/import policy
|
|-- Representation Bridge Contract
|   |-- source profile
|   |-- target profile
|   |-- canonical object
|   |-- preservation claims
|   |-- expected loss
|
|-- Witness Contract
|   |-- evidence bundles
|   |-- model witnesses
|   |-- candidate witnesses
|   |-- canonical witness facts
|   |-- L1/L2/L2M/L3/L4/L5 runtime path
|
|-- Auto-Profile Learning Contract
|   |-- segmentation discovery
|   |-- relation discovery
|   |-- candidate profile synthesis
|   |-- fixture generation
|   |-- cross-model adjudication
|
|-- Distributed Model Node Protocol
|   |-- node-local inference
|   |-- model witness emission
|   |-- cross-node replay
|   |-- cluster adjudication
|
|-- Search and Social Evidence Ingestion
|   |-- source records
|   |-- claim witnesses
|   |-- source reliability diagnostics
|   |-- contradiction witnesses
|
|-- Registries and Implementation Specs
|   |-- schema registry
|   |-- family registry
|   |-- profile synthesis registry
|   |-- normalizer profiles
|   |-- transport profiles
|   |-- policy shield
|   |-- migration guide
|   |-- retention diagnostics
|
`-- Research and Reference Profiles
    |-- Roman numerals
    |-- English claim/evidence
    |-- glyphic script visual-semantic
    |-- EDO
    |-- acoustics
    |-- QCD analogy
    |-- selective witness state spaces
    |-- GCD-jump recurrences
    `-- pronic-centered polygon families
```

---

## 3. Primary data movement

The standard runtime flow is:

```text
raw event
-> source/transport validation
-> evidence bundle
-> modality decode
-> candidate witness extraction
-> registry lookup
-> normalizer selection
-> canonicalization
-> policy gate
-> lookup memory
-> recurrent state
-> retention diagnostics
-> replay identity
-> possible meta or architecture action
```

The auto-profile learning flow is:

```text
unprofiled stream
-> evidence bundle cluster
-> model witnesses
-> segmentation candidates
-> relation candidates
-> witness candidates
-> profile candidate
-> normalizer candidate
-> bridge candidate
-> fixture pack
-> replay trace set
-> adjudication
-> registry staging
-> sandbox or rejection
```

The two flows are intentionally separate. The first flow uses approved profiles. The second flow proposes new profiles.

---

## 4. Ownership boundaries

| Concern | Owning document |
|---|---|
| Positive core and family-aware representation | DPFC |
| Runtime trust and failure states | Witness Contract |
| Bridge profile schema and preservation/loss rules | Representation Bridge Contract |
| Learned profile lifecycle | Auto-Profile Learning Contract |
| Multi-model distributed witness emission | Distributed Model Node Protocol |
| Search/social source evidence | Search Social Evidence Ingestion |
| Profile staging and status ladder | Profile Synthesis Registry |
| Versioned IDs and compatibility | Schema Registry |
| Family declaration and promotion | Family Registry |
| Deterministic normal-form construction | Normalizer Profiles |
| Transport and source wrappers | Transport Profiles |
| Runtime modes, vetoes, bypass, rollback | Policy Shield Guide |
| Semantic changes and replay migration | Migration Guide |
| Measurement of preservation | Retention Diagnostics |
| Historical fixtures and lab lineage | Lab Evidence Registry |

---

## 5. What systems must not confuse

1. Raw source data is not a witness fact.
2. A witness candidate is not canonical identity.
3. A model output is not authority.
4. A learned profile is not a promoted profile.
5. Search support is not proof.
6. Social agreement is not proof.
7. A glyphic visual identity is not necessarily a translation.
8. A normalized English claim is not necessarily a true claim.
9. A bridge that preserves value may still lose display or provenance.
10. A policy-approved runtime gate is not a mathematical theorem.

---

## 6. Minimal implementation shape

A minimal v1.4 implementation should include:

```text
EvidenceBundleStore
ModelWitnessStore
CandidateWitnessStore
CanonicalWitnessStore
SchemaRegistry
FamilyRegistry
ProfileSynthesisRegistry
NormalizerRegistry
BridgeRegistry
PolicyShield
ReplayHarness
RetentionDiagnostics
MigrationPlanner
DistributedNodeEventLog
```

Minimum APIs:

```text
ingest_evidence()
emit_model_witness()
create_candidate_witness()
synthesize_profile_candidate()
validate_profile_candidate()
canonicalize()
bridge()
policy_gate()
record_replay()
score_retention()
stage_profile()
promote_or_reject_profile()
```

---

## 7. Reading order

For architecture review:

1. README
2. Source Architecture Overview
3. DPFC
4. Witness Contract
5. Representation Bridge Contract
6. Auto-Profile Learning Contract
7. Distributed Model Node Protocol
8. Search/Social Evidence Ingestion
9. Profile Synthesis Registry
10. Policy Shield Guide
11. Migration Guide

For implementation:

1. Schema Registry
2. Family Registry
3. Normalizer Profiles
4. Representation Bridge Contract
5. Transport Profiles
6. Witness Contract
7. Auto-Profile Learning Contract
8. Retention Diagnostics
9. Policy Shield Guide
10. Migration Guide


---

## 8. Draft 2 architecture clarification

> **Status tag:** reference

Draft 2 adds a central glossary and hardens the profile lifecycle.

The architecture now separates four distinct concerns:

1. **Profile synthesis:** candidate creation, testing, rejection, demotion, and promotion requests.
2. **Family registration:** promoted runtime-referenceable profiles and families.
3. **Learning mode:** whether auto-profile learning may run and what sources/models it may invoke.
4. **Runtime mode:** whether a profile, witness, bridge, source, or gate may influence operation.

A learned or hand-authored profile moves through the Profile Synthesis Registry first. If it is promoted to `reference_profile` or `normative_profile`, it receives a Family Registry handoff record and a runtime-referenceable Family Registry entry.

