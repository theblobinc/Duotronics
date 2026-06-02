# Corpus Index - Duotronic Witness Contract v1.7 Draft 1

## Active status

- Package: Duotronic Witness Contract v1.7 Draft 1
- Status: completed implementation-review candidate; not frozen
- Base: v1.6 Draft 5.2.2 exact SQL hardened completion candidate
- Active metadata: `PACKAGE_METADATA_v1_7_draft_1.json`
- Active validator: `executable/validators/validate_v1_7_draft_1_corpus.py`

## Inherited corpus

All v1.6 Draft 5.2.2 files are preserved in this package. The inherited corpus includes:

- evidence claim schemas,
- compound claim and inference witness schemas,
- replay and verification grammar schemas,
- non-collapse state and transition schemas,
- policy decision and authority schemas,
- logical observer kernel contracts,
- SQL persistence hardening,
- OpenAPI runtime surfaces,
- Lean/Lake proof authority,
- TLA+ state-machine artifacts,
- package inventory and hash-closure tooling.

## v1.7 normative additions

### Bayesian top-order facility

Primary contract:

- `BAYESIAN_LOGIC_TOP_ORDER_FACILITY_CONTRACT_v1_0.md`

Schemas:

- `schemas/bayesian_model.schema.json`
- `schemas/bayesian_prior.schema.json`
- `schemas/bayesian_likelihood.schema.json`
- `schemas/bayesian_update_witness.schema.json`
- `schemas/bayesian_posterior_state.schema.json`
- `schemas/bayesian_decision_witness.schema.json`
- `schemas/bayesian_calibration_report.schema.json`

Fixtures:

- `refs/fixtures/valid_bayesian_prior.fixture.json`
- `refs/fixtures/valid_bayesian_likelihood.fixture.json`
- `refs/fixtures/valid_bayesian_update_witness.fixture.json`
- `refs/fixtures/valid_bayesian_posterior_state.fixture.json`
- `refs/fixtures/invalid_bayesian_posterior_sum.fixture.json`

Formal and runtime artifacts:

- `Duotronic/BayesianLogic.lean`
- `executable/sql/draft1_7_bayesian_knot_additions.sql`
- `executable/openapi/draft1_7_bayesian_knot_openapi.yaml`

### Knot theory witness addendum

Primary contract:

- `knot_theory/KNOT_THEORY_WITNESS_ADDENDUM_v1_0.md`

Schemas:

- `schemas/knot_diagram_witness.schema.json`
- `schemas/knot_braid_word_witness.schema.json`
- `schemas/knot_reidemeister_move_witness.schema.json`
- `schemas/knot_invariant_witness.schema.json`
- `schemas/knot_equivalence_witness.schema.json`

Fixtures:

- `refs/fixtures/valid_knot_diagram_witness.fixture.json`
- `refs/fixtures/valid_knot_reidemeister_move_witness.fixture.json`
- `refs/fixtures/valid_knot_invariant_witness.fixture.json`
- `refs/fixtures/valid_knot_equivalence_witness.fixture.json`
- `refs/fixtures/invalid_knot_equivalence_without_trace.fixture.json`

Formal and runtime artifacts:

- `Duotronic/KnotTheory.lean`
- `executable/sql/draft1_7_bayesian_knot_additions.sql`
- `executable/openapi/draft1_7_bayesian_knot_openapi.yaml`

## v1.7 kernel additions

New syscall registrations:

- `bayes_update`
- `bayes_calibrate`
- `bayes_decide`
- `knot_encode`
- `knot_move`
- `knot_invariant`
- `knot_equivalence`

New instruction sets:

- Bayesian reasoning instruction set
- Knot theory instruction set

New invariants:

- K11. Posterior probability is not proof, truth, theorem, policy approval, or human attestation.
- K12. Bayesian decision is not policy approval unless a policy decision witness separately authorizes it.
- K13. Knot diagram identity is not knot-type equivalence unless witnessed by a declared equivalence path.
- K14. Invariant equality is not equivalence unless the invariant is declared complete for the domain and backed by proof authority.
- K15. Reidemeister traces are mathematical transition witnesses and must preserve source and target diagram references.

## Validation command

```bash
python executable/validators/validate_v1_7_draft_1_corpus.py
```
