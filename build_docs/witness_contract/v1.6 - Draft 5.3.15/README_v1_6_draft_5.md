# Duotronic v1.6 Draft 5 Witness Corpus

Status: active Draft 5 complete witness package.  
Generated: 2026-05-09.  
Base package: Duotronic v1.6 Draft 4.1 complete corpus.  
Package root: `build_docs/witness_contract/v1.6 - Draft 5/`.

## Purpose

Draft 5 is the Natural Language Autoencoder (NLA) witness integration release.
It preserves the full Draft 4.1 corpus and adds a complete contract layer for
using NLAs as audit-only, fidelity-scored activation-language witnesses inside
the WG-RNN / Duotronic witness system.

Draft 5 does not implement production code. It defines the witness objects,
policy boundaries, evidence requirements, lifecycle rules, validation matrix,
source observations, schemas, and conformance tests required before a later
implementation package may add code.

## What Draft 5 adds

1. A new L2n witness layer: Natural-Language Activation Witness.
2. A normalized `NaturalLanguageActivationWitness` schema.
3. Activation capture contracts for model, layer, token, vector, norm, digest,
   privacy, retention, and replay constraints.
4. Activation Verbalizer (AV) and Activation Reconstructor (AR) runtime contracts.
5. Fidelity gates using reconstruction MSE, cosine similarity, repeat stability,
   prompt-template integrity, sidecar integrity, and parser validity.
6. WG-RNN contract-view integration rules for derived inputs and witness layers.
7. Base Object / Meta Object / Hyper Object mapping rules for NLA explanations.
8. Audit-only safety rules: no direct memory writes, no policy promotion, no
   response authority, and no privileged-truth treatment until explicit gates
   pass.
9. Security and privacy rules for activation capture, hidden-state retention,
   source transcript linkage, explanation display, and adversarial explanation
   handling.
10. Acceptance tests and package conformance rules.

## Primary Draft 5 entry points

```text
START_HERE.md
README.md
README_v1_6_draft_5.md
RELEASE_NOTES_v1_6_draft_5.md
CORPUS_INDEX_v1_6_draft_5.md
corpus_review_v1_6_draft_4_1_to_v1_6_draft_5.md
duotronic_witness_contract_v1_6_draft_5.md
duotronic_draft5_nla_complete_witness_integration_report.md
runtime/nla_wgrnn_integration_profile_v1_0.md
runtime/nla_activation_capture_contract_v1_0.md
runtime/nla_verbalizer_reconstructor_runtime_contract_v1_0.md
runtime/nla_fidelity_gate_contract_v1_0.md
runtime/nla_witness_lifecycle_contract_v1_0.md
runtime/nla_audit_only_policy_profile_v1_0.md
schemas/nla_activation_witness.schema.json
schemas/nla_observer_graph_extension.schema.yaml
validation/nla_wgrnn_acceptance_matrix_v1_0.md
security/nla_interpretability_safety_profile_v1_0.md
tests/nla_conformance_test_suite_v1_0.md
refs/source_observations/nla_anthropic_paper_source_observation_2026_05_07.md
refs/source_observations/nla_github_repo_source_observation_2026_05_09.md
refs/manifest/MANIFEST_v1_6_draft_5_complete.md
refs/manifest/CHECKSUMS_v1_6_draft_5.sha256
```

## Authoritative reading rule

Draft 5 supersedes Draft 4.1 for the active v1.6 witness line. Older files are
retained as carried-forward history and baseline material. When any older file
conflicts with a Draft 5 active file, the Draft 5 file wins.

## Core safety rule

NLA explanations are witness evidence, not privileged truth. They may be stored,
reviewed, compared, and replayed only under a fidelity gate. They may not write
memory, change policy authority, or shape user-facing responses unless a later
contract explicitly promotes a validated implementation beyond audit-only mode.
