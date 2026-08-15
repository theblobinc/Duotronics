# Duotronic v1.6 Draft 5.1 Witness Corpus

Status: active Draft 5.1 complete witness package.  
Generated: 2026-05-09.  
Base package: uploaded Duotronic v1.6 Draft 4 corpus.  
Package root: `build_docs/witness_contract/v1.6 - Draft 5.1/`.

## Purpose

Draft 5.1 is the NLA authority and self-training witness release. It carries
forward the full Draft 4 corpus, reinstates the Draft 5 NLA witness layer, and
adds the new authority additions needed for a generic WG-RNN NLA system:

1. Generic truth-observer activation profiles.
2. NLA training memory cells inside the WG-RNN witness lattice.
3. Internal NLA curriculum and failure memory.
4. Self-training run witnesses.
5. Model-lineage and rollback authority.
6. Shadow, audit, and release promotion gates.
7. Safety rules that prevent young self-trained NLAs from writing memory,
   changing policy, or replacing active authority without evidence.

This is a witness-contract package, not a code implementation. The next separate
Markdown file should map these contracts to `srnn_server` implementation changes.

## Core change from Draft 5

Draft 5 made NLA an audit-only L2n Natural-Language Activation Witness. Draft
5.1 adds the authority framework around that layer:

```text
L2n   Natural-Language Activation Witness
L2nt  NLA Training Memory Cell
L2no  Generic Truth-Observer Activation Interface
L2nl  NLA Model Lineage and Promotion Authority
```

## Core rule

Self-training NLA memory is allowed. Automatic self-trust is not.

```text
WG-RNN may collect, score, curate, replay, and train NLA adapters from its own
witness stream. It may not let those adapters write memory, change authority,
replace models, or shape user-facing behavior until promotion gates pass and a
release witness approves the change.
```

## Primary Draft 5.1 entry points

```text
START_HERE.md
README.md
README_v1_6_draft_5_1.md
RELEASE_NOTES_v1_6_draft_5_1.md
CORPUS_INDEX_v1_6_draft_5_1.md
duotronic_witness_contract_v1_6_draft_5_1.md
duotronic_draft5_1_authority_self_training_complete_witness_report.md
authority/truth_observer_activation_authority_profile_v1_0.md
authority/nla_training_memory_cell_authority_contract_v1_0.md
authority/nla_self_training_authority_contract_v1_0.md
authority/nla_model_lineage_and_promotion_authority_contract_v1_0.md
authority/nla_shadow_audit_release_gate_contract_v1_0.md
runtime/truth_observer_activation_registry_contract_v1_0.md
runtime/nla_internal_training_memory_runtime_contract_v1_0.md
runtime/nla_curriculum_and_eval_runtime_contract_v1_0.md
schemas/nla_self_training_witness.schema.json
schemas/truth_observer_activation_profile.schema.yaml
validation/nla_self_training_authority_acceptance_matrix_v1_0.md
security/nla_self_training_safety_profile_v1_0.md
tests/nla_self_training_conformance_suite_v1_0.md
refs/manifest/MANIFEST_v1_6_draft_5_1_complete.md
```

## Authoritative reading rule

Draft 5.1 supersedes Draft 5 and Draft 4.x for active NLA authority and
self-training interpretation. Older files remain present for continuity unless a
Draft 5.1 active file supersedes them.
