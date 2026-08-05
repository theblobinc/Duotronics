# Corpus Review - v1.6 Draft 4 to v1.6 Draft 4.1

Status: active Draft 4.1 review note.  
Generated: 2026-05-09.

## Review basis

Draft 4.1 was produced from the uploaded `v1.6 - Draft 4.zip` package and the
Draft 4 review findings against the current SRNN Server codebase. The review
focused on mismatches between the contract corpus, Draft 3 witness-contract
lineage, and implementation surfaces that Draft 4 did not fully bind.

## Findings carried into Draft 4.1

1. The runtime still carries legacy witness contract version and path aliases.
2. MCP recurrence tools have a more advanced source/test status than Draft 3,
   but still need explicit maturity states before release claims.
3. WG-RNN chat prompt injection is a contract boundary and requires evidence.
4. Browser Chat / Workbench invocation has its own auth, signature, nonce,
   allowlist, and mutation-surface semantics.
5. Agent Lab mutation evidence must include active safety configuration.
6. Runtime model flags must distinguish requested from applied features.
7. Runtime readiness evidence must persist as release-bundle evidence, not just
   transient status output.

## Changes made

- Added Draft 4.1 entry points and release notes.
- Added closeout contracts for each missing witness boundary.
- Added a Draft 4.1 conformance delta validation plan.
- Added migration guidance from Draft 4 to Draft 4.1.
- Regenerated corpus index, manifest, release JSON, validation summary, and
  SHA256 checksums from the resulting package tree.

## Result

Draft 4.1 is the recommended v1.6 Draft 4.x package for the next implementation
pass. Draft 4 remains historical and carried-forward, but Draft 4.1 is the active
contract boundary.
