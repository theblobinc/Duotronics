# v1.5 Draft 2 Reading Guide

**Status:** Internal corpus map
**Version:** reading-guide@v1.5-draft-2
**Document kind:** Corpus map, reading order, and role-based entry points
**Primary purpose:** Give human reviewers and machine-learning / augmented-intelligence systems a single place to learn what every document in `build_docs/witness_contract/v1.5 - Draft 2/` is, what it owns, and in what order to read it for a given role.

---

## 1. Top-level entry points

Read these first, regardless of role.

1. `duotronic_program_charter_v1_0.md` — program scope, separation rule, and relationship to the legacy chapter material.
2. `README_v1_5_draft_2.md` — what the v1.5 Draft 2 release contains.
3. `v1_5_draft_2_reading_guide.md` — this document.
4. `refs/duotronic_source_architecture_overview_v1_7.md` — architecture map.
5. `refs/duotronic_glossary_v1_0.md` — terminology authority.
6. `duotronic_canonical_implementation_target_v0_1.md` — canonical implementation target status (TBD).

## 2. Core normative documents

These three define the runtime trust and representational core.

1. `duotronic_polygon_family_calculus_v5_15.md` — DPFC: realized magnitudes, family numerals, conversion, bridge boundaries, export/import policy.
2. `duotronic_witness_contract_v10_16.md` — runtime trust: evidence, witnesses, canonicalization, lookup memory, recurrent state, replay, policy gates.
3. `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md` — distributed cluster layer on top of the above.

## 3. Owning documents by concern

| Concern | Owning document |
|---|---|
| Positive core, family-aware representation | `duotronic_polygon_family_calculus_v5_15.md` |
| Runtime trust, failure states, bypass, replay | `duotronic_witness_contract_v10_16.md` |
| Distributed cluster, federation, scheduling | `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md` |
| Bridge profile schema, preservation/loss | `refs/duotronic_representation_bridge_contract_v1_1.md` |
| Learned profile lifecycle | `refs/duotronic_auto_profile_learning_contract_v1_3.md` |
| Multi-model distributed witness emission | `refs/duotronic_distributed_model_node_protocol_v1_2.md` |
| Search and social source evidence | `refs/duotronic_search_social_evidence_ingestion_v1_3.md` |
| Profile staging and status ladder | `refs/duotronic_profile_synthesis_registry_v1_2.md` |
| Versioned IDs and compatibility | `refs/duotronic_schema_registry_v1_10.md` |
| Family declaration and promotion | `refs/duotronic_family_registry_v1_4.md` |
| Deterministic normal-form construction | `refs/duotronic_normalizer_profiles_v1_3.md` |
| Transport and source wrappers | `refs/duotronic_transport_profiles_v1_3.md` |
| Inter-node DBP full-duplex profile | `refs/duotronic_dbp_inter_node_full_duplex_profile_v1_0.md` |
| Node admission, heartbeat, revocation | `refs/duotronic_node_federation_protocol_v1_0.md` |
| Distributed task delegation and resource witnesses | `refs/duotronic_distributed_task_delegation_and_resource_witness_contract_v1_0.md` |
| Container/Docker node lifecycle | `refs/duotronic_container_deployment_and_node_lifecycle_reference_v1_0.md` |
| Cluster conformance fixtures | `refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md` |
| Witness-gated recurrent cell (WG-RNN) | `refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md` |
| Lookup memory and replay profile | `refs/duotronic_lookup_memory_and_replay_profile_v1_2.md` |
| Internal decision and planning | `refs/duotronic_internal_decision_and_planning_contract_v1_2.md` |
| Chronological self-evidence | `refs/duotronic_chronological_self_evidence_contract_v1_2.md` |
| Model diversity and adjudication | `refs/duotronic_model_diversity_and_adjudication_governance_v1_1.md` |
| Runtime modes, vetoes, bypass, rollback | `refs/duotronic_policy_shield_guide_v1_8.md` |
| Semantic changes and replay migration | `refs/duotronic_migration_guide_v1_3.md` |
| Measurement of preservation | `refs/duotronic_retention_diagnostics_v1_4.md` |
| Historical fixtures and lab lineage | `refs/duotronic_lab_evidence_registry_v1_7.md` |
| Evidence purge and privacy deletion | `refs/duotronic_evidence_purge_and_privacy_deletion_contract_v1_0.md` |
| Human review and escalation | `refs/duotronic_human_review_and_escalation_protocol_v1_0.md` |
| Meta-runtime contract | `refs/duotronic_meta_runtime_contract_v0_5.md` |
| Corpus index | `refs/duotronic_lab_integrated_source_corpus_index_v1_13.md` |

