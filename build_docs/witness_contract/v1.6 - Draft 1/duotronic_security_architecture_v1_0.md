# Duotronic Security Architecture v1.0

**Status:** normative security contract  
**Version:** security-architecture@v1.0  
**Document kind:** threat model, authentication, authorization, transport security, data integrity, and dependency-risk specification

## 1. Security goals

1. Protect canonical witness and mathematical identity from unauthorized mutation.
2. Prevent interpreter runtimes from escaping sandbox boundaries.
3. Prevent Redis, Milvus, caches, search indexes, or MCP endpoints from becoming hidden authorities.
4. Make all authority-changing actions auditable and replayable.
5. Preserve purge, privacy, and human review boundaries.

## 2. Principal model

```yaml
Principal:
  principal_id: string
  principal_kind: human | service | node | runtime | oracle | mcp_endpoint | admin | anonymous
  auth_method: token | mTLS | signed_envelope | local_socket | none
  scopes: []
  status: active | suspended | revoked
```

Required scopes include:

```text
duotronic:evidence:write
duotronic:witness:canonicalize
duotronic:math:write
duotronic:math:promote
duotronic:interpreter:execute
duotronic:proof:check
duotronic:policy:override
duotronic:srnn:task:write
duotronic:mcp:query
duotronic:admin:review
```

## 3. Authentication rules

1. Public unauthenticated writes are forbidden.
2. Node-to-node writes require mTLS or signed DBP envelopes.
3. MCP endpoint queries require endpoint registration and scope `duotronic:mcp:query`.
4. Admin decisions require human or configured governance principal, not a raw model output.

## 4. Network security

1. PostgreSQL, Redis, Milvus, Lisp bridge, Julia bridge, and MCP endpoints must not be exposed publicly by default.
2. Service-to-service traffic outside a single host should use mTLS or a private network overlay.
3. Redis may hold enrollment tokens and ephemeral coordination state only with TTLs.
4. Milvus may hold embeddings only with PostgreSQL back references.

## 5. Sandbox threat model

Untrusted code may attempt to:

1. exfiltrate secrets;
2. modify canonical stores;
3. consume resources indefinitely;
4. abuse network access;
5. poison caches or vector indexes;
6. fabricate proof or witness results.

Mitigations are defined in `duotronic_sandbox_specification_v1_0.md`.

## 6. Data integrity

1. Every DBP envelope stores payload hash and canonical identity hash.
2. Audit events form a hash chain.
3. Replay packages include all source hashes.
4. Artifact stores must be content-addressed or include tamper-evident metadata.
5. Signature verification failures produce `source_integrity_reject`.

## 7. Dependency management

1. Runtime images must pin language versions and package lockfiles.
2. Proof checkers and interpreters must publish runtime fingerprints.
3. Vulnerability scans must produce `DependencyRiskWitness` records for production candidates.
4. Emergency dependency revocation must demote affected proof/computation authority to `audit_only` until revalidated.

## 8. Secret handling

Secrets must not appear in evidence payloads, interpreter stdout, DBP envelopes, replay packages, or human review packets unless specifically authorized as sensitive evidence. Redaction must happen before vector indexing.

## 9. Incident states

```text
suspected_key_leak
runtime_escape_attempt
policy_bypass_attempt
unauthorized_canonical_write
replay_hash_mismatch
mcp_endpoint_integrity_failure
vector_index_poisoning
redis_state_conflict
```

Each incident state creates an evidence bundle, audit event, policy review, and replay impact record.

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
