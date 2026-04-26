# English Claim and Evidence as a Duotronic Semantic Witness Profile v0.2

**Status:** Reference candidate profile  
**Version:** english-claim-evidence-profile@v0.2  
**Supersedes:** english-claim-evidence-profile@v0.1  
**Document kind:** Reference profile for natural-language witness extraction  
**Primary purpose:** Define how English text can be treated as a source of claim, entity, stance, evidence, contradiction, and provenance witnesses without treating text as truth by default.

---

## 1. Research boundary

English is not a numeric family. It is a natural-language evidence environment.

This profile does not attempt to define all English grammar. It defines a practical witness extraction layer for internal systems that read documents, posts, transcripts, messages, search results, and model outputs.

---

## 2. Core rule

A normalized English claim is not a true claim.

It is a canonical object that can be:

1. cited;
2. compared;
3. contradicted;
4. supported;
5. linked to source spans;
6. used in search;
7. routed through policy;
8. stored in lookup memory with authority limits.

---

## 3. Object types

The profile may produce:

1. `TextSpanWitness`;
2. `EntityWitness`;
3. `ClaimWitness`;
4. `EvidenceSpanWitness`;
5. `QuoteWitness`;
6. `StanceWitness`;
7. `ContradictionWitness`;
8. `TemporalAssertionWitness`;
9. `SourceAttributionWitness`;
10. `UncertaintyWitness`.

---

## 4. Claim witness schema

```yaml
ClaimWitness:
  claim_witness_id: string
  source_evidence_id: string
  normalized_claim_text: string
  claim_hash: string
  source_span: string
  speaker_or_author_ref: string | null
  modality: asserted | quoted | questioned | denied | joked | hypothetical | unknown
  entities: []
  temporal_scope: string | null
  evidence_status: supported | contradicted | disputed | unsupported | unknown
  trust_status: candidate | canonicalized | audit_only | rejected
```

---

## 5. Normalization

English claim normalization may include:

1. whitespace normalization;
2. quote boundary preservation;
3. entity canonicalization where supported;
4. tense and modality preservation;
5. source span pinning;
6. claim hash generation;
7. speaker/author preservation;
8. uncertainty preservation.

It must not remove modality in a way that changes meaning. "X happened", "X did not happen", "Did X happen?", and "Someone joked that X happened" are different.

---

## 6. Source relation

Every claim witness should retain a source relation:

```text
source text span
-> extracted claim
-> normalized claim
-> evidence relation
-> policy status
```

If the source span is missing, the witness should be audit-only or rejected.

---

## 7. Social and search behavior

When the English text comes from search or social platforms, the profile must preserve:

1. platform;
2. retrieval time;
3. author or source hash where available;
4. thread context;
5. quote/repost context;
6. edit/delete status if available;
7. source reliability diagnostic;
8. contradiction links.

---

## 8. Failure cases

1. quotation treated as assertion;
2. sarcasm treated as fact without uncertainty;
3. source span missing;
4. author attribution missing when required;
5. contradiction collapsed into agreement;
6. summary treated as original source;
7. unsupported claim promoted as truth;
8. model-generated text treated as external evidence.

---

## 9. Fixture set

Minimum fixtures should include:

1. direct assertion;
2. denial;
3. question;
4. quote;
5. attributed quote;
6. hypothetical;
7. contradiction pair;
8. unsupported claim;
9. claim with strong source;
10. social post with thread context;
11. transcript-derived claim;
12. model-output-derived claim.

---

## 10. Promotion target

This profile should remain `research_profile` or `sandbox_runtime_profile` until source-span preservation, modality preservation, contradiction handling, and policy integration are stable.


---

## 11. Draft 2 claim equivalence rule

> **Status tag:** normative for this profile

Two claim witnesses are equivalent only if one of the following is true:

1. their `normalized_claim_text` strings are identical after the profile's declared normalization;
2. a declared synonym/paraphrase bridge maps one claim to the other and emits a `BridgeResult`;
3. a human or policy-approved adjudication record links them as equivalent.

The default normalization for simple equality is:

```text
trim whitespace
-> lowercase
-> normalize internal whitespace
-> remove non-semantic punctuation only if declared
```

The default normalization must not remove:

1. negation;
2. modality;
3. speaker attribution;
4. temporal scope;
5. uncertainty markers;
6. quoted-vs-asserted distinction.

### 11.1 Modality preservation

Modality must match exactly unless a lossy equivalence bridge is declared.

Examples that are not equivalent by default:

```text
"X happened."
"X did not happen."
"Did X happen?"
"Alice claimed X happened."
"Alice joked that X happened."
"Suppose X happened."
```

### 11.2 Conflicting extractions from same source

If two model witnesses extract conflicting claims from the same source span, the system must create either:

1. a contradiction witness;
2. an ambiguity witness; or
3. an adjudication record.

It must not choose one claim silently.

### 11.3 Raw status value

Allowed `trust_status` values for this profile are:

```text
raw
candidate
canonicalized
audit_only
rejected
```
