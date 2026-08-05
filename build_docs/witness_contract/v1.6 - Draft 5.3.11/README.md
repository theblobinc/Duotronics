# Duotronic Witness Contract v1.6 Draft 5.3.11

This is a standalone, permanently not-frozen, non-authoritative corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_11.json`, then follow `START_HERE.md`.

Draft 5.3.11 closes the portable Draft 5.3.10 findings:

- production trust-root ancestry now permits immutable root-owned `/` and system ancestors while requiring a private service-owned final root; every component remains no-follow and non-writable by group/other, and UID/GID zero is rejected before configuration is consumed;
- cache-key `status_changed_at` must be non-future and coherent with `valid_from`, `valid_until`, active, retired, and revoked state; the timestamp is signed in cache-validity evidence and rechecked during replay;
- service configuration, compiler registries, proof-policy registries, trusted-artifact registries, platform evidence, and cache-signing registries use duplicate-rejecting canonical JSON before schema/signature verification; authority schema documents reject duplicate keys;
- stale rows after cache-key rotation or registry replacement are preserved, audited, and rejected with `cache_key_rotation_requires_new_idempotency_key`; the service never silently deletes or re-executes them;
- Python evidence is one hash-covered artifact per interpreter target, merged deterministically without overwriting prior runs or allowing validated/unavailable overlap.

The prior exact SQLite identity, connection cleanup, deadline-through-publication, owner-fenced leases, dual-domain execution evidence, Lean-command reconstruction, mandatory sandbox evidence, and cache/witness signer separation remain active.

The corpus contains merged current source only. Earlier source-package ZIPs are not embedded. `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_11.json` records predecessor digests without making them runtime authority inputs.

Measured current-revision evidence covers Python 3.12.13 and Python 3.13.5: 248/248 tests pass on each interpreter in normal and development warnings-as-errors modes. The exact counts are regenerated from `unittest.TestResult`; narrative and machine totals must agree.

Run the complete portable workflow with either target interpreter (the shipped per-interpreter record for the other target is retained and re-merged):

```sh
python3 executable/validators/generate_draft5_3_11_python_evidence.py
python3 executable/validators/build_schema_registry_v5311.py
node executable/validators/validate_draft5_3_11_schemas.mjs --phase all
python3 executable/validators/build_draft5_3_11_manifests.py
python3 executable/validators/validate_draft5_3_11_corpus.py
```

Portable passing results do not grant theorem, promotion, or release authority. Strict Lean, strict TLC, governed hermetic-image execution, signed OCI-image attestation, signed verifier-executable attestation, reproducible inspector-build attestation, clean committed-source provenance, and external governance authorization remain eight independent incomplete gates.
