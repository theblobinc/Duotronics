# Start Here — Duotronic v1.6 Draft 5.3.3

**Status:** complete active living draft; permanently not frozen.

## Deterministic boot

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_3.json`.
2. Require `active_version == "v1.6-draft-5.3.3"` and
   `freeze_state == "permanently_not_frozen"`.
3. Verify the inventory and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_3.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_3.json` for canonical writes.
5. Run `python3 executable/validators/validate_draft5_3_3_corpus.py`.
6. Reject any required missing, duplicate, failed, skipped, or unknown phase.
7. Load the active contract and canonical resolver.
8. Keep theorem authority disabled unless the deployment separately satisfies
   the real-image, strict-evidence, protected-key, and external-trust conditions.

## Authority rules

- Requests select a governance-signed `compiler_profile_id`; they never supply
  executable paths, digests, environment, authority outputs, or timestamps.
- Accepted sources are copied to an immutable snapshot. Prebuilt outputs,
  symlinks, executables, and native plugins are rejected.
- The exact deterministic target uses direct theorem-to-statement term binding.
- Authority comes only from canonical structured Lean environment/type/axiom
  output, never stdout regexes or source searches.
- Lake, actual Lean, stdlib, dependency closure, image, verifier binary, and
  sandbox policy are separate signed fields.
- Key lifecycle and supersession records require signed governance authorization.
- Historical authority uses a signed explicit as-of snapshot.
- Authority records are append-only; corrections supersede rather than mutate.
- Positive-baseline computation produces evidence and never bypasses promotion.

## Database migration order

1. `executable/sql/draft5_2_schema_additions.sql`
2. `migration/draft5_2_2_to_draft5_3_1.sql`
3. `migration/draft5_3_1_to_draft5_3_2.sql`
4. `migration/draft5_3_2_to_draft5_3_3.sql`

Register the SQLite cryptographic functions before applying authority writes.
The final migration provisions no governance key; external trust provisioning is
a deployment responsibility and fails closed when absent.

## Strict evidence

The portable validator reports strict Lean, strict TLC, hermetic real-Lean
integration, and external signature separately. Their absence does not freeze or
invalidate the living draft; it disables the authority claims that require them.
