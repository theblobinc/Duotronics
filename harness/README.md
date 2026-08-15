# Duotronic Witness Contract external-activation lab

This directory is the MCP-operated development, qualification, and rollout suite for current and historical Witness Contract revisions. It keeps mutable development workspaces on the server, runs external activation probes that cannot execute in chat, preserves measurements for independent attestation, publishes complete standalone corpus directories, and provides an explicit audited path to stage, activate, or roll back a published contract on the WG-RNN runtime.

## Boundary

- The contract corpus, repository source, and evidence are mounted read-only. At run time the 27 MB corpus is copied to a private ephemeral `/work` tmpfs so Lean and TLC can create build/state files without mutating the source corpus.
- Every formal, cryptographic, schema, vector, provenance, and external-gate probe executes in the rootless Podman Compose sandbox.
- The host Python process only validates inputs, creates a resolved Compose file, observes the container, collects logs, and tears the project down.
- The sandbox has no external network: each run gets a unique Compose-managed internal network with no external route. It also has a read-only root filesystem, no capabilities, no-new-privileges, non-root UID/GID, bounded CPU/memory/processes, and an ephemeral project/container name.
- The VM may grant full authority inside the test-only `duotronic://authority/sandbox/witness-harness-vm` namespace after all 12 gates verify. That authority is explicitly `production_eligible: false`, cannot reach the live runtime, and cannot be imported as production evidence.
- `contract_control.py` is a separate production lifecycle plane. Its list/create/diff/snapshot/sandbox/publish/stage actions remain runtime-disconnected; only the explicit `activate`, `rollback`, and `runtime-status` actions contact the production runtime.
- Sandbox activation reports may state `authority_activated: true` together with `authority_scope: sandbox-only`; they always state `production_authority_activated: false` and `production_runtime_connected: false`.

## Development workflow through MCP

1. Run `witness_activation_harness_build` after changing harness code or the TLC layer. It builds a thin child image from the local versioned toolchain base. Run `witness_activation_harness_build_toolchain` only when the base is absent or Lean/Java/Python/PQ versions change. If `/var/www/xavi/updates/.podman-deploy-priority` exists, either build records `state: deferred` and exits without contending with the active deployment; rerun after the lock clears.
2. Run `witness_contract_sandbox_gate` for a fast targeted probe (it skips the release-wide portable suite and is never activation-eligible), or `witness_contract_sandbox_all` for full qualification and all 12 gates.
3. Read the measurement in `logs/<run-id>/measurements/<gate_id>.json`.
4. Have the authorized external verifier/attestor sign an evidence envelope bound to that exact subject and result ID.
5. Put the public envelope at `harness/evidence/<gate_id>.json`; keep private keys outside this repository and outside harness logs.
6. Rerun the gate through MCP. It is verified only if the sandbox probe passes and the fresh ML-DSA-87 envelope validates against `harness/evidence/trust_registry.json`.
7. Run all 12 gates before handing a candidate toward runtime staging.

Missing evidence is a normal development result: the gate is `blocked`, not skipped or passed. Probe measurements are still retained so an independent system can attest them.

## Compose sandbox toolchain

The versioned image contains and runs:

- Lean/Lake 4.29.1 and the corpus strict Lean runner
- Java 17 and the official TLA+ Tools/TLC 1.8.0 JAR, pinned by SHA-512, plus the corpus strict TLC runner
- Python 3, the complete 5.3.17 portable corpus validator, identity vectors, and provider tests
- ML-DSA-87, ML-KEM-1024, KMAC256, and AES-256-GCM-SIV providers
- Git, JQ, SQLite, and Zstandard utilities

The image and generated Compose environment set `PYTHONPATH=/work/corpus` for corpus-local imports and bind the strict runner to `/opt/tla2tools/tla2tools.jar`; all formal toolchains therefore execute inside the sandbox. `Containerfile.toolchain-base` owns the heavyweight, rarely changing Lean/Java/Python/PQ layer. `Containerfile.activation` is a thin child containing TLC and harness code, so normal development rebuilds avoid re-downloading and re-extracting Lean. Both build paths use pinned inputs, local Podman layers, full build logs, and image metadata.

