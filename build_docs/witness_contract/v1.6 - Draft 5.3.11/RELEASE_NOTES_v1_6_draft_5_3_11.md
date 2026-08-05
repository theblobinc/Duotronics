# Release Notes — v1.6 Draft 5.3.11

Draft 5.3.11 is a standalone, permanently unfrozen corrective development corpus based on Draft 5.3.10. It embeds no predecessor ZIPs; all active changes are merged, while predecessor hashes remain informational lineage only.

## Closed Draft 5.3.10 findings

- The non-root production loaders now accept a normal `/etc/witness-authority` shape: `/` and immutable system ancestors may be root-owned, all components reject symlinks and group/world writes, and the final private trust root remains service-owned. Root execution is rejected before configuration loading.
- Cache-signing chronology now rejects future `status_changed_at` values for active, retired, and revoked keys. Status changes must be inside the governed interval; retirement aligns with `valid_until`; revocation and successor/predecessor ordering are explicit.
- Cache-envelope v3 signs `status_changed_at`. Replay recomputes current chronology and compares the complete signing-time validity evidence.
- Service configuration, compiler registries, proof-policy registries, trusted-artifact registries, platform evidence, and cache-signing registries require duplicate-free canonical JSON before schema/signature checks. Authority schema documents reject duplicate keys.
- Stale cache rows caused by rotation or registry replacement are preserved and rejected with `cache_key_rotation_requires_new_idempotency_key`. No silent row deletion or re-execution occurs.
- Python evidence is generated per interpreter and merged deterministically. Validated and unavailable targets are disjoint, every target appears exactly once, and the combined matrix binds each evidence file by SHA-256.

## Measured portable results

- Python 3.12.13: 248/248 tests passed; development warnings-as-errors clean.
- Python 3.13.5: 248/248 tests passed; development warnings-as-errors clean.
- 108 schemas compile; 39 active schemas pass strict checks.
- 39 valid fixtures are accepted; 41 adversarial fixtures are rejected.

Final required-phase and package-closure totals are generated from the exact shipped bytes. These portable results do not satisfy any external activation gate.

## Authority status

Strict Lean, strict TLC, governed-image execution, signed OCI image build attestation, signed verifier executable attestation, reproducible inspector build attestation, clean committed-source provenance, and external governance authorization remain incomplete. Theorem, promotion, and release authority remain disabled.
