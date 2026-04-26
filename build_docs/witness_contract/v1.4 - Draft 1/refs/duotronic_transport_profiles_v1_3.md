# Duotronic Transport and Source Profiles v1.3

**Status:** Source-spec baseline candidate  
**Version:** transport-source-profiles@v1.3  
**Document kind:** Normative transport/source boundary contract plus reference profiles  
**Primary purpose:** Define Witness8, DBP, WSB2, EvidenceBundle, SourceEvidenceRecord, ModelWitness transport boundaries, and ingestion wrappers without confusing transport or source encoding with canonical semantics.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

This document governs carrier forms and source wrappers.

It includes:

1. Witness8 rows;
2. DBP frames;
3. WSB2 sparse rows;
4. evidence bundles;
5. source evidence records;
6. model witness payload wrappers;
7. node witness event wrappers;
8. media transcript wrappers;
9. search result set wrappers;
10. social thread wrappers.

---

## 2. Transport-before-semantics rule

A transport or source wrapper must be validated before its payload is interpreted.

Failed transport is not absence. Failed source retrieval is not zero. Empty search result is not proof of absence unless the query and source profile explicitly support that conclusion.

---

## 3. Evidence bundle profile

An evidence bundle is the universal source wrapper for v1.4.

Required fields:

1. evidence ID;
2. source type;
3. source reference;
4. capture time;
5. capture node ID;
6. raw payload hash;
7. MIME type;
8. modality;
9. source integrity;
10. provenance;
11. privacy class;
12. trust status.

---

## 4. Token-free absence

Transport systems may represent no active payload as token-free absence only where the transport profile declares that behavior.

Token-free absence is not:

1. numeric zero;
2. malformed payload;
3. rejected payload;
4. unknown value;
5. empty string unless declared.

---

## 5. Source wrapper classes

| Wrapper | Use |
|---|---|
| `EvidenceBundle` | generic raw evidence wrapper |
| `SourceEvidenceRecord` | search/social/document source record |
| `SearchResultSet` | grouped search result context |
| `ThreadContextRecord` | social/discussion context |
| `TranscriptEvidenceRecord` | audio/video transcript wrapper |
| `ModelOutputEnvelope` | model-output carrier before structured witness extraction |
| `NodeWitnessEvent` | distributed node event wrapper |

---

## 6. Validation requirements

Transport/source validation must check:

1. schema shape;
2. required fields;
3. payload hash;
4. connector version;
5. source reference shape;
6. privacy class;
7. timestamp validity;
8. parent/source context;
9. platform-specific constraints;
10. integrity tag where available.

---

## 7. Failure states

```text
failed_frame
failed_shape_check
failed_security_check
missing_hash
payload_unavailable
connector_failed
source_deleted
source_edited_after_capture
privacy_blocked
context_missing
transport_bypass_required
```

---

## 8. Non-claims

Transport and source profiles carry information. They do not define canonical semantics by themselves.
