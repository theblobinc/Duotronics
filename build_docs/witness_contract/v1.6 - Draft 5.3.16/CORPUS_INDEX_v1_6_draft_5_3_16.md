# Corpus Index — Duotronic Witness Contract v1.6 Draft 5.3.16

**Lifecycle:** permanently not frozen.  
**Authority:** theorem, promotion, and release authority disabled.  
**Release class:** authenticated three-identity audit-boundary corrective corpus.

## Entry points

- `CANONICAL_CORPUS_v1_6_draft_5_3_16.json`
- `START_HERE.md`
- `duotronic_witness_contract_v1_6_draft_5_3_16.md`
- `RELEASE_NOTES_v1_6_draft_5_3_16.md`
- `DRAFT5_3_16_CORRECTIVE_ASSURANCE_REPORT.md`
- `migration/draft5_3_15_to_draft5_3_16_migration_runbook.md`

## Runtime and validation

- Audit primitives: `executable/runtime/cache_audit.py`
- Publisher/anchor services: `executable/runtime/cache_audit_services.py`
- Production launchers: `executable/runtime/cache_audit_publisher_server.py`, `executable/runtime/cache_audit_anchor_server.py`
- Production integration: `executable/validators/run_production_loader_integration.py`
- Corpus validator: `executable/validators/validate_draft5_3_16_corpus.py`
- Schema generator: `executable/validators/build_schema_registry_v5316.py`
- Python evidence: `executable/validators/generate_draft5_3_16_python_evidence.py`

The file-backed anchor is development-only. See `DRAFT5_3_16_RELEASE_GATE_STATUS.json` for incomplete external authority gates.
