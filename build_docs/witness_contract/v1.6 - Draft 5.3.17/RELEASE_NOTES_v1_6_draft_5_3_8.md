# Release Notes — v1.6 Draft 5.3.8

Draft 5.3.8 is a standalone, permanently unfrozen corrective development corpus based on Draft 5.3.7. It does not embed earlier source-package ZIPs; predecessor hashes are recorded in a non-authoritative lineage file and all active changes are merged into this package.

This revision closes the reviewed authority-path defects:

- completed idempotency hits now re-resolve policy and verify a signed cache envelope, the compiler-witness signature and signer, status equality, and every request, identity, claim, theorem, source, profile, policy, and artifact binding;
- callers cannot assert `subject_id`; trusted authentication middleware must provide the principal and that identity is bound end to end;
- environment and entrypoint measurements are mandatory, the complete environment-key set is checked, runtime-created keys are governed explicitly, and undeclared keys fail closed;
- semantic witness identity excludes ephemeral host paths and execution metadata, which remain signed under a separate execution-evidence identity;
- production SQLite connections are explicitly closed, file security is checked for the database/WAL/SHM set, and in-flight, completed, total-row, and database-size admission is bounded;
- Python 3.12 and 3.13 are declared supported, test counts come from structured `unittest` results, and warning detection is independent of count extraction;
- the runtime README and active schemas, fixtures, OpenAPI, registry, tests, package metadata, and validator are current for 5.3.8.

No external gate is claimed complete. Strict Lean, strict TLC, governed-image execution, signed build attestations, reproducible inspector evidence, committed-source provenance, and governance authorization remain pending; all authority stays disabled.
