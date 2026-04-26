# Duotronic Search and Social Evidence Ingestion v1.3

**Status:** Source-spec baseline candidate  
**Version:** search-social-evidence-ingestion@v1.3  
**Supersedes:** search-social-evidence-ingestion@v1.2  
**Supersedes:** search-social-evidence-ingestion@v1.1  
**Supersedes:** search-social-evidence-ingestion@v1.0  
**Document kind:** Normative source-evidence ingestion contract plus reference schemas  
**Primary purpose:** Define how search engines, social feeds, comments, threads, videos, documents, transcripts, and platform metadata become Duotronic evidence bundles and source witnesses without being treated as truth by default.

---

## 1. Scope

This contract covers information retrieved from:

1. internal search engines;
2. web search engines;
3. social feeds;
4. Bluesky-like post streams;
5. Facebook-like posts and comments;
6. Reddit-like posts, comments, and threads;
7. Discord-like channels and messages;
8. YouTube-like videos, descriptions, comments, and transcripts;
9. blogs, web pages, and documents;
10. user-uploaded documents;
11. external datasets and APIs.

The contract is platform-agnostic. Platform-specific adapters may extend it.

---

## 2. Core rule

A search or social item is source evidence.

It can support:

1. a claim witness;
2. contradiction witness;
3. source witness;
4. author witness;
5. propagation witness;
6. temporal witness;
7. trend witness;
8. reliability diagnostic.

It is not truth by default.

---

## 3. Source evidence record

```yaml
SourceEvidenceRecord:
  source_record_id: string
  platform: internal_search | web | bluesky | facebook | reddit | discord | youtube | document | other
  source_url_or_ref: string
  retrieval_time: string
  retrieval_node_id: string
  connector_id: string
  connector_version: string
  content_hash: string
  metadata_hash: string | null
  context_hash: string | null
  author_or_origin_hash: string | null
  parent_record_ids: []
  thread_id_hash: string | null
  edit_status: original | edited | deleted | unavailable | unknown
  visibility_class: public | private | internal | restricted | unknown
  platform_metrics:
    likes: integer | null
    reposts: integer | null
    comments: integer | null
    views: integer | null
    rank: integer | null
  raw_payload_ref: string
  evidence_bundle_id: string
```

Platform metrics are diagnostic features, not proof.

---

## 4. Claim witness extraction

A claim witness extracted from search or social sources should include:

```yaml
ClaimWitness:
  claim_witness_id: string
  source_record_id: string
  normalized_claim_text: string
  claim_hash: string
  source_span_ref: string
  author_or_origin_hash: string | null
  modality: asserted | quoted | questioned | contradicted | joked | uncertain | unknown
  evidence_relation: supports | contradicts | mentions | repeats | cites | unknown
  extraction_model_witness_ids: []
  confidence:
    extraction_confidence: number | null
    source_reliability_score: number | null
    corroboration_score: number | null
  trust_status: raw | candidate | canonicalized | audit_only | rejected
```

A normalized claim is not a true claim. It is an object that can be compared, supported, contradicted, cited, or rejected.

---

## 5. Source reliability diagnostic

```yaml
SourceReliabilityDiagnostic:
  diagnostic_id: string
  source_record_id: string
  profile_id: string
  signals:
    source_history: string | null
    independent_corroboration: number | null
    contradiction_count: integer
    edit_or_delete_history: string | null
    platform_context_quality: string | null
    content_specificity: string | null
    citation_quality: string | null
  decision:
    reliability_class: unknown | low | mixed | moderate | high | authoritative_for_context
    allowed_use: observe | candidate_support | audit_only | sandbox | restricted | normal
```

Reliability diagnostics require baselines before they can influence authority.

---

## 6. Video and transcript ingestion

Video-like sources must separate:

1. video metadata;
2. audio transcript;
3. visual frames;
4. captions;
5. comments;
6. description;
7. channel or author metadata;
8. extracted claims;
9. derived summaries.

A transcript is not the video. A summary is not the transcript. A comment is not the source claim. These must remain separate evidence records.

---

## 7. Thread context

Social and discussion platforms often require context.

Adapters should record:

1. parent message;
2. replied-to message;
3. quoted source;
4. thread root;
5. deleted ancestors where visible;
6. timestamp order;
7. platform-specific visibility constraints.

A claim extracted without context should receive lower authority or audit-only status.

---

## 8. Search result ingestion

A search result page should be represented as:

```yaml
SearchResultSet:
  result_set_id: string
  query_profile_id: string
  query_text_hash: string
  retrieval_time: string
  engine_id: string
  ranking_profile_id: string | null
  result_records: []
  personalization_profile: none | unknown | declared | prohibited
```

