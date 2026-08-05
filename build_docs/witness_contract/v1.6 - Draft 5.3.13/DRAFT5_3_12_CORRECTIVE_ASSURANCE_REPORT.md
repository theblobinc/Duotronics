# Draft 5.3.12 Corrective Assurance Report

Draft 5.3.12 closes the portable Draft 5.3.11 validator-stall and stale-cache-authentication findings in source and regression evidence.

- Validator subprocesses use RLIMIT-bounded temporary capture files, bounded process-group and descendant termination, bounded reaping, closed parent descriptors, and nested substage markers.
- Descendants are identified by PID plus Linux process start-time ticks, preventing signals from being redirected after PID reuse. Ten complete 85-phase runs passed per interpreter.
- Concurrent repetition stress removed the old 50 ms lease-heartbeat floor; renewal remains proportional for short leases, while final publication is still owner-fenced. The regression now observes an actual expiry extension with event-synchronized authority and replay threads instead of relying on scheduler-sensitive sleeps.
- Historical cache replay is authenticated against a governance-signed registry lineage before any rotation-specific classification or evidence emission.
- Unknown, forged, altered, and revoked historical rows remain integrity failures; only an authenticated governed predecessor produces v2 stale-row evidence followed by the stable `409` policy.
- The production-loader integration harness uses a real `/etc/witness-authority` chroot shape and actual non-root identity transition. Its execution is explicitly unavailable in this one-ID user namespace, so no passing integration claim is made.
- The existing tiered root ownership, duplicate-rejecting trusted JSON, cache-key chronology, Python evidence merge, and stable stale-row policy remain enforced.

Portable conformance is non-authoritative. All eight external activation gates remain incomplete; theorem, promotion, and release authority remain disabled; lifecycle remains permanently not frozen.
