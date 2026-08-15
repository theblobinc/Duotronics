# Draft 5.2 Implementation Completion Matrix v1.0

| Requirement | Completed corpus artifact | Runtime obligation |
|---|---|---|
| First-class atomic claims | `schemas/evidence_claim.schema.json` | Persist and expose `/evidence/claims`. |
| First-class compositional claims | `schemas/composition_policy.schema.json`, `schemas/compound_claim_witness.schema.json` | Enforce arity, scope, policy, and non-collapse checks. |
| Inference witnesses | `schemas/inference_witness.schema.json` | Reject theorem/proof promotion without proof witness. |
| Replay assumption manifests | `schemas/replay_assumption_manifest.schema.json` | Block deep-time replay when required assumptions are unsatisfied. |
| Verification grammar | `schemas/verification_grammar.schema.json` | Execute only deterministic allowed ops. |
| Verification result | `schemas/verification_result.schema.json` | Record pass/fail/inconclusive/error for replay checks. |
| Pragmatic force markers | `schemas/pragmatic_context.schema.json` | Require audience, channel, scope, force, policy decision. |
| Policy force extension | `schemas/policy_decision_evidence_extension.schema.json` | Preserve requested/allowed/denied force semantics. |
| Delegated authority chains | `schemas/authority_delegation_chain.schema.json` | Enforce scope, depth, runtime, revocation, and expiry. |
| Non-collapse primitive | `schemas/non_collapse_state.schema.json` | Never allow silent collapse target lists. |
| Non-collapse transitions | `schemas/non_collapse_transition.schema.json` | Emit transition witness for every state change. |
| Schema-level forbidden transition locks | `schemas/claim_status_transition.schema.json` | Deny theorem/proof upgrades without proof refs. |
| API exposure | `executable/openapi/draft5_2_evidence_language_openapi.yaml` | Implement request/response/error behavior. |
| Storage exposure | `executable/sql/draft5_2_schema_additions.sql` | Apply additive migration and indexes. |
| Deep-time replay conformance | `refs/fixtures/draft5_2_evidence_language/*`, `executable/tests/draft5_2_conformance_vectors.json` | Turn vectors into executable tests. |
