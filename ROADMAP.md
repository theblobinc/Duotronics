# Duotronics Roadmap

## Vision
Build a rigorous, falsifiable, and implementation-ready Duotronics stack that:
1. runs on classical binary hardware first,
2. maps cleanly to quantum-compatible execution models,
3. preserves Duotronic semantics (`empty`, `unknown`, `zero`) and provenance,
4. eventually informs purpose-built Duotronic hardware.

This roadmap treats Duotronics as a **semantic + operator + validation architecture** first, then a hardware architecture.

---

## North-star outcomes

### Outcome A — Semantic correctness
- No silent coercion of `unknown` to numeric values.
- Every derived quantity carries provenance (`depends_on`, assumptions, confidence).
- Mapping policy changes (including offset conventions) are versioned and migration-safe.

### Outcome B — Cross-platform executability
- Identical reference workloads execute under:
  - a binary backend,
  - a quantum-simulation backend,
  - selected real quantum hardware targets (when practical).
- Cross-backend agreement is measured by witness suites with explicit tolerances.

### Outcome C — Unified representational layer
- Polygon packaging supports both digital and analogue-like observables through a common schema.
- Heterogeneous data (symbolic, numeric, sampled signals, constrained physical values) map to a single coherent state model.

### Outcome D — Hardware readiness
- By the time hardware design begins, the methodology has stable operator contracts, benchmark suites, and migration protocols.

---

## Guiding principles
1. **Gate-first development**: no feature without at least one corresponding witness gate.
2. **Version everything**: schemas, policies, operators, and benchmark suites.
3. **Backend neutrality**: define semantics independent of execution substrate.
4. **Reproducibility over novelty**: prioritize replayable runs and falsification.
5. **Hardware-last discipline**: defer custom hardware until software semantics are stable.

---

## Phased roadmap

## Phase 0 (0–2 months): Foundation hardening
**Goal:** convert current workbook guidance into enforceable implementation contracts.

### Deliverables
- Canonical schema package (`state`, `polygon`, `catalog_entry`, `witness_result`).
- Formal status lattice for values:
  - `known`,
  - `unknown`,
  - `conditional`,
  - `structurally_absent`.
- Offset-policy registry with explicit policy IDs and migration notes.
- Minimal “truth procedure” spec (what counts as supported claim vs unsupported claim).

### Exit criteria
- CI can validate schema conformance and reject unknown-coercing operators.
- At least 3 hard witnesses:
  - unknown-propagation witness,
  - offset-consistency witness,
  - canonicalization idempotence witness.

---

## Phase 1 (2–5 months): Binary reference engine (authoritative implementation)
**Goal:** establish the classical baseline where correctness is easiest to debug.

### Deliverables
- Reference runtime in a stable systems language (or mixed stack) with:
  - operator interface contracts,
  - deterministic execution mode,
  - structured provenance capture.
- Catalog generation and replay tooling.
- Scorecard engine with gate-first ranking.
- Benchmark packs:
  - tiny sanity,
  - medium regression,
  - stress/invalidation.

### Truth-procedure implementation (v1)
Define machine-checkable truth states for any claim:
- `validated`: passes required witnesses under declared regime/tolerance,
- `conditionally_valid`: passes under explicit assumptions,
- `falsified`: fails any hard gate,
- `unresolved`: insufficient evidence.

### Exit criteria
- Full deterministic replay from config + seed + version hash.
- All v1 claims machine-labeled by truth state.
- Regression suite stable for 4 consecutive weeks.

---

## Phase 2 (5–9 months): Dual-mode representation (digital + analogue inputs)
**Goal:** make polygon packaging truly multimodal while preserving semantic rigor.

### Deliverables
- Encoding spec for heterogeneous measurements into polygon/state fields:
  - discrete symbols,
  - sampled continuous signals,
  - uncertainty intervals/distributions,
  - physical constraints.
- Quantization/normalization policies with reversible transforms where possible.
- Information-density diagnostics (how much uncertainty/compression each encoding adds).

### Core method
Represent each embedded datum as:
- value representation,
- uncertainty representation,
- provenance representation,
- transform-chain representation.

This preserves the “infinite complexity in principle, bounded by quantifiable information in practice” idea without overclaiming physical infinity.

### Exit criteria
- Mixed-input benchmark suite runs end-to-end.
- Witness shows no loss of unknown/conditional semantics through encoding pipeline.

