# Duotronic v1.6 Draft 3 Release Notes

**Status:** Research specification draft  
**Version:** release-notes@v1.6-draft-3  
**Document kind:** Release notes  
**Primary purpose:** Summarize Draft 3 changes from Draft 2.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Release theme

Draft 3 moves v1.6 from implementation readiness into runtime tuning readiness. The draft adds operational recurrence guidance for live SRNN/MCP deployments and documents current source updates from the SRNN repository.

## 2. Major changes

1. Runtime recurrence tuning profile added.
2. Temporal witness and absence profile added.
3. WG-RNN gate defaults made reference-only rather than normative constants.
4. MCP observed tools separated from desired target tools.
5. Missing runtime tools backlog added.
6. Live recurrent witness overlay contract added.
7. Stdio principal policy added.
8. Direct mutation tools security addendum upgraded to include allowed-root constraints and mutation sync obligations.
9. Manifest documents moved into `refs/manifest/`.
10. Complete integration document added for runtime recurrence, MCP, SRNN source deltas, and corpus policy.

## 3. Current SRNN source observations integrated

Draft 3 records these source-facing updates:

- identity oracle adapters are auto-registered through package import side effects;
- stdio sessions may resolve a configured default principal;
- direct file and command tools are constrained by an allowed host root;
- stale ephemeral evidence is tested for quarantine/block-promotion behavior;
- slow-changing stale evidence is tested for authority degradation;
- daemon status exposes a live recurrent witness overlay;
- cognition snapshot tooling no longer assumes a physical `step` column and derives step from JSON state;
- the live overlay prefers canonical loops such as `chrono-main` over test loops unless explicitly requested.

## 4. Compatibility

Draft 3 is backward-compatible with Draft 2 documents. Unchanged Draft 2 documents remain in the corpus unless superseded by a Draft 3 document.

## 5. Draft 3 source-refresh update

A source-refresh update has been added to this Draft 3 package. It is additive and preserves the original Draft 3 release notes.

The update adds source-aligned documents for SDK/OpenAPI, formal models, mutation policy, security closure, phase-3 validation, cognition step migration, live recurrent witness overlay, and WG-RNN temporal authority runtime behavior.
