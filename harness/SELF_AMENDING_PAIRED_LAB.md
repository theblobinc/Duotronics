# Self-amending paired corpus/runtime laboratory

The harness treats the Witness Contract corpus as the logical policy and memory plane, and the sandbox runtime as the executable recurrent plane. A development generation always contains both.

```text
immutable corpus parent + immutable runtime parent + external snapshot
  -> witnessed observations
  -> WG-RNN candidate proposals
  -> deterministic policy filter
  -> child corpus + child runtime
  -> portable, unit, formal, migration, replay and rollback checks
  -> rootless Podman sandbox-runtime execution inside the libvirt VM
  -> twelve externally attested activation gates
  -> sandbox-only paired candidate
```

The system is recursive because the next generation reads the previous candidate's corpus rules, runtime state, proposal history, rejected counterexamples and qualification evidence. It is self-referential because the corpus can describe the schemas, tests and policy governing its own next revision, while the runtime can propose changes to the machinery that interprets those rules.

Self-reference never means self-authority. The following remain separate objects: proposal, candidate files, computation witness, test result, external attestation, gate result, sandbox activation and production authorization. A recurrent or neural result can propose a document, schema, test or runtime patch. It cannot sign external evidence, weaken a gate, relabel sandbox evidence as production, publish a corpus, stage a production runtime or activate production.

## Paired output

Every cycle emits:

- `corpus-candidate/`: complete standalone child corpus;
- `runtime-candidate/`: complete child runtime source;
- `paired-candidate.json`: SHAKE256-512 identities and shared lineage;
- `proposal.json`: exact structured changes;
- `external-snapshot.json`: immutable external-data provenance;
- test, runtime-health, migration, replay, rollback and gate receipts;
- a sandbox activation record only after all twelve gates verify.

## External data

The default bridge is an MCP-synchronized, immutable snapshot. This permits data from the larger WG-RNN server, its APIs, formal workers, model workers, data lake and operator-supplied fixtures without sharing host filesystems, Podman sockets, databases or credentials with the VM. Each snapshot declares origin, stability class, content identity, size, collection time and permitted purposes.

Direct network access is a separate future profile and remains disabled by default. It must use an explicit endpoint allowlist, bounded requests, credential references supplied at run time, response-size limits and a recorded stable projection. Production control endpoints are never members of that allowlist.

## Recursive acceptance

Low-risk candidate proposals may be materialized automatically. Materialization is not acceptance. The candidate pair must prove parent lineage, corpus validity, runtime tests, runtime health, compatibility, external-snapshot provenance, recurrent replay, migration safety, rollback restoration and all twelve activation gates. Publication and production rollout stay separate explicit lifecycle actions.
