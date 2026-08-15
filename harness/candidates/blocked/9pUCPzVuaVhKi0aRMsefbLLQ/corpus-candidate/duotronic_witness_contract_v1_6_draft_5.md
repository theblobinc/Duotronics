# Duotronic Witness Contract v1.6 Draft 5

Status: active consolidated witness contract.  
Generated: 2026-05-09.  
Supersedes: `duotronic_draft4_1_contract_closeout_report.md` for active witness
layer interpretation while retaining all Draft 4.1 closeout rules.

## 1. Scope

This contract defines the v1.6 Draft 5 witness surface for Duotronic WG-RNN and
SRNN runtime systems. It adds Natural Language Autoencoder support as a new
activation-language witness modality.

Draft 5 is contract-only. Code implementation, deployment, model training, and
runtime startup evidence are separate deliverables.

## 2. Witness layer stack

The active layer stack is:

```text
L0  Source Observation and External Evidence
L1  Runtime Observation and Direct Tool Evidence
L2  Recurrent Witness State
L2m Lookup Witness State
L2n Natural-Language Activation Witness State
L3  Meta-Recurrent Witness State
L4  Architectural Witness State
L5  Cosmological Witness State
```

L2n is not a policy authority. It is an evidence layer that translates captured
activation vectors into natural-language explanations and scores those
explanations against reconstruction and replay evidence.

## 3. Natural-Language Activation Witness

A Natural-Language Activation Witness is a record with the following minimum
semantics:

```yaml
NaturalLanguageActivationWitness:
  witness_id: stable identifier
  loop_id: WG-RNN loop identifier
  source_model: model, backend, layer, token, d_model
  activation: vector reference, digest, norm, capture timestamp
  verbalizer: AV model, sidecar, prompt integrity, explanation text
  reconstructor: AR model, reconstruction reference, MSE, cosine
  fidelity: parser status, reconstruction status, repeat stability, confidence
  lifecycle: captured, verbalized, scored, accepted, quarantined, promoted
  policy: may_influence_response, may_write_memory, may_promote_witness
```

The canonical machine form is `schemas/nla_activation_witness.schema.json`.

## 4. Truth boundary

NLA explanations are evidence. They are not privileged access to model intent,
not a proof of hidden cognition, and not a substitute for replay, direct logs,
state snapshots, or human review.

The following claims are forbidden unless explicitly supported by later release
witnesses:

1. The model definitely intended X because the NLA said X.
2. The model remembered X because the NLA explanation contained X.
3. The model may write memory because the NLA explanation was high-confidence.
4. The policy gate may be bypassed because the NLA explanation appeared safe.
5. NLA explanations are causal proof without intervention evidence.

## 5. Fidelity gate

An NLA witness may be accepted only if all required gates pass:

1. Activation capture provenance gate.
2. Model-layer compatibility gate.
3. Sidecar integrity gate.
4. Injection-template integrity gate.
5. Explanation parser gate.
6. AR reconstruction gate or explicit unscored diagnostic classification.
7. Repeat stability gate for promoted evidence.
8. Policy gate.
9. Replay reproducibility gate for release claims.

The full gate is specified in `runtime/nla_fidelity_gate_contract_v1_0.md`.

## 6. WG-RNN integration

WG-RNN may consume NLA evidence as derived diagnostic inputs:

```json
{
  "l2n_nla_present": true,
  "nla_fidelity_score": 0.0,
  "nla_cosine_similarity": 0.0,
  "nla_explanation_stability": 0.0,
  "nla_eval_awareness_signal": 0.0,
  "nla_reward_model_signal": 0.0,
  "nla_hidden_intent_signal": 0.0,
  "nla_human_review_required": true
}
```

These inputs may influence diagnostics and review routing in Draft 5. They may
not directly influence user-facing answers or memory writes.

## 7. Object mapping

An accepted NLA witness maps to object layers as follows:

| Layer | Mapping |
|---|---|
| Base Object | One activation-language explanation plus fidelity/provenance |
| Meta Object | Stable theme across multiple NLA witnesses in one loop/session |
| Hyper Object | Recurring high-level pattern across loops, models, or tasks |

Promotion from Base to Meta or Hyper requires repeatability, source diversity,
and human-review policy gates.

## 8. Audit-only policy

Draft 5 sets NLA mode to audit-only by default:

```yaml
nla_policy_mode: audit_only
may_store_witness: true
may_display_to_operator: true
may_route_human_review: true
may_write_user_memory: false
may_change_policy_authority: false
may_shape_assistant_response: false
may_trigger_automated_mutation: false
```

## 9. Compatibility

A released AV/AR pair is compatible only with the model family, layer, d_model,
tokenizer, prompt template, injection metadata, scale factors, and sidecar fields
for which it was trained. Compatibility may not be inferred from model name
alone.

## 10. Release evidence

A later implementation release must provide:

1. Captured activation fixture.
2. AV explanation fixture.
3. AR reconstruction fixture.
4. Fidelity metrics.
5. Repeat decode metrics.
6. Failure/quarantine cases.
7. Human-review sample.
8. Storage/replay proof.
9. Policy non-escalation proof.
10. Security/privacy review.
