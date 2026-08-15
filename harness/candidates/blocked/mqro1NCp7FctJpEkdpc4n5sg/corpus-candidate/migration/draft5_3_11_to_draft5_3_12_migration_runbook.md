# Draft 5.3.11 → Draft 5.3.12 Migration Runbook

Draft 5.3.12 changes validator orchestration and the governed cache-registry/replay contract. It does not reinterpret existing authority SQL records; `migration/draft5_3_6_to_draft5_3_7.sql` remains the latest authority-database migration.

1. Keep theorem, promotion, and release authority disabled.
2. Install `cache_registry_lineage_v1.schema.json` and `cache_stale_row_evidence_v2.schema.json` with the complete active schema set.
3. Add `cache_registry_lineage_file` to production service configuration.
4. Sign a lineage document that identifies the current registry and every retained historical registry by canonical SHAKE256-512.
5. Ensure each historical successor path is complete, acyclic, strictly chronological, and terminates at the current registry.
6. Retain historical public verification keys under governance; do not retain retired private signing keys.
7. Deploy the Draft 5.3.12 service so stale replay authenticates the row before emitting evidence or returning the stable conflict.
8. Replace the monolithic validator with `validate_draft5_3_12_corpus.py`; require bounded capture, bounded reaping, and descendant-cleanup regressions to pass.
9. Run `run_production_loader_integration.py` in a host or user namespace that represents the intended service UID/GID. An `environment_unavailable` result is not a pass.
10. Generate one Python record per available interpreter, explicitly mark unavailable targets, and merge the matrix.
11. Rebuild the schema registry and package manifests, then validate a fresh extraction.
12. Complete the eight external activation gates before enabling any authority path.
