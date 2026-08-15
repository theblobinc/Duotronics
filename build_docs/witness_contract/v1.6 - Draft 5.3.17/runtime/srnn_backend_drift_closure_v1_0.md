# SRNN Backend Drift Closure v1.0

Status: source-refresh integration note.

## Observed drift

Draft 3 saw multiple SRNN backend changes in one day, including:

- SDK and formal model implementation.
- OpenAPI export.
- Cognition step migration.
- Proof interchange fixtures.
- Mutation policy.
- Live recurrent witness overlay.
- Stale evidence behavior.
- Python SDK test-runner correction.
- WGRNN Firehose package changes.

## Closure rule

Every backend drift item must be classified as:

```yaml
BackendDriftRecord:
  change_id: string
  source_commit: string
  affected_contracts: list[string]
  migration_required: boolean
  test_required: list[string]
  docs_updated: boolean
  runtime_verified: boolean
```

## Draft 2 queue compatibility warning

Do not point a Draft 3 runtime at a Draft 2 task queue schema without an explicit compatibility adapter. Silent witness promotion mismatches are more dangerous than hard failures.

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
