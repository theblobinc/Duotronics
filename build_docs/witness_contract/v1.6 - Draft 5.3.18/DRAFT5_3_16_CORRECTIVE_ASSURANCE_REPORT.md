# Draft 5.3.16 Corrective Assurance Report

## Verdict

Draft 5.3.16 closes the Draft 5.3.15 portable findings concerning peer authentication, per-artifact audit-key lifecycle, strict anchor transitions, terminal-tail verification, cross-segment idempotency, recovery authorization lifecycle, and production audit-service integration. No portable result enables authority.

## Trust-boundary changes

Publisher and anchor servers authenticate both kernel-reported peer credentials and signed requests bound to operation, request ID, principal, payload digest, deadline, nonce, target service, and socket identity. Receipt, record, checkpoint, recovery, and anchor scopes are distinct and evaluated from governed registries at the signed artifact timestamp.

Anchor states permit only exact no-op or sequence-plus-one updates inside a segment, preserve immutable governance bindings, and include predecessor-state hashes. The local file-backed store is non-authoritative because filesystem rollback by its protection-domain owner is not independently impossible. Activation requires TPM/HSM monotonic state, WORM/object-lock storage, a transparency service, or equivalent external trust.

Successor creation verifies the canonical terminal-record digest against both checkpoint and anchor tails, as well as outer and embedded predecessor segment identities. Global event-ID storage prevents duplicate commitment across rotation and restart. Recovery authorizations expire, have a short maximum lifetime, bind exact before-state and file identities, and are durably consumed once.

## Production execution

The integration runs three identities: proof service UID/GID 65534, publisher UID/GID 65533, and anchor UID/GID 65532. It invokes both real proof loaders, publishes through the real publisher and anchor servers, verifies the durability receipt, checks record/checkpoint/anchor persistence, restarts the publisher, reconciles the duplicate as already committed, and denies an unrelated UID despite socket-group access and copied request material.

## Authority boundary

The eight external gates remain incomplete. The corpus is permanently not frozen and non-authoritative; theorem, promotion, and release authority remain disabled.
