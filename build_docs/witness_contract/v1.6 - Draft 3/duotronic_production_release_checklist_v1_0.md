# Duotronic Production Release Checklist v1.0

**Status:** Draft 2 release gate checklist

## 1. Corpus checks

- [ ] Every active document has status, version, and purpose.
- [ ] Manifest lists all Markdown files.
- [ ] v1.5 carry-forward mapping exists.
- [ ] Draft 1 retained documents are marked historical if superseded.
- [ ] Release notes are complete.

## 2. Backend checks

- [ ] API contract has OpenAPI artifact.
- [ ] Database schema has migration scripts.
- [ ] Policy engine has executable fixtures.
- [ ] MCP self-test passes.
- [ ] Database list-tables returns normal local schema, not fallback-only result.
- [ ] Cognition tools do not return schema errors.
- [ ] Direct mutation tools are disabled or explicitly approved.

## 3. Security checks

- [ ] STRIDE model reviewed.
- [ ] Sandbox limits tested.
- [ ] Secrets redacted in audit logs.
- [ ] Backup snapshot created before risky changes.
- [ ] Git sync behavior tested.
- [ ] Emergency disable switches exist.

## 4. Mathematical checks

- [ ] Proof witness fixtures pass.
- [ ] Computation-only evidence cannot promote theorem.
- [ ] Langlands objects have status separation.
- [ ] Open conjectures are not marked theorem without proof.
- [ ] DMQL query fixtures pass.

## 5. Operations checks

- [ ] Prometheus metrics emitted.
- [ ] OpenTelemetry traces emitted.
- [ ] Backup restore tested.
- [ ] Replay package verified.
- [ ] Human review queue tested.
- [ ] Incident state routing tested.

## 6. MCP/SRNN checks

- [ ] MCP tool manifest captured.
- [ ] Capability report captured.
- [ ] Policy explanations captured for high-risk tools.
- [ ] Minecraft mode intentionally configured.
- [ ] Multimodal ingest fixture tested.
- [ ] Oracle job `witness_event_id` persisted.

## 7. Release decision

A release candidate may be cut only when all critical checks pass or waivers are recorded as `ReleaseWaiverWitness` objects.