---

## Phase 3 (9–14 months): Quantum compatibility layer
**Goal:** run Duotronic operators on quantum-compatible abstractions while preserving semantics.

### Deliverables
- Intermediate Representation (IR) for operators and state transforms, backend-agnostic.
- Binary backend adapter (reference) + quantum-simulation adapter.
- Mapping guide from Duotronic operators to quantum primitives:
  - unitary-compatible pieces,
  - variational workflows,
  - measurement/post-processing semantics.
- Noise-aware witness extensions for quantum runs.

### Hard problem policy
If a semantic cannot be represented natively in quantum execution (e.g., unknown/conditional provenance), it must be handled by explicit side-channel metadata rather than silently dropped.

### Exit criteria
- Agreement reports between binary and quantum-sim backends across shared suites.
- Published tolerance envelopes for expected divergence under noise.

---

## Phase 4 (14–20 months): Cross-backend verification and scale
**Goal:** prove that the method is substrate-portable and operationally useful.

### Deliverables
- Cross-backend conformance suite:
  - binary,
  - quantum simulator,
  - optional real-QPU test lane.
- Pareto dashboards for accuracy/stability/cost/runtime.
- Drift and migration tooling for long-lived catalog epochs.

### Exit criteria
- Stable cross-backend trend reports.
- Automated invalidation sweep when policies/operators change.
- Clear “best variant by workload class” selections.

---

## Phase 5 (20+ months): Duotronic hardware architecture program
**Goal:** begin hardware co-design only after semantic and operator stability is demonstrated.

### Workstreams
1. **Requirements extraction**
   - operator kernels most worth acceleration,
   - memory/provenance access patterns,
   - precision and noise budgets.
2. **Candidate substrates**
   - multi-level cell / analogue-mixed architectures,
   - photonic or memristive concepts,
   - hybrid control planes.
3. **Compiler/runtime co-design**
   - map IR to hardware instructions,
   - preserve provenance and truth-state outputs.

### Exit criteria
- Hardware feasibility document tied to measured software bottlenecks.
- Prototype emulation layer demonstrating speed/energy hypotheses before fabrication.

---

## Truth-framework architecture (concise)

Each claim must specify:
- regime,
- observable,
- tolerance,
- required witnesses,
- backend context.

Evaluation pipeline:
1. Parse claim spec.
2. Execute required witnesses.
3. Aggregate evidence with gate-first logic.
4. Emit truth state + counterexamples + provenance bundle.

This is the formal mechanism for “logical procedures for determining truth.”

---

## Minimum tooling plan

- `duo-schema`: schema + versioning tools.
- `duo-catalog`: polygon catalog generation + canonicalization.
- `duo-ops`: operator library and IR exporters.
- `duo-runner`: backend execution harness.
- `duo-witness`: witness engine.
- `duo-score`: ranking/pareto/trend reports.
- `duo-migrate`: schema/policy/epoch migration assistant.

---

## Risks and mitigations

### Risk: semantic drift
- **Mitigation:** mandatory migration witnesses and policy IDs.

### Risk: “infinite complexity” interpreted as unbounded precision claims
- **Mitigation:** separate representational richness from measurable information bounds.

### Risk: backend mismatch (binary vs quantum)
- **Mitigation:** IR-first architecture and explicit tolerance envelopes.

### Risk: premature hardware focus
- **Mitigation:** enforce Phase 5 entry gate requiring stable software evidence.

---

## First 6 execution sprints (2 weeks each)

1. **Sprint 1:** finalize schema v0 + status lattice + validation CLI.
2. **Sprint 2:** implement unknown-propagation and offset witnesses.
3. **Sprint 3:** deterministic binary runner + provenance output.
4. **Sprint 4:** scorecard and truth-state classifier (`validated`, `conditional`, `falsified`, `unresolved`).
5. **Sprint 5:** mixed digital/analogue encoding prototype + diagnostics.
6. **Sprint 6:** operator IR draft + binary adapter proof-of-concept.

At Sprint 6 close, hold a roadmap review with hard go/no-go gates for quantum layer start.

---

## Definition of success (program level)

You are “moving in the right direction” when:
- the same claim can be replayed and independently re-verified,
- uncertainty is represented explicitly instead of erased,
- variants are compared by evidence, not narrative,
- backend differences are quantified rather than ignored,
- hardware decisions are derived from measured bottlenecks and stable semantics.
