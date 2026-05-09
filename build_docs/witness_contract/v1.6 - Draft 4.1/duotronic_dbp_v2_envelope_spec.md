# DBP v2 Object Envelope Specification

**Status:** normative wire and storage contract  
**Version:** dbp-v2-envelope@v1.0  
**Document kind:** canonical object envelope specification  
**Primary purpose:** Define the portable object wrapper used across APIs, storage, replay, federation, task queues, and interpreter/proof witnesses.

## 1. Envelope purpose

The DBP v2 envelope is the common frame for identity-bearing objects. It separates payload bytes from authority, policy, replay, provenance, and signature metadata.

## 2. Canonical envelope shape

```yaml
DBPv2Envelope:
  dbp_version: "2.0"
  envelope_id: string
  object_kind: string
  schema:
    schema_id: string
    schema_version: string
    schema_hash: string
  identity:
    canonical_identity_hash: string
    normalizer_id: string
    normalizer_version: string
    serializer_id: string
    serializer_version: string
  payload:
    media_type: application/json | application/octet-stream | text/plain | custom
    inline: object | string | null
    artifact_ref: string | null
    payload_hash: string
    payload_size: integer
  authority:
    authority_scope: representation_identity | runtime_gate | lookup_fact | claim_support | proof_status | computation_result | action_record | custom
    runtime_mode: normal | restricted | sandbox | audit_only | degraded | blocked
    trust_status: raw | candidate | canonicalized | audit_only | rejected | deprecated
    truth_status: not_applicable | unknown | supported | contradicted | disputed | policy_accepted | theorem | conjecture | computation
  provenance:
    producer_principal_id: string
    producer_node_id: string
    source_refs: []
    evidence_bundle_ids: []
    parent_envelope_ids: []
    created_at: string
  policy:
    policy_snapshot_id: string
    policy_decision_id: string
    obligations: []
  replay:
    replay_identity_ref: string
    replay_package_id: string | null
    deterministic: boolean
    expected_output_hash: string | null
  signature:
    signing_key_ref: string | null
    signature_alg: string | null
    signature: string | null
```

## 3. Hashing rule

`canonical_identity_hash` is computed over the canonical serialized identity fields only. It must not include transient fields such as request ID, created timestamp, UI display labels, temporary file paths, or cache keys.

`payload_hash` is computed over exact payload bytes. If `payload.inline` is JSON, the hash must use the canonical JSON serializer declared by the schema.

## 4. Object kinds

Required v1.6 object kinds include:

```text
EvidenceBundle
CandidateWitness
CanonicalWitnessFact
CanonicalMathObject
MathClaim
ClaimStatusTransition
LanglandsObject
LanglandsBridgeWitness
InterpreterRunWitness
ProofCheckerRunWitness
PolicyDecision
SRNNTaskWitness
OracleJobWitness
TemporalMetaObjectWitness
ReplayPackage
CorpusMigrationWitness
HumanReviewDecision
```

## 5. Validation stages

```text
parse envelope
-> validate DBP version
-> validate schema reference
-> validate payload hash
-> validate canonical identity fields
-> validate policy reference
-> validate replay reference if required
-> verify signature if present
-> persist or reject
```

## 6. Federation rule

Inter-node DBP envelopes must be accepted only after node admission policy and source integrity checks. A syntactically valid envelope from an untrusted node is evidence, not authority.

## 7. Replay rule

A replay package must include every DBP envelope needed to rebuild the target result, or provide policy-approved replay-equivalence references for external artifacts.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