The checked-in `compose.activation.yaml` is the human-readable policy template. Every run writes an exact, absolute-path `compose.resolved.json` to its log bundle and invokes it through `podman --remote=false compose`. The policy declares `pids_limit: 512`; because the installed Podman Compose 1.0.6 provider does not forward that field, the host orchestrator applies the same cgroup limit with `podman container update --pids-limit 512` after container creation, measures the effective `/sys/fs/cgroup/pids.max` value inside the running sandbox, and only then releases the sandbox start barrier. A UID-wide `nproc` limit is intentionally not used because it can count unrelated processes owned by the rootless host user.

## Files

- `activation_gate_registry_v1.json`: exact 12-gate external activation registry.
- `activation_evidence_schema_v1.json`: version-locked signed-evidence schema.
- `vm_control.py`: default MCP-facing libvirt VM lifecycle, input synchronization, guest execution, log retrieval, and automatic shutdown. It has no host-Podman code path.
- `vm/guest/guest_runner.py`: confined named-operation guest API; rootless Podman Compose is invoked only inside the VM.
- `vm/bootstrap-host.sh`: one-time administrator bootstrap for QEMU/libvirt, the verified cloud image, qcow2 disk, cloud-init, and domain definition.
- `external_attestation_workflow.py`: production/external export, ingest, and inventory workflow. It cannot issue or sign evidence.
- `sandbox_attestor.py`: independent guest-container issuer for test-only evidence. It creates twelve ephemeral ML-DSA-87 keypairs, emits only public trust material and signed evidence, and marks every artifact non-production.
- `activation_harness.py`: guest-side multi-version rootless Podman Compose orchestration and teardown.
- `activation_sandbox.py`: version-dynamic in-sandbox qualification, probes, measurements, and ML-DSA-87 evidence verification.
- `contract_control.py`: confined development workspace, publish, stage, activate, health-check, automatic rollback, and manual rollback lifecycle controller.
- `contract_control_selftest.py`: deterministic lifecycle, confinement, activation-boundary, and runtime-selection tests.
- `compose.activation.yaml`: audited sandbox policy template.
- `Containerfile.toolchain-base`: heavyweight pinned Lean/Java/Python/PQ base, rebuilt only on toolchain changes.
- `Containerfile.activation`: thin TLC and harness-code image built from the versioned toolchain base.
- `activation_harness_selftest.py`: registry, Compose policy, toolchain, lifecycle, logging, and authority tests.
- `RUNTIME_HANDOFF_CHECKLIST_5_3_17.md`: work required after qualification and before runtime activation.
- `bin/ci/external_activation.sh`: local wrapper; operations should normally use the MCP bounded commands.

## VM isolation boundary

The default sandbox path is now MCP -> system libvirt/QEMU VM -> non-root `harness` user -> guest rootless Podman Compose. The host controller never calls Podman and never shares the host Podman socket, container storage, runtime network, or bind-mounted repository with the guest. It sends an explicit corpus snapshot, a Git bundle plus host cleanliness receipt, and signed-evidence inputs over SSH; it retrieves the complete guest run tree into `logs/<run-id>/vm-guest/`.

The VM is named `duotronic-witness-harness`, uses 6 vCPUs, 8 GiB RAM, and a thin 64 GiB qcow2 disk under `/datastore2/xavi/witness-harness-vm`. A normal test run starts it on demand and requests clean shutdown after log collection. The guest also has a six-hour fail-safe poweroff timer. A forced destroy is never automatic.

The one-time administrator bootstrap dynamically resolves the newest released Ubuntu Server LTS from Canonical at execution time, identifies the cached image with SHAKE256-512, and refuses fixed-version provisioning before defining the VM. It generates a dedicated 4096-bit SSH management key for the MCP service user, installs QEMU/libvirt, and refuses to overwrite an existing domain or disk. The guest nftables policy rejects new connections to private/host networks while preserving established MCP SSH sessions and public package access. After bootstrap, bounded MCP commands provide lifecycle, health, guest-only toolchain/image builds, single/all-gate execution, exact-challenge evidence verification, attestation request/export/import/status, full sandbox-runtime activation, and guest artifact collection. MCP control remains a named-operation API: there is no blanket root shell, host Podman access, production runtime network, or production activation authority.

