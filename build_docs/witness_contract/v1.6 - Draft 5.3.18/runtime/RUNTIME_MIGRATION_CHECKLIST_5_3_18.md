# Runtime Migration Checklist — 5.3.18

## Required protocol work

- [ ] Add `authority_namespace`, `authority_profile`, `evidence_environment`, `production_eligible`, suite ID, and trust-registry snapshot ID to every authority-bearing database row and API object.
- [ ] Reject any edge, aggregate, signature, or activation whose authority domain differs from its endpoints or challenge.
- [ ] Make sandbox and production trust roots, keys, policies, databases, logs, and activation namespaces disjoint.
- [ ] Prohibit sandbox-to-production promotion; production always performs a new challenge and new external measurements.
- [ ] Persist exact original probe measurements immutably.
- [ ] Persist fresh revalidation as a new linked object; never overwrite the original measurement.
- [ ] Implement the three stability classes and per-probe stable projections.
- [ ] Treat undeclared output variance as failure and declared volatile telemetry as non-authoritative.
- [ ] Implement typed evidence edges and the 5.3.18 relation registry.
- [ ] Require twelve distinct, registered gate IDs in one authority domain before aggregate activation.
- [ ] Add freshness, revocation, chronology, policy, and registry-snapshot checks.
- [ ] Add Merkle segment/checkpoint support for eligible high-volume edges.
- [ ] Keep individual ML-DSA-87 signatures for governance and activation boundaries.
- [ ] Cache provider/public-key state only by suite plus registry snapshot; invalidate on trust changes.
- [ ] Parallelize independent canonicalization, digest, signature, graph, and inclusion-proof verification.
- [ ] Expose the activation state vector as display-only metadata.

## Storage and API

- [ ] Tables: authority domains, probe challenges, original measurements, revalidations, attestations, evidence edges, gate results, checkpoints, aggregates, activations, revocations.
- [ ] Unique constraints bind object IDs to authority namespace and registry snapshot.
- [ ] Append-only chronology for measurements, edges, aggregates, and activation events.
- [ ] API returns original and revalidation measurements separately.
- [ ] API never reports sandbox activation as production eligibility.
- [ ] Audit export includes graph root, checkpoint proofs, suite, policy, registry snapshot, and domain.

## Harness and release gates

- [ ] Run schema and negative fixtures in the rootless guest Compose stack.
- [ ] Run Lean and TLC authority-domain/non-promotion models.
- [ ] Run all twelve externally attested gates and verify a sandbox activation.
- [ ] Confirm production flags remain false after full sandbox activation.
- [ ] Benchmark 1, 12, 100, and 1,000 evidence objects at 1, 2, 4, and 6 workers.
- [ ] Record median and tail latency for canonicalization, identifiers, Merkle construction/proofs, ML-DSA sign, and ML-DSA verify.
- [ ] Establish budgets from measured guest results; do not invent targets.
- [ ] Run mutation tests: changed domain, registry, edge endpoint, stable projection, gate ID, and checkpoint proof.
- [ ] Generate the complete manifest and validate inherited baseline retention.
- [ ] Publish only through an explicitly authorized lifecycle action.
- [ ] Connect or activate production only through a separately authorized production action.
