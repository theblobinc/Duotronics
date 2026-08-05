# SRNN Source Update Review for Draft 3 Update

**Status:** Research specification draft  
**Version:** source-review@v1.6-draft-3-update-2026-04-30  
**Document kind:** Markdown specification  
**Primary purpose:** Record the newest SRNN source-code changes that affect the v1.6 Draft 3 corpus.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Review result

The SRNN repo has moved beyond the previously documented Draft 3 state. The updated corpus now incorporates three new implementation layers:

1. Draft 2 executable artifacts and OpenAPI export.
2. SDK/formal-model artifacts.
3. Phase 3 security, testing, and mutation-policy artifacts.

## 2. Draft 2 executable artifacts

The source now includes an API router for Duotronic v1.6. The router advertises the following endpoint groups:

- health/version/capabilities;
- math objects, claims, domains, query;
- DBP envelopes and DBP wrapping;
- witnesses;
- replay status, replay packages, replay verification;
- policy decision;
- interpreter runs;
- Langlands objects and claims;
- proofs and conjectures;
- admin review queue.

The corpus updates the API contract and OpenAPI inventory accordingly.

## 3. Cognition step compatibility

The source includes two complementary approaches for cognition snapshot step compatibility:

1. An additive database migration that adds a `step` column and backfills from `state_json.native_index`, `state_json.step_count`, or `state_json.step`.
2. Runtime/MCP tooling that derives step from `state_json` instead of requiring a physical `step` column.

Corpus decision: both are valid. The migration improves database compatibility; JSON-derived step prevents old tooling assumptions from becoming hard runtime requirements.

## 4. SDK and formal models

The source includes:

- Python SDK skeleton with client, auth, models, setup, tests, and README.
- JavaScript/TypeScript SDK skeleton with client, auth, models, package metadata, TypeScript config, and testing setup.
- TLA+ task delegation and policy core specification.
- Lean 4 Duotronic core theorem module and proof roadmap.

Corpus decision: SDKs are implementation adapters. They must not be authority sources. Formal models are proof artifacts only to the extent that checker results and theorem completion are recorded.

## 5. Security and mutation policy

The source includes a STRIDE SDK threat model and mutation-policy framework. The threat model identifies critical gaps:

- response integrity signatures;
- request authentication signatures;
- fine-grained scope authorization;
- append-only audit log integrity verification;
- proof signature and proof checker hardening.

The mutation policy classifies automated edits by path and mutation kind. Core oracle/witness logic is default-deny; sensitive policy/replay/proof logic requires review; generated SDK/OpenAPI artifacts can be regenerated under controlled policy.

## 6. WG-RNN temporal authority

The WG-RNN runtime bridge now establishes:

- always-enabled authoritative rollout behavior;
- prototype-backed mode when Duotronics runtime imports succeed;
- authoritative shim fallback when imports are missing;
- 10-feature runtime input tensor;
- temporal authority and freshness gating;
- stale ephemeral evidence quarantine;
- stale slow-changing evidence authority degradation;
- recurrent witness temporal mirror with half-life decay, burst counts, long-gap counts, and lost witness records.

Corpus decision: Draft 3 must treat these source behaviors as runtime witness contract requirements, not implementation anecdotes.

## 7. Working tree note

The source review observed a modified phase-3 test suite file and untracked worktree directories. The updated corpus records this as a release risk: apply the corpus after reviewing whether those worktree changes should be committed, removed, or retained as experimental state.

## Draft 4 carry-forward update - 2026-05-08

This document is retained in the v1.6 Draft 4 corpus as part of the full Draft 3
carry-forward. Draft 4 adds newer SRNN Server runtime observations rather than
removing this baseline. For current Draft 4 interpretation, read:

- `README_v1_6_draft_4.md`
- `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
- `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
- `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
- `runtime/llama_server_runtime_readiness_contract_v1_0.md`

Draft 4 updates the runtime boundary with the current SRNN compose stack,
per-node `wg-rnn` service, GPU-worker llama-server large-model path, runtime
model manifest/smoke/bench endpoints, memlock diagnostics, and Agent Lab/MCP
backup-log witness handling. This update does not claim live production
certification; it records the source-observed contract and follow-up validation
requirements.
