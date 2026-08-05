# Start Here — Duotronic v1.6 Draft 5.3.1

**Status:** active, complete corrective draft; not frozen.

## Deterministic boot

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_1.json`.
2. Require `active_version == "v1.6-draft-5.3.1"` and `freeze_state == "not_frozen"`.
3. Verify every non-excluded inventory entry against `refs/manifest/CHECKSUMS_v1_6_draft_5_3_1.sha256`.
4. Load only the schema files named by `refs/schema_registry_v1_6_draft_5_3_1.json` for canonical writes. V1 schemas remain readable for legacy replay.
5. Run `python3 executable/validators/validate_draft5_3_1_corpus.py`. A missing dependency, skipped required phase, checksum mismatch, or fixture mismatch is a failure.
6. Load `duotronic_witness_contract_v1_6_draft_5_3_1.md` and `kernel/corpus_boot_and_canonical_resolver_v1_0.md`.
7. Enter safe mode if the descriptor, hashes, schemas, database generation, or authority profile is ambiguous.

## Non-negotiable rules

1. Evidence is not proof; proof is not policy; policy is not truth.
2. `zero`, `absence`, `unknown`, `invalid`, `empty`, and `null` remain distinct.
3. `computed`, `conjectural`, `theorem`, `self_trained`, and `authoritative` remain distinct.
4. A theorem promotion is valid only through one matching content-bound compiler witness, proof witness, policy decision, status event, relevant allowed non-collapse transition, and promotion gate.
5. Authority records are append-only. A correction supersedes a record and never edits it in place.
6. Advisory Lean/TLA checks cannot authorize theorem promotion.
7. Deep-time replay cannot pass vacuously.
8. A positive-baseline codeword is a representation of a payload, not a redefinition of the payload. A child's local baseline is decoded before the parent consumes it.

## Validation

From the corpus root:

```bash
python3 -m pip install -r requirements-validation.txt
npm ci
python3 executable/validators/validate_draft5_3_1_corpus.py
```

The final report is written to `DRAFT5_3_1_VALIDATION_REPORT.json`. The build is acceptable only when `overall_status` is `passed` and `required_skipped` is zero. Strict Lean and TLC are separate release evidence and may remain unavailable in this unfrozen draft; their unavailability must be reported, never converted into a pass.

## Mathematical profile

Read `mathematics/Duotronic_Positive_Baseline_Polygonal_Computation_v1.2.md` for the full technical framework and `mathematics/positive_baseline_witness_integration_profile_v1_0.md` for its Witness Contract binding. The executable reference is `executable/runtime/positive_baseline.py`.
