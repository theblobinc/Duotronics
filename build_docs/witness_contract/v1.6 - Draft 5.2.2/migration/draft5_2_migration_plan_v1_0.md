# Draft 5.2 Migration Plan v1.0

## Strategy

Draft 5.2 migrations are additive. Existing Draft 5.1 witnesses remain readable.

## New tables

- `srnn_composition_policies`
- `srnn_compound_claim_witnesses`
- `srnn_inference_witnesses`
- `srnn_temporal_scope_witnesses`
- `srnn_authority_delegation_chains`
- `srnn_replay_assumption_manifests`
- `srnn_verification_grammars`
- `srnn_replay_signs`
- `srnn_non_collapse_events`
- `srnn_claim_operator_edges`

## Existing table extensions

- truth observer registry gains pragmatic context fields.
- NLA release bundles gain replay assumption and verification grammar refs.
- NLA training witnesses gain non-collapse class and force indicators.
- replay packages gain replay assumption manifest ref and verification grammar ref.

## Compatibility

Null/default values preserve Draft 5.1 behavior until Draft 5.2 enforcement is enabled.
