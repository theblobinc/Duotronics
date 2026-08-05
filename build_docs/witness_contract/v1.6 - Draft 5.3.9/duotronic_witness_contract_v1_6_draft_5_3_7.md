# Duotronic Witness Contract v1.6 Draft 5.3.7

**Status:** corrective development draft; permanently not frozen. Theorem, promotion, and release authority are disabled by default.

Draft 5.3.7 incorporates Draft 5.3.6 except where this document, the active descriptor, versioned schemas, migration, sandbox profile, or executable validator expressly supersede it. Historical artifacts remain replay-only and are never upgraded by interpretation.

## Domain-specific file-size authority

The obsolete generic production field `file_size_limit` is forbidden. An effective invocation selects exactly one governed limit:

- `untrusted_compilation` selects `compiler_artifact_file_size_limit`.
- `trusted_inspection` selects `inspection_output_bytes_limit`.

Unknown domains and missing, Boolean, non-integer, negative, zero, excessive, or mismatched limits fail closed. The selected `domain_file_size_limit` is bound into the exact OCI argv, canonical invocation digest, verifier result, compiler witness, proof-check result, and replay record. The trusted runtime must measure `RLIMIT_FSIZE` and require exact equality with that selected limit.

## Control evidence semantics

The six control states are distinct:

1. `requested` records policy intent.
2. `emitted` is reconstructed from the exact executed argv.
3. `accepted` is populated only after the target runtime starts and accepts the control.
4. `applied` is populated only from runtime evidence of application.
5. `measured` contains direct observations, including exact `rlimit_fsize` evidence.
6. `derived` contains host-derived facts bound to a sealed evidence root.

Pre-execution failures leave `accepted`, `applied`, and `measured` empty. Requested values are never copied into evidence states as proof of application.

## Validation accounting

Regression totals are generated from `unittest` discovery. Required validation fails for stale or inconsistent totals, duplicate test IDs, skipped tests, warnings, resource warnings, or a difference between discovered and passed counts. Draft 5.3.6's narrative count of 127 is corrected to the observed 128-test baseline; Draft 5.3.7's current total is generated in `DRAFT5_3_7_REGRESSION_COUNTS.json`.

## Authority boundary

Portable regression and schema validation do not activate authority. Strict Lean, strict TLC, a governed hermetic Lean image run, signed OCI-image and verifier-executable attestations, reproducible inspector-build attestations, clean committed-source provenance, and external governance authorization remain eight independent external gates. Unless each is supplied and verified, theorem authority, promotion authority, and release authority remain disabled.
