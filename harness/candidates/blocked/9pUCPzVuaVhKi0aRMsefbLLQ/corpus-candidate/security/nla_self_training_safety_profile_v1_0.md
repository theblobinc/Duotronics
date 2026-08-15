# NLA Self-Training Safety Profile v1.0

Status: active Draft 5.1 safety profile.

## Threat model

Self-training can amplify false explanations, privacy leaks, reward hacking,
model-specific artifacts, and authority confusion. Draft 5.1 treats NLA
self-training as a governed model-development pipeline.

## Primary risks and controls

| Risk | Control |
|---|---|
| self-trust loop | shadow/audit/release gates |
| training on private text | privacy class and retention review |
| hallucinated explanation amplification | failure memory and heldout replay |
| regression hidden by average metrics | failure-case eval and regression count |
| model mismatch | observer activation profile and sidecar digest |
| silent active replacement | promotion authority and operator approval |
| rollback failure | rollback ref required before promotion |
| policy escalation | may_change_policy_authority=false by schema |
| memory contamination | NLA training memory separate from user memory |

## Hard denials

1. Live online self-modification in active mode.
2. Self-trained model replacing active model without release gate.
3. Training on private/restricted examples without review.
4. Treating self-trained NLA output as privileged truth.
5. Allowing self-trained NLA to write memory or trigger mutation.
