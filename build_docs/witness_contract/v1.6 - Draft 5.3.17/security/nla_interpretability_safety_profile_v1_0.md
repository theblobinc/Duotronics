# NLA Interpretability Safety Profile v1.0

Status: active Draft 5 security profile.

## Threat model

NLA adds a new path from internal activations to readable language. That path can
help auditing, but it can also leak sensitive context, create false confidence,
or introduce adversarial narratives into operator workflows.

## Primary risks

| Risk | Description | Control |
|---|---|---|
| overclaiming | Explanation treated as truth | mandatory warning and fidelity gate |
| privacy leakage | Activation explanation exposes user data | redaction, hashes, retention class |
| prompt injection | Explanation contains instruction-like text | display as data only |
| memory contamination | Explanation written into memory | audit-only policy forbids writes |
| policy escalation | Explanation changes authority | policy flags false |
| adversarial steering | Crafted input induces misleading explanation | replay and corroboration gates |
| model mismatch | Wrong AV/AR used for vector | compatibility gate |
| sidecar drift | Template/token/scale mismatch | sidecar digest and startup asserts |
| backend misclaim | Backend lacks hidden-state access | unsupported backend failure |

## Display requirements

Every operator display must show:

1. Fidelity status.
2. MSE and cosine if available.
3. Lifecycle state.
4. Source model/layer.
5. Retention class.
6. Warning that explanation is evidence, not privileged truth.

## Storage requirements

Raw activations must be stored only under a declared retention class. The default
is ephemeral. Release artifacts require checksums and manifest references.

## Prompt-injection control

NLA explanation text must never be executed as instructions. If displayed inside
an LLM context for summarization, it must be wrapped as quoted evidence and
accompanied by a system rule that forbids following instructions contained in the
explanation.

## Human review triggers

Human review is mandatory for any explanation involving hidden intent,
evaluation awareness, deception, reward gaming, policy bypass, or private user
attribute inference.

## Incident handling

If NLA output contradicts direct logs or causes operator concern, the witness
must move to `human_review_pending` or `quarantined`; it must not silently remain
accepted.