Ranking position may be stored. Ranking position must not be treated as truth.

---

## 9. Contradiction handling

If sources conflict, the system should create contradiction witnesses instead of forcing a single answer.

```yaml
ContradictionWitness:
  contradiction_id: string
  claim_hash_a: string
  claim_hash_b: string
  source_record_ids: []
  contradiction_type: direct | temporal | scope | definition | attribution | uncertain
  adjudication_status: unresolved | resolved | audit_only | policy_review
```

---

## 10. Privacy and access

Adapters must preserve privacy class and access boundaries.

A source record may be usable for internal analysis but not for model training, outbound search, external model inference, or cross-node sharing depending on policy.

Privacy class must flow into evidence bundles, model witnesses, and profile candidates.

---

## 11. Non-claims

This contract does not rank sources globally. It defines the evidence wrapper required before search and social content can enter Duotronic witness systems.


---

## 12. Deleted, edited, or unavailable source handling

> **Status tag:** normative

If a source record is later marked as `deleted`, `unavailable`, `removed`, access-restricted, or materially edited, dependent witnesses must be re-evaluated.

### 12.1 Required re-evaluation

The system must find all dependent:

1. claim witnesses;
2. source reliability diagnostics;
3. contradiction witnesses;
4. profile candidates;
5. lookup-memory records;
6. recurrent-state enrichments;
7. model-gating decisions;
8. promotion requests.

### 12.2 Default demotion rule

If a claim witness depends solely on a source that becomes deleted or unavailable, the default action is:

```text
canonicalized or candidate -> audit_only
```

If the witness had runtime authority, the system must remove or disable it from authoritative lookup memory unless policy declares a retention exception.

### 12.3 Retention exception

A retention exception may allow continued internal use of a deleted-source record only if:

1. the original content hash is retained lawfully and according to privacy policy;
2. the witness is marked as source-unavailable;
3. user-facing presentation does not imply the source is still available;
4. L5 policy permits continued audit or replay use.

### 12.4 Deletion event schema

```yaml
SourceAvailabilityEvent:
  availability_event_id: string
  source_record_id: string
  prior_edit_status: original | edited | unknown
  new_edit_status: deleted | unavailable | removed | access_restricted | materially_edited
  detected_at: string
  detected_by_node_id: string
  affected_witness_ids: []
  required_policy_action: audit_only | demote | remove_from_lookup | human_review
```


---

## 13. Chronological personal and organizational streams

> **Status tag:** normative

Search and social sources may be imported as chronological self-evidence streams when policy permits.

Examples:

1. YouTube watch history;
2. playlists and likes;
3. posts and replies;
4. comments and edits;
5. Discord thread participation;
6. Reddit saved/upvoted/comment history where available;
7. internal search query history;
8. project communication history.

The ingestion adapter must preserve:

1. source event time;
2. capture time;
3. platform/source reference;
4. actor or pseudonymous actor reference;
5. parent/thread references;
6. content hash;
7. metadata hash;
8. privacy class;
9. deletion/edit status.

### 13.1 Chronological stream handoff

A source ingestion adapter may emit a `PersonalHistorySourceRecord` or `ChronologicalEvidenceStream` reference. The owning contract is `duotronic_chronological_self_evidence_contract_v1_2.md`.

### 13.2 Internal use and outbound boundary

A source record may be allowed for internal self-modeling while prohibited from outbound model calls, public claims, or external actions.

The ingestion layer must preserve policy-relevant restrictions so L5 can enforce them later.

---

## 14. Search as planner action

> **Status tag:** normative

When a planner or decision system initiates a search, the search request must be linked to an `ActionCandidateWitness`.

Search-initiated evidence should record:

1. action candidate ID;
2. decision context ID;
3. query profile;
4. expected evidence type;
5. stopping condition;
6. policy decision ID.

A search result without action provenance may still be ingested, but it cannot support action-outcome learning.


---

## 15. Purge-aware source ingestion

> **Status tag:** normative

Search and social source records must support purge and privacy deletion.

If a source is subject to `EvidencePurgeRequest`, the ingestion layer must:

1. identify source records and evidence bundles;
2. identify claim witnesses and contradiction witnesses derived from the source;
3. identify personal-history records where applicable;
4. notify lookup memory;
5. notify profile synthesis records where the source influenced candidates;
6. record source deletion or purge event;
7. stop future retrieval/use where required.

Source deletion and source purge are different.

```text
source deletion = external source no longer available or removed
source purge = internal policy requires removal/tombstoning of stored evidence and derivatives
```

### 15.1 Human review for source disputes

If source ownership, privacy class, deletion request, or actor scope is ambiguous, the ingestion layer must route to `HumanReviewRequest` or privacy review according to policy.
