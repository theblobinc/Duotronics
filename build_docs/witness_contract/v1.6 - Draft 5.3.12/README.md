# Duotronic Witness Contract v1.6 Draft 5.3.12

This is a standalone, permanently not-frozen, non-authoritative corrective development corpus. Begin with `CANONICAL_CORPUS_v1_6_draft_5_3_12.json`, then follow `START_HERE.md`.

Draft 5.3.12 adds bounded validator capture/reaping, nested progress evidence, and authenticated historical cache-registry replay. A stale row is classified as rotation-specific only after its signer, signature, and signed registry lineage are verified. Unknown, forged, altered, or revoked historical signers fail as integrity errors.

The production integration harness builds an `/etc/witness-authority`-style chroot and runs both actual loaders after `setgid`/`setuid`. This sandbox cannot represent the intended non-root UID, so the included evidence is `environment_unavailable`, not passed. Authority remains fail-closed.

The corpus contains merged current source only. Earlier source-package ZIPs are not embedded. `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_12.json` records predecessor digests without making them runtime authority inputs.

Run the documented workflow with each available target interpreter:

```sh
python3 executable/validators/generate_draft5_3_12_python_evidence.py --record-only
python3 executable/validators/generate_draft5_3_12_python_evidence.py --merge-only
python3 executable/validators/build_schema_registry_v5312.py
node executable/validators/validate_draft5_3_12_schemas.mjs --phase all
python3 executable/validators/build_draft5_3_12_manifests.py
python3 executable/validators/validate_draft5_3_12_corpus.py
```

The eight external activation gates remain independently incomplete. Theorem, promotion, and release authority remain disabled.
