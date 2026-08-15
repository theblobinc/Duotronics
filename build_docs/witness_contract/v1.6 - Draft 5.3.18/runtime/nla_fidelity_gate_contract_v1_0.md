# NLA Fidelity Gate Contract v1.0

Status: active Draft 5 contract.  
Applies to: acceptance, quarantine, and promotion of NLA witnesses.

## Purpose

The fidelity gate prevents natural-language explanations from being treated as
truth without reconstruction, stability, provenance, and policy checks.

## Gate stages

```text
capture_gate
  -> compatibility_gate
  -> sidecar_gate
  -> parser_gate
  -> reconstruction_gate
  -> repeat_stability_gate
  -> policy_gate
  -> lifecycle_decision
```

## Metrics

```yaml
NlaFidelityMetrics:
  mse: number | null
  cosine_similarity: number | null
  repeat_stability: number | null
  parser_valid: boolean
  sidecar_valid: boolean
  replay_valid: boolean
  confidence: number
```

## Default thresholds

The following thresholds are defaults for Draft 5 validation. Implementation may
make them configurable, but release reports must record the actual thresholds.

```yaml
thresholds:
  accepted_cosine_min: 0.80
  high_confidence_cosine_min: 0.90
  accepted_mse_max: 0.40
  high_confidence_mse_max: 0.20
  repeat_stability_min: 0.70
  promoted_repeat_stability_min: 0.85
  parser_valid_required: true
  sidecar_valid_required: true
```

## Lifecycle decision table

| Condition | Decision |
|---|---|
| capture invalid | failed |
| incompatible model/layer/d_model | failed |
| sidecar invalid | failed |
| parser invalid | diagnostic_only |
| AR unavailable | unscored_diagnostic |
| cosine below threshold | quarantined |
| repeat stability below threshold | accepted_single_use_only |
| all gates pass | accepted |
| all gates pass plus human/replay review | promotable |

## Confidence computation

Draft 5 defines confidence as a bounded aggregate:

```text
confidence = weighted_mean(
  reconstruction_score,
  repeat_stability,
  parser_validity,
  sidecar_validity,
  replay_validity,
  provenance_completeness
)
```

No confidence score may exceed the reconstruction score when AR scoring exists.

## Promotion constraints

An NLA witness may be promoted to Meta Object only if:

1. Lifecycle is accepted.
2. Repeat stability meets promoted threshold.
3. At least one corroborating witness exists or human review approves.
4. The promoted claim is phrased as an interpretability hypothesis.

An NLA witness may be promoted to Hyper Object only if the pattern recurs across
multiple loops, tasks, or model contexts.

## Quarantine handling

Quarantined witnesses remain useful for debugging. They may be inspected by
operators, but they must not appear in active memory summaries or policy fields.

## Release reporting

Every release report that mentions NLA must include counts for:

1. captured
2. verbalized
3. scored
4. accepted
5. quarantined
6. diagnostic-only
7. failed
8. promoted
9. human-reviewed
10. replay-verified
