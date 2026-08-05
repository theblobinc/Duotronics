# Start Here - Duotronic v1.6 Draft 4.1

Status: active Draft 4.1 reading guide.  
Generated: 2026-05-09.

## Purpose

Start here for the completed Draft 4.1 package. Draft 4.1 is the full Draft 4
corpus plus the closeout layer needed before moving to the next contract phase.

The most important rule: Draft 4.1 separates what the SRNN Server source shows,
what tests cover, what runtime tools can expose, and what a production release
is allowed to claim.

## Fast path for implementation readers

1. `README_v1_6_draft_4_1.md` - package orientation and active authority.
2. `RELEASE_NOTES_v1_6_draft_4_1.md` - changes from Draft 4.
3. `corpus_review_v1_6_draft_4_to_v1_6_draft_4_1.md` - review summary and
   closure rationale.
4. `duotronic_draft4_1_contract_closeout_report.md` - all closeout items and
   readiness classification.
5. `duotronic_draft4_1_witness_contract_version_alias_and_migration_profile_v1_0.md`
   - runtime `v8` / Draft 4.1 / v11 aliasing rules.
6. `mcp/mcp_recurrence_tool_availability_matrix_v1_6_draft_4_1.md` - recurrence
   tool maturity and release-claim gating.
7. `runtime/wgrnn_chat_context_injection_witness_contract_v1_0.md` - how WG-RNN
   memory state may be injected into chat context.
8. `browser/browser_chat_workbench_invocation_witness_contract_v1_0.md` - browser
   invocation authority and mutation evidence.
9. `runtime/runtime_feature_applicability_witness_contract_v1_0.md` - requested
   versus applied runtime feature evidence.
10. `runtime/runtime_readiness_evidence_persistence_profile_v1_0.md` - runtime
    readiness evidence persistence.
11. `refs/manifest/MANIFEST_v1_6_draft_4_1_complete.md` - complete package file
    list.

## Fast path for governance and security readers

1. `duotronic_draft4_1_agent_lab_mutation_safety_config_witness_profile_v1_0.md`
2. `browser/browser_chat_workbench_invocation_witness_contract_v1_0.md`
3. `mcp/mcp_recurrence_tool_availability_matrix_v1_6_draft_4_1.md`
4. `security/gpu_worker_runtime_security_and_memlock_profile_v1_0.md`
5. `security/direct_mutation_tool_enforcement_v1_2.md`
6. `duotronic_mutation_policy_validation_profile_v1_1.md`
7. `duotronic_security_architecture_v1_0.md`
8. `duotronic_stridethreat_model_v1_0.md`

## Fast path for SRNN runtime readers

1. `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
2. `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
3. `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
4. `duotronic_draft4_runtime_model_observability_profile_v1_0.md`
5. `runtime/llama_server_runtime_readiness_contract_v1_0.md`
6. `runtime/runtime_feature_applicability_witness_contract_v1_0.md`
7. `runtime/runtime_readiness_evidence_persistence_profile_v1_0.md`
8. `runtime/wgrnn_chat_context_injection_witness_contract_v1_0.md`

## Non-claims

Draft 4.1 does not claim the production cluster has been started from this
package, every container has been live-verified, or every SRNN test passed in the
package-generation environment. It defines the contract and evidence required for
those claims.
