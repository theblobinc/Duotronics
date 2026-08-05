# SRNN Server Draft 4.1 Source Observation Notes

Status: source-observation note for Draft 4.1.  
Generated: 2026-05-09.

## Purpose

This note records the implementation surfaces that motivated Draft 4.1 closeout
contracts. It is not a production runtime certification.

## Observed source-aligned surfaces

- Runtime state carries recurrent witness, lookup witness, meta-recurrent,
  architectural, cosmological, WG-RNN runtime, witness contract version, and
  telemetry schema fields.
- Agent Lab and diagnostics expose contract views and still rely on legacy
  witness-contract version/path aliases.
- Recurrence MCP tests exercise previously target-only recurrence tools and
  scope boundaries.
- WG-RNN chat path builds model context from cognition snapshots, readiness,
  authority, policy mode, recall context, and contract views.
- Browser Chat exposes a separate invocation surface involving auth, signatures,
  nonces, allowlists, and workbench tool execution.
- GPU worker and llama-server runtime paths expose runtime status, command
  construction, model manifests, smoke/bench flows, logs, failed-start handling,
  and runtime feature controls.

## Contract consequence

Draft 4.1 treats the above as contract boundaries requiring explicit evidence
objects before release claims are allowed.
