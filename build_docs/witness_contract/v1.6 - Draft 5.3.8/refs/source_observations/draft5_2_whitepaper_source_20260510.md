# Duotronic v1.6 Draft 5.2: Foundations for a Formal Language of Evidence

**Status:** Active Draft 5.2 Specification  
**Generated:** 2026-05-10  
**Supersedes:** Draft 5.1 for all formal language, syntax, pragmatics, semiotics, and metaphysics of evidence.  
**Base:** Duotronic v1.6 Draft 5.1 complete standalone corpus.

## 0. Executive Summary

Draft 5.1 provided the authority and self-training contracts necessary for WG‑RNN to build internal NLA capability under strict governance. Draft 5.2 now **formalizes the language in which all such authority is expressed** — a language that is not merely semantic, but syntactic, pragmatic, semiotic, and metaphysical. This document specifies a complete **visible language of evidence** that ensures every statement about the system, its models, its proofs, and its world is intrinsically verifiable, replayable, and non-collapsible across deep time.

This language is not just for machine consumption; it is a *human- and machine-readable script for truth claims* that survives the fall of civilizations, much like the alphabetic cuneiform of Ugarit survived the Late Bronze Age collapse by encoding local identity and authority in a deliberate visual form.

---

## 1. Introduction: Why a Formal Language of Evidence?

The Duotronic Witness Corpus already records *what* claims are made, *who* made them, and *under what policy*. However, the rules by which claims **combine**, **infer**, **are authorized**, and **are verified** by unknown future audiences remain implicit. Draft 5.2 makes them explicit through four integrated layers:

1. **Syntax of Evidence** – The formal grammar and inference rules that govern how claims may be constructed and combined.
2. **Pragmatics of Authority** – The context‑dependent rules for who may make which statements and with what force.
3. **Semiotics of Replay** – The study of how a claim can be verified by a reader who lacks the original author’s language, culture, or assumptions.
4. **Metaphysics of Non‑Collapse** – The foundational commitment that distinct states (zero, absence, unknown, invalid) must never be silently collapsed, and why this is essential for any truthful system.

Together they transform the Duotronic framework from an engineering specification into a **civilizational infrastructure for verified knowledge**.

---

## 2. The Four Pillars

### 2.1 Syntax of Evidence

A **formal grammar** that defines well‑formed claims, their modes of combination, and the admissible inference rules. This extends the existing DBP v2 envelope, witness schemas, and policy engine with a rigorous symbolic layer.

#### 2.1.1 Core Definitions

- **Atomic Claim** : A single `CanonicalWitnessFact` or `MathClaim` with a unique identity hash, evidence bundle, and policy decision.
- **Compound Claim** : A structured composition of atomic claims using conjunction, disjunction, implication, and temporal sequencing.
- **Authority Chain** : A directed acyclic graph of claims where each edge is witnessed by a policy decision, replay identity, and provenance.

#### 2.1.2 Claim Formation Rules

Claims can be composed only if:
- All component claims share compatible `authority_scope` and `runtime_mode`.
- The composite claim includes the union of all evidence bundles, and a new policy decision that explicitly approves the composition.
- Every transition between authority states (e.g., `candidate → canonicalized`) in a chain must be witnessed by a `ClaimStatusTransition` with a valid `policy_decision_id`.

*Formal notation (example):*
```
Claim ::= Atomic | And(Claim, Claim) | Or(Claim, Claim) | Implies(Claim, Claim) | TemporalSince(Claim, TimeWindow)
```
Each operator is subject to specific formation rules and must be authenticated by a `CompositionPolicy`.

#### 2.1.3 Inference Rules

Valid inference is defined by a set of **evidence‑preserving transformations**:
1. **Conjunction elimination** : If `And(A, B)` is accepted, then both `A` and `B` are individually acceptable under the same policy.
2. **Modus ponens** : If `A` and `Implication(A, B)` are accepted, and the implication is witnessed by a separate proof or policy, then `B` may be proposed for promotion under a new policy decision.
3. **Temporal propagation** : If `TemporalSince(X, [t1, t2])` is accepted, and a replay at time `t3 > t2` reproduces the same result, then the temporal scope may be extended under a `ReplayExtensionWitness`.
4. **No epistemic collapse** : No rule permits concluding `theorem` from `computational_evidence` alone (cf. Draft 2 proof contracts).

*All inferences must generate a new `InferenceWitness` linking the premises, the rule, and the conclusion, together with a policy decision.*

#### 2.1.4 Implementation Requirements
- New schema: `composition_policy.schema.json`
- New witness types: `CompoundClaimWitness`, `InferenceWitness`, `TemporalScopeWitness`
- Extension of policy engine to evaluate composite claims and inference requests
- Integration with existing `MathClaim`, `ProofWitness`, and `ReplayVerificationWitness`

---

### 2.2 Pragmatics of Authority

