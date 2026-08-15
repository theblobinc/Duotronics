# Start Here - Duotronic v1.6 Draft 5.1

Status: active Draft 5.1 reading guide.  
Generated: 2026-05-09.

## Read this first

Draft 5.1 adds authority and self-training contracts for WG-RNN NLA. It does not
ship implementation code. It tells Copilot, implementers, and reviewers what the
system must prove before any self-trained NLA model receives authority.

## Fast path

1. `duotronic_witness_contract_v1_6_draft_5_1.md` - consolidated active witness contract.
2. `duotronic_draft5_1_authority_self_training_complete_witness_report.md` - summary of what was added.
3. `authority/truth_observer_activation_authority_profile_v1_0.md` - generic truth-observer contract.
4. `authority/nla_training_memory_cell_authority_contract_v1_0.md` - WG-RNN memory cells for internal NLA data.
5. `authority/nla_self_training_authority_contract_v1_0.md` - self-training run authority.
6. `authority/nla_model_lineage_and_promotion_authority_contract_v1_0.md` - model versioning and promotion.
7. `authority/nla_shadow_audit_release_gate_contract_v1_0.md` - shadow/audit/release gates.
8. `runtime/truth_observer_activation_registry_contract_v1_0.md` - runtime registry shape.
9. `runtime/nla_internal_training_memory_runtime_contract_v1_0.md` - persistence/runtime details.
10. `runtime/nla_curriculum_and_eval_runtime_contract_v1_0.md` - curriculum and evaluation.
11. `schemas/nla_self_training_witness.schema.json` - machine schema.
12. `validation/nla_self_training_authority_acceptance_matrix_v1_0.md` - acceptance matrix.
13. `security/nla_self_training_safety_profile_v1_0.md` - safety profile.
14. `tests/nla_self_training_conformance_suite_v1_0.md` - conformance suite.
15. `refs/manifest/MANIFEST_v1_6_draft_5_1_complete.md` - package inventory.

## Non-goal

This zip does not implement training code. The next file should be a separate
implementation guide for `srnn_server`.
