# Duotronic Witness Contract v1.6 Draft 5.3.8

This is a standalone, permanently unfrozen corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_8.json`, then follow `START_HERE.md`.

Draft 5.3.8 treats completed idempotency rows as untrusted signed cache envelopes; re-verifies policy, principal, request, claim, source, status, and compiler-witness bindings on every hit; requires authenticated middleware identity; measures the mandatory environment and entrypoint controls; separates semantic witness identity from execution evidence; closes every SQLite connection; and bounds in-flight and total cache state.

The corpus contains the merged current source only. Earlier source-package ZIPs are not embedded. `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_8.json` records predecessor digests without making them authority inputs.

Run portable validation with Python 3.12 or 3.13:

```sh
python3 executable/validators/generate_draft5_3_8_regression_counts.py
python3 executable/validators/build_schema_registry_v538.py
node executable/validators/validate_draft5_3_8_schemas.mjs --phase all
python3 executable/validators/build_draft5_3_8_manifests.py
python3 executable/validators/validate_draft5_3_8_corpus.py
```

Executed matrix evidence is recorded in `DRAFT5_3_8_PYTHON_MATRIX_VALIDATION.json`.

Portable passing results do not grant theorem, promotion, or release authority. All eight external activation gates remain independently required.
