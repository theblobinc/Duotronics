# Corpus Index v1.6 Draft 5.2.2

Status: completion candidate; not frozen pending strict Lake/Lean and TLC CI runs.

## Governing entry points

- `START_HERE.md`
- `README.md`
- `PACKAGE_METADATA_v1_6_draft_5_2_2.json`
- `PACKAGE_INVENTORY_v1_6_draft_5_2_2.json`
- `refs/manifest/MANIFEST_v1_6_draft_5_2_2_complete.md`
- `refs/manifest/CHECKSUMS_v1_6_draft_5_2_2.sha256`

## Operating-system and kernel layer

- `EVIDENCE_LANGUAGE_OPERATING_SYSTEM_PRIMER_v1_0.md`
- `kernel/logical_observer_kernel_contract_v1_0.md`
- `kernel/corpus_boot_and_canonical_resolver_v1_0.md`
- `executable/kernel/logical_observer_kernel_syscalls.yaml`

## Formal layer

Draft 5.2.2 is not TLA-only. It combines:

- TLA+ state-machine models under `formal/tlaplus/`
- Lean/Lake proof authority under `lean-toolchain`, `lakefile.lean`, `Duotronic.lean`, and `Duotronic/`
- Advisory runners under `executable/formal/`

Strict freeze requires successful CI runs for both:

```bash
lake build
python executable/formal/run_tla_model_check.py --mode strict
```

## Lean proof-authority layer

- `kernel/lean_proof_authority_contract_v1_0.md`
- `schemas/lean_compiler_witness.schema.json`
- `schemas/proof_witness.schema.json`
- `schemas/theorem_promotion_gate.schema.json`
- `Duotronic/ProofAuthority.lean`
- `Duotronic/Kernel.lean`

## Persistence layer

- `executable/sql/draft5_2_schema_additions.sql`

Draft 5.2.2 SQL hardening requires theorem/proof-verified claims and transitions to carry proof witness refs, Lean compiler witness refs, theorem promotion gate IDs, and non-collapse/policy evidence. The corrective pass also requires exact JSON witness-ID membership: an allowed theorem promotion gate must match the exact proof and Lean compiler witness IDs carried by the claim and transition JSON arrays.

## Validation

Run:

```bash
python executable/validators/validate_draft5_2_2_corpus.py
```

This validator checks schemas, fixtures, SQL constraints/triggers, exact theorem-gate witness-ID membership, formal parity, kernel syscall coverage, Lean static/advisory status, and package inventory hash closure.

## Release/freeze status

Not frozen. The strict execution paths are wired but require an environment with Lake/Lean and TLC installed.
