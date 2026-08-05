# Release Notes — v1.6 Draft 5.3.9

Draft 5.3.9 is a standalone, permanently unfrozen corrective development corpus based on Draft 5.3.8. It does not embed earlier source-package ZIPs; predecessor hashes are recorded in a non-authoritative lineage file and all active changes are merged into this package.

This revision closes the reviewed Draft 5.3.8 production-shape defects:

- compiler and consumer agree that the generated binding is exactly one compiled module, and a producer-to-consumer regression enforces the contract;
- the inspector validates `/handoff`, rejects ambient `LEAN_PATH`, and initializes Lean with the sealed `/handoff/olean` search root;
- keep-ID mount ownership is checked against the trusted launcher identity and the handoff is host-sealed read-only before inspection;
- the Lake target, build Containerfile, runtime image, reproducible-build script, protocol, and documentation select `formal/draft5_3_6/lean`;
- compiler and inspector domains each have separately typed launcher/runtime evidence with argv, mounts, identity, controls, limits, and timing;
- every submitted source is compiled with the governed warning-as-error CLI option and warning diagnostics are rejected;
- one monotonic deadline covers both OCI domains, and active idempotency leases are renewed with owner fencing;
- production cache signing requires its own key, principal, authorization scope, rotation record, and governance-signed registry entry; key reuse is rejected;
- completion-time database growth, exact SQLite schema/integrity, full ancestry, descriptor-relative reopening, and canonical duplicate-free cached JSON are enforced;
- the runtime image explicitly pins Python and `cryptography`, verifies Lean tools and the inspector, and the validator runs each phase in a bounded process group with progress markers;
- the runtime README and active schemas, fixtures, OpenAPI, registry, tests, package metadata, and validator are current for 5.3.9.

No external gate is claimed complete. Strict Lean, strict TLC, governed-image execution, signed build attestations, reproducible inspector evidence, committed-source provenance, and governance authorization remain pending; all authority stays disabled.
