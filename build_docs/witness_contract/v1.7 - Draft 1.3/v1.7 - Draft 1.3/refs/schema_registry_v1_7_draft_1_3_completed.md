# Draft 1.3 Active Alias for `schema_registry_v1_7_draft_1_2_completed.md`

# Schema Registry - v1.7 Draft 1.2

## Active schema set

- `schemas/authority_delegation_chain.schema.json`
- `schemas/bayesian_calibration_report.schema.json`
- `schemas/bayesian_conditioning_witness.schema.json`
- `schemas/bayesian_decision_witness.schema.json`
- `schemas/bayesian_likelihood.schema.json`
- `schemas/bayesian_loss_matrix_witness.schema.json`
- `schemas/bayesian_marginalization_witness.schema.json`
- `schemas/bayesian_model.schema.json`
- `schemas/bayesian_negative_evidence_witness.schema.json`
- `schemas/bayesian_posterior_predictive_witness.schema.json`
- `schemas/bayesian_posterior_state.schema.json`
- `schemas/bayesian_prior.schema.json`
- `schemas/bayesian_update_replay_witness.schema.json`
- `schemas/bayesian_update_witness.schema.json`
- `schemas/claim_status_transition.schema.json`
- `schemas/composition_policy.schema.json`
- `schemas/compound_claim_witness.schema.json`
- `schemas/conflict_adjudication_witness.schema.json`
- `schemas/corpus_rule_resolution_witness.schema.json`
- `schemas/evidence_claim.schema.json`
- `schemas/execution_trace.schema.json`
- `schemas/inference_witness.schema.json`
- `schemas/kernel_error_witness.schema.json`
- `schemas/kernel_state.schema.json`
- `schemas/kernel_transaction.schema.json`
- `schemas/knot_braid_relation_witness.schema.json`
- `schemas/knot_braid_word_witness.schema.json`
- `schemas/knot_canonicalization_witness.schema.json`
- `schemas/knot_diagram_witness.schema.json`
- `schemas/knot_equivalence_authority_path.schema.json`
- `schemas/knot_equivalence_witness.schema.json`
- `schemas/knot_invariant_completeness_witness.schema.json`
- `schemas/knot_invariant_witness.schema.json`
- `schemas/knot_markov_move_witness.schema.json`
- `schemas/knot_presentation_transition_witness.schema.json`
- `schemas/knot_reidemeister_move_witness.schema.json`
- `schemas/knot_reidemeister_trace_witness.schema.json`
- `schemas/lean_compiler_witness.schema.json`
- `schemas/logical_memory_cell.schema.json`
- `schemas/logical_observer_profile.schema.json`
- `schemas/nla_activation_witness.schema.json`
- `schemas/nla_self_training_witness.schema.json`
- `schemas/non_collapse_state.schema.json`
- `schemas/non_collapse_transition.schema.json`
- `schemas/observer_capability_token.schema.json`
- `schemas/observer_task.schema.json`
- `schemas/policy_decision_evidence_extension.schema.json`
- `schemas/pragmatic_context.schema.json`
- `schemas/proof_witness.schema.json`
- `schemas/replay_assumption_manifest.schema.json`
- `schemas/replay_sign.schema.json`
- `schemas/resource_budget_witness.schema.json`
- `schemas/task_frame.schema.json`
- `schemas/task_result_witness.schema.json`
- `schemas/task_step_witness.schema.json`
- `schemas/temporal_scope_witness.schema.json`
- `schemas/theorem_promotion_gate.schema.json`
- `schemas/verification_grammar.schema.json`
- `schemas/verification_result.schema.json`

Draft 1.2 adds typed knot encodings, split braid/Markov transition witnesses, Bayesian posterior predictive/marginalization/conditioning/negative-evidence/loss-matrix witnesses, and stricter replay semantics.


---

## Draft 1.3 Redo Supplement

This Draft 1.3 alias is the active reader entrypoint. It carries forward the Draft 1.2 registry semantics and explicitly binds them to Draft 1.3's SQL persistence registry, runtime semantic boundary, expanded positive fixture coverage, duplicate Bayesian hypothesis-ID rejection, and deeper typed knot-encoding semantic validation.

Active companions:

- `refs/schema_sql_persistence_registry_v1_7_draft_1_3.json`
- `RUNTIME_SQL_SEMANTIC_BOUNDARY_v1_7_draft_1_3.md`
- `executable/tests/draft1_7_bayesian_knot_conformance_vectors.json`
- `executable/validators/validate_v1_7_draft_1_3_corpus.py`
