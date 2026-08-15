# Draft 5.3.15 → Draft 5.3.16 migration runbook

Draft 5.3.16 changes the audit service protocol and is not an in-place authority activation.

1. Keep theorem, promotion, and release authority disabled.
2. Provision distinct proof-service, publisher, and anchor identities.
3. Replace world-accessible or unauthenticated sockets with mode-0660 governed endpoints.
4. Provision proof→publisher and publisher→anchor request-signing keypairs separately from record, receipt, and anchor keys.
5. Load governance-signed record, receipt, and anchor lifecycle registries; reject cycles, expiry, revocation, or scope mismatch.
6. Start the anchor service, then publisher, then proof service. Verify `SO_PEERCRED` and signed-request denial tests.
7. Rebuild the global publisher event-ID index from governed historical segments before accepting writes.
8. Reissue recovery authorizations under v2 with short expiry, exact file identities, and one-time consumption.
9. Treat the bundled file-backed anchor as development-only. An activation candidate must connect an independently monotonic backend.
10. Run the full Draft 5.3.16 validator and real cross-UID integration before deployment.
