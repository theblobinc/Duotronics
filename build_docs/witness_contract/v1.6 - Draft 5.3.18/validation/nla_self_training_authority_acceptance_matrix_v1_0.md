# NLA Self-Training Authority Acceptance Matrix v1.0

Status: active Draft 5.1 validation matrix.

## Acceptance levels

| Level | Name | Meaning |
|---|---|---|
| A0 | Contract present | Draft 5.1 docs and schemas exist |
| A1 | Registry capable | Truth observers can register capabilities |
| A2 | Memory capable | Training examples persist with privacy/retention |
| A3 | Training capable | Candidate adapters can train offline |
| A4 | Shadow capable | Candidate runs without affecting outputs |
| A5 | Audit capable | Candidate emits audit-only witnesses |
| A6 | Release capable | Candidate can be promoted with approval and rollback |

This zip reaches A0. Implementation must prove A1-A6.

## Required validation cases

| Case | Requirement | Pass condition |
|---|---|---|
| observer_registry | register observer profile | profile validates and stores |
| unsupported_backend | no hidden states | residual NLA fails closed |
| memory_cell_separation | NLA training memory is not user memory | no user-memory writes |
| curriculum_gate | raw example cannot train | rejected until curated |
| heldout_protection | heldout not used in training | manifest validation passes |
| self_training_schema | training witness validates | JSON schema passes |
| shadow_gate | candidate cannot affect outputs | output diff is zero by authority |
| audit_gate | candidate emits audit-only evidence | no memory/policy mutation |
| release_gate | promotion requires approval | no active model without approval |
| rollback | rollback ref works | previous model ref recoverable |

## Release claim rule

A system may not claim self-trained NLA authority unless A1 through A6 pass and a
release bundle references all evidence.
