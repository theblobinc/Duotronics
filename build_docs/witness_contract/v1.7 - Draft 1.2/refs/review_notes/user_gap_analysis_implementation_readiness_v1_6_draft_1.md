# Imported Reviewer Note — Pasted markdown(24).md

**Status:** imported review evidence  
**Purpose:** Preserve user-provided review text that informed v1.6 Draft 2.

---

The Duotronic v1.6 Draft 1 corpus is already substantial—it defines the mathematical canon, witness contracts, backend spine, polyglot runtime, and carries forward every v1.5 concern. However, before this can become a **production‑ready specification that an engineering team can implement**, several areas need additional detail or entirely new documents.

Below is a structured gap analysis, grouped by domain, with concrete suggestions for what to add.

---

## 1. Implementation‑level specifications

The current documents describe roles, schemas, and invariants. They do **not** yet specify how the system actually works at the code/API level.

**Missing:**
- **API contracts** for the transition API (Python/FastAPI). What endpoints exist? Request/response schemas? How does witness submission work?
- **Database schemas** (PostgreSQL) for canonical objects, witnesses, tasks, and migration records.
- **Wire protocol** details for the JSON‑RPC bridge to Lisp and Julia. What exactly do the request/response payloads look like? How is the circuit breaker configured?
- **DBP v2 object envelope** specification. The corpus mentions it repeatedly but never defines its structure.
- **Policy decision engine** specification. The policy shield is mentioned as gating various actions; there is no document that says *how* a policy is expressed, evaluated, or overridden.

**Suggested new documents:**
- `duotronic_api_contract_v1_0.md`
- `duotronic_database_schema_v1_0.md`
- `duotronic_polyglot_bridge_protocol_v1_0.md`
- `duotronic_dbp_v2_envelope_spec.md`
- `duotronic_policy_engine_spec_v1_0.md`

---

## 2. Security and trust model

The corpus touches lightly on sandboxing and policy gates, but there is no overarching threat model or security architecture.

**Missing:**
- **Authentication and authorization model.** How are nodes, users, and workers identified? Who can submit mathematical objects, trigger interpreter runs, or approve promotions?
- **Network security** for inter-component communication (PostgreSQL, Redis, Lisp/Julia bridges, multimodal ingest).
- **Sandbox hardening specification** – beyond “network disabled by default” and “filesystem write policy”, what exact mechanisms are used (e.g., container images, seccomp profiles, gVisor)?
- **Data integrity and tamper evidence** – while hashes are recorded, there is no description of how they are used to detect corruption or malicious alteration.
- **Vulnerability management** plan for dependencies (proof assistants, interpreters).

**Suggested new documents:**
- `duotronic_security_architecture_v1_0.md`
- `duotronic_sandbox_specification_v1_0.md`

---

## 3. Operational documentation

Running a distributed system with multiple runtimes, stores, and witness pipelines requires operations guidance.

**Missing:**
- **Deployment architecture** – container orchestration, scaling rules, resource requirements.
- **Monitoring and observability** – what metrics, logs, and traces must be emitted? How are critical health signals (e.g., Lisp bridge latency, queue depth) surfaced?
- **Backup and disaster recovery** for the canonical PostgreSQL store and replay packages.
- **SLAs / non‑functional requirements** – expected throughput, latency bounds, available uptime.
- **Upgrade procedures** for transitioning from v1.5 to v1.6 in a live environment.

**Suggested new documents:**
- `duotronic_deployment_guide_v1_0.md`
- `duotronic_operations_manual_v1_0.md`
- `duotronic_migration_runbook_v1_6.md`

---

## 4. Specification governance and versioning

The corpus itself lacks meta‑rules about how it is maintained.

**Missing:**
- **Specification versioning policy.** When does a new normative draft supersede an old one? How are errata handled?
- **Change control process** – who can approve modifications to the mathematical canon or witness schemas? Is there an RFC‑like process?
- **Deprecation lifecycles** for old object shapes (the v1.5 `CorpusMigrationWitness` concept is mentioned but not formalized).
- **Licensing and intellectual property** – the corpus is published as Markdown, but no license (e.g., CC‑BY, MIT) is declared.

