# Proof Authority Retention and Observability Profile v1.0

## Observability

Permitted operational fields include execution ID, compiler profile, snapshot
ID, semantic witness ID, stage durations, resource usage, stable failure code,
image digest, OCI runtime digest, sandbox invocation digest, and result-signature
status.

Logs must not contain private signing material, unredacted environment,
sensitive host paths, authority database contents, arbitrary submitted source,
or verifier requests unless a separately governed incident policy requires it.

## Retention

- Mutable submissions: retain only through snapshot acceptance or governed
  incident investigation.
- Immutable snapshots and generated modules: retain while referenced by an
  issued witness or archive them under content-addressed durable storage.
- Intermediate compiler output: delete after trusted inspection unless an
  explicit failure-retention policy applies.
- Signed verifier results, compiler witnesses, authority events, snapshots, and
  promotion records: retain append-only or preserve through a verifiable
  archival replacement.
- Failed artifacts: retain by bounded policy with redaction and access control.

Deletion must not make an already issued authority record unverifiable. A
retention change is a governed policy event and applies prospectively unless an
explicit correction says otherwise.
