# Draft 4.1 Conformance Delta Validation Plan

Status: active Draft 4.1 validation plan.  
Generated: 2026-05-09.

## Purpose

This plan defines the minimum tests or evidence records needed to validate the
Draft 4.1 closeout layer after the documentation is committed.

## Validation cases

### V41-001 Contract version alias evidence

Assert that runtime evidence bundles include `WitnessContractVersionAlias` when
runtime state reports legacy `v8` names.

Expected result: release claims name both the runtime alias and Draft 4.1 corpus
version.

### V41-002 MCP recurrence tool maturity

Collect the live MCP tool manifest and execute representative read and write
recurrence calls under scoped principals.

Expected result: each tool is classified as `runtime_observed` or remains below
that level; no unobserved tool is release-verified.

### V41-003 WG-RNN chat context injection

Trigger a chat request with cognition-state injection and capture the resulting
context witness.

Expected result: the witness contains loop, node, readiness, authority, recall,
freshness, prompt hash, and no-unwitnessed-claims constraint.

### V41-004 Browser Chat / Workbench invocation

Exercise signed browser requests, nonce replay, allowlist denial, enabled
workbench operation, and disabled workbench operation.

Expected result: every invocation has an audit witness with request hash,
principal/subject, allowlist decision, mutation surface, and result/denial.

### V41-005 Mutation safety config

Capture mutation-safety config before a safe test mutation.

Expected result: mutation evidence references the active safety config and any
backup, git sync, or approval records.

### V41-006 Runtime feature applicability

Load a runtime profile with features such as context size, no-mmap, mlock,
CPU-MoE split, and KV cache type controls.

Expected result: evidence separates requested, translated, applied, unsupported,
and ignored features.

### V41-007 Runtime readiness persistence

Run status, smoke, and bench flows for a claimed model.

Expected result: readiness evidence persists status payload hash, effective
command hash, log hash, smoke result, benchmark result, and model identity.

## Exit criteria

```yaml
Draft41ConformanceExitCriteria:
  package_manifest_valid: required
  checksum_file_present: required
  V41_001: required
  V41_002: required_for_mcp_release_claims
  V41_003: required_for_chat_memory_claims
  V41_004: required_for_browser_tool_claims
  V41_005: required_for_mutation_claims
  V41_006: required_for_runtime_feature_claims
  V41_007: required_for_model_readiness_claims
```
