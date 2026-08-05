# Source Observation - NLA Authority Additions

Status: Draft 5.1 source observation.  
Generated: 2026-05-09.

## Observed basis

The NLA paper describes Natural Language Autoencoders as an unsupervised method
that uses an Activation Verbalizer to map activations to text and an Activation
Reconstructor to map text back to activations. It optimizes reconstruction rather
than directly optimizing faithfulness or interpretability.

The Draft 5.1 authority additions follow from this: if WG-RNN trains internal
AV/AR adapters, it must preserve reconstruction, replay, heldout, failure, and
promotion evidence before trusting those adapters.

## Contract effect

This observation motivates:

1. NLA training memory cells.
2. Self-training witness objects.
3. Truth-observer activation profiles.
4. Shadow/audit/release gates.
5. Model lineage and rollback.
6. Safety rule: self-training does not equal self-trust.
