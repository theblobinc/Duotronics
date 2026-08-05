# Duotronic Witness Contract v1.6 Draft 5.3.10

This is a standalone, permanently not-frozen, non-authoritative corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_10.json`, then follow `START_HERE.md`.

Draft 5.3.10 closes the remaining portable Draft 5.3.9 trust-semantics findings. The idempotency store closes every connection acquired before validation, migrates only an exactly verified predecessor schema, compares normalized table and index SQL, `table_xinfo`, `index_list`, `index_xinfo`, primary-key order, affinities, constraints, defaults, uniqueness, and partial-index state, and binds the canonical schema digest to migration metadata.

Cache signing now uses a governance-signed v2 registry with mandatory RFC 3339 intervals, current-time enforcement, complete predecessor references, ordered lineage, and cycle rejection. Only a currently active, time-valid key may sign or replay a cache row; retired and revoked keys invalidate prior cache rows. Each envelope binds its registry snapshot and signing-time validity decision, and replay emits a fresh registry-bound verification evidence record.

One monotonic deadline is checked before and after compiler-witness signing, result validation, cache-envelope signing, final lease renewal, and durable SQLite completion. SQLite busy timeouts consume only the remaining request budget, and a completion that crosses the deadline is removed before failure is returned. The trusted Lean consumer reconstructs the complete ordered command set from the pinned executable, sealed module and output paths, warning policy, working directory, and exact environment identity, rejecting altered, missing, extra, or reordered hashes.

The corpus contains merged current source only. Earlier source-package ZIPs are not embedded. `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_10.json` records predecessor digests without making them authority inputs.

Python evidence uses three distinct fields: `target_python_versions`, `validated_python_versions`, and `unavailable_python_versions`. Draft 5.3.10 targets Python 3.12 and 3.13. This package was executed on Python 3.12.13; Python 3.13 was unavailable, so no current-revision Python 3.13 execution claim is made.

Run portable validation with a target interpreter:

```sh
python3 executable/validators/generate_draft5_3_10_regression_counts.py
python3 executable/validators/build_schema_registry_v5310.py
node executable/validators/validate_draft5_3_10_schemas.mjs --phase all
python3 executable/validators/build_draft5_3_10_manifests.py
python3 executable/validators/validate_draft5_3_10_corpus.py
```

Portable passing results do not grant theorem, promotion, or release authority. All eight external activation gates remain independently required.
