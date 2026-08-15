# Duotronic v1.6 Draft 3 Updated Corpus

**Status:** Research specification draft  
**Version:** v1.6-draft-3-update-2026-04-30-source-refresh  
**Document kind:** Markdown specification  
**Primary purpose:** Declare the updated Draft 3 corpus after the latest SRNN source review.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Summary

This package is an updated v1.6 Draft 3 corpus. It preserves the previous Draft 3 corpus in full and applies one more source-code refresh against the current `theblobinc/srnn_server` repository and MCP runtime observations.

This is not Draft 4. It is a Draft 3 update set intended to be applied on top of the earlier Draft 3 documents.

## 2. What changed in this update

The update adds and cross-links the following implementation-facing documents:

- `duotronic_srnn_source_update_review_2026_04_30_draft_3_update.md`
- `duotronic_draft_3_source_refresh_summary_2026_04_30.md`
- `duotronic_sdk_and_openapi_integration_profile_v1_1.md`
- `duotronic_sdk_threat_model_security_closure_plan_v1_0.md`
- `duotronic_mutation_policy_defaults_profile_v1_0.md`
- `duotronic_formal_models_and_proof_status_profile_v1_0.md`
- `duotronic_cognition_step_migration_and_snapshot_profile_v1_1.md`
- `duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md`
- `duotronic_live_recurrent_witness_overlay_contract_v1_1.md`
- `duotronic_phase3_validation_suite_profile_v1_0.md`
- `duotronic_openapi_runtime_surface_inventory_v1_0.md`
- `duotronic_update_application_notes_v1_6_draft_3.md`
- `refs/manifest/MANIFEST_v1_6_draft_3_updated.md`

## 3. Source review basis

This update incorporates these current SRNN directions:

1. Draft 2 artifacts are now represented by an executable FastAPI router, an OpenAPI export, proof interchange fixtures, and a compatibility migration for cognition snapshot `step`.
2. Draft 2 phase 2 added Python and JavaScript SDK skeletons plus TLA+ and Lean 4 formal models.
3. Draft 2 phase 3 added SDK threat modeling, mutation policy defaults, browser-test configuration, and a unified phase-3 validation suite.
4. WG-RNN runtime behavior now explicitly enforces temporal authority, stale evidence behavior, quarantine behavior, and authority degradation behavior.
5. Live recurrent witness overlays now surface temporal authority and last update records through runtime status.

## 4. Apply guidance

When applying this corpus:

1. Keep the existing Draft 3 files.
2. Add the new files in this package.
3. Prefer the `*_v1_1.md` files over their `*_v1_0.md` counterparts where both exist.
4. Treat the source refresh review as an implementation-observation record, not as a claim that all listed code paths have production-grade security closure.
5. Treat the formal model documents as formalization scaffolding unless a theorem is explicitly marked proved and checker-verified.

## 5. Manifest

The updated manifest lives at:

```text
refs/manifest/MANIFEST_v1_6_draft_3_updated.md
```
