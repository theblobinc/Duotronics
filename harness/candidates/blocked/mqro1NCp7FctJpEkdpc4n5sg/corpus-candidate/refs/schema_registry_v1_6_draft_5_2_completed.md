# Draft 5.2 Completed Schema Registry

## Status

Completion candidate registry. All schemas are local, standalone, and versioned.

## Normative schemas

- `schemas/evidence_claim.schema.json`
- `schemas/composition_policy.schema.json`
- `schemas/compound_claim_witness.schema.json`
- `schemas/inference_witness.schema.json`
- `schemas/claim_status_transition.schema.json`
- `schemas/pragmatic_context.schema.json`
- `schemas/policy_decision_evidence_extension.schema.json`
- `schemas/authority_delegation_chain.schema.json`
- `schemas/non_collapse_state.schema.json`
- `schemas/non_collapse_transition.schema.json`
- `schemas/replay_assumption_manifest.schema.json`
- `schemas/replay_sign.schema.json`
- `schemas/temporal_scope_witness.schema.json`
- `schemas/verification_grammar.schema.json`
- `schemas/verification_result.schema.json`
- `schemas/nla_activation_witness.schema.json`
- `schemas/nla_self_training_witness.schema.json`

## Schema lock rules

1. Theorem and proof-verified transitions require proof witness references.
2. Deep-time replay requires required assumptions and deterministic verification grammar.
3. Compound and composition operators have schema-level arity locks.
4. Pragmatic force must be explicit and must not exceed delegation limits.
5. Non-collapse states cannot silently list allowed collapse targets; all transitions use `non_collapse_transition/v1`.
6. Runtime/API/storage representations must preserve schema version, policy decision, force marker, and non-collapse references.

## Logical observer kernel schemas

- `schemas/logical_observer_profile.schema.json`
- `schemas/observer_capability_token.schema.json`
- `schemas/resource_budget_witness.schema.json`
- `schemas/observer_task.schema.json`
- `schemas/task_frame.schema.json`
- `schemas/task_step_witness.schema.json`
- `schemas/task_result_witness.schema.json`
- `schemas/kernel_transaction.schema.json`
- `schemas/kernel_error_witness.schema.json`
- `schemas/corpus_rule_resolution_witness.schema.json`
- `schemas/conflict_adjudication_witness.schema.json`
- `schemas/kernel_state.schema.json`
- `schemas/execution_trace.schema.json`
- `schemas/logical_memory_cell.schema.json`

## Additional lock rules

7. Observer tasks cannot commit without `TaskResultWitness`.
8. Kernel transactions cannot commit without emitted and persisted witnesses.
9. Resource budgets for replay-safe execution deny network, randomness, and wall-clock access.
10. Canonical rule resolution must emit a witness and must not silently fall back to historical drafts.
