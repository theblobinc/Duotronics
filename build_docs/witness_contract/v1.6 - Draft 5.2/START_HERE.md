# Start Here - Duotronic v1.6 Draft 5.2 Completion Candidate

**Status:** completed review candidate, not frozen.  
**Generated:** 2026-05-11.

## Read this first

Draft 5.2 is the formal evidence-language layer of the Duotronic witness contract. Treat it as a self-referential operating corpus: it defines the objects, transitions, authority gates, replay assumptions, and non-collapse rules that an AI or runtime must follow when making or checking claims.

## Operating sequence for an AI/runtime

1. Identify the claim or operation.
2. Represent atomic claims with `schemas/evidence_claim.schema.json`.
3. Represent compound claims with `schemas/compound_claim_witness.schema.json` and `schemas/composition_policy.schema.json`.
4. Represent inference with `schemas/inference_witness.schema.json`.
5. Attach pragmatic context with `schemas/pragmatic_context.schema.json`.
6. Attach policy force and decision details with `schemas/policy_decision_evidence_extension.schema.json`.
7. Create non-collapse state and transition records with `schemas/non_collapse_state.schema.json` and `schemas/non_collapse_transition.schema.json`.
8. For replay, require `schemas/replay_assumption_manifest.schema.json`, `schemas/verification_grammar.schema.json`, `schemas/replay_sign.schema.json`, and `schemas/verification_result.schema.json`.
9. Persist through `executable/sql/draft5_2_schema_additions.sql`.
10. Expose through `executable/openapi/draft5_2_evidence_language_openapi.yaml`.
11. Validate the corpus and fixtures with `executable/validators/validate_draft5_2_corpus.py`.

## Freeze prohibition

Do not label this corpus frozen until the runtime implementation has passed schema validation, conformance fixtures, deep-time replay tests, non-collapse transition tests, authority delegation tests, and human review.

## Safety invariant

No system may convert one epistemic, semantic, authority, or replay state into another without an explicit witness, policy decision, and non-collapse transition. Silent collapse is invalid behavior.

## Logical observer kernel boot sequence

After the evidence-language operating sequence, a logical observer runtime MUST boot the kernel layer:

1. Load `kernel/logical_observer_kernel_contract_v1_0.md`.
2. Run the boot and canonical resolver protocol in `kernel/corpus_boot_and_canonical_resolver_v1_0.md`.
3. Load `executable/kernel/logical_observer_kernel_syscalls.yaml`.
4. Validate observer, capability, task, transaction, error, memory, conflict, and resource schemas.
5. Use `CorpusRuleResolutionWitness` whenever active Draft 5.2 files and retained Draft 5.1 gates could both apply.
6. Refuse, defer, fork, or escalate every unresolved ambiguity; never silently select a historical rule.

## TLA+ model checking

For the TLA+-only formal layer, start with `DRAFT5_2_TLA_PLUS_IMPLEMENTATION_REPORT_v1_0.md`, then run:

```bash
python executable/formal/run_tla_model_check.py --mode advisory
```

Use strict mode once TLC is installed or `TLA2TOOLS_JAR` points to `tla2tools.jar`. No Lean toolchain is added by this update.