Run `witness_harness_vm_sandbox_activate_all` with `version=published:v1.6 - Draft 5.3.17` and a suitable timeout to execute the complete sandbox lifecycle. It starts the VM, performs a first all-gate probe pass, runs a separate rootless attestor container, creates twelve independent test issuer identities, reruns and verifies all gates, persists a sandbox activation record, collects the complete guest log tree, and shuts the VM down.

Administrator bootstrap syntax:

```bash
sudo bash /var/www/xavi/Duotronics/harness/vm/bootstrap-host.sh tbi
```

Use the actual MCP service account if it is not `tbi`. Restart the MCP adapter/session after bootstrap so its new `kvm` and `libvirt` group memberships take effect. Then run `witness_harness_vm_status`, `witness_harness_vm_build_all`, and the VM gate commands.

## External-attestation workflow

Each run creates an exact-subject challenge for all selected gates. `external_attestation_workflow.py export-requests` writes a version-locked request bundle naming the required issuer scope, claims, probe result, SHAKE256-512 subject, and ML-DSA-87 suite. Evidence can only be ingested from `harness/evidence`; it is copied into the immutable per-run inbox with a pending-verification receipt. The guest rerun performs schema, freshness, issuer scope, required-claim, subject, measurement, payload-commitment, trust-registry, revocation, and ML-DSA-87 verification.

The production/external workflow never possesses issuer private keys and never self-signs production evidence. Gates 8 and 10 continue to require external issuers for production. In the VM-only profile, a separate attestor container simulates those independent roles with distinct ephemeral test keys; every key, trust record, envelope, and activation record is namespace-bound and `production_eligible: false`. Evidence ingestion rejects mismatched challenges before execution. The verification pass enforces probe-run, subject, trust domain, freshness, claims, payload commitment, issuer scope, and ML-DSA-87 signatures; it retains the exact signed first-pass measurement and separately records the fresh revalidation measurement. An all-12 verified aggregate activates the sandbox runtime only and never connects the production runtime.

The MCP sequence is: `witness_harness_vm_run_all` -> `witness_attestation_export_requests` -> external issuers perform the requested work and sign evidence -> `witness_attestation_ingest` for each gate -> `witness_harness_vm_verify_all` -> `witness_attestation_status`.

## Exact gates

1. `strict_lean`
2. `strict_tlc`
3. `governed_hermetic_execution`
4. `image_build_attestation`
5. `verifier_build_attestation`
6. `reproducible_inspector_build`
7. `committed_source_provenance`
8. `external_governance_authorization`
9. `post_quantum_provider_attestation`
10. `production_key_ceremony`
11. `encrypted_recovery_drill`
12. `mixed_version_rollback_drill`

Every gate requires signed evidence. Production gates 8 and 10 explicitly forbid harness self-issuance. The VM profile tests their complete mechanics with separate sandbox-only issuer identities whose keys and evidence are rejected by the production trust profile.

## Per-run logs

Every operation creates `logs/<UTC-run-id>/` before doing work and retains it on success, blocking evidence, validation failure, timeout, interruption, Compose error, or cleanup failure. A qualification run includes:

- `host.log`, `host.log.ndjson`, and exact `commands.jsonl`
- rootless/Compose preflight and image metadata
- `compose.resolved.json`, Compose stdout, and Compose stderr
- live container and internal-network inspections, cgroup PID-limit enforcement, and evaluated sandbox controls
- `working-corpus.json`, `toolchain-inventory.json`, and `qualification-suite.json`
- `sandbox.log.ndjson`, per-command records, and one measurement per gate
- `sandbox-report.json` and final `aggregate-report.json`
- Compose-down, forced-removal, container-absence, and per-run network-absence cleanup proof

The log tree is ignored by Git except `logs/.gitkeep`. Never put private evidence, recovery plaintext, or production key material in it.

## Runtime handoff

Only an all-12 verified aggregate with `qualification_complete: true` may become eligible for runtime staging. Even then, `runtime_handoff_eligible` is not activation authority; governance authorization, production key ceremony, a versioned runtime adapter, shadow verification, and a separate operator action remain mandatory.


## MCP contract lifecycle

Contract references are explicit: `workspace:<directory>` is mutable development state and `published:<directory>` is a standalone corpus under `build_docs/witness_contract`. Bare names are accepted only when unambiguous.

