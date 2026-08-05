# NLA Self-Training Governance State Machine v1.0

Status: active Draft 5.1 governance state machine.

```text
collect -> curate -> train_candidate -> evaluate -> shadow -> audit -> release_candidate -> approved_release
                   \-> rejected
shadow -> rejected
 audit -> rejected
 release_candidate -> rejected
```

## Promotion requirements

- `collect`: evidence capture only.
- `curate`: training data passes retention, redaction, and fidelity rules.
- `train_candidate`: offline or bounded training run only.
- `evaluate`: replay set and regression checks required.
- `shadow`: candidate may run but cannot influence production witnesses.
- `audit`: candidate may produce audit evidence with labels.
- `release_candidate`: requires model lineage, rollback ref, and operator review.
- `approved_release`: requires explicit approval artifact.

Self-training never equals self-trust. A trained adapter may not replace the
active NLA model without replay evidence and approval.
