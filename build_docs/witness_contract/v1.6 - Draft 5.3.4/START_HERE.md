# Start Here — Duotronic v1.6 Draft 5.3.4

**Status:** corrective development draft; permanently not frozen.  
**Theorem/promotion authority:** disabled unless every deployment gate passes.

## Deterministic boot

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_4.json` only.
2. Require `active_version == "v1.6-draft-5.3.4"`, permanent-unfrozen
   lifecycle, disabled default theorem authority, and release authority false.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_4.json` and
   `refs/manifest/CHECKSUMS_v1_6_draft_5_3_4.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_4.json` for canonical writes.
5. Run `python3 executable/validators/validate_draft5_3_4_corpus.py`.
6. Reject missing, duplicate, failed, skipped, or unknown required phases.
7. Load the active contract, resolver, v3 compiler witness, v2 authority
   snapshot, v1 event ledger, v2 sandbox, and 5.3.4 SQL migration.
8. Keep theorem authority disabled unless real-image, strict formal, build
   attestation, protected-key, and external-governance evidence all pass.

## Non-negotiable rules

- Snapshot first; hash only sealed snapshot bytes.
- Submitted Lean never receives the verifier request or final result mount.
- Accept only an authorized Ed25519-signed trusted-verifier result.
- Bind verifier, Lean, Lake, stdlib, dependencies, image, OCI runtime, and
  effective sandbox invocation independently.
- Apply exact governance action scopes and authorization windows.
- Replay with effective time and ledger high-water sequence.
- Treat backdating and supersession as explicit signed corrections.
- Preserve authority records append-only.
- Never promote mathematical computation directly to theorem.

## Database migration order

1. `executable/sql/draft5_2_schema_additions.sql`
2. `migration/draft5_2_2_to_draft5_3_1.sql`
3. `migration/draft5_3_1_to_draft5_3_2.sql`
4. `migration/draft5_3_2_to_draft5_3_3.sql`
5. `migration/draft5_3_3_to_draft5_3_4.sql`

Register SQLite canonicalization, SHA-256, event-root, and Ed25519 functions
before migration or authority writes. The portable corpus provisions no
production governance key, release activation, or theorem authority.

Successful external evidence may activate a deployment, but it never freezes
this contract. A later revision becomes the new active root and retains this
one as historical evidence.
