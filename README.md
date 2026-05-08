# Duotronics

Duotronics is a specification and systems-design program for witness-bearing
computing. It defines how a system can represent, transport, validate, replay,
govern, and evolve identity-bearing facts across recurrent, distributed,
multimodal, and policy-constrained runtimes without collapsing distinctions such
as absence vs zero, transport validity vs semantic validity, or model output vs
authority.

This repository is the specification and corpus authority for Duotronics. It is
where the program's contracts, profiles, conformance assets, formalization
artifacts, migration notes, and research workbooks live.

Duotronics is not just about one runtime, one protocol, one model stack, or one
application domain. It is intended to be useful anywhere systems need to answer
questions like:

- What exactly happened?
- What evidence supports that claim?
- What policy governed the transition?
- Can the state change be replayed and audited later?
- Can multiple models, tools, humans, and machines participate without
  collapsing authority boundaries?
- Can the system prove that something was quarantined, removed, redacted,
  invalidated, or retained under policy?

## Table Of Contents

- [Executive Summary](#executive-summary)
- [What Duotronics Is](#what-duotronics-is)
- [What Duotronics Is Not](#what-duotronics-is-not)
- [The Ecosystem At A Glance](#the-ecosystem-at-a-glance)
- [Why Duotronics Exists](#why-duotronics-exists)
- [Core Principles](#core-principles)
- [Applied Domains And Use Cases](#applied-domains-and-use-cases)
- [How The Companion Repositories Fit](#how-the-companion-repositories-fit)
- [Architecture Stack](#architecture-stack)
- [Current Corpus Authority](#current-corpus-authority)
- [Repository Map](#repository-map)
- [Reading Paths By Role](#reading-paths-by-role)
- [Current Status And Non-Claims](#current-status-and-non-claims)
- [Contribution Guidance](#contribution-guidance)
- [License](#license)

## Executive Summary

At the highest level, Duotronics is a framework for building systems that can
reason, act, and evolve while remaining auditable, replayable, and governed.

The program combines:

- a witness calculus for evidence-bearing facts and transitions;
- a representational layer for canonical identity and mathematical structure;
- a recurrent memory model with explicit write, decay, quarantine, and
  promotion gates;
- a distributed systems layer for federation, task delegation, transport, and
  resource witnessing;
- a governance layer for policy evaluation, human review, purge authorization,
  migration, and retention handling;
- a conformance and formalization layer for testing, proofs, executable
  artifacts, and implementation readiness.

This makes Duotronics relevant to a wide range of domains, including AI safety,
cybernetics, data science, formal knowledge systems, multimodal runtime design,
distributed infrastructure, online safety and audit assurance, and high-rigor
event-sourced operations.

The latest center of gravity in this repository is the v1.6 Draft 3 corpus and
its RC-closure package under
[build_docs/witness_contract/v1.6 - Draft 3/](build_docs/witness_contract/v1.6%20-%20Draft%203/),
which expands the program with executable artifacts, migration and rollback
guidance, stronger runtime boundaries, formal-semantics planning, richer
observability material, and implementation-facing closure of previously
identified blockers.

## What Duotronics Is

Duotronics is best understood as all of the following at once:

1. A witness architecture.
   Every meaningful event can be represented as an evidence-bearing transition,
   rather than as an opaque side effect in a log file or a black-box model.

2. A governance architecture.
   State changes are not merely executed; they are admitted, rejected,
   quarantined, escalated, replayed, or purged under explicit policy.

3. A recurrent systems architecture.
   Memory is not a passive store. It is governed, decayed, promoted, and shaped
   through recurrence and authority rules.

4. A mathematical and representational architecture.
   Canonical identity, family-native representations, conversion, proof status,
   and formal semantics are part of the system design, not afterthoughts.

5. A distributed systems architecture.
   Nodes, tools, tasks, resources, transport lanes, and runtime capabilities can
   all participate in a federated, witness-bearing network.

6. A conformance program.
   The goal is not only to describe the system in prose, but to define fixtures,
   executable artifacts, tests, schemas, migration rules, and verification paths
   that implementations can be measured against.

## What Duotronics Is Not

Duotronics is not:

- a single application;
- a single model or training pipeline;
- a claim that model output is authoritative by default;
- a claim that transport validity implies semantic truth;
- a fixed commitment to one language, storage engine, or deployment substrate;
- a replacement for human review, legal judgment, or operational governance;
- a finished production certification or compliance stamp.

It is a specification-first program that aims to make trustworthy, auditable,
policy-aware systems easier to design and validate.

## The Ecosystem At A Glance

Duotronics now spans a small ecosystem rather than a single repository.

| Component | Role | What it contributes |
|---|---|---|
| [Duotronics](https://github.com/theblobinc/Duotronics) | Specification authority | Core contracts, corpus, conformance, formalization, governance, research inputs |
| [duotronic-bus-protocol](https://github.com/theblobinc/duotronic-bus-protocol) | Transport and interchange layer | Fixed-shape binary framing, DBP v1/v2, security profiles, sparse witness transport, protocol fixtures |
| [srnn_server](https://github.com/theblobinc/srnn_server) | Federated runtime implementation | FastAPI-based runtime, agents, cognition loops, multimodal ingest, vector storage, task routing, deployment topology |

These repositories are related but not interchangeable:

- Duotronics defines the semantics, authority boundaries, and governance model.
- DBP defines how structured frames move across transport boundaries without
  losing deterministic shape.
- SRNN Server demonstrates how Duotronics-style principles can be realized in a
  live recurrent and federated runtime.

## Why Duotronics Exists

Modern systems often fail in exactly the places that matter most:

- logs say something happened, but not whether it was valid;
- models produce outputs, but no authority rule says whether they may change
  state;
- transport checks pass, but semantic meaning is ambiguous;
- actions are executed, but their policy basis is unclear;
- data is deleted, but there is no safe proof of what changed;
- multiple tools and agents interact, but the system cannot reconstruct why a
  decision was made;
- distributed services coordinate, but no shared witness identity ties their
  behavior together.

Duotronics exists to address those gaps by making state transitions explicit,
governed, replayable, and interoperable.

## Core Principles

### 1. Witness before assertion

Duotronics prefers evidence-bearing objects over undocumented state mutation.
A system should be able to say not only that something occurred, but what the
relevant witness, provenance, policy, and replay identity were.

### 2. Separation of transport, semantics, identity, and authority

One of the most important Duotronic distinctions is that these are not the same
thing:

- frame validity;
- semantic validity;
- canonical identity;
- policy authority.

That separation is reflected both in the core corpus and in DBP v2 profiles.

### 3. Replayability matters

If a system cannot replay a meaningful transition path, it is difficult to
audit, debug, compare, migrate, or trust. Duotronics treats replay packages,
memory update records, and recurrence traces as first-class artifacts.

### 4. Memory must be governed

The witness-gated recurrent cell (WG-RNN) makes memory lifecycle explicit:

- write;
- candidate write;
- quarantine;
- decay;
- promote;
- no-op with evidence.

This is useful far beyond neural-network research. It applies to any system that
needs controlled persistence under uncertainty or policy constraints.

### 5. Absence is not zero

Duotronics repeatedly protects distinctions that other systems often collapse.
Absence, nullability, token-free zero, stale evidence, and invalidity all need
clear semantics if a system is going to be trustworthy.

### 6. Human review is part of the architecture

Human escalation, overrides, promotion approval, purge authorization, and policy
review are architectural primitives, not awkward exceptions bolted onto a fully
automated system.

### 7. Formalization and conformance should follow the prose

The program does not stop at conceptual description. It pushes toward manifests,
schemas, executable artifacts, proof planning, benchmark assets, and
implementation-readiness closure.

## Applied Domains And Use Cases

Duotronics is intentionally broader than any one vertical. The same witness and
governance architecture can support many different kinds of systems.

### AI safety and model governance

Duotronics is well suited to AI systems that need stronger control over what a
model may influence and how its outputs are recorded.

Useful contributions here include:

- policy-gated action surfaces;
- separation between model suggestion and state authority;
- model diversity and adjudication governance;
- replayable records for model-mediated transitions;
- explicit human review and escalation paths;
- sandbox and security constraints for high-risk actions;
- verified-vs-target runtime capability distinction for tool ecosystems.

Relevant documents:

- [duotronic_policy_engine_spec_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_policy_engine_spec_v1_0.md)
- [duotronic_human_review_state_machine_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_human_review_state_machine_v1_0.md)
- [duotronic_mcp_server_tooling_integration_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_mcp_server_tooling_integration_v1_0.md)
- [duotronic_mcp_missing_runtime_tools_backlog_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_mcp_missing_runtime_tools_backlog_v1_0.md)
- [duotronic_model_diversity_and_adjudication_governance_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/refs/duotronic_model_diversity_and_adjudication_governance_v1_1.md)

### Online safety, moderation assurance, and regulator-readable evidence

Duotronics is highly applicable to systems that need auditable governance around
review, quarantine, purge, retention, attestation, and accountability.

Potential uses include:

- documenting the path from evidence intake to final decision;
- tracking which policy governed a moderation or risk decision;
- proving that quarantine, review, removal, invalidation, or retention occurred;
- generating safe post-action records when payloads themselves cannot be kept;
- supporting appeal, override, and incident-review workflows;
- producing evidence packs for audits, internal review, or external oversight.

Relevant documents:

- [duotronic_witness_contract_v11_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_witness_contract_v11_0.md)
- [duotronic_human_review_state_machine_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_human_review_state_machine_v1_0.md)
- [duotronic_replay_package_spec_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_replay_package_spec_v1_0.md)
- [duotronic_admin_interface_spec_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_admin_interface_spec_v1_0.md)
- [duotronic_evidence_purge_and_privacy_deletion_contract_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/refs/duotronic_evidence_purge_and_privacy_deletion_contract_v1_0.md)

### Cybernetics and adaptive control

Duotronics is also a cybernetic architecture: it structures sensing,
interpretation, policy gating, recurrence, memory update, and action in a loop.

This is relevant for:

- adaptive control systems;
- robotics and embodied agents;
- human-in-the-loop safety systems;
- closed-loop observation -> decision -> action pipelines;
- environments where feedback quality and authority level matter.

The key value is not just control, but controlled control: each transition can be
typed, reviewed, replayed, and bounded by policy.

Relevant documents:

- [duotronic_runtime_recurrence_complete_integration_document_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_runtime_recurrence_complete_integration_document_v1_0.md)
- [duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md)
- [duotronic_temporal_witness_and_absence_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_temporal_witness_and_absence_profile_v1_0.md)
- [duotronic_multimodal_witness_runtime_profile_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_multimodal_witness_runtime_profile_v1_1.md)

### Mathematics, formal knowledge, and canon management

Duotronics includes a serious mathematical and formal layer. It is not only a
runtime architecture; it is also a program for structured representation,
conversion, theorem/proof governance, and canon-aware identity.

This makes it relevant to:

- mathematical knowledge systems;
- proof-status management;
- structured conjecture and theorem pipelines;
- family-native representational systems;
- formal semantics and proof-assistant workflows.

Relevant documents:

- [duotronic_polygon_family_calculus_v6_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_polygon_family_calculus_v6_0.md)
- [duotronic_mathematical_canon_contract_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_mathematical_canon_contract_v1_0.md)
- [duotronic_proof_and_conjecture_witness_contract_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_proof_and_conjecture_witness_contract_v1_0.md)
- [duotronic_formal_semantics_and_verification_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_formal_semantics_and_verification_v1_0.md)
- [formal/](build_docs/witness_contract/v1.6%20-%20Draft%203/formal/)

### Data science, ML operations, and reproducible evidence pipelines

For data science teams, Duotronics offers a way to treat feature production,
model scoring, multimodal enrichment, schema evolution, and replayability as a
single coherent system rather than disconnected tools.

Relevant capabilities include:

- schema registry and compatibility discipline;
- replayable update packages and memory traces;
- multimodal ingest contracts;
- feature and profile synthesis governance;
- executable artifacts and conformance suites;
- explicit database and API surface definitions.

Relevant documents:

- [duotronic_conformance_test_suite_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_conformance_test_suite_v1_0.md)
- [duotronic_database_schema_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_database_schema_v1_0.md)
- [duotronic_api_contract_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_api_contract_v1_0.md)
- [duotronic_sdk_and_openapi_integration_profile_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_sdk_and_openapi_integration_profile_v1_1.md)
- [duotronic_openapi_and_sdk_plan_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_openapi_and_sdk_plan_v1_0.md)

### Distributed systems, transport, and interoperable federation

Duotronics has a strong distributed-systems orientation. Nodes, tasks,
resources, authorities, and witness-bearing messages must interoperate across a
federated runtime without losing determinism.

This makes it relevant to:

- multi-node AI systems;
- federated agent networks;
- event-bearing service meshes;
- deterministic transport and decoding pipelines;
- resource witnessing and task delegation;
- cross-runtime migration and rollout planning.

Relevant documents:

- [duotronic_v1_6_distributed_self_governing_recurrent_network_addendum.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_v1_6_distributed_self_governing_recurrent_network_addendum.md)
- [duotronic_deployment_guide_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_deployment_guide_v1_0.md)
- [duotronic_srnn_integration_addendum_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_srnn_integration_addendum_v1_0.md)
- [duotronic_interoperability_standards_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_interoperability_standards_profile_v1_0.md)
- [duotronic_dbp_inter_node_full_duplex_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/refs/duotronic_dbp_inter_node_full_duplex_profile_v1_0.md)

### Security, privacy, observability, and operations

The corpus also covers operational seriousness: principal boundaries, mutation
controls, threat modeling, observability profiles, audit surfaces, and migration
discipline.

This is useful for:

- secure agent and tool execution;
- change-management evidence;
- operational risk reduction;
- production hardening and failure forensics;
- privacy deletion and purge-impact handling;
- system-health observability across heterogeneous runtimes.

Relevant documents:

- [duotronic_security_architecture_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_security_architecture_v1_0.md)
- [duotronic_stridethreat_model_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_stridethreat_model_v1_0.md)
- [duotronic_observability_opentelemetry_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_observability_opentelemetry_profile_v1_0.md)
- [duotronic_mutation_policy_defaults_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_mutation_policy_defaults_profile_v1_0.md)
- [duotronic_mutation_policy_validation_profile_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_mutation_policy_validation_profile_v1_1.md)

### Multimodal, simulation, and research systems

The program is not restricted to text or symbolic state. The corpus explicitly
supports multimodal witness ingestion and research-oriented pipelines involving
video, audio, image, CV, sensor, and fused payloads.

This creates room for:

- multimodal recurrent memory systems;
- simulated environments and embodied agents;
- world-state witnesses and temporal deltas;
- scientific instrumentation and experimental pipelines;
- long-horizon research profiles.

Relevant documents:

- [duotronic_multimodal_witness_runtime_profile_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_multimodal_witness_runtime_profile_v1_1.md)
- [duotronic_use_case_examples_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_use_case_examples_v1_0.md)
- [refs/examples/](build_docs/witness_contract/v1.6%20-%20Draft%203/refs/examples/)
- [refs/research_profiles/](build_docs/witness_contract/v1.6%20-%20Draft%203/refs/research_profiles/)

## How The Companion Repositories Fit

### Duotronic Bus Protocol

The companion repository
[duotronic-bus-protocol](https://github.com/theblobinc/duotronic-bus-protocol)
provides a transport-oriented realization of Duotronic design principles.

Key ideas from DBP include:

- fixed-shape 4096-byte frames;
- deterministic positional decoding;
- explicit structural vs semantic regions;
- security profiles for authenticity, replay resistance, and confidentiality;
- Adaptive Band Borrowing (ABB) for controlled lane reuse;
- WSB2 for sparse witness transport;
- the crucial distinction that frame validity does not imply semantic validity,
  canonical identity, or policy authority.

In other words, DBP handles the bytes and transport contract, while Duotronics
defines what those bytes mean, how witnesses are canonicalized, and what policy
can authorize after transport-level validation succeeds.

### SRNN Server

The companion repository
[srnn_server](https://github.com/theblobinc/srnn_server) demonstrates how
Duotronic ideas can be operationalized in a live federated runtime.

Capabilities reflected in its current architecture include:

- a FastAPI-based runtime shell with agent and compatibility surfaces;
- federated deployment across nodes and roles;
- recurrent memory and cognition loops;
- multimodal ingestion and enrichment patterns;
- vector storage and similarity infrastructure;
- model routing and multi-backend inference;
- observability and operations surfaces;
- deployment-aware composition of storage, queueing, search, and worker layers.

SRNN Server should be read as an implementation-oriented companion, not as the
thing that replaces the Duotronics corpus. Duotronics remains the contract and
authority layer; SRNN Server shows how those ideas can become a running system.

## Architecture Stack

One useful way to think about Duotronics is as a layered stack.

### 1. Representational and mathematical layer

This layer covers canonical identity, family-native representations, conversion,
proof status, and mathematical canon management.

Primary references:

- [duotronic_polygon_family_calculus_v6_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_polygon_family_calculus_v6_0.md)
- [duotronic_mathematical_canon_contract_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_mathematical_canon_contract_v1_0.md)

### 2. Witness and governance layer

This layer defines witness objects, memory update records, policy gates,
human-review mechanics, purge handling, retention, and replay identity.

Primary references:

- [duotronic_witness_contract_v11_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_witness_contract_v11_0.md)
- [duotronic_policy_engine_spec_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_policy_engine_spec_v1_0.md)
- [duotronic_replay_package_spec_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_replay_package_spec_v1_0.md)

### 3. Runtime recurrence layer

This layer covers the witness-gated recurrent cell, temporal authority,
multimodal updates, cognition boundaries, and memory lifecycle.

Primary references:

- [duotronic_runtime_recurrence_complete_integration_document_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_runtime_recurrence_complete_integration_document_v1_0.md)
- [duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md)
- [duotronic_multimodal_witness_runtime_profile_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_multimodal_witness_runtime_profile_v1_1.md)

### 4. Transport and federation layer

This layer covers node federation, inter-node transport, DBP-oriented exchange,
resource witnessing, and delegation.

Primary references:

- [duotronic_v1_6_distributed_self_governing_recurrent_network_addendum.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_v1_6_distributed_self_governing_recurrent_network_addendum.md)
- [duotronic_srnn_integration_addendum_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_srnn_integration_addendum_v1_0.md)
- [duotronic_dbp_inter_node_full_duplex_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/refs/duotronic_dbp_inter_node_full_duplex_profile_v1_0.md)

### 5. Security and operations layer

This layer covers mutation control, principal identity, observability, admin
workflow, production checklisting, and rollout discipline.

Primary references:

- [duotronic_security_architecture_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_security_architecture_v1_0.md)
- [duotronic_observability_opentelemetry_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_observability_opentelemetry_profile_v1_0.md)
- [duotronic_production_release_checklist_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_production_release_checklist_v1_0.md)

### 6. Conformance and formalization layer

This layer covers tests, benchmark assets, executable artifacts, formal models,
OpenAPI planning, and implementation-readiness closure.

Primary references:

- [duotronic_conformance_test_suite_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_conformance_test_suite_v1_0.md)
- [formal/](build_docs/witness_contract/v1.6%20-%20Draft%203/formal/)
- [executable/](build_docs/witness_contract/v1.6%20-%20Draft%203/executable/)

## Current Corpus Authority

The active documentation center is:

- [build_docs/witness_contract/v1.6 - Draft 3/](build_docs/witness_contract/v1.6%20-%20Draft%203/)

Start here for orientation:

1. [START_HERE_v1_6_draft_3_rc_closure.md](build_docs/witness_contract/v1.6%20-%20Draft%203/START_HERE_v1_6_draft_3_rc_closure.md)
2. [RC_BLOCKER_CLOSURE_MATRIX_v1_6_draft_3.md](build_docs/witness_contract/v1.6%20-%20Draft%203/RC_BLOCKER_CLOSURE_MATRIX_v1_6_draft_3.md)
3. [README_v1_6_draft_3.md](build_docs/witness_contract/v1.6%20-%20Draft%203/README_v1_6_draft_3.md)
4. [duotronic_program_charter_v1_6.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_program_charter_v1_6.md)
5. [refs/manifest/](build_docs/witness_contract/v1.6%20-%20Draft%203/refs/manifest/)

If you want the shortest path to the major conceptual pillars, read these next:

- [duotronic_witness_contract_v11_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_witness_contract_v11_0.md)
- [duotronic_polygon_family_calculus_v6_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_polygon_family_calculus_v6_0.md)
- [duotronic_v1_6_distributed_self_governing_recurrent_network_addendum.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_v1_6_distributed_self_governing_recurrent_network_addendum.md)
- [duotronic_runtime_recurrence_complete_integration_document_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_runtime_recurrence_complete_integration_document_v1_0.md)

## Repository Map

### Active specification corpus

- [build_docs/witness_contract/](build_docs/witness_contract/) - versioned Duotronics drafts from earlier lines through v1.6.
- [build_docs/witness_contract/v1.6 - Draft 3/](build_docs/witness_contract/v1.6%20-%20Draft%203/) - latest active corpus package.

### Conformance and implementation-readiness assets

- [harness/](harness/) - conformance harness, runtime scaffolding, and test utilities.
- [harness/conformance_harness-buildv1.md](harness/conformance_harness-buildv1.md) - harness build and execution notes.
- [prototypes/wgrnn/](prototypes/wgrnn/) - WG-RNN research prototype package.
- [prototypes/wgrnn/README.md](prototypes/wgrnn/README.md) - prototype scope and quick start.

### Historical and research inputs

- [Duotronics_Concept_Source_Paper.md](Duotronics_Concept_Source_Paper.md) - early concept material.
- [ROADMAP.md](ROADMAP.md) - phase structure and program evolution.
- Root chapter exports and draft math materials - bounded research workbook inputs retained as source context.

## Reading Paths By Role

### If you are a strategist, reviewer, or program lead

Read in this order:

1. This README
2. [START_HERE_v1_6_draft_3_rc_closure.md](build_docs/witness_contract/v1.6%20-%20Draft%203/START_HERE_v1_6_draft_3_rc_closure.md)
3. [duotronic_program_charter_v1_6.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_program_charter_v1_6.md)
4. [RC_BLOCKER_CLOSURE_MATRIX_v1_6_draft_3.md](build_docs/witness_contract/v1.6%20-%20Draft%203/RC_BLOCKER_CLOSURE_MATRIX_v1_6_draft_3.md)

### If you are focused on AI safety and governance

Read in this order:

1. [duotronic_witness_contract_v11_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_witness_contract_v11_0.md)
2. [duotronic_policy_engine_spec_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_policy_engine_spec_v1_0.md)
3. [duotronic_human_review_state_machine_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_human_review_state_machine_v1_0.md)
4. [duotronic_security_architecture_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_security_architecture_v1_0.md)
5. [duotronic_replay_package_spec_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_replay_package_spec_v1_0.md)

### If you are focused on cybernetics, memory, or cognition

Read in this order:

1. [duotronic_runtime_recurrence_complete_integration_document_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_runtime_recurrence_complete_integration_document_v1_0.md)
2. [duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_wgrnn_temporal_authority_runtime_contract_v1_1.md)
3. [duotronic_temporal_witness_and_absence_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_temporal_witness_and_absence_profile_v1_0.md)
4. [duotronic_multimodal_witness_runtime_profile_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_multimodal_witness_runtime_profile_v1_1.md)
5. [prototypes/wgrnn/README.md](prototypes/wgrnn/README.md)

### If you are focused on mathematics or formal systems

Read in this order:

1. [duotronic_polygon_family_calculus_v6_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_polygon_family_calculus_v6_0.md)
2. [duotronic_mathematical_canon_contract_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_mathematical_canon_contract_v1_0.md)
3. [duotronic_proof_and_conjecture_witness_contract_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_proof_and_conjecture_witness_contract_v1_0.md)
4. [duotronic_formal_semantics_and_verification_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_formal_semantics_and_verification_v1_0.md)
5. [formal/](build_docs/witness_contract/v1.6%20-%20Draft%203/formal/)

### If you are focused on data science or implementation

Read in this order:

1. [duotronic_conformance_test_suite_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_conformance_test_suite_v1_0.md)
2. [duotronic_database_schema_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_database_schema_v1_0.md)
3. [duotronic_api_contract_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_api_contract_v1_0.md)
4. [duotronic_sdk_and_openapi_integration_profile_v1_1.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_sdk_and_openapi_integration_profile_v1_1.md)
5. [executable/](build_docs/witness_contract/v1.6%20-%20Draft%203/executable/)

### If you are focused on transport or protocol engineering

Read in this order:

1. [duotronic_v1_6_distributed_self_governing_recurrent_network_addendum.md](build_docs/witness_contract/v1.6%20-%20Draft%203/duotronic_v1_6_distributed_self_governing_recurrent_network_addendum.md)
2. [refs/duotronic_dbp_inter_node_full_duplex_profile_v1_0.md](build_docs/witness_contract/v1.6%20-%20Draft%203/refs/duotronic_dbp_inter_node_full_duplex_profile_v1_0.md)
3. [duotronic-bus-protocol](https://github.com/theblobinc/duotronic-bus-protocol)

## Current Status And Non-Claims

The current active corpus is documentation-rich and implementation-facing, with
v1.6 Draft 3 bringing stronger closure on executable artifacts, conformance,
runtime boundaries, formalization planning, and migration readiness.

That said, this repository should still be read carefully:

- it is the authority for contracts and corpus, not a blanket claim that every
  runtime decision is final or production-certified;
- it separates verified capability from desired target capability;
- it expects implementations to emit evidence rather than rely on prose claims;
- it treats prototypes as research or proving assets unless explicitly promoted;
- it does not collapse governance into model output or transport success.

In short: Duotronics is ambitious, broad, and increasingly concrete, but it is
still intentionally explicit about what is specified, what is implemented, what
is verified, and what remains a target or future closure item.

## Contribution Guidance

If you are contributing to this repository:

1. Preserve the distinction between transport, semantic validity, canonical
   identity, and policy authority.
2. Do not introduce implicit state transitions where witness-bearing records are
   expected.
3. Prefer additive, replay-safe evolution over destructive semantic changes.
4. Update manifests, review notes, release notes, and conformance material when
   contracts change.
5. Keep security-sensitive behavior aligned with principal, mutation, and
   human-review controls.
6. Treat this repository as the semantics and conformance authority, even when
   companion runtimes evolve faster.

## License

MIT License. See [LICENSE](LICENSE).