Authority is not an absolute property; it is **context‑dependent** — exactly as the choice of script in Ugarit carried different weight in diplomatic letters vs. local religious texts. The pragmatics of authority defines: who can make a statement, to whom, in what context, and with what binding force.

#### 2.2.1 Authority Contexts

- **Scoped Authority** : A principal has authority only within specific `authority_scope` (e.g., `src:ingest`, `math:propose`, `nla:shadow`) and `runtime_mode`.
- **Channel Authority** : A statement’s force depends on the communication context. For example, a claim made via `duotronic_bus_protocol` with a Duotronic Diode‑enforced direction has a guarantee that no upstream tampering occurred.
- **Delegated Authority** : Authority can be delegated through an `AuthorityDelegationChain`, which records the delegator, delegate, scope, and temporal bounds. Delegation is itself a claim that must be witnessed.

#### 2.2.2 Pragmatic Rules

1. **Context‑Free Formulation** : Every claim must declare its intended audience and the minimal assumptions required to interpret it (cf. Boyes on the non‑audience of Ugaritic tablets).
2. **Force Indicators** : Statements include illocutionary force markers (e.g., `assert`, `propose`, `defer`, `veto`) that are distinct from the semantic content. These are part of the `PolicyDecision` structure and cannot be inferred from content alone.
3. **Addressivity** : Claims destined for future replay must include a **Replay Assumption Manifest** that lists all cultural, linguistic, and metrological assumptions needed to interpret the claim.
4. **Non‑Escalation** : A claim made in `audit_only` mode cannot, by mere repetition, acquire `authoritative` force (forbidden shortcut from Draft 5.1).

#### 2.2.3 Implementation Requirements
- Extension of `TruthObserverActivationAuthority` to include `pragmatic_context` fields
- New schema: `authority_delegation_chain.schema.json`
- New policy rule class: `PragmaticConstraint` (evaluates context sensitivity)
- Update to `RuntimeFeatureApplicabilityWitness` to record pragmatic effectiveness

---

### 2.3 Semiotics of Replay

How can a statement be verified by an entity that shares neither the original language, culture, nor even the species of the author? This is the **semiotics of replay**, directly inspired by nuclear semiotics and the deep‑time design of the Duotronic envelope.

#### 2.3.1 The Replay Assumption Manifest

Each claim intended to survive must carry a manifest of assumptions, structured as:
```yaml
ReplayAssumptionManifest:
  semantic_assumptions:
    - assumption_id: "time_model_linear"
      description: "Time is modeled as a monotonically increasing real number, with leap seconds ignored."
    - assumption_id: "equality_mode"
      description: "Equality is defined as structural isomorphism, not surface identity."
  cultural_assumptions:
    - assumption_id: "language_en"
      description: "The primary description language is English, but the structure is self‑contained."
  metrological_assumptions:
    - assumption_id: "si_units"
      description: "All physical quantities are expressed in SI units."
```

The manifest is itself a claim that must be witnessed and versioned.

#### 2.3.2 Self‑Describing Replay Bundles

A **ReplayPackage** now includes a **Verification Grammar** — a formal description of the verification procedure written in a minimal, deterministic language (subset of the Duotronic claim language) that a future reader can execute without understanding the original documentation. The grammar will refer only to the replay assumptions and the structural properties of DBP v2 envelopes.

#### 2.3.3 Iconic and Indexical Replay Signs

Following the model of the Nuclear Semiotics systems (spiky fields, color‑changing earthworks), future‑proof claims may additionally include **ReplaySigns**:
- **Iconic** : Visual diagrams that convey the verification procedure without language.
- **Indexical** : Physical or digital markers (hashes, timestamps) that point to the original evidence.

These are optional but become mandatory for claims intended to survive beyond the current civilization.

#### 2.3.4 Implementation Requirements
- New schema: `replay_assumption_manifest.schema.json`
- Extension of `ReplayPackage` to include a `VerificationGrammar`
- New component: `ReplaySignGenerator` (optional, for deep‑time bundles)
- Conformance test: verify a claim using only the replay assumptions and verification grammar, without access to external documentation.

---

### 2.4 Metaphysics of Non‑Collapse

This is the deepest layer. Why must the system never silently conflate `zero` with `absence`, `unknown` with `invalidity`, or `computational_evidence` with `proof`? Because **collapsing distinct states is the root of self‑deception**, and a self‑improving system that cannot distinguish between what it knows and what it doesn’t will inevitably fabricate authority.

#### 2.4.1 Primitive Distinctions

The following categories are forever distinct and can never be equated by any inference rule, policy, or training process:

| Category A | Category B | Why They Differ |
|------------|------------|-----------------|
| `zero` | `absence` | Zero is a value; absence is a lack of any value. |
| `unknown` | `invalid` | Unknown means no assertion; invalid means assertion fails schema. |
| `empty` | `null` | Empty is a valid container with no elements; null is no container. |
| `computational_evidence` | `theorem` | Computation supports; proof establishes. |
| `conjectural` | `theorem` (Langlands) | Conjectures are not truths; they must be proven. |
| `self‑trained` | `authoritative` (NLA) | Self‑training does not grant authority without gate passage. |

