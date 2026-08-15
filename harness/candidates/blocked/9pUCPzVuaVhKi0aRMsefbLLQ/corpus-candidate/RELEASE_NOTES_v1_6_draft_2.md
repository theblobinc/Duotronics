# Release Notes — Duotronic v1.6 Draft 2

## Status

Draft 2 is a completeness and production-readiness pass over v1.6 Draft 1.

## Major additions

1. **Formal semantics and verification**
   - Adds `duotronic_formal_semantics_and_verification_v1_0.md`.
   - Defines a plan for Lean/Coq/TLA+ modeling of core invariants.
   - Introduces safety properties such as theorem-promotion soundness and conjecture containment.

2. **Threat model**
   - Adds `duotronic_stridethreat_model_v1_0.md`.
   - Uses STRIDE categories across API, database, MCP, bridge runtimes, interpreter sandbox, GitHub/repo tooling, backups, and Minecraft tools.

3. **Proof and certificate interoperability**
   - Adds `duotronic_proof_interchange_and_certificates_v1_0.md`.
   - Adds proof-carrying computation semantics.
   - Standardizes proof-witness distinction between proof objects, proof checker runs, computational certificates, and advisory computations.

4. **Human review workflow**
   - Adds `duotronic_human_review_state_machine_v1_0.md`.
   - Defines reviewer ticket lifecycle, quorum, arbiter escalation, review packets, and decision forms.

5. **MCP server tooling integration**
   - Adds live MCP snapshot and policy observation documents.
   - Adds an explicit MCP query witness type for tool observations.
   - Records observed tool count, scope model, transport protection, and self-test state.

6. **SRNN backend integration**
   - Updates the corpus to reflect:
     - auto-registration of identity oracle adapters;
     - direct filesystem and command execution MCP tools;
     - auto backup/git sync on mutating MCP tools;
     - audit redaction for sensitive arguments;
     - multimodal witness ingestion;
     - Minecraft/Mineflayer tool policy;
     - cognition-loop migration issue.

7. **Operational hardening**
   - Adds production release checklist.
   - Adds observability profile for OpenTelemetry and Prometheus.
   - Adds standards-alignment document for OpenAPI, JWS, SHA3-256, problem details, and proof interchange.

## Compatibility

Draft 2 keeps the Draft 1 corpus content and v1.5 carry-forward coverage. Files that were Draft 1-specific are retained with historical suffixes where necessary.
