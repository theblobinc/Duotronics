# Migration Runbook - v1.6 Draft 4 to v1.6 Draft 4.1

Status: active Draft 4.1 migration runbook.  
Generated: 2026-05-09.

## Scope

This runbook describes how to replace Draft 4 with Draft 4.1 in the witness
contract corpus while preserving the full Draft 4 file body.

## Steps

1. Copy the complete `v1.6 - Draft 4.1/` directory into
   `build_docs/witness_contract/`.
2. Treat `START_HERE.md` and `README.md` as the active local entry points.
3. Treat `START_HERE_v1_6_draft_4_1.md`, `README_v1_6_draft_4_1.md`,
   `RELEASE_NOTES_v1_6_draft_4_1.md`, and `CORPUS_INDEX_v1_6_draft_4_1.md` as
   the active versioned entry points.
4. Keep Draft 4 files for traceability unless a downstream consumer requires
   pruning.
5. Update any external release notes or build index to point to
   `refs/manifest/MANIFEST_v1_6_draft_4_1_complete.md`.
6. Before production claims, collect the runtime evidence bundle listed in
   `duotronic_draft4_1_contract_closeout_report.md`.

## Compatibility

Draft 4.1 is backward-compatible with Draft 4 as a corpus package. It is stricter
than Draft 4 for release claims because it requires explicit evidence for
version aliasing, MCP tool maturity, chat context injection, browser invocation,
mutation safety config, runtime applicability, and readiness persistence.
