# NLA WG-RNN Integration Profile v1.0

Status: active Draft 5 runtime integration profile.  
Applies to: WG-RNN, SRNN cognition loops, Duotronic witness lattice.

## Purpose

This profile defines how Natural Language Autoencoder evidence attaches to the
WG-RNN witness system. It is an integration contract, not a code implementation
plan.

## Layer assignment

NLA evidence is assigned to L2n:

```text
L2n Natural-Language Activation Witness State
```

L2n is lower than L3 Meta-Recurrent Witness and cannot independently change
meta-policy, architecture state, cosmological constraints, mutation authority,
or user memory.

## Data flow

```text
WG-RNN or model execution event
  -> activation capture request
  -> activation vector digest and bounded storage reference
  -> AV explanation
  -> AR reconstruction and fidelity score
  -> NaturalLanguageActivationWitness
  -> Base Object
  -> optional Meta Object after repeatability and review gates
  -> optional Hyper Object after cross-loop recurrence gates
```

## Contract-view fields

WG-RNN contract views may expose the following optional NLA fields:

```json
{
  "witness_layers": {
    "l2n_nla": true
  },
  "nla": {
    "present": true,
    "policy_mode": "audit_only",
    "latest_witness_id": "nla_...",
    "latest_lifecycle_state": "accepted",
    "latest_fidelity_status": "high",
    "latest_cosine_similarity": 0.91,
    "latest_mse": 0.18,
    "latest_repeat_stability": 0.84,
    "human_review_required": false,
    "may_influence_response": false,
    "may_write_memory": false,
    "may_promote_witness": false
  }
}
```

## Derived inputs

NLA may contribute diagnostic-only derived inputs:

```json
{
  "nla_fidelity_score": 0.91,
  "nla_explanation_stability": 0.84,
  "nla_contradiction_delta": 0.12,
  "nla_eval_awareness_signal": 0.0,
  "nla_reward_model_signal": 0.0,
  "nla_hidden_intent_signal": 0.0
}
```

These fields must be ignored by any memory writer, mutation tool, or policy
authority path in Draft 5.

## Observer graph placement

NLA is an observer node that consumes captured activation vectors and emits Base
Objects. It must not directly consume private chain-of-thought text unless that
text is already part of an approved internal audit dataset.

```yaml
node_type: activation_interpretability_observer
input_contracts:
  - activation_vector_ref
  - source_model_ref
  - token_position_ref
  - nla_model_sidecar_ref
output_contracts:
  - NaturalLanguageActivationWitness
  - BaseObject
mode: audit_only
```

## Base Object mapping

A Base Object derived from NLA must include:

1. Explanation text.
2. Activation provenance.
3. Fidelity metrics.
4. Capture timestamp.
5. Sidecar digest.
6. Policy flags.
7. Human-review routing status.

## Meta Object promotion

A Meta Object may be created from NLA only when:

1. At least two accepted NLA witnesses support the same theme.
2. At least one non-NLA evidence path agrees or human review approves.
3. The theme is represented as a hypothesis, not a fact.
4. The promotion event records reviewer or automated validation evidence.

## Hyper Object promotion

A Hyper Object may be created only when the pattern recurs across loops,
sessions, tasks, or model families and passes cross-source replay checks.

## Failure handling

If AV output is unparsable, AR is unavailable, sidecar checks fail, or fidelity
falls below threshold, WG-RNN must record the attempt as failed or quarantined
and must not expose it as accepted witness evidence.
