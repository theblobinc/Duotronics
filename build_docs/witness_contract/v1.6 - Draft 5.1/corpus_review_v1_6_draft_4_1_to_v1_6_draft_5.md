# Corpus Review - v1.6 Draft 4.1 to v1.6 Draft 5

Status: transition review.  
Generated: 2026-05-09.

## Review question

Can the Duotronic witness corpus support Natural Language Autoencoders as a
first-class WG-RNN witness modality without collapsing explanations into
unverified truth claims?

## Answer

Yes. Draft 5 adds NLA as an audit-only L2n witness layer. It treats AV outputs
as evidence that must be scored by AR reconstruction, repeat stability, sidecar
integrity, parser validity, and replay provenance before promotion.

## New source assumptions

The NLA source material defines an Activation Verbalizer that maps vectors to
text and an Activation Reconstructor that maps text back to vectors. The public
repo treats reconstruction MSE/cosine as the fidelity signal for whether the
natural-language explanation preserved the activation direction. Draft 5 adopts
that shape but does not assume any released checkpoint is compatible with every
WG-RNN backend.

## Draft 4.1 rules retained

1. Runtime version aliases remain explicit.
2. Tool maturity remains separated into source-observed, test-backed,
   runtime-verified, and release-verified states.
3. WG-RNN chat context injection remains bounded by readiness, authority, policy
   mode, and no-unwitnessed-capability rules.
4. Browser/workbench invocation witnessing remains separate from Agent Lab.
5. Mutation safety config evidence remains required for mutation claims.
6. Runtime requested/applied/unsupported feature distinction remains mandatory.

## Draft 5 closure items

| Area | Draft 4.1 state | Draft 5 update |
|---|---|---|
| Activation interpretability | Not first-class | Adds L2n NLA witness layer |
| Vector capture | Not specified | Adds capture contract |
| AV/AR runtime | Not specified | Adds runtime contract |
| Fidelity | Not specified | Adds MSE/cosine/stability gate |
| Policy | Not specified | Adds audit-only policy profile |
| Schema | Not specified | Adds JSON/YAML schemas |
| Validation | Not specified | Adds acceptance matrix and conformance suite |
| Security | Not specified | Adds interpretability safety profile |

## Remaining implementation work

Implementation is intentionally out of scope for this zip. The next standalone
Markdown file should define modules, services, migrations, runtime flags, test
paths, and operator steps needed to implement Draft 5 in `srnn_server`.
