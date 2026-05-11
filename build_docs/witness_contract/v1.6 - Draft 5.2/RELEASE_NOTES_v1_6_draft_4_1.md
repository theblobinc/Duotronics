# Release Notes - Duotronic v1.6 Draft 4.1

Status: release notes.  
Generated: 2026-05-09.  
Supersedes: `RELEASE_NOTES_v1_6_draft_4.md` for the active Draft 4.x line.

## Summary

Draft 4.1 completes Draft 4 by adding the missing bridge between source-observed
SRNN behavior and witness-contract release claims. The package preserves all
Draft 4 files and adds updated entry points, a refreshed manifest, checksums, and
new contract documents.

## Included update classes

### 1. Full Draft 4 carry-forward

The uploaded Draft 4 archive is used as the physical base for Draft 4.1. All
Markdown and non-Markdown artifacts are retained unless superseded by an active
Draft 4.1 entry point.

### 2. Version alias and migration closure

Draft 4.1 records that the runtime may still expose legacy fields such as
`witness_contract_version: v8` while the corpus is Duotronic v1.6 Draft 4.1 and
some implementation docstrings reference the `duotronic_witness_contract_v11_0.md`
lineage. Draft 4.1 treats these as aliases that require explicit migration
witnessing, not as contradictory contract identities.

### 3. MCP recurrence tool maturity closure

Draft 4.1 adds an explicit matrix for recurrence tools that were Draft 3 targets
and are now source-observed or test-backed. A tool is not release-certified until
it has the corresponding runtime evidence and release bundle linkage.

### 4. WG-RNN chat context injection closure

Draft 4.1 defines how WG-RNN state, contract views, readiness, authority,
policy mode, recall context, and freshness constraints may be placed into chat
context. It also defines the no-unwitnessed-memory and no-unwitnessed-capability
claim rule.

### 5. Browser Chat / Workbench authority closure

Draft 4.1 adds a witness contract for signed browser requests, nonce replay
protection, allowlisted MCP calls, and workbench mutation surfaces. This closes
the gap between MCP governance and browser-mediated execution.

### 6. Mutation safety config closure

Draft 4.1 adds a required witness object for mutation safety configuration:
preflight backups, auto backup, git sync, git push, S3/remote backup policy, and
configuration digest.

### 7. Runtime applicability and persistence closure

Draft 4.1 separates requested, translated, applied, and unsupported runtime
features. It also requires readiness evidence to be persisted with references to
logs, command hashes, runtime config digests, smoke results, benchmark results,
and model-file evidence.

## Release boundary

Draft 4.1 is a complete corpus and conformance package. It is suitable to commit
as the next witness-contract directory. Production certification still requires a
runtime evidence bundle generated from the target SRNN deployment.
