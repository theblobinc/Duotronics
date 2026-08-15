# Duotronic v1.6 Draft 4.1 Complete Corpus

Status: active Draft 4.1 complete corpus package.  
Generated: 2026-05-09  
Base package: uploaded `v1.6 - Draft 4.zip`.  
Package root: `build_docs/witness_contract/v1.6 - Draft 4.1/`.

## Summary

v1.6 Draft 4.1 is a complete successor package to Draft 4. It preserves the full
Draft 4 corpus and closes the witness-contract gaps found during the Draft 4
review against the current SRNN Server codebase and the Draft 3 witness-contract
lineage.

Draft 4.1 is not a thin appendix. It is the full Draft 4 corpus plus updated
entry points, manifests, checksums, closeout reports, and new contract documents
that bind runtime reality to release claims.

## What changed from Draft 4

Draft 4.1 adds the following closeout layer:

1. Witness contract version aliasing and migration rules for the runtime `v8`
   lineage, the Duotronic v1.6 Draft 4.1 corpus, and the canonical
   `duotronic_witness_contract_v11_0.md` specification line.
2. MCP recurrence tool availability and maturity classification so Draft 3
   target tools are not over-promoted without source, test, runtime, and release
   evidence.
3. WG-RNN chat context-injection witness rules for prompt construction, memory
   visibility, readiness, authority, policy mode, and no-unwitnessed-capability
   claims.
4. Browser Chat / Workbench invocation witnessing for signed requests, nonce
   replay protection, allowlisted MCP calls, workbench Python/file/command
   mutation surfaces, and audit/result links.
5. Agent Lab mutation safety config witnessing for backup requirements, auto
   backup, git sync/push policy, S3 and remote backup policy, and config digest
   capture.
6. Runtime feature applicability witnessing so requested model/runtime flags are
   separated from translated, applied, and unsupported backend features.
7. Runtime readiness evidence persistence rules tying status, command, logs,
   smoke, bench, and model-file evidence to durable witness records.
8. Draft 4.1 conformance delta validation plan and migration runbook.

## Primary Draft 4.1 entry points

```text
START_HERE.md
README.md
START_HERE_v1_6_draft_4_1.md
README_v1_6_draft_4_1.md
RELEASE_NOTES_v1_6_draft_4_1.md
CORPUS_INDEX_v1_6_draft_4_1.md
corpus_review_v1_6_draft_4_to_v1_6_draft_4_1.md
duotronic_draft4_1_contract_closeout_report.md
duotronic_draft4_1_witness_contract_version_alias_and_migration_profile_v1_0.md
mcp/mcp_recurrence_tool_availability_matrix_v1_6_draft_4_1.md
runtime/wgrnn_chat_context_injection_witness_contract_v1_0.md
browser/browser_chat_workbench_invocation_witness_contract_v1_0.md
duotronic_draft4_1_agent_lab_mutation_safety_config_witness_profile_v1_0.md
runtime/runtime_feature_applicability_witness_contract_v1_0.md
runtime/runtime_readiness_evidence_persistence_profile_v1_0.md
refs/manifest/MANIFEST_v1_6_draft_4_1_complete.md
refs/manifest/CHECKSUMS_v1_6_draft_4_1.shake256_512
```

## Authoritative reading rule

Draft 4.1 is authoritative for the v1.6 Draft 4.x line. Files whose names still
contain Draft 1, Draft 2, Draft 3, or Draft 4 remain present as carried-forward
history or source baseline material unless a Draft 4.1 file supersedes them.
When a Draft 4.1 entry point conflicts with an older carried-forward document,
Draft 4.1 wins.

## Release-status boundary

Draft 4.1 is package-complete and contract-complete for the closeout items above.
It does not claim production cluster startup, live container verification, full
SRNN test-suite pass, or operator-approved production release unless those
runtime evidence records are added by a later release witness bundle.

## Apply rule

Copy or commit the entire directory as a complete corpus package:

```text
build_docs/witness_contract/v1.6 - Draft 4.1/
```

Do not apply Draft 4.1 by copying only the new files. The package is intended to
be a complete standalone directory.
