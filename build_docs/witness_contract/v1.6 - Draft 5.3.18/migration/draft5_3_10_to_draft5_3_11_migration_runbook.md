# Draft 5.3.10 → Draft 5.3.11 Service Migration Runbook

Draft 5.3.11 changes production trust-root ownership, authority-bearing JSON canonicality, cache-key status chronology, stale-row behavior, cache-envelope evidence, and Python validation assembly. It does not reinterpret existing authority SQL records; `migration/draft5_3_6_to_draft5_3_7.sql` remains the latest authority-database migration.

## Deployment sequence

1. Run the authority under a dedicated non-root UID/GID. UID or GID zero is forbidden.
2. Use an absolute trust root such as `/etc/witness-authority`. `/` and immutable system ancestors may remain root-owned `0755`; none may be group/world writable or symlinked. Set the final trust root and sensitive subdirectories to the service UID with private modes.
3. Store sensitive files as service-owned, regular, single-link `0600` files. Do not place the trust root below a writable ancestor.
4. Canonically encode `service-config.json`, compiler registry, proof-policy registry, trusted-artifact registry, platform-capability evidence, and cache-signing registry: UTF-8, duplicate-free, sorted keys, compact separators, and no alternate numeric representation or trailing newline.
5. Governance-sign registries only after canonical encoding. The loader parses canonical bytes before schema and signature verification.
6. Upgrade cache writes to `idempotency_cache_envelope/v3`. Include `status_changed_at` in the signed validity evidence.
7. Validate every cache record at the governed current time. Active status changes must be non-future and inside the interval. Retirement occurs exactly at `valid_until`; revocation occurs at its recorded status change. Rotation predecessors must be complete, older, same-principal, same-scope, non-active, and acyclic.
8. Preserve completed rows signed under a superseded registry. Return `409 cache_key_rotation_requires_new_idempotency_key`; clients must submit a fresh idempotency key. Do not silently delete or re-execute stale rows.
9. Generate a per-interpreter evidence record with `generate_draft5_3_11_python_evidence.py` under each claimed Python target, then merge. Require the validated and unavailable sets to be disjoint and each target to appear exactly once.
10. Rebuild the schema registry and package manifests, then run the monolithic validator independently under Python 3.12 and Python 3.13.

The Draft 5.3.10 SQLite v2 schema, connection failure cleanup, deadline-through-publication, lease renewal/loss fencing, and trusted Lean command reconstruction remain unchanged and required.

## Activation state

This migration creates no release-activation evidence. Theorem, promotion, and release authority remain disabled until all eight external activation gates are independently verified and externally authorized.
