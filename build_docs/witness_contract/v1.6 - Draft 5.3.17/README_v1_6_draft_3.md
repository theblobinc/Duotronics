# Duotronic v1.6 Draft 3 Corpus

**Status:** Research specification draft  
**Version:** v1.6-draft-3  
**Document kind:** Release overview and reading entry point  
**Primary purpose:** Declare the complete Draft 3 corpus, preserve Draft 2 coverage, and add runtime recurrence tuning, MCP verified/target-tool separation, and current SRNN source updates.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Summary

v1.6 Draft 3 is a complete Markdown corpus upgrade over v1.6 Draft 2. It keeps the v1.5 carry-forward corpus and the Draft 2 implementation-readiness pass, then adds a runtime tuning layer for recurrence and cognition.

Draft 3 makes three changes normative for the implementation-facing profile:

1. Time, absence, decay, and gap accounting are witness-bearing runtime objects.
2. Current MCP capabilities must be separated from desired target capabilities.
3. SRNN source-code observations from the current repository are now represented as corpus update records, including stdio principal policy, allowed-root constraints for direct mutation tools, live recurrent witness overlay, stale-evidence authority behavior, and identity-oracle auto-registration.

## 2. What Draft 3 adds

New or substantively upgraded documents include:

- `duotronic_runtime_recurrence_tuning_profile_v1_0.md`
- `duotronic_temporal_witness_and_absence_profile_v1_0.md`
- `duotronic_wgrnn_gate_reference_defaults_v1_0.md`
- `duotronic_mcp_missing_runtime_tools_backlog_v1_0.md`
- `duotronic_mcp_verified_vs_target_tool_matrix_v1_0.md`
- `duotronic_srnn_source_update_review_2026_04_30_draft_3.md`
- `duotronic_live_recurrent_witness_overlay_contract_v1_0.md`
- `duotronic_stdio_principal_policy_v1_0.md`
- `duotronic_direct_mutation_tools_security_addendum_v1_1.md`
- `duotronic_runtime_recurrence_complete_integration_document_v1_0.md`

## 3. Manifest location change

All manifest documents now live under:

```text
refs/manifest/
```

This includes retained Draft 1 and Draft 2 manifests plus `MANIFEST_v1_6_draft_3_complete.md`.

## 4. Reading order

For implementation:

1. `README_v1_6_draft_3.md`
2. `duotronic_runtime_recurrence_complete_integration_document_v1_0.md`
3. `duotronic_runtime_recurrence_tuning_profile_v1_0.md`
4. `duotronic_temporal_witness_and_absence_profile_v1_0.md`
5. `duotronic_wgrnn_gate_reference_defaults_v1_0.md`
6. `duotronic_mcp_verified_vs_target_tool_matrix_v1_0.md`
7. `duotronic_srnn_source_update_review_2026_04_30_draft_3.md`
8. `duotronic_live_recurrent_witness_overlay_contract_v1_0.md`
9. `duotronic_policy_engine_spec_v1_0.md`
10. `duotronic_security_architecture_v1_0.md`
11. `refs/manifest/MANIFEST_v1_6_draft_3_complete.md`

## 5. Non-claims

Draft 3 does not claim all target MCP tools already exist. It explicitly distinguishes:

- verified tools observed in the MCP server;
- target tools required for stronger recurrence operations;
- backlog items that must not be treated as available runtime authority.

Draft 3 does not change the policy that unresolved mathematical conjectures may be represented and studied but not promoted to theorem without proof authority.

## 6. Draft 3 source-refresh update

An updated Draft 3 source refresh has been added in this package. Start with:

- `README_v1_6_draft_3_updated.md`
- `RELEASE_NOTES_v1_6_draft_3_updated.md`
- `duotronic_draft_3_source_refresh_summary_2026_04_30.md`
- `duotronic_srnn_source_update_review_2026_04_30_draft_3_update.md`
- `refs/manifest/MANIFEST_v1_6_draft_3_updated.md`

This update incorporates the latest SRNN source changes after the previous Draft 3 package, including SDK/formal-model artifacts, OpenAPI export, phase-3 threat modeling, mutation policy, validation suite, cognition migration, and WG-RNN temporal authority behavior.

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
