# Draft 5 to Draft 5.1 Reconciliation Audit

Status: corrected complete-corpus audit.  
Generated: 2026-05-09.

## Purpose

This audit exists because Draft 5.1 must be a successor to Draft 5, not a rebuild
from Draft 4 and not a partial authority addendum. The corrected package keeps all
Draft 5 files and adds Draft 5.1 authority/self-training files.

## Reconciliation result

```yaml
base_package: v1.6 Draft 5
successor_package: v1.6 Draft 5.1
strategy: full carry-forward plus authority overlay
draft5_files_carried_forward: true
draft5_nla_contracts_carried_forward_as_full_bodies: true
draft4_1_bridge_layer_carried_forward: true
draft5_1_authority_layer_added: true
standalone_complete_corpus_rule_added: true
```

## Important preservation rule

Draft 5 versioned files such as `duotronic_witness_contract_v1_6_draft_5.md`,
`runtime/nla_wgrnn_integration_profile_v1_0.md`, and
`schemas/nla_activation_witness.schema.json` are preserved from Draft 5. Draft
5.1 adds new versioned files rather than replacing those full bodies with short
summaries.
