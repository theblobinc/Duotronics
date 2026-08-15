# Draft 5.3.3 Corrective Assurance Report

## Review findings addressed

| Draft 5.3.2 finding | Draft 5.3.3 correction |
| --- | --- |
| Executable pin could self-authorize | Requests select only a profile in a governance-signed registry. |
| Compiler digest named Lake | Lake and actual Lean have independent fields; legacy compiler digest equals Lean. |
| Prebuilt `.olean` source/binary gap | Prebuilt and native artifacts are rejected; a new immutable snapshot is built from source. |
| Host environment and network inherited | Canonical sandbox has a minimal environment, no network, read-only mounts, dropped capabilities, and resource limits. |
| TOCTOU and random target | Before/after/copy hashes must agree; generated path and witness ID are deterministic. |
| Mocked tests did not run Lean | Mocked tests are labelled non-authoritative; a separate protected-image integration runner exercises real Lean cases. |
| Human-readable axiom parsing | Only canonical structured verifier JSON is authoritative. |
| Unsigned lifecycle/supersession | Governance authorization, key events, and supersessions are signed and SQL-verified. |
| Wall-clock historical replay | Signed authority snapshots and explicit as-of views are canonical for history. |
| Caller-provided authority time | Request API and service do not accept authority timestamps. |

## Assurance boundary

The portable tests validate host orchestration and rejection logic with simulated
structured results. They cannot attest to a production image or external trust
root. The corpus therefore records strict Lean, strict TLC, real hermetic Lean
integration, and external governance signature as separate authority-activation
evidence. Their absence never becomes a pass.

## Lifecycle decision

Per the author’s direction, the Witness Contract is a living contract and is
permanently not frozen. External evidence may activate specific authority
functions in a deployment, but cannot convert this evolving specification into
a frozen artifact.
