# Corpus Index — Duotronic Witness Contract v1.6 Draft 5.3.15

**Lifecycle:** permanently not frozen.  
**Authority:** theorem, promotion, and release authority disabled.  
**Release class:** corrective, externally anchored, governed-audit development corpus.

## Entry points

- Canonical descriptor: `CANONICAL_CORPUS_v1_6_draft_5_3_15.json`
- Primary contract: `duotronic_witness_contract_v1_6_draft_5_3_15.md`
- Start guide: `START_HERE.md`
- Release notes: `RELEASE_NOTES_v1_6_draft_5_3_15.md`
- Corrective assurance: `DRAFT5_3_15_CORRECTIVE_ASSURANCE_REPORT.md`
- Migration: `migration/draft5_3_14_to_draft5_3_15_migration_runbook.md`
- Review checklist: `refs/review/v1.6_draft_5.3.15_update_checklist.md`

## Runtime and audit authority

- Proof service: `executable/runtime/proof_check_service.py`
- Proof authority: `executable/runtime/proof_authority.py`
- Audit primitives: `executable/runtime/cache_audit.py`
- Publisher and anchor services: `executable/runtime/cache_audit_services.py`
- Production loader integration: `executable/validators/run_production_loader_integration.py`

## Validation

- Corpus validator: `executable/validators/validate_draft5_3_15_corpus.py`
- Schema registry builder: `executable/validators/build_schema_registry_v5315.py`
- Schema validator: `executable/validators/validate_draft5_3_15_schemas.mjs`
- Python evidence: `executable/validators/generate_draft5_3_15_python_evidence.py`
- Reliability runner: `executable/validators/run_draft5_3_15_validator_reliability.py`
- Manifest builder: `executable/validators/build_draft5_3_15_manifests.py`

## Authority boundary

Portable validation and successful non-root loader execution do not complete the eight external activation gates. See `DRAFT5_3_15_RELEASE_GATE_STATUS.json`.
