# Release Notes - Duotronic v1.6 Draft 5.1

Status: release notes.  
Generated: 2026-05-09.

## Summary

Draft 5.1 extends Draft 5 by adding the authority, memory, and self-training
contracts required for WG-RNN to build internal NLA capability over time.

The new design allows WG-RNN to:

1. Register any AI model as a truth observer.
2. Determine what evidence the observer can expose: hidden states, logits,
   embeddings, output text, tool traces, or only API-level outputs.
3. Capture activation evidence when the backend supports it.
4. Store NLA examples in explicit WG-RNN memory cells.
5. Build internal NLA training datasets from accepted and failed witnesses.
6. Train candidate AV/AR adapters under bounded offline jobs.
7. Evaluate candidates against replay, reconstruction, stability, confabulation,
   and policy tests.
8. Promote candidates only through shadow, audit, and release gates.

## Major new contracts

```text
authority/truth_observer_activation_authority_profile_v1_0.md
authority/nla_training_memory_cell_authority_contract_v1_0.md
authority/nla_self_training_authority_contract_v1_0.md
authority/nla_model_lineage_and_promotion_authority_contract_v1_0.md
authority/nla_shadow_audit_release_gate_contract_v1_0.md
runtime/truth_observer_activation_registry_contract_v1_0.md
runtime/nla_internal_training_memory_runtime_contract_v1_0.md
runtime/nla_curriculum_and_eval_runtime_contract_v1_0.md
schemas/nla_self_training_witness.schema.json
schemas/truth_observer_activation_profile.schema.yaml
validation/nla_self_training_authority_acceptance_matrix_v1_0.md
security/nla_self_training_safety_profile_v1_0.md
tests/nla_self_training_conformance_suite_v1_0.md
```

## Release boundary

Draft 5.1 is contract-complete for the authority additions. It does not claim
that internal NLA training jobs, LoRA adapters, model registries, or live
activation capture are already implemented.
