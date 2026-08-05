# Start Here — Duotronic v1.6 Draft 5.3.6

**Status:** completed corrective development draft; permanently not frozen.  
**Theorem/promotion authority:** disabled unless every external activation gate passes.

## Deterministic boot

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_6.json` only.
2. Require active version `v1.6-draft-5.3.6`, permanent-unfrozen lifecycle,
   disabled theorem/promotion defaults, and release authority false.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_6.json` and
   `refs/manifest/CHECKSUMS_v1_6_draft_5_3_6.sha256` against final bytes.
4. Load `refs/schema_registry_v1_6_draft_5_3_6.json`; reject unclassified or
   noncanonical schemas on active write surfaces.
5. Read `PACKAGE_PROVENANCE_v1_6_draft_5_3_6.json`; treat
   `unpublished_workspace` as an activation blocker.
6. Run `python3 executable/validators/validate_draft5_3_6_corpus.py`.
7. Reject missing, duplicate, failed, skipped, or unknown required phases.
8. Keep authority disabled unless strict Lean/TLC, governed-image inspection,
   reproducible build, committed-source, protected-key, and external-governance
   evidence all pass.

## Non-negotiable rules

- Resolve and authorize the immutable policy decision before OCI execution.
- Open the source root once; traverse descriptor-relatively under governed bounds.
- Hash only sealed snapshot inputs.
- Select each domain wrapper with explicit OCI `--entrypoint`.
- Keep final signed-result storage absent from both containers.
- Derive and hash the exact executed OCI argv from one sealed invocation.
- Bind policy-derived source, time, artifact, handoff, inspection, and result limits.
- Bind requested, emitted, accepted, measured, and derived controls separately.
- Consume and verify the exact compiled `.olean` handoff manifest.
- Require recursive compiled dependency and axiom inspection to pass.
- Validate canonical schemas before signatures and persistence.
- Persist bounded principal-scoped idempotency with recoverable leases.
- Reject runtime-version mismatch and UID/GID zero.
- Bound output while it is produced and terminate descendants on exhaustion.
- Use only the registered canonical synchronous proof-check route.
- Preserve authority records append-only and replay at an immutable ledger cutoff.
- Never promote mathematical computation directly to theorem.

## Database migration order

1. `executable/sql/draft5_2_schema_additions.sql`
2. `migration/draft5_2_2_to_draft5_3_1.sql`
3. `migration/draft5_3_1_to_draft5_3_2.sql`
4. `migration/draft5_3_2_to_draft5_3_3.sql`
5. `migration/draft5_3_3_to_draft5_3_4.sql`
6. `migration/draft5_3_4_to_draft5_3_5.sql`
7. `migration/draft5_3_5_to_draft5_3_6.sql`

Register canonical JSON, SHA-256, event-root, and Ed25519 SQLite functions
before migrations or authority writes. This corpus provisions no production
key, release activation, theorem gate, or promotion authority.
