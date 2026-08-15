# Corpus Review: v1.6 Draft 2 to v1.6 Draft 3

**Status:** Research specification draft  
**Version:** corpus-review@v1.6-draft-3  
**Document kind:** Corpus review note  
**Primary purpose:** Record the review decisions used to promote Draft 2 into Draft 3.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Review inputs

Draft 3 incorporates a runtime review focused on temporal recurrence, L2/L2M/WG-RNN memory behavior, L3/L4/L5 cognition constraints, and MCP runtime observability.

The review identified one key distinction that Draft 2 had not made explicit enough: **current MCP capabilities are not the same as desired recurrence-control tools**. Draft 3 therefore adds a verified-vs-target tool matrix and a missing-tool backlog.

## 2. Accepted changes

| Area | Decision |
|---|---|
| Temporal representation | Add first-class `TemporalWitness`, `AbsenceWitness`, and gap accounting. |
| L2 recurrence | Require `MemoryUpdateRecord` for writes, decays, quarantines, skipped writes, and policy-clamped updates. |
| L2M memory | Split timescales from L2 and use explicit associative slots. |
| Decay | Model decay as a witness proposal and lifecycle event, not a hidden parameter. |
| Gate thresholds | Provide reference defaults, not normative constants. |
| L3 cognition | Constrain L3 by max delta and promotion budget. |
| L4/L5 governance | Route structural changes and profile promotion through proposal/review/policy paths. |
| MCP tools | Separate observed tools from target tools; add backlog. |
| Manifest layout | Move manifests to `refs/manifest/`. |

## 3. Rejected or narrowed changes

- “Older slots decay faster” was narrowed. Age is only one input; decay must consider stability class, evidence density, contradiction rate, last replay success, and policy scope.
- Numeric thresholds such as 0.65 and 0.85 are retained only as reference defaults.
- Direct theorem promotion by similarity or recurrence behavior remains forbidden.

## 4. Draft 3 promotion condition

A runtime may claim v1.6 Draft 3 recurrence conformance only if it can produce replayable records for temporal witnesses, absence witnesses, memory updates, gate decisions, policy clamps, and L3/L4/L5 actions.
