# Duotronic Observability and OpenTelemetry Profile v1.0

**Status:** Draft 2 normative observability profile

## 1. Required traces

Trace spans must be emitted for:

1. evidence ingestion;
2. canonicalization;
3. interpreter run;
4. proof checker run;
5. policy evaluation;
6. human review decision;
7. MCP tool call;
8. SRNN oracle job;
9. backup snapshot;
10. git-sync attempt;
11. replay package creation.

## 2. Required metrics

Prometheus metric examples:

```text
duotronic_witness_ingest_total
duotronic_canonicalization_failures_total
duotronic_policy_decision_total
duotronic_interpreter_run_seconds
duotronic_proof_checker_run_seconds
duotronic_mcp_tool_call_total
duotronic_mcp_tool_call_failures_total
duotronic_sandbox_timeout_total
duotronic_replay_mismatch_total
duotronic_human_review_queue_depth
duotronic_backup_snapshot_total
duotronic_git_sync_failures_total
```

## 3. Required log fields

Structured logs must include:

```yaml
timestamp: string
service: string
trace_id: string
span_id: string
principal_id: string | null
object_id: string | null
witness_id: string | null
policy_decision_id: string | null
tool_name: string | null
risk: string | null
ok: boolean
error_code: string | null
```

## 4. Redaction

Logs must redact:

1. passwords;
2. API keys;
3. admin keys;
4. tokens;
5. private proof payloads if marked sensitive;
6. `.env` material;
7. raw social/private evidence where policy requires privacy.

## 5. Current MCP observation

Draft 2 records that MCP self-test was green while some API responses were fallback/degraded. Observability must distinguish:

```text
healthy
degraded_fallback
schema_mismatch
unavailable
permission_denied
```

## Draft 4 carry-forward update - 2026-05-08

This document is retained in the v1.6 Draft 4 corpus as part of the full Draft 3
carry-forward. Draft 4 adds newer SRNN Server runtime observations rather than
removing this baseline. For current Draft 4 interpretation, read:

- `README_v1_6_draft_4.md`
- `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
- `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
- `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
- `runtime/llama_server_runtime_readiness_contract_v1_0.md`

Draft 4 updates the runtime boundary with the current SRNN compose stack,
per-node `wg-rnn` service, GPU-worker llama-server large-model path, runtime
model manifest/smoke/bench endpoints, memlock diagnostics, and Agent Lab/MCP
backup-log witness handling. This update does not claim live production
certification; it records the source-observed contract and follow-up validation
requirements.
