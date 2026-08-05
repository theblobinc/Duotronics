# Duotronic Witness Contract v1.6 Draft 5.3.9

This is a standalone, permanently unfrozen corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_9.json`, then follow `START_HERE.md`.

Draft 5.3.9 makes the governed two-domain Lean path internally coherent: the generated binding is part of the compiled-module set, the inspector resolves modules only through the host-sealed `/handoff/olean` root, keep-ID ownership is host-verified and sealed between domains, and the build target, image, scripts, protocol, and registry select one source generation. Compile and inspection receive separately typed trusted runtime evidence. Warnings-as-errors applies to every submitted module.

The request service uses one monotonic deadline, renews owner-fenced idempotency leases, requires a distinct production cache-signing authority, enforces completion-time byte limits, rejects noncanonical or duplicate-key cached JSON, and verifies the SQLite schema, integrity, ancestry, and object set.

The corpus contains the merged current source only. Earlier source-package ZIPs are not embedded. `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_9.json` records predecessor digests without making them authority inputs.

Run portable validation with Python 3.12 or 3.13:

```sh
python3 executable/validators/generate_draft5_3_9_regression_counts.py
python3 executable/validators/build_schema_registry_v539.py
node executable/validators/validate_draft5_3_9_schemas.mjs --phase all
python3 executable/validators/build_draft5_3_9_manifests.py
python3 executable/validators/validate_draft5_3_9_corpus.py
```

Executed matrix evidence is recorded in `DRAFT5_3_9_PYTHON_MATRIX_VALIDATION.json`.

Portable passing results do not grant theorem, promotion, or release authority. All eight external activation gates remain independently required.
