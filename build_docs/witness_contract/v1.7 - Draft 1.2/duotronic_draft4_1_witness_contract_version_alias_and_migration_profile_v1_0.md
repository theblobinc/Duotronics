# Witness Contract Version Alias and Migration Profile - v1.6 Draft 4.1

Status: active Draft 4.1 contract profile.  
Generated: 2026-05-09.  
Supersedes: implicit version assumptions in Draft 4.

## Purpose

This profile closes the version-identity gap between the current SRNN runtime,
the v1.6 Draft 4.1 corpus, and the historical witness-contract specification
lineage.

The runtime may still expose legacy names such as `witness_contract_version: v8`
and files such as `docs/WITNESS_CONTRACT_v8.md`, while the active corpus is
Duotronic v1.6 Draft 4.1 and implementation comments may reference
`duotronic_witness_contract_v11_0.md`. Draft 4.1 treats these as explicit aliases
that must be carried in witness evidence.

## Canonical object

```yaml
WitnessContractVersionAlias:
  schema: witness-contract-version-alias@v1
  srnn_runtime_contract_version: v8
  srnn_runtime_telemetry_schema_version: telemetry@v1
  duotronic_corpus_version: v1.6-draft-4.1
  duotronic_package_root: build_docs/witness_contract/v1.6 - Draft 4.1/
  canonical_contract_doc: duotronic_witness_contract_v11_0.md
  legacy_runtime_contract_paths:
    - docs/WITNESS_CONTRACT_v8.md
    - docs/WITNESS_CONTRACT-v2.md
  migration_status: alias_required
  claim_rule: runtime v8 fields are compatibility aliases, not proof of native Draft 4.1 migration
```

## Required evidence fields

Every release or runtime evidence bundle that cites witness contract identity
MUST include:

```yaml
WitnessContractIdentityEvidence:
  observed_at: timestamp
  observed_by: string
  runtime_loop_id: string | null
  runtime_node_id: string | null
  observed_runtime_contract_version: string
  observed_telemetry_schema_version: string | null
  package_contract_version: v1.6-draft-4.1
  canonical_contract_doc_sha256: sha256 | null
  alias_profile_sha256: sha256
  alias_resolution: compatible | incompatible | unknown
  migration_action_required: boolean
```

## Compatibility rules

1. `v8` is compatible with Draft 4.1 only when this alias profile is present in
   the same evidence bundle.
2. `v8` MUST NOT be described as Draft 4.1-native.
3. Draft 4.1 release claims MUST name the package version and the runtime alias
   separately.
4. A future migration may change `migration_status` to `migrated` only after the
   runtime state, path resolver, diagnostic payloads, and tests stop requiring
   the alias profile.
5. Historical Draft 2, Draft 3, and Draft 4 files remain traceable history unless
   contradicted by a Draft 4.1 active profile.

## Migration checklist

```yaml
Draft41VersionMigrationChecklist:
  update_runtime_default_contract_version: pending
  update_agent_lab_contract_path_resolution: pending
  update_diagnostic_contract_view: pending
  update_wgrnn_contract_view: pending
  add_alias_profile_to_release_bundle: required_now
  add regression test for alias profile: required_now
```