The registered MCP commands provide the complete lifecycle:

- `witness_contract_versions`: list workspaces, published corpora, staged state, and active runtime state.
- `witness_contract_workspace_create`, `witness_contract_workspace_status`, `witness_contract_workspace_diff`, and `witness_contract_workspace_discard`: manage mutable on-server development versions. File reads and edits use Xavi OPS MCP `dev_rpc` inside the returned workspace path.
- `witness_contract_snapshot`: compute a complete SHAKE256-512 tree snapshot without adding generated files to the corpus.
- `witness_contract_sandbox_gate` and `witness_contract_sandbox_all`: test any workspace or published version in the rootless Podman Compose lab.
- `witness_contract_publish`: atomically copy a workspace into a new published standalone directory; published directories are never overwritten or deleted by the controller.
- `witness_contract_runtime_stage`: bind a published version to its latest exact-corpus qualification report and record all blockers.
- `witness_contract_runtime_activate`: activate a staged version. Qualified mode requires an exact all-12 verified report. Development mode requires the literal `ALLOW_NONAUTHORITATIVE_DEVELOPMENT_ACTIVATION` confirmation and records `non_authoritative: true`.
- `witness_contract_runtime_status` and `witness_contract_runtime_rollback`: inspect or atomically restore the previous active contract. Rollback requires `ROLLBACK_ACTIVE_WITNESS_CONTRACT`.

Runtime selection is stored atomically in `runtime-v3/config/active_witness_contract.json`. At startup, runtime and runtime MCP resolve only a simple child directory inside their read-only `/runtime/corpus-history` mount; malformed, missing, symlinked, or traversal selections fall back to the existing Draft 5.3.16 mount. Activation rebuilds the runtime image, recreates only the runtime container, checks health, and automatically restores the previous state if either restart or health verification fails.


## Paired self-amending corpus/runtime lab

A development cycle now produces one cryptographically bound pair instead of changing a corpus in place:

- parent corpus: the selected workspace or published corpus, synchronized read-only;
- parent runtime: the current runtime v3 source tree, including uncommitted development files but excluding state, logs, virtual environments, credentials, private keys, tokens, and environment files;
- candidate corpus and candidate runtime: immutable child copies produced only inside guest rootless Podman;
- external data: an optional named snapshot from `external_data/<name>`, credential-screened, content-addressed with SHAKE256-512, and mounted read-only;
- proposal: an optional `proposals/<name>` document using `duotronic-paired-change-proposal/v1`; only confined `write_text` and exact `replace_text` operations are accepted;
- recurrent witness: deterministic diagnostic state that binds the parent pair, child pair, external snapshot, and applied changes. It can recommend a new child but cannot create authority.

The VM first materializes the pair, builds the runtime candidate image from that exact runtime snapshot, starts isolated ephemeral PostgreSQL and Redis services, compiles and tests the runtime, probes `/health`, `/openapi.json`, and `/v1/self-development/plan`, captures container logs, and tears the runtime stack down. The candidate corpus is then run through the full external-attestation workflow and all 12 activation gates. Only a pair with a qualified runtime candidate and 12 verified gates is exported to `candidates/<pair-id-suffix>/`.

The runtime candidate network is internal and exposes no host port. Ollama, Milvus, Xavi MCP, repository tools, ops tools, code interpreter, production data, production credentials, and production activation are disabled. Sandbox authority may become active only in `duotronic://authority/sandbox/witness-harness-vm`; every report remains `production_eligible: false`.

MCP operations:

- `witness_harness_paired_selftest`: compile the paired control plane and run its policy/boundary tests.
- `witness_harness_vm_paired_cycle`: no-proposal baseline pair from `version`.
- `witness_harness_vm_paired_cycle_with_data`: add a named immutable `external_data_set`.
- `witness_harness_vm_paired_cycle_with_proposal`: evaluate a named confined `proposal` against a named external snapshot.
- `witness_harness_paired_inventory`: read-only inventory of available inputs and exported pairs.

Every VM run is collected under `logs/<run-id>/`, including runtime build/test output, resolved Compose documents, API probes, runtime container logs, recurrent witness state, pair manifest, all gate measurements, attestation envelopes, activation lifecycle, and VM-controller audit events. Parent corpus/runtime inputs are never overwritten.
