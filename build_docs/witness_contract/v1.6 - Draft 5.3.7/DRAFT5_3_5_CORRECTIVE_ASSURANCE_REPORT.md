# Draft 5.3.5 Corrective Assurance Report

This revision implements the Draft 5.3.4 independent remediation checklist as
an executable cross-layer correction. The contract, runtime, policy resolver,
sandbox adapter, trusted wrappers, schemas, fixtures, OpenAPI, WSGI adapter,
SQLite migration, Lean target, TLA model, validators, manifests, and active boot
pointers use the same 5.3.5 authority identities.

Portable tests exercise explicit OCI domain dispatch; one-to-one sandbox
control mapping; measured runtime identity and non-root rejection; policy
status, scope, time, signature, and relabel resistance; FD-relative snapshot
bounds; streaming output quotas and descendant termination; synchronous API
idempotency; complete schema classification; SQL policy binding; and recursive
package closure.

Portable evidence does not establish that a governed image, Lean toolchain,
TLC toolchain, security profile, or external key actually ran in a production
deployment. Those gates remain separate and incomplete. Source provenance is
also deliberately marked `unpublished_workspace` because no clean committed
source state is available in this workspace. Theorem, promotion, and release
authority therefore remain disabled.
