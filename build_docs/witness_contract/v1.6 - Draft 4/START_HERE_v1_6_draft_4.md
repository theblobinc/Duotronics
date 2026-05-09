# Start Here - Duotronic v1.6 Draft 4

Status: active Draft 4 reading guide.
Generated: 2026-05-08

## Purpose

Start here if you need the completed Draft 4 package. This directory contains
the full Draft 3 corpus plus the Draft 4 SRNN runtime update layer. It is meant
to be comprehensive enough to stand on its own.

## Fast path for implementation readers

1. `README_v1_6_draft_4.md` - orientation and Draft 4 release boundary.
2. `RELEASE_NOTES_v1_6_draft_4.md` - what changed from Draft 3.
3. `duotronic_draft4_srnn_source_refresh_2026_05_08.md` - current SRNN source
   observations and their contract implications.
4. `duotronic_srnn_federated_runtime_stack_profile_v1_0.md` - compose/runtime
   topology update.
5. `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md` - large
   model GPU-worker and llama-server runtime profile.
6. `runtime/llama_server_runtime_readiness_contract_v1_0.md` - readiness and
   runtime-status witness contract.
7. `duotronic_draft4_runtime_model_observability_profile_v1_0.md` - smoke,
   bench, model manifest, and effective-command evidence.
8. `duotronic_draft4_validation_and_completeness_report.md` - package integrity
   and validation statement.
9. `refs/manifest/MANIFEST_v1_6_draft_4_complete.md` - complete file list.

## Fast path for governance and security readers

1. `duotronic_draft4_agent_lab_mutation_backup_witness_profile_v1_0.md`
2. `security/gpu_worker_runtime_security_and_memlock_profile_v1_0.md`
3. `security/direct_mutation_tool_enforcement_v1_2.md`
4. `duotronic_mutation_policy_validation_profile_v1_1.md`
5. `duotronic_security_architecture_v1_0.md`
6. `duotronic_stridethreat_model_v1_0.md`

## Fast path for SRNN runtime readers

1. `duotronic_runtime_recurrence_complete_integration_document_v1_0.md`
2. `duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md`
3. `duotronic_multimodal_witness_runtime_profile_v1_1.md`
4. `runtime/srnn_backend_drift_closure_v1_0.md`
5. `duotronic_srnn_backend_current_state_review_2026_04_30.md`
6. `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
7. `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`

## What is different from Draft 3

Draft 3 closed the initial implementation-readiness and RC-blocker gap. Draft 4
updates that comprehensive body to reflect the newer SRNN Server runtime shape:

- unified compose profiles and node-specific role composition;
- explicit `wg-rnn` recurrent cognition service in compose;
- Ollama proxy and remote proxy as model-delegation boundaries;
- GPU worker support for large llama-server-backed narrative models;
- explicit 262144-context model profiles for Qwen/DeepSeek-style large models;
- runtime flags for no-mmap, mlock, n_cpu_moe, and KV cache types;
- runtime model manifests, smoke tests, benchmark endpoints, memlock diagnostics;
- tests that assert command construction, startup/failed-start handling,
  runtime config aliasing, model cache separation, and binary status reporting;
- Agent Lab/MCP backup-log evidence as a mutation witness stream.

## Non-claims

Draft 4 does not claim that the production cluster was started from this package,
that every container was live-verified in this environment, or that every test
passed here. It records the current contract, source-observed implementation
surface, and validation expectations for the next implementation pass.
