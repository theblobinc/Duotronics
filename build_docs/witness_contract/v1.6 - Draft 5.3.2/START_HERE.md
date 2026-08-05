# Start Here — Duotronic v1.6 Draft 5.3.2

**Status:** active corrective development corpus; not frozen.

## Deterministic boot

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_2.json`; no other artifact selects the active generation.
2. Require `active_version == "v1.6-draft-5.3.2"` and `freeze_state == "not_frozen"`.
3. Verify every non-excluded inventory entry against `refs/manifest/CHECKSUMS_v1_6_draft_5_3_2.sha256`.
4. Load only schemas named by `refs/schema_registry_v1_6_draft_5_3_2.json` for canonical writes.
5. Run `python3 executable/validators/validate_draft5_3_2_corpus.py`.
6. Reconcile the report's phase identifiers with the descriptor. Any required missing, failed, or skipped phase is a boot failure.
7. Load `duotronic_witness_contract_v1_6_draft_5_3_2.md` and the canonical resolver.
8. Enter safe mode if descriptor, hashes, database generation, effective verifier key, signature binding, or formal-toolchain coverage is ambiguous.

## Authority rules

1. Evidence is not proof; proof is not policy; policy is not truth.
2. The named Lean theorem must compile at the exact claimed type through the generated statement-binding target.
3. A source-text match, comment, successful unrelated Lake target, or caller-supplied result has no theorem authority.
4. Compiled axiom inspection must complete; `sorryAx` and unauthorized axioms block promotion.
5. Lake is resolved only by an absolute verifier configuration and an independently pinned binary SHA-256; PATH lookup is forbidden.
6. Compiler and proof signatures must verify over canonical payloads that exactly match the stored authority fields.
7. The verifier key must be within its validity window and its latest effective lifecycle event must be `active`.
8. Authority records are append-only; revocation and supersession are new events, not updates.
9. Deep-time replay cannot pass vacuously.
10. Positive-baseline codewords are representations of payloads, not redefinitions of zero, absence, invalidity, or unknown state.

## Validation

From the corpus root:

```bash
python3 -m pip install -r requirements-validation.txt
python3 executable/validators/validate_draft5_3_2_corpus.py
```

AJV and its JavaScript runtime dependencies are vendored and hash-covered; `npm ci` is not required for canonical schema validation. The report is `DRAFT5_3_2_VALIDATION_REPORT.json`. Acceptance requires `overall_status: passed`, an empty `required_missing` set, zero required failures, and zero required skips.

Strict Lean and TLC are separate freeze evidence. Their absence is recorded as an optional blocker and never converted into a strict pass.

## Database path

For a new database, apply in order:

1. `executable/sql/draft5_2_schema_additions.sql`
2. `migration/draft5_2_2_to_draft5_3_1.sql`
3. `migration/draft5_3_1_to_draft5_3_2.sql`

The application must register the cryptographic/canonicalization SQLite functions defined by `executable/runtime/proof_authority.py` before inserting verifier keys or signature bindings. Without them, authority creation fails closed.
