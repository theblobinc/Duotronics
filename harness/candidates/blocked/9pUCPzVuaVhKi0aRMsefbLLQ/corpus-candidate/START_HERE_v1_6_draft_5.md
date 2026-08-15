# Start Here - Duotronic v1.6 Draft 5

Status: active Draft 5 reading guide.  
Generated: 2026-05-09.

## Purpose

Start here for the NLA witness release. Draft 5 adds Natural Language
Autoencoder support as a fully specified witness layer for WG-RNN, while keeping
all implementation work out of this zip. A later standalone implementation file
can describe code changes against this contract.

## Fast path

1. `README_v1_6_draft_5.md` - package orientation.
2. `RELEASE_NOTES_v1_6_draft_5.md` - changes from Draft 4.1.
3. `duotronic_witness_contract_v1_6_draft_5.md` - consolidated active witness
   contract with L2n Natural-Language Activation Witness.
4. `duotronic_draft5_nla_complete_witness_integration_report.md` - summary of
   the complete NLA addition.
5. `runtime/nla_wgrnn_integration_profile_v1_0.md` - how NLA attaches to WG-RNN.
6. `runtime/nla_activation_capture_contract_v1_0.md` - activation capture rules.
7. `runtime/nla_verbalizer_reconstructor_runtime_contract_v1_0.md` - AV/AR
   runtime requirements.
8. `runtime/nla_fidelity_gate_contract_v1_0.md` - scoring and gating.
9. `runtime/nla_witness_lifecycle_contract_v1_0.md` - object lifecycle and
   promotion/quarantine rules.
10. `runtime/nla_audit_only_policy_profile_v1_0.md` - safety boundary.
11. `schemas/nla_activation_witness.schema.json` - canonical machine schema.
12. `validation/nla_wgrnn_acceptance_matrix_v1_0.md` - acceptance criteria.
13. `security/nla_interpretability_safety_profile_v1_0.md` - security/privacy.
14. `tests/nla_conformance_test_suite_v1_0.md` - conformance tests.
15. `refs/manifest/MANIFEST_v1_6_draft_5_complete.md` - package inventory.

## Non-goal for this package

This package intentionally does not include the code implementation plan. The
next standalone Markdown file should map these contracts to files, modules,
services, migrations, and tests in `srnn_server`.

## Core claim

Draft 5 makes NLA a first-class Duotronic witness modality. It does not make NLA
an autonomous memory writer, policy authority, or response generator.
