# Duotronic Witness Contract v1.6 Draft 5.3.7

This is a standalone, permanently unfrozen corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_7.json`, then follow `START_HERE.md`.

Draft 5.3.7 supersedes Draft 5.3.6 only on its explicitly versioned active surfaces. It closes domain-specific file-size binding and exact `RLIMIT_FSIZE` measurement, distinguishes six control evidence states, generates regression totals from discovery, makes warning-free development-mode execution mandatory, and deterministically closes SQLite test connections.

Run portable validation with:

```sh
python3 executable/validators/generate_draft5_3_7_regression_counts.py
python3 executable/validators/build_schema_registry_v537.py
node executable/validators/validate_draft5_3_7_schemas.mjs --phase all
python3 executable/validators/build_draft5_3_7_manifests.py
python3 executable/validators/validate_draft5_3_7_corpus.py
```

Portable passing results do not grant theorem, promotion, or release authority. Eight external activation gates remain independently required. The exact Draft 5.2.2 through 5.3.6 packages are retained under `history/source_packages/`.