## 4. Reading order by role

### 4.1 Architecture review

1. `duotronic_program_charter_v1_0.md`
2. `README_v1_5_draft_2.md`
3. `refs/duotronic_source_architecture_overview_v1_7.md`
4. `duotronic_polygon_family_calculus_v5_15.md`
5. `duotronic_witness_contract_v10_16.md`
6. `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md`
7. `refs/duotronic_representation_bridge_contract_v1_1.md`
8. `refs/duotronic_auto_profile_learning_contract_v1_3.md`
9. `refs/duotronic_distributed_model_node_protocol_v1_2.md`
10. `refs/duotronic_search_social_evidence_ingestion_v1_3.md`
11. `refs/duotronic_profile_synthesis_registry_v1_2.md`
12. `refs/duotronic_policy_shield_guide_v1_8.md`
13. `refs/duotronic_migration_guide_v1_3.md`

### 4.2 Implementation

1. `duotronic_canonical_implementation_target_v0_1.md`
2. `refs/duotronic_schema_registry_v1_10.md`
3. `refs/duotronic_family_registry_v1_4.md`
4. `refs/duotronic_normalizer_profiles_v1_3.md`
5. `refs/duotronic_transport_profiles_v1_3.md`
6. `refs/duotronic_dbp_inter_node_full_duplex_profile_v1_0.md`
7. `duotronic_witness_contract_v10_16.md`
8. `refs/duotronic_distributed_task_delegation_and_resource_witness_contract_v1_0.md`
9. `refs/duotronic_node_federation_protocol_v1_0.md`
10. `refs/duotronic_container_deployment_and_node_lifecycle_reference_v1_0.md`
11. `refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md`
12. `refs/duotronic_lookup_memory_and_replay_profile_v1_2.md`
13. `refs/duotronic_retention_diagnostics_v1_4.md`
14. `refs/duotronic_policy_shield_guide_v1_8.md`
15. `refs/duotronic_migration_guide_v1_3.md`
16. `refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md`

### 4.3 Governance and review

1. `duotronic_program_charter_v1_0.md`
2. `refs/duotronic_policy_shield_guide_v1_8.md`
3. `refs/duotronic_evidence_purge_and_privacy_deletion_contract_v1_0.md`
4. `refs/duotronic_human_review_and_escalation_protocol_v1_0.md`
5. `refs/duotronic_model_diversity_and_adjudication_governance_v1_1.md`
6. `refs/duotronic_migration_guide_v1_3.md`
7. `refs/duotronic_meta_runtime_contract_v0_5.md`

### 4.4 Research-profile authoring

1. `refs/duotronic_auto_profile_learning_contract_v1_3.md`
2. `refs/duotronic_profile_synthesis_registry_v1_2.md`
3. `refs/duotronic_normalizer_profiles_v1_3.md`
4. `refs/duotronic_representation_bridge_contract_v1_1.md`
5. `refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md`
6. `refs/research_profiles/` (existing reference candidates)

## 5. Schemas, examples, fixtures

| Asset | Path |
|---|---|
| Starter object shapes | `refs/schemas/duotronic_v1_5_draft_2_starter_object_shapes.json` |
| Worked self-informing loop example | `refs/examples/duotronic_worked_self_informing_loop_youtube_music_v1_0.md` |
| WG-RNN PyTorch skeleton | `refs/examples/duotronic_wgrnn_pytorch_skeleton_v1_0.md` |
| Cluster conformance fixtures | `refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md` |
| Release manifest | `refs/release_manifest_v1_5_draft_2.json` |

## 6. Corpus review trail

The corpus review notes record what changed between drafts. Read them in order if you need to understand why a section exists.

1. `corpus_review_v1_3_draft_4_to_v1_4_draft.md`
2. `corpus_review_v1_4_draft_to_v1_4_draft_2.md`
3. `corpus_review_v1_4_draft_2_to_v1_4_draft_3.md`
4. `corpus_review_v1_4_draft_3_to_v1_4_draft_4.md`
5. `corpus_review_v1_4_draft_4_to_v1_4_draft_5.md`
6. `corpus_review_v1_4_draft_5_to_v1_5_draft.md`
7. `corpus_review_v1_5_draft_to_v1_5_draft_2.md`
8. `corpus_review_v1_5_draft_2_finalization.md`
9. `corpus_review_v1_5_draft_2_consistency_pass.md`

## 7. Authority

This guide does not redefine any document. If it disagrees with an owning document, the owning document controls. Update this guide whenever a new document is added to the v1.5 Draft 2 corpus or when an owning-document mapping in section 3 changes.