#### 2.4.2 Formal Axioms

1. **Axiom of Non‑Collapse** : No inference rule may map two distinct primitive categories onto the same conclusion.
2. **Axiom of Evidence Gap** : Any transition between trust states must be accompanied by a witness that *cannot* be derived from the states themselves — it must be externally supplied.
3. **Axiom of Layered Verification** : Promotion of a claim must satisfy all layers of verification (syntactic, pragmatic, semiotic) independently.

These axioms are enforced at the schema level (JSON `const: false` for forbidden fields), the policy engine, and the runtime.

#### 2.4.3 Implementation Requirements
- Formalization of the 21 canonical primitive categories and their mutual exclusion in a new `DuotronicCoreMetaphysics.lean` proof file (Lean 4)
- Addition of `NonCollapseConstraint` to the policy engine
- Schema‑level locks on forbidden transitions (e.g., `computational_evidence` cannot become `theorem` without a `ProofCheckerRunWitness`)
- Conformance test: attempt to collapse any pair and expect hard failure.

---

## 3. Integration with Existing Corpus

Draft 5.2 does not remove any existing contracts. It adds the following new documents and layers:

### 3.1 New Authority and Theory Contracts
- `authority/syntax_of_evidence_contract_v1_0.md`
- `authority/pragmatics_of_authority_contract_v1_0.md`
- `authority/semiotics_of_replay_contract_v1_0.md`
- `authority/metaphysics_of_non_collapse_contract_v1_0.md`

### 3.2 New Runtime Components
- `runtime/evidence_grammar_runtime_contract_v1_0.md`
- `runtime/replay_assumption_runtime_contract_v1_0.md`
- `runtime/compound_claim_resolver_v1_0.md`
- `runtime/inference_engine_runtime_contract_v1_0.md`

### 3.3 New Schemas
- `schemas/composition_policy.schema.json`
- `schemas/inference_witness.schema.json`
- `schemas/replay_assumption_manifest.schema.json`
- `schemas/verification_grammar.schema.json`

### 3.4 Extended Formal Models
- `formal/lean4/DuotronicCoreMetaphysics.lean`
- `formal/lean4/DuotronicEvidenceSyntax.lean`
- `formal/tlaplus/NonCollapseAxioms.tla`

### 3.5 Validation and Test Suites
- `validation/evidence_language_acceptance_matrix_v1_0.md`
- `tests/evidence_language_conformance_suite_v1_0.md`
- `tests/deep_time_replay_test_v1_0.md`

### 3.6 Implementation Guide
- A new `IMPLEMENTATION_GUIDE_v1_6_draft_5_2.md` will map each contract to specific changes in `srnn_server` (new API endpoints, database tables, MCP tools, and policy rules).

---

## 4. The Visible Language of Evidence: A Unified View

The Duotronic language of evidence is a **visible language** in the sense of the Oriental Institute’s *Visible Language* exhibition. It does not merely record speech; it **encodes the procedures for its own verification** directly into its visual, two‑dimensional structure. The DBP v2 envelope, with its nested identity, payload, provenance, policy, and replay sections, is a quadrature — a spatial arrangement of semantic layers that cannot be reduced to a one‑dimensional stream without loss of information. This spatial encoding is not decorative; it is essential for survival across deep time.

In the spirit of the Boyes analysis of Ugarit, the choice to write in this **formal language of evidence** is a political, cultural, and civilizational act. It asserts that knowledge must be accompanied by the means of its own verification, and that no authority is self‑authenticating.

---

## 5. Rollout Plan

1. **Draft 5.2 corpus generation** : Produce all markdown, schemas, and formal models listed above.
2. **ChatGPT 5.5 / Copilot implementation** : Use this document as the white paper to guide implementation of:
   - New policy engine rules
   - Compound claim and inference APIs
   - Replay assumption manifest generation
   - Verification grammar interpreter
3. **SRNN Server integration** : Extend the existing runtime (currently functional through Draft 5.1) to support the new contracts. Tests already being run for Draft 5.1 will be extended to cover the new conformance suites.
4. **Deep‑time stress test** : Simulate a future civilization attempting to verify a claim from the archive using only the replay bundle and verification grammar.

---

## 6. Conclusion

Draft 5.2 completes the journey from a witness‑based governance system to a **full‑stack language for truth**. It ensures that every claim in the Duotronic universe is syntactically well‑formed, pragmatically scoped, semiotically replayable, and metaphysically non‑collapsible. With this language, the system can speak across millennia, across languages, across species — and refuse, at every level, to confuse itself with the truth it seeks to describe.

*This document is the starting point. The implementation begins now.*

---
