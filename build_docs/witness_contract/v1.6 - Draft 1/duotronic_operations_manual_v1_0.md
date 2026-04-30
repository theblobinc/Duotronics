# Duotronic Operations Manual v1.0

**Status:** operational reference with normative incident boundaries  
**Version:** operations-manual@v1.0

## 1. Health signals

Required health checks:

```text
API liveness and readiness
PostgreSQL connection and migration version
Redis connection and queue depth
Milvus connection and collection status
policy snapshot loaded
interpreter sandbox worker availability
Lisp bridge circuit state
Julia bridge circuit state
SRNN oracle queue depth
MCP endpoint reachability if enabled
artifact store read/write check
replay verifier availability
```

## 2. Metrics

Required metrics:

```text
dbp_envelope_write_count
dbp_envelope_reject_count
canonical_witness_count
policy_decision_count_by_decision
interpreter_run_count_by_language
interpreter_run_failure_count_by_reason
proof_checker_success_count
proof_checker_failure_count
srnn_oracle_job_queue_depth
srnn_oracle_job_latency_ms
witness_event_id_missing_count
mcp_query_latency_ms
mcp_query_failure_count
replay_verification_failure_count
human_review_queue_depth
```

## 3. Logs

Logs must include request IDs, envelope IDs, policy decision IDs, replay identity refs, and principal IDs. Logs must not include secrets, full sensitive payloads, or unredacted private evidence unless a restricted log sink is configured.

## 4. Backup and recovery

1. PostgreSQL backups are mandatory for canonical state.
2. Artifact store backups must be content-addressed and hash-verified.
3. Redis backups are optional unless used for delayed workflow state; Redis is not canonical.
4. Milvus indexes are rebuildable from PostgreSQL and artifacts; backup is recommended for recovery speed but not truth.
5. Replay packages must be exportable for every promoted profile and theorem-status claim.

## 5. Disaster recovery test

A conforming staging environment must periodically run:

```text
restore PostgreSQL backup
-> restore artifact store
-> rebuild Redis ephemeral state
-> rebuild Milvus projections
-> verify policy snapshots
-> run replay package smoke tests
-> run conformance fixtures
```

## 6. Incident response

Incident classes:

```text
canonical_store_corruption
policy_engine_unavailable
interpreter_sandbox_escape
mcp_endpoint_malformed_response
srnn_oracle_job_backlog
witness_event_id_gap
replay_verification_mismatch
human_review_sla_breach
```

Each incident creates an `OperationalIncidentWitness` and may trigger policy degradation.

## 7. SLA targets for prototype candidates

Initial non-production targets:

```text
API health response: < 500 ms
policy preflight p95: < 250 ms
canonical witness write p95: < 1000 ms
interpreter queue admission: < 2000 ms
SRNN oracle job p95 latency: profile-defined
MCP query p95: endpoint-defined
replay verification: batch/offline
```

These are targets, not guarantees. Production SLA must be declared separately.

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