**Suggested new document:**
- `duotronic_specification_governance_v1_0.md`
- A `LICENSE` file at the corpus root.

---

## 5. Detailed example walkthroughs

The conformance fixtures give minimal test cases, but there are no end‑to‑end narratives that show how the system handles a complete mathematical claim.

**Missing:**
- Walkthrough of adding a new theorem (including proof witness, checker run, policy promotion, and storage).
- Walkthrough of a Langlands computational experiment (from interpreter request to witness record, and why it stays `computational_evidence`).
- Walkthrough of a witness‑gated recurrent cell updating its state from a multimodal video + audio stream.

**Suggested new document:**
- `duotronic_use_case_examples_v1_0.md`

---

## 6. Testing and conformance certification

The corpus defines what a conformant system must do, but not how conformance is proven.

**Missing:**
- **Test suite specification** – what automated tests must pass for an implementation to claim v1.6 conformance?
- **Fixture packs** – a downloadable set of canonical objects, witnesses, and expected replay outputs that any implementation can validate.
- **Interoperability tests** – if multiple implementations exist, how do they verify interoperation (node federation, task delegation)?
- **Proof‑checker integration test** – e.g., a Lean/Coq proof that is accepted by the configured proof authority.

**Suggested new documents:**
- `duotronic_conformance_test_suite_v1_0.md`
- A companion repository `duotronic-fixtures-v1.6` with machine‑readable fixture data.

---

## 7. Clarification of ambiguous terms

Several concepts are mentioned but not fully unpacked:

- **DPFC (Polygon Family Calculus)** is said to remain as a “representational discipline” but its role in the broader canon is vague. A short document or appendix could map DPFC primitives (presence/absence, family declarations, etc.) onto the new CanonicalMathObject / MathFamilyDeclaration schemas.
- **CorpusMigrationWitness** is used to handle backward compatibility, but its exact schema and lifecycle are never defined.
- **Replay packages** – what exactly does a replay bundle contain? How is deterministic replay verified?
- **SRNN “loop ID, node ID, oracle job ID”** – these are mentioned in the backend patch, but the full task queue schema is not documented.
- **“Policy gate”** is mentioned dozens of times; an actual policy rule syntax (e.g., JSON policy documents, Rego) is missing.

**Suggested new documents:**
- `duotronic_dpfc_canon_bridge_v1_0.md` (or an appendix to polygon family calculus)
- `duotronic_corpus_migration_witness_spec_v1_0.md`
- `duotronic_replay_package_spec_v1_0.md`

---

## 8. Human interface and tooling

The corpus assumes human review and escalation but doesn’t describe any user interface or administrator tools.

**Missing:**
- **Admin CLI / dashboard** – how does an operator inspect the corpus, approve promotions, view contradictions?
- **Review queue interface** – what does a human reviewer see when an interpreter run needs evaluation?
- **Search and query language** – the all‑math witness contract lists example queries, but there is no document specifying the query syntax or API.

**Suggested document:**
- `duotronic_admin_interface_spec_v1_0.md`

---

## Summary of recommended additions

| Priority | Document / Artifact |
|----------|---------------------|
| Critical | API contract, database schema, policy engine spec, DBP v2 envelope |
| High | Security architecture, deployment guide, migration runbook, bridge protocol |
| Medium | Operations manual, conformance test suite, replay package spec, specification governance |
| Lower | Use‑case examples, admin interface, DPFC‑canon bridge, downloadable fixtures |

Adding these would transform the corpus from a **comprehensive architectural intent** into a **complete, implementable, and maintainable specification**. Many of these could be deferred to a v1.6 Draft 2, but even a few key ones (especially the API and policy engine) would significantly reduce ambiguity for early implementors.
