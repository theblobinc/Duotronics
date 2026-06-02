# Duotronic v1.6 Draft 3 Updated Release Notes

**Status:** Research specification draft  
**Version:** release-notes@v1.6-draft-3-update-2026-04-30  
**Document kind:** Markdown specification  
**Primary purpose:** Summarize the updated Draft 3 source refresh changes.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Release theme

This update turns Draft 3 from a recurrence/MCP tuning corpus into a source-aligned implementation corpus. The main change is documentation of the newest SRNN implementation layer: SDKs, OpenAPI, formal methods, mutation policy, threat model, proof interchange, cognition migration, and WG-RNN temporal authority tests.

## 2. New implementation themes

### 2.1 API and SDK hardening

The corpus now distinguishes:

- API shape exists;
- OpenAPI export exists;
- SDK skeletons exist;
- response signatures, request signatures, fine-grained scopes, and immutable audit proofs remain release-blocking hardening items.

### 2.2 Formal methods scope

The corpus now records that TLA+ and Lean 4 formal models exist as implementation artifacts, but not all theorem stubs are complete. Any `sorry` or proof stub is a non-canonical proof gap.

### 2.3 Mutation policy

The corpus now documents default-deny mutation policy for critical code paths, review-required paths for policy/replay/proof logic, auto-allowed helper paths, and generated-artifact paths.

### 2.4 WG-RNN temporal authority

The updated runtime contract now incorporates source evidence that WG-RNN is always enabled in authoritative mode, falls back to an authoritative shim when Duotronics prototype imports are missing, and emits a `last_update_record` with gate values, replay identity, policy decision ID, and temporal authority fields.

### 2.5 Cognition migration

The update records the two compatible approaches that now coexist:

- additive `step` migration for compatibility with historical tooling;
- step derivation from `state_json` for tools that do not assume a physical `step` column.

## 3. Compatibility

This update is additive. Existing Draft 3 documents remain valid unless superseded by a same-topic `v1_1` document.
