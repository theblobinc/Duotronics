# Release Notes - Duotronic v1.6 Draft 5

Status: release notes.  
Generated: 2026-05-09.  
Supersedes: Draft 4.1 for active witness interpretation.

## Summary

Draft 5 adds complete Natural Language Autoencoder witness support to the
Duotronic v1.6 corpus. The release is contract-complete, not code-complete.
It defines what an NLA witness is, where it attaches to WG-RNN, how it is scored,
what policy boundaries apply, and how later implementation work must validate it.

## Major additions

### L2n Natural-Language Activation Witness

Draft 5 introduces L2n as a peer/sub-layer of recurrent witness evidence. L2n
stores natural-language explanations of captured activation vectors, paired with
reconstruction evidence and fidelity scores.

### NaturalLanguageActivationWitness schema

A new JSON schema defines source model identity, layer/token coordinates,
activation references, AV/AR model metadata, sidecar integrity, explanation text,
reconstruction metrics, policy flags, provenance, and lifecycle status.

### Activation capture contract

Draft 5 defines how activation vectors may be captured, hashed, retained,
redacted, replayed, linked to transcripts, and prevented from becoming hidden
unbounded memory.

### AV/AR runtime contract

Draft 5 defines the runtime obligations of the Activation Verbalizer and
Activation Reconstructor, including sidecar loading, prompt-template integrity,
injection metadata, output parsing, scoring, runtime health, and unsupported
backend handling.

### Fidelity gate

Draft 5 prevents unscored or low-fidelity explanations from acting as truth. A
witness can progress only if reconstruction, stability, parser, sidecar, replay,
and provenance gates pass.

### Audit-only safety boundary

NLA evidence may be displayed, stored, searched, compared, and replayed. It may
not directly write user memory, promote policy authority, or shape model output
until a later release explicitly changes the policy.

## Relationship to Draft 4.1

Draft 4.1 closed gaps around version aliasing, MCP recurrence tool maturity,
WG-RNN chat injection, browser/workbench invocation witnessing, mutation safety,
runtime feature applicability, and readiness persistence. Draft 5 keeps those
rules and adds NLA as a new witness modality.

## Release non-claims

Draft 5 does not claim that NLA models are deployed, that activations are being
captured in production, that SGLang or Transformers services are running, or that
native AV/AR models have been trained for every WG-RNN runtime model. It defines
the evidence required before those claims may be made.
