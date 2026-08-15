# Draft 5.1 Authority and Self-Training Complete Witness Report

Status: complete Draft 5.1 report.  
Generated: 2026-05-09.

## Executive summary

Draft 5.1 completes the NLA authority additions discussed after Draft 5. It
allows WG-RNN to move from external-only NLA toward internally trained NLA
adapters, but keeps the system bounded by witness evidence, replay gates,
lineage, review, and rollback.

## Added authority surfaces

| Surface | Contract |
|---|---|
| Generic truth observer activation authority | `authority/truth_observer_activation_authority_profile_v1_0.md` |
| WG-RNN NLA training memory cells | `authority/nla_training_memory_cell_authority_contract_v1_0.md` |
| Self-training run authority | `authority/nla_self_training_authority_contract_v1_0.md` |
| Model lineage and promotion authority | `authority/nla_model_lineage_and_promotion_authority_contract_v1_0.md` |
| Shadow/audit/release gates | `authority/nla_shadow_audit_release_gate_contract_v1_0.md` |
| Runtime observer registry | `runtime/truth_observer_activation_registry_contract_v1_0.md` |
| Runtime training memory persistence | `runtime/nla_internal_training_memory_runtime_contract_v1_0.md` |
| Curriculum/eval runtime | `runtime/nla_curriculum_and_eval_runtime_contract_v1_0.md` |
| Self-training schema | `schemas/nla_self_training_witness.schema.json` |
| Acceptance matrix | `validation/nla_self_training_authority_acceptance_matrix_v1_0.md` |

## Implementation meaning

This package completely specifies the authority model. It does not implement the
code. A future implementation guide should map these contracts to modules,
tables, runtime flags, MCP tools, tests, and rollout phases.

## Safety outcome

The resulting system may train from its own witness stream, but it may not trust
itself merely because it trained itself. Authority requires evidence.
