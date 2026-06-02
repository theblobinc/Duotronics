# Source Observation - Anthropic NLA Paper

Status: Draft 5 source observation.  
Observed source: uploaded HTML copy of `Natural Language Autoencoders Produce
Unsupervised Explanations of LLM Activations`.  
Publication date shown in source: 2026-05-07.

## Relevant observed claims

1. Natural Language Autoencoders generate natural-language explanations of LLM
   activations.
2. The method uses two modules: an Activation Verbalizer that maps activations to
   text and an Activation Reconstructor that maps text back to activations.
3. AV and AR are jointly trained to reconstruct residual-stream activations.
4. The optimization target is reconstruction, not direct interpretability or
   faithfulness.
5. The resulting explanations can be useful in model auditing.
6. Case studies include unverbalized evaluation awareness, language switching,
   misreported tool calls, and reward reasoning.

## Draft 5 interpretation

Draft 5 adopts the AV/AR pair as a witness modality but does not treat AV output
as privileged truth. The AR reconstruction path and repeatability gates are used
as evidence controls.

## Contract effect

This source motivates:

1. `NaturalLanguageActivationWitness`.
2. L2n witness layer.
3. Fidelity gate.
4. Audit-only policy mode.
5. Human review triggers for hidden-intent and evaluation-awareness findings.
