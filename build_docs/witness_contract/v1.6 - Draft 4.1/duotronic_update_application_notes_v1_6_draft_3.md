# Draft 3 Update Application Notes

**Status:** Research specification draft  
**Version:** draft3-update-application-notes@v1.0  
**Document kind:** Markdown specification  
**Primary purpose:** Explain how to apply this updated Draft 3 package.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Apply order

1. Apply the previous v1.6 Draft 3 corpus if it is not already present.
2. Add all files from this updated package.
3. Keep `refs/manifest/` as the manifest home.
4. Prefer `v1_1` files over older `v1_0` files when both cover the same topic.
5. Review current SRNN working tree state before committing generated or modified test files.

## 2. Files that supersede earlier Draft 3 files

| New file | Supersedes or extends |
|---|---|
| `duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md` | `duotronic_wgrnn_gate_reference_defaults_v1_0.md` for runtime source behavior |
| `duotronic_live_recurrent_witness_overlay_contract_v1_1.md` | `duotronic_live_recurrent_witness_overlay_contract_v1_0.md` |
| `duotronic_cognition_step_migration_and_snapshot_profile_v1_1.md` | `duotronic_cognition_loop_migration_note_v1_0.md` |
| `duotronic_sdk_and_openapi_integration_profile_v1_1.md` | API/SDK prose that predates executable OpenAPI |
| `duotronic_sdk_threat_model_security_closure_plan_v1_0.md` | older generic security backlog |
| `duotronic_mutation_policy_defaults_profile_v1_0.md` | generic source-governance notes |

## 3. Release-candidate blockers after this update

- Implement response signatures.
- Implement request signatures.
- Implement fine-grained scopes.
- Implement append-only audit chain verification.
- Add explicit OpenAPI schemas.
- Resolve or document working-tree modifications.
- Complete high-priority Lean 4 proof stubs or mark them explicitly as unproved.
- Run and capture phase-3 validation report.
