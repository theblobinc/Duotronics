# Draft 5.3.6 → Draft 5.3.7 Migration Runbook

Draft 5.3.7 is a new-write boundary. Draft 5.3.6 objects and the exact source ZIP remain immutable replay inputs; they are not rewritten or silently reinterpreted.

## Field transition

- The obsolete generic `file_size_limit` name is accepted only in historical Draft 5.3.6-and-earlier replay objects.
- New invocations bind the domain-selected value as `domain_file_size_limit`.
- `untrusted_compilation` selects `compiler_artifact_file_size_limit`.
- `trusted_inspection` selects `inspection_output_bytes_limit`.
- Objects containing the obsolete field at the Draft 5.3.7 boundary fail schema validation.

## Evidence transition

Draft 5.3.7 preserves six distinct states: requested, emitted, accepted, applied, measured, and derived. Pre-execution invocations contain requested and argv-derived emitted controls only. Accepted, applied, measured, and derived state is populated only by its corresponding post-execution evidence channel.

## Validation transition

The release validator discovers tests dynamically, records discovered and passed counts, rejects unexpected skips or duplicated discovery, and runs the full suite under `python -X dev -W error`. Narrative counts must equal the generated machine-readable report.

## Activation state

This migration does not create release-activation evidence. Theorem, promotion, and release authority remain disabled until all eight external activation gates are independently verified and externally authorized.
