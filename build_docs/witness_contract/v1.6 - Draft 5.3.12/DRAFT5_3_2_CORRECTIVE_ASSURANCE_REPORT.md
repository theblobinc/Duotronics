# Draft 5.3.2 Corrective Assurance Report

**Status:** implemented development corrections; not frozen.

## Closed reproduced defects

| Draft 5.3.1 defect | Draft 5.3.2 control | Executable regression |
| --- | --- | --- |
| Claimed theorem type differed from compiled declaration | Generated exact target checks `example : claimed := theorem` | `test_compiled_true_cannot_authorize_claimed_false` |
| `sorry` variants escaped source scan | Compiled `#print axioms` result rejects `sorryAx`; warnings fatal | `test_exact_sorry_is_rejected_from_compiled_axioms`, `test_have_sorry_is_rejected_from_compiled_axioms` |
| Comment-only theorem name passed regex | Generated imported target must elaborate the identifier | `test_comment_only_theorem_cannot_pass` |
| Artifact outside or unrelated to build | Artifact must be inside the source root and the generated exact target imports its module | external-artifact and exact-target tests |
| Spoofed `lake` on PATH | PATH lookup forbidden; absolute executable and SHA-256 pin required | PATH-spoof and wrong-digest tests |
| Descriptor phases not reconciled | Missing/failed/skipped/duplicate sets derived from descriptor and actual result IDs | three phase-reconciliation tests |
| Expired/revoked/superseded verifier remained active | Append-only key registrations/events and current-effective view | lifecycle SQL tests |
| SQL trusted decorative signatures | Canonical payload bindings call Ed25519 verification and compare every authority field | SQL cryptographic and tamper tests |
| Active proof-authority TLA model absent | V2 and V3 specs/configs are active strict-manifest entries | formal-manifest coverage phase |

## Remaining freeze blockers

- Strict Lean has not run because Lake is unavailable in the build environment.
- Strict TLC has not run because `tla2tools.jar` is unavailable.
- No external governance signature exists.
- Independent human review and release approval remain outstanding.

The required portable conformance phases may pass while these optional strict-release phases remain skipped. This means the development corpus is internally coherent; it does not authorize a frozen release.
