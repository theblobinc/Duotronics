# Release Notes — v1.6 Draft 5.3.7

Draft 5.3.7 is a permanently unfrozen corrective development draft based on the exact Draft 5.3.6 archive.

It removes the obsolete generic file-size control from active production surfaces, binds a domain-selected limit through execution and witness identity, requires exact `RLIMIT_FSIZE` measurement, and separates requested, emitted, accepted, applied, measured, and derived control semantics.

Validation accounting is generated from discovery. The Draft 5.3.6 baseline is corrected from a stale narrative value of 127 to the observed 128 tests. The Draft 5.3.7 total is generated rather than handwritten, and validation fails on mismatches, skips, duplicates, or warnings. Test-created SQLite connections are closed deterministically.

Schemas, fixtures, SQL migration, sandbox profile, OpenAPI, formal model, registry, and release metadata are versioned for 5.3.7. Older schemas and all exact historical archives are retained.

No external gate is claimed complete. Strict Lean, strict TLC, governed-image execution, signed build attestations, reproducible inspector evidence, committed-source provenance, and governance authorization remain pending; all authority stays disabled.
