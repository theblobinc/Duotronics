# Perceptual Interfaces for Symbolic Computation:  
## A Reference Architecture with Perceptual Symbolic Interface Implementation

**Version 3.5 – Realism on Bandwidth, Confidence‑Aware Mapping, Walk‑Up‑And‑Use Familiarization, and Sharper Evaluation**  
**License:** MIT (see Appendix A)  
**Date:** July 2026  
**Status:** Comprehensive engineering architecture and research blueprint. Distinguishes reusable architecture from reference implementation.

---

## Abstract

We propose **perceptual interfaces for symbolic computation**-a new interface category that translates the internal state of formal verification and symbolic reasoning engines into continuous, perceivable sensory streams. Unlike physical sensors that expose temperature, pressure, or light, symbolic engines expose computational quantities: proof state, satisfiability, consistency, ambiguity, contradiction, and completeness. These are not physical quantities but abstract properties of formal systems, and they have not previously been treated as candidates for direct perceptual encoding. This document presents a reference architecture organized around an explicit **Symbolic State Abstraction Layer (SSAL)** that decouples symbolic computation from perceptual rendering, making the architecture reusable across verifiers, modalities, and domains. We provide a formal model of symbolic state vectors separated into formal, epistemic, and meta‑state; an information‑theoretic analysis of channel capacity; a phased implementation roadmap; and a thorough treatment of human factors, training, and ethical risks. A reference implementation, **Perceptual Symbolic Interface**, instantiates the architecture as a haptic wristband, but the broader contribution is the architectural pattern itself. All cognitive benefit claims are presented as testable hypotheses, not established findings. The work is grounded in HCI, sensory substitution, and formal methods, and is intended as a systems‑engineering foundation for building and evaluating perceptual interfaces to symbolic reasoning.

---

## Executive Summary

**Core Contribution:** A reference architecture for **perceptual interfaces to symbolic computation**-systems that encode the state of formal reasoning engines into sensory patterns that users are hypothesized to learn to interpret as a peripheral awareness of logical structure.

**Why Symbolic Computation Needs Its Own Perceptual Interface:**
Physical sensors (thermometers, cameras, microphones) expose physical quantities. Symbolic engines (theorem provers, model checkers, SMT solvers, rule engines) expose a different class of information: proof existence, contradiction, satisfiability, ambiguity, completeness, and formal consistency. These are computational, not physical, properties. They have traditionally been accessed only through text-requiring conscious, focused attention. We argue that this class of information is sufficiently distinct, structured, and high‑value to warrant its own perceptual interface design patterns, analogous to how graphical user interfaces emerged for spatial and visual computation.

**The Architecture (Four Layers):**
1. **Symbolic Computation Layer:** Formal verification engines (Lean, Z3, TLA⁺) or rule engines.
2. **Symbolic State Abstraction Layer (SSAL):** Decouples computation from rendering. Produces a standardized state vector with separate formal, epistemic, and meta‑state components.
3. **Perceptual Encoding Layer:** Compresses the state vector into a codebook of sensory prototypes, optimized for the target modality.
4. **Modality Rendering Layer:** Delivers the encoded patterns through haptics, audio, visual overlays, or embedded content.

**Reference Implementation (Perceptual Symbolic Interface):** A haptic wristband instantiating the architecture. Includes a lite mode for walk‑up‑and‑use utility (sub‑minute familiarization) and an optional progressive curriculum.

**Key Features:**
- **Architecture‑first, implementation‑second:** The SSAL and encoding principles apply to any symbolic engine and any sensory modality.
- **Walk‑up‑and‑use utility:** Lite mode requires only brief familiarization, not extended training.
- **Deterministic anchor:** Fail‑closed verification backend with cryptographic provenance.
- **Closed‑loop:** User corrections feed back into the symbolic engine.
- **Empirically grounded evaluation plan:** All benefit claims are testable hypotheses.

**Maturity:** Phase 1 prototypes feasible within months for domain‑specific corpora (Rust type safety, medical guidelines). Open‑domain verification is a longer‑term research goal.

---

## 1. Introduction

Human reasoning is remarkably flexible but struggles to sustain high‑precision, contradiction‑free inference over extended chains. Formal verification tools-theorem provers, model checkers, SAT/SMT solvers-can produce sound proofs within their formal assumptions, but their output is typically text, isolated from our moment‑to‑moment perceptual experience. Sensory substitution research has demonstrated that the brain can learn to interpret novel sensory patterns as meaningful information: for example, converting camera images into soundscapes [1] or tactile vocoders for speech [2]. This raises a question: can we apply that same principle to the output of formal reasoning, delivering verification results not as text to be read, but as patterns to be felt or heard?

This paper proposes a new interface category: **perceptual interfaces for symbolic computation**. We argue that symbolic engines-theorem provers, model checkers, SMT solvers, rule engines, and formal knowledge bases-produce a class of information that is qualitatively different from physical sensor data. Physical sensors expose temperature, pressure, light, and sound. Symbolic engines expose proof state, satisfiability, consistency, ambiguity, contradiction, and completeness. These are computational, not physical, properties. They are structured, deterministic, and often high‑stakes. Yet they have traditionally been accessed only through text, requiring conscious, focused attention to interpret. We propose that this class of information is sufficiently distinct and valuable to warrant its own perceptual interface design patterns, analogous to how graphical user interfaces emerged for spatial and visual computation, or how auditory displays emerged for sonification of physical data.

The contribution of this paper is a **reference architecture** for building such interfaces. The architecture is organized around a central abstraction-the **Symbolic State Abstraction Layer (SSAL)**-that decouples the symbolic computation engine from the perceptual rendering. This decoupling makes the architecture reusable: the same state abstraction can feed a haptic wristband, an audio display, a visual overlay, or an augmented reality interface. The same encoding principles apply whether the underlying engine is a theorem prover, a type checker, a model checker, or a medical rule engine.

We present a reference implementation, **Perceptual Symbolic Interface**, as a haptic wristband that instantiates the architecture. The design is inspired by the concept of a **deterministic anchor** from the Duotronics Framework [3]-an external invariant reference hypothesized to stabilize high‑precision processing. However, this document does not depend on the biological claims of that framework. Instead, we use it as an engineering heuristic: the anchor should be fail‑closed, low‑entropy, and capable of continuous, rapid updates. Our central engineering claim is that formal verification output can be encoded as a **perceptual channel**-a source of peripheral awareness of the state of a symbolic reasoning process-rather than remaining merely a software tool that produces text.

This document is an engineering architecture and research blueprint. It aims to provide sufficient detail for a team to build, test, and iterate a prototype that instantiates the architecture, while keeping the architecture itself general enough to apply beyond any single implementation. We ground the work in HCI, extended cognition, and sensory substitution. We define the SSAL and the formal, epistemic, and meta‑state components of the symbolic state vector. We analyze perceptual channel capacity with explicit information loss and uncertainty propagation. We detail a phased roadmap with error budgets and latency distributions. We explore human factors, accessibility, and error taxonomy. All cognitive benefit claims are stated as testable hypotheses, and we provide an evaluation plan to test them.

### 1.1 Scope and Limitations

Perceptual Symbolic Interface is **not** a general truth‑detector. It communicates the state of a deterministic reasoning process operating over a specific formal corpus and formalization. Its reliability is bounded by the completeness of the corpus, the correctness of the formalization, and the latency of claim extraction. We openly acknowledge that open‑domain, real‑time verification of arbitrary natural language remains a hard research problem and is addressed only in our most exploratory phase (Phase 3). The immediate, buildable system targets structured, domain‑specific inputs such as code, medical checklists, and formal contracts.

### 1.2 Epistemological Stance

Throughout this document, we distinguish between:
- **Engineering architecture:** the reusable structure of the system (SSAL, encoding layer, modality rendering).
- **Design objectives:** properties we aim to achieve (e.g., reduced task completion time with the interface).
- **Testable hypotheses:** claims about user behavior or cognition that can be evaluated experimentally (e.g., "lite mode users will detect contradictions faster than unaided users").
- **Established findings:** statements supported by cited literature.
- **Reference implementation details:** specifics of Perceptual Symbolic Interface that instantiate but do not define the architecture.

Where the text states that a benefit "is expected" or "is hypothesized," we are making a prediction to be tested, not a claim of demonstrated fact.

### Notation Table

| Symbol | Meaning |
|--------|---------|
| \(S\) | Symbolic state vector from SSAL |
| \(S_{\text{formal}}\) | Formal state: validity, proof depth, conflict count, conflict type |
| \(S_{\text{epistemic}}\) | Epistemic state: parser confidence, formalization confidence, solver confidence |
| \(S_{\text{meta}}\) | Meta‑state: novelty, ambiguity, temporal change, resource limit |
| \(H\) | Sensory parameter space (ideal output from encoder) |
| \(\hat{H}\) | Percept as actually received by the user (after hardware and perceptual channel) |
| \(M\) | Encoding mapping \(M: S \rightarrow H\) |
| \(A = (D, W, C, T, P)\) | Deterministic anchor (engine, witness, consistency, temporal stability, provenance) |
| \(I(X;Y)\) | Mutual information between \(X\) and \(Y\) |
| \(L\) | Conditional entropy \(H(S|\hat{H})\): remaining uncertainty after perception |
| \(R\) | Operational evaluation metric (weighted combination of NASA‑TLX, time, error rate) |

### Explicit Assumptions

1. **Trusted verifier:** The verification engine (e.g., Lean, Z3) correctly implements its formal semantics and is not compromised.
2. **Trusted corpus:** The formal knowledge base is cryptographically signed and has not been tampered with.
3. **Bounded latency:** For domain‑specific corpora in Phase 1, end‑to‑end latency is <20 ms; for later phases, latency is bounded but may be larger.
4. **Successful claim extraction:** In Phase 1, the restricted‑grammar parser extracts claims without semantic distortion; in later phases, extraction errors are treated as uncertainty.
5. **Calibrated user perception:** With appropriate familiarization (or in lite mode), we hypothesize users can achieve the discrimination thresholds assumed in the bandwidth analysis. This is a testable hypothesis.
6. **Local processing integrity:** All sensitive data is processed on‑device; remote corpus updates are verified before use.
7. **Closed‑loop stability:** We assume the user is rational and will eventually correct errors upon receiving a reliable INVALID signal; the system is designed to not induce oscillation. This is a design assumption to be validated.

---

## 2. Related Work and Foundations

### 2.1 Human Perceptual Interfaces for Symbolic Systems

The idea of representing abstract information through sensory displays is central to several HCI traditions. **Calm technology** [4] and **ambient displays** [5] propose that information can be conveyed through subtle, peripheral stimuli (light, sound, vibration) that do not demand focal attention. **Ecological interface design** [6] emphasizes making constraints and affordances directly perceivable. Our approach extends these concepts to the domain of formal reasoning: we aim to make logical validity, consistency, and proof depth as perceivable as the color of a traffic light.

**Peripheral interaction** [7] aims for background processing of information; the haptic stream from Perceptual Symbolic Interface is designed to be monitored with low attentional demand, rising to focal attention only when anomalies occur. This aligns with the concept of **cognitive prostheses** [8]-external devices that extend human cognitive capacities by providing continuous feedback hypothesized to become integrated into the user's cognitive loop.

**Cognitive load theory** [9] predicts that offloading reasoning to an external channel can free up working memory. By translating symbolic checks into sensory patterns, we aim to reduce the burden of constantly re‑verifying mental models, keeping visual and linguistic channels free for other tasks. Whether this offloading actually occurs is a central empirical question for the evaluation plan (Section 15).

**Embodied cognition** [10] and **active perception** [11] frameworks further suggest that perception and action are tightly coupled; rhythmic haptic feedback may create an "embodied" understanding of formal structure, not unlike how musicians feel meter. This is a motivating analogy, not a proven mechanism.

### 2.2 Sensory Substitution and Perceptual Learning

Sensory substitution devices (SSDs) are the closest technological analogs. The vOICe system converts visual images into complex soundscapes, and experienced users report a form of "visual" experience [12]. BrainPort uses an electrotactile tongue display to convey visual information [13]. These devices demonstrate that the brain can adapt to entirely novel sensory mappings when the signal is consistently coupled with task‑relevant information. We hypothesize that symbolic information-validity, confidence, novelty-can be similarly encoded and learned.

Perceptual learning research [14] shows that with repeated exposure, discrimination of fine sensory differences improves dramatically. This underpins our training curriculum: we predict users will progress from simple to complex mappings, gradually building a sensory vocabulary. However, individual variability is high; not all users will achieve expert‑level discrimination, and we therefore design the system with a "lite mode" that requires only brief familiarization and is intended to provide immediate utility.

### 2.3 Extended and Distributed Cognition

Extended mind theory [15] and distributed cognition [16] argue that cognitive processes routinely span brain, body, and external artifacts. Perceptual Symbolic Interface is designed to act as a **cognitive artifact** that externalizes the results of formal reasoning, making them available to perception. Unlike a screen that requires reading, a sensory stream is hypothesized to be processed peripherally, freeing up visual and linguistic resources.

### 2.4 Formal Verification and Symbolic AI

Formal verification tools (Lean [17], Coq [18], Isabelle [19], Z3 [20], TLA⁺ [21]) can produce deterministic, witnessed judgments about logical statements, program correctness, and system behavior. However, their output is typically textual, requiring focused interpretation. Recent work on neuro‑symbolic AI [28, 29] and AI‑assisted programming (e.g., GitHub Copilot) does not address the perceptual delivery of verification results. Our contribution is to bridge formal methods and perceptual interfaces, treating the verifier as a continuous sensor rather than a batch tool.

### 2.5 Why Symbolic Computation Deserves Its Own Perceptual Interface

Physical sensors expose physical quantities: thermometers expose temperature, cameras expose light, microphones expose sound. These quantities are continuous, noisy, and governed by physical law. Symbolic engines expose a qualitatively different class of information:

- **Proof state:** Does a formal proof exist for a given claim?
- **Satisfiability:** Is a set of constraints mutually consistent?
- **Contradiction:** Has a logical inconsistency been detected?
- **Ambiguity:** Are there multiple competing formal interpretations of the same input?
- **Completeness:** Does the formal corpus cover all relevant cases?
- **Consistency:** Are all assertions in a knowledge base mutually compatible?

These are not physical quantities. They are discrete, structured, deterministic (relative to a formal system), and often high‑stakes. They have traditionally been accessed only through text-requiring conscious, sequential, effortful interpretation. We argue that this class of information is sufficiently distinct and valuable to warrant its own perceptual interface design patterns. This is analogous to how graphical user interfaces emerged as a distinct interface category for spatial and visual computation, or how auditory displays emerged for sonification of physical data streams. The reference architecture presented here is a first step toward establishing design patterns for this new category.

### 2.6 Positioning of Perceptual Symbolic Interface

The table below positions the proposed interface category relative to existing systems:

| System | Information Type | Perceptual Channel? | Continuous? | Deterministic? | Training | Bandwidth |
|--------|-----------------|---------------------|-------------|----------------|----------|-----------|
| IDE warnings | Textual symbolic | No (text) | No | Partial | Low | Low |
| Compiler errors | Textual symbolic | No (text) | No | Yes (text) | Low | Low |
| Vibration notifications | Simple discrete | Yes (haptic) | Yes | No | Low | Very Low |
| Sensory substitution (vOICe) | Physical (visual→audio) | Yes | Yes | No | High | High |
| **Perceptual interface to symbolic computation (Perceptual Symbolic Interface)** | **Computational symbolic** | **Yes** | **Yes** | **Yes** | **Configurable** | **Moderate** |

### 2.7 Design Objectives

The following table articulates our design objectives. All Perceptual Symbolic Interface performance claims are hypotheses to be tested, not demonstrated facts.

| Feature | Unaided Human | Traditional IDE/Tool | Perceptual Symbolic Interface (Design Objective) |
|---------|---------------|----------------------|-------------------------------|
| Verification mode | Conscious, sequential, effortful | On‑demand, textual, focused | Peripheral, continuous, low‑attention (hypothesized) |
| Attention required | High | High (reading) | Low (separate channel) (design objective) |
| Feedback latency | Seconds–minutes | Seconds (compile) | Milliseconds (real‑time) |
| Proof witness | Internal (mental model) | On error/request | Continuously available on tap |
| Works while reading/coding | Distracting | Distracting (context switch) | Does not compete with vision (vibrotactile) |
| Continuous monitoring | No (only when actively checking) | No (batched) | Yes (ambient stream) |
| Cognitive offload | None | Partial (must interpret text) | Hypothesized: externalized to peripheral perception |

---

## 3. The Four-Layer Reference Architecture

The core contribution of this paper is a **four‑layer reference architecture** for perceptual interfaces to symbolic computation. The layers are:

1. **Symbolic Computation Layer:** The formal verification engine, theorem prover, model checker, rule engine, or knowledge base that produces judgments about claims.
2. **Symbolic State Abstraction Layer (SSAL):** A standardized, engine‑agnostic representation of the symbolic computation's output. This layer decouples the computation from the rendering, making the architecture reusable.
3. **Perceptual Encoding Layer:** Compresses the SSAL state vector into a codebook of sensory prototypes, optimized for the target modality and the user's perceptual capabilities.
4. **Modality Rendering Layer:** Delivers the encoded patterns through haptics, audio, visual overlays, or embedded content.

```
┌────────────────────────────────────────────────────┐
│              USER CONTENT (text, code, speech)       │
└──────────────────────┬─────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────┐
│   LAYER 1: SYMBOLIC COMPUTATION                     │
│   (Lean, Z3, TLA+, rule engines, knowledge bases)   │
│   • Deterministic or probabilistic reasoning        │
│   • Produces raw judgments, proofs, counterexamples  │
└──────────────────────┬─────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────┐
│   LAYER 2: SYMBOLIC STATE ABSTRACTION (SSAL)        │
│   • Engine‑agnostic state vector S                  │
│   • Separates formal, epistemic, meta‑state         │
│   • Normalizes across verifier types                │
│   • Attaches provenance metadata                    │
└──────────────────────┬─────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────┐
│   LAYER 3: PERCEPTUAL ENCODING                      │
│   • Vector quantization into prototype codebook     │
│   • Adaptive compression based on state frequency   │
│   • Uncertainty‑preserving mapping                  │
│   • Personalization via implicit feedback           │
└──────────────────────┬─────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────┐
│   LAYER 4: MODALITY RENDERING                       │
│   • Haptic (wristband, phone vibration)             │
│   • Visual (screen overlay, AR glasses, icon glow)  │
│   • Audio (earcons, spatial audio, sonification)    │
│   • Embedded (feed annotation, search highlighting) │
└──────────────────────┬─────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────┐
│   USER PERCEPTION & ACTION (correction, query)       │
└──────────────────────┬─────────────────────────────┘
                       ▼
              (loop back to Layer 1 or Content)
```

This architecture is the reusable contribution. Perceptual Symbolic Interface is one reference implementation that instantiates it as a haptic wristband, but any symbolic engine and any sensory modality can be substituted. The SSAL is the critical abstraction that enables this generality.

---

## 4. The Deterministic Anchor

Before defining the SSAL in detail, we establish the properties required of the symbolic computation layer. A **deterministic anchor** is a symbolic engine that serves as a trustworthy, continuous source of verification state.

### 4.1 Formal Definition

A **deterministic anchor** is a tuple \(A = (D, W, C, T, P)\) where:
- \(D\): a deterministic verification engine that, given a formal claim \(\phi\) and a corpus \(K\), produces a result \(r \in \{\text{VALID}, \text{INVALID}, \text{UNKNOWN}, \text{PENDING}\}\).
- \(W\): a witness function that provides a verifiable artifact for any \(r \in \{\text{VALID}, \text{INVALID}\}\) (e.g., a proof or a counterexample). \(W\) is total on these outputs.
- \(C\): a consistency contract ensuring that the system never simultaneously claims \(\phi\) is VALID and \(\phi\) is INVALID for the same \(K\).
- \(T\): a temporal stability property requiring that if \(K\) is unchanged, \(D(K, \phi)\) yields the same result over repeated queries.
- \(P\): **provenance metadata** recording corpus version, cryptographic signatures, source provenance, and timestamp.

**Informally:** A deterministic anchor is a computation whose output is reproducible, auditable, and externally verifiable. You can trust its output not because it is infallible, but because it is transparent: every result comes with a witness that can be independently checked.

**Properties:**
- **Reproducibility:** \(\forall \phi, K\), \(D(K,\phi)\) is deterministic.
- **Witness completeness:** If \(D(K,\phi) \in \{\text{VALID}, \text{INVALID}\}\), then \(W\) produces a checkable artifact.
- **Fail‑closed behavior:** If the engine cannot reach a conclusion within a bounded time or detects a resource limit, it returns PENDING or UNKNOWN, never a guess.
- **Monotonicity (corpus growth):** For a growing \(K\) (only adding true statements), a VALID result remains VALID, and an INVALID result remains INVALID, unless the claim is retracted.
- **Provenance integrity:** \(P\) is cryptographically bound to the result.

**Real‑world caveats:** In practice, SMT solvers and other tools frequently return UNKNOWN with no counterexample; the “resource limit” flag may trigger non‑deterministically depending on timing. The architecture accounts for this by mapping UNKNOWN to the UNCERTAIN intent class. The anchor’s guarantees hold only when the underlying engine provides them; the SSAL does not invent certainty where none exists. Moreover, epistemic confidences (especially `parser_confidence`) are estimates; calibrating them to match true error probabilities is a separate challenge, and over‑confidence in these numbers could lead to misplaced trust. The system mitigates this by making confidence transparent and inspectable.

This definition serves as the design contract for any symbolic engine plugged into Layer 1 of the architecture.

---

## 5. The Symbolic State Abstraction Layer (SSAL)

The SSAL is the central architectural innovation. It takes the raw output of any symbolic engine and produces a standardized, engine‑agnostic state vector that the perceptual encoding layer can consume. This decoupling is what makes the architecture reusable across engines and modalities.

### 5.1 The Three Components of Symbolic State

The SSAL organizes the verifier's output into three categories, reflecting a clean separation of concerns:

#### 5.1.1 Formal State (\(S_{\text{formal}}\))

What the verifier has determined about the **logical status** of the claim itself:

- \(v \in \{\text{VALID}, \text{INVALID}, \text{UNKNOWN}, \text{AMBIGUOUS}, \text{PENDING}\}\) – core validity.
- \(d \in \mathbb{N}\) – proof depth (coarse: shallow, moderate, deep, very deep).
- \(\kappa \in \mathbb{N}\) – number of detected conflicts or constraint violations.
- \(\tau \in \text{enum}\) – conflict type (logical contradiction, type error, missing premise, etc.).

**Semantics of validity states:**
- **VALID:** A witness (proof) exists in the corpus.
- **INVALID:** A witness (disproof/counterexample) exists.
- **UNKNOWN:** No witness exists in either direction (the corpus is silent on this claim).
- **PENDING:** The verifier is actively computing; a result may be forthcoming.
- **AMBIGUOUS:** Multiple competing formalizations of the claim exist, and they disagree; no canonical interpretation is chosen.

These definitions are critical for both system design and user understanding. They establish that the anchor reports on the state of a formal system relative to a specific corpus-not on objective truth.

#### 5.1.2 Epistemic State (\(S_{\text{epistemic}}\))

What is known about the **quality of the pipeline** that produced the formal state-how much we should trust that the formal state accurately reflects the user's intended claim:

- \(c_{\text{parser}} \in [0,1]\) – confidence that the natural language claim was correctly extracted.
- \(c_{\text{formalization}} \in [0,1]\) – confidence that the formalization into logic is correct.
- \(c_{\text{solver}} \in [0,1]\) – confidence in the solver's result. For deterministic provers, this is 1.0 when a result exists; for probabilistic or incomplete solvers, it reflects solver uncertainty.

Separating epistemic state from formal state is essential. A VALID result with low parser confidence means something very different from a VALID result with high confidence: the former should prompt the user to verify that the system understood their claim correctly, while the latter can be trusted as an accurate reflection of the formal system's judgment.

#### 5.1.3 Meta‑State (\(S_{\text{meta}}\))

Contextual information about the claim and the verification process:

- \(n \in \{0,1\}\) – novelty: is this claim new or previously seen?
- \(a \in [0,1]\) – ambiguity score: how many alternative interpretations exist?
- \(\iota \in \text{enum}\) – temporal consistency: did the judgment change from the previous tick?
- \(\varepsilon \in \{0,1\}\) – resource limit: did the verifier hit a time or memory bound?

### 5.2 Why This Separation Matters

This tripartite separation is, we believe, an original systems design contribution. In traditional verification tools, these three categories of information are often conflated: a single "error message" mixes what was found (formal), how confident the tool is (epistemic), and whether this is a new or recurring issue (meta). By separating them at the SSAL level, we enable:

- **Independent handling:** The perceptual encoding can treat each category differently. Formal state drives the core signal (valid/invalid). Epistemic state modulates confidence and uncertainty cues. Meta‑state provides context (novelty, change) without cluttering the core signal.
- **Engine independence:** Different symbolic engines produce different raw outputs. The SSAL normalizes them into this common vocabulary. A type checker's "type mismatch" and a theorem prover's "contradiction" both map to INVALID with different conflict types.
- **Modality independence:** The same SSAL output can drive a haptic display, a visual overlay, or an audio stream without modification. The modality renderer only needs to know how to encode the standardized state vector.

### 5.3 Formal SSAL Interface Definition

To ensure interoperability, the SSAL exposes a well‑defined interface. Below is a schema expressed in a Protocol Buffers‑like notation (a JSON Schema is provided in Appendix G).

```protobuf
message SymbolicState {
  FormalState formal = 1;
  EpistemicState epistemic = 2;
  MetaState meta = 3;
  Provenance provenance = 4;
}

message FormalState {
  enum Validity {
    VALID = 0;
    INVALID = 1;
    UNKNOWN = 2;
    AMBIGUOUS = 3;
    PENDING = 4;
  }
  Validity validity = 1;
  int32 proof_depth = 2;   // coarse ordinal: 0=shallow, 1=moderate, 2=deep, 3=extensive
  int32 conflict_count = 3;
  ConflictType conflict_type = 4;
}

message EpistemicState {
  float parser_confidence = 1;        // 0.0–1.0
  float formalization_confidence = 2; // 0.0–1.0
  float solver_confidence = 3;        // 0.0–1.0
}

message MetaState {
  bool is_novel = 1;
  float ambiguity_score = 2;          // 0.0–1.0
  enum TemporalChange {
    UNCHANGED = 0;
    CHANGED = 1;
    TRANSITION_TO_VALID = 2;
    TRANSITION_TO_INVALID = 3;
  }
  TemporalChange temporal_change = 3;
  bool resource_exhausted = 4;
}

message Provenance {
  string corpus_hash = 1;             // Merkle root
  string engine_id = 2;               // e.g., "lean-4.0.0"
  int64 timestamp = 3;                // Unix epoch
  bytes signature = 4;                // cryptographic signature
}
```

This formal contract allows any engine adapter to produce a valid SSAL state, and any perceptual encoder to consume it without knowing the engine's internals. Provenance travels with every state, enabling full auditability.

### 5.4 Scope of Engine‑Agnosticism

The SSAL is designed for **sound‑and‑complete formal reasoning engines** that can produce proof objects or counterexamples. These include theorem provers, type checkers, SAT/SMT solvers (when they can provide models or proofs), and deterministic rule engines. It can also accommodate systems that return UNKNOWN with a resource limit flag. However, probabilistic reasoners, inductive logic programming systems, or purely statistical AI models that lack discrete, checkable proof artifacts fall outside the SSAL’s primary scope. For such systems, the epistemic state would dominate, and the formal state would be largely UNKNOWN. While the SSAL can still represent their outputs, its full vocabulary of proof depth and conflict type would be unused. We explicitly restrict the architecture’s guaranteed interoperability to engines that can expose at least a validity verdict and, when positive, a witness.

### 5.5 Information-Theoretic Framing

The SSAL produces a state vector \(S\) with entropy \(H(S)\). The perceptual encoder maps this to an ideal sensory output \(H\), but the user actually receives \(\hat{H}\) after hardware limitations and perceptual channel effects. The relevant information quantity is \(I(S; \hat{H})\)-the mutual information between the SSAL state and what the user perceives. The remaining uncertainty after perception is the conditional entropy:

\[
L = H(S | \hat{H})
\]

This is the information that is "lost" to the user-the uncertainty that remains about the symbolic state even after receiving the percept. Our engineering objective is to minimize \(L\) subject to perceptual bandwidth constraints and the user's training level.

---

## 6. Information Theory and Channel Capacity

### 6.1 Perceptual Channel Capacity

The SSAL state vector \(S\) has entropy \(H(S)\). Under a uniform distribution, this could be ~20–25 bits, but real‑world verification output is highly non‑uniform: most states are VALID, deep proofs are rare, and conflicts are infrequent. The effective entropy is likely 8–15 bits in typical use. However, even this exceeds the perceptual channel capacity.

Lab studies of vibrotactile perception [22, 23, 24, 25] suggest information transfer rates of 5–10 bits per stimulus for trained participants under ideal conditions. In real‑world, mobile environments with dual‑task interference, actual throughput may be substantially lower-perhaps 2–4 bits per percept. For the lite mode (5 intent classes), this translates to a requirement of roughly 2.3 bits per percept, which is at the lower boundary of feasibility under load. The claim that lite mode patterns can be discriminated “within minutes” is a hypothesis to be empirically validated; it is not a given. A low‑fidelity discrimination study prior to full system build is recommended.

Temporal redundancy (\(H(S_t | S_{t-1})\) low) and the fact that most percepts are CONFIRM allow the system to use change‑based encoding: a quiet baseline with high‑salience transitions.

### 6.2 Uncertainty Propagation

The perceptual encoding must preserve the distinction between different sources of epistemic uncertainty. Low parser confidence should feel different from low solver confidence, because the user's remedial action differs. We propose encoding these as separate perceptual dimensions (e.g., tremolo for parser uncertainty, amplitude wobble for formalization uncertainty). This is a design hypothesis to be tested.

### 6.3 Adaptive Compression

The codebook mapping SSAL states to prototypes can be dynamically adjusted using online clustering or information bottleneck methods [26]. Frequently occurring states receive more precise prototypes; rare but high‑stakes states (INVALID) are assigned distinctive, hard‑to‑miss patterns.

---

## 7. Perceptual Encoding Layer (Modality‑Agnostic)

The encoding layer translates the SSAL state into a **sensory parameter space** that is independent of any specific modality. The mapping is many‑to‑one, driven by bandwidth constraints and behavioral priorities.

### 7.1 Refined Behavioral Intent Mapping with Confidence Thresholds

Before selecting sensory parameters, the encoder classifies the SSAL state into a **behavioral intent class** \(B\). To avoid startling users with low‑confidence contradictions, we introduce a two‑stage classification:

**Step 1 - Preliminary class:**
- Any INVALID formal state with *all* epistemic confidences above a high‑confidence threshold (e.g., 0.8) → **REJECT** (true contradiction).
- Any INVALID formal state where *any* epistemic confidence is below that threshold → **LOW_CONFIDENCE_REJECT** (potential false alarm).
- If formal state is VALID but any epistemic confidence is below 0.6 → **UNCERTAIN**.
- If formal state is PENDING and resource limit is false → **WAIT**.
- If formal state is PENDING and resource limit is true → **ALERT**.
- If formal state is AMBIGUOUS → **ALERT**.
- If formal state is UNKNOWN → **UNCERTAIN**.
- Otherwise, **CONFIRM**.

**Step 2 - Sensory mapping:**
- **REJECT** → high‑salience sharp double pulse (as before).
- **LOW_CONFIDENCE_REJECT** → **ALERT** pattern (rapid triple pulse) to signal that inspection is needed, but the contradiction may be spurious. This prevents the system from crying wolf.
- The other intent classes map as previously defined.

This refinement ensures that the system never delivers a startling REJECT when the evidence is shaky. It also gives the user a clear signal that something is potentially wrong but requires human judgment.

### 7.2 Sensory Parameter Space

Once an intent class is assigned, the encoder selects parameters in a **modality‑independent sensory space**. This space is defined by a set of abstract perceptual dimensions:

- **Intensity:** overall strength of the signal (analogous to amplitude or brightness).
- **Rhythm:** temporal pattern (steady, pulsing, intermittent, accelerating).
- **Texture:** fine‑grained temporal or frequency variation (smooth, rough, warbling).
- **Spatial distribution:** location or spread across the sensory field (center, periphery, left, right, surround).
- **Modulation:** dynamic change in any parameter over time (tremolo, vibrato, fade).

Each intent class maps to a distinctive profile in this space. For example:

| Intent Class | Intensity | Rhythm | Texture | Spatial | Modulation |
|--------------|-----------|--------|---------|---------|------------|
| CONFIRM | Low–moderate | Steady, slow | Smooth | Diffuse, all actuators | None |
| REJECT | High | Sharp double pulse | Rough, transient | Alternating left‑right | None |
| WAIT | Low | Intermittent tick | Soft | Single point | None |
| UNCERTAIN | Moderate | Irregular slow pulses | Warbling | Two opposing points | Slow tremolo |
| ALERT (incl. low‑conf. REJECT) | High | Rapid triple pulse | Rough | All actuators, surround | Amplitude swell |

This abstract specification is then concretized for each target modality by the rendering layer (Section 8). The key point is that the encoding logic-the mapping from SSAL state to sensory intent-is completely modality‑independent.

### 7.3 Encoding Constraints

The mapping \(M: S \rightarrow H\) must satisfy:
- **Injectivity of intent classes:** Different intent classes must never map to indistinguishable sensory profiles.
- **Surjectivity:** The sensory space should be fully utilized, but not over‑populated beyond the user's discrimination capacity.
- **Gray‑consistency:** Adjacent states (e.g., CONFIRM and UNCERTAIN) should map to perceptually similar patterns.
- **Stability:** Small fluctuations in epistemic confidence or meta‑state should not cause jarring perceptual shifts if the intent class remains the same.

### 7.4 Adaptive and Personalized Encoding

The specific parameters within each intent class can be personalized using the calibration procedure (Section 10.3). The codebook of sensory prototypes can be refined over time using implicit feedback.

---

## 8. Modality Rendering Layer

The rendering layer translates the abstract sensory parameters into physical stimuli for a specific modality. This layer is intentionally decoupled from semantic interpretation.

### 8.1 General Rendering Pipeline

\[
\text{Abstract parameters} \rightarrow \text{Modality‑specific mapping} \rightarrow \text{Actuator commands}
\]

The rendering engine operates on a fixed‑rate scheduler (e.g., 50 Hz). It maintains a real‑time queue of parameter updates, applies temporal shaping, and outputs low‑level signals.

### 8.2 Modality‑Specific Instantiations

#### 8.2.1 Haptic Instantiation

For a wristband with multiple LRAs:
- **Intensity** maps to vibration amplitude.
- **Rhythm** maps to on‑off pulse patterns and durations.
- **Texture** maps to frequency (smooth low‑frequency for CONFIRM, high‑frequency roughness for REJECT).
- **Spatial distribution** maps to which actuators are active.
- **Modulation** maps to amplitude or frequency variation over time.

#### 8.2.2 Auditory Instantiation

- **Intensity** → volume.
- **Rhythm** → temporal pattern of tones.
- **Texture** → timbre (consonant chord for CONFIRM, dissonant cluster for REJECT).
- **Spatial distribution** → panning or 3D position.
- **Modulation** → vibrato or tremolo.

#### 8.2.3 Visual Instantiation

- **Intensity** → brightness or opacity.
- **Rhythm** → blinking or pulsing frequency.
- **Texture** → pattern or gradient.
- **Spatial distribution** → position on screen.
- **Modulation** → color shift or saturation change.

### 8.3 Modality Selection Rationale

Haptics are the reference modality for Perceptual Symbolic Interface because they offer low attentional demand, privacy, and do not compete with visual tasks. However, the architecture explicitly supports multimodal deployments.

---

## 9. Interaction Walkthrough: A Developer Reviewing a Pull Request

To ground the architecture, we describe Alice, a developer using Perceptual Symbolic Interface while reviewing a Rust pull request.

1. **Input:** IDE extension extracts changed code and sends it to the claim extractor.
2. **Formalization:** The extractor parses claims (e.g., "variable `x` satisfies `Send`").
3. **Verification (Layer 1):** Lean 4 kernel checks claims against a corpus. Results: most are VALID; one is INVALID with high confidence.
4. **SSAL (Layer 2):** The INVALID claim becomes \(v = \text{INVALID}\), parser_confidence=0.95, formalization_confidence=0.99, solver_confidence=1.0. All confidences exceed the REJECT threshold → intent class = REJECT.
5. **Encoding (Layer 3):** REJECT maps to a sharp double pulse on alternating actuators.
6. **Rendering (Layer 4):** The wristband delivers the pattern. Alice feels the pulse, immediately knows something is wrong, taps the wristband, and sees the counterexample on her phone. She corrects the code. The verifier re‑evaluates, returning VALID → CONFIRM → smooth hum.
7. **Closed Loop:** Correction feeds back, closing the loop.

Now suppose a claim is INVALID but parser_confidence is only 0.5 (the input was ambiguous). The intent class becomes LOW_CONFIDENCE_REJECT → ALERT (rapid triple pulse). Alice feels the alert, understands that the system may be uncertain about the claim, and inspects carefully before deciding.

---

## 10. Calibration, Walk‑Up‑And‑Use Familiarization, and Training

### 10.1 Lite Mode: Walk‑Up‑And‑Use Utility

Perceptual Symbolic Interface ships with a **lite mode** that maps the five intent classes to distinctive haptic patterns as described above. We hypothesize that users can learn to discriminate these patterns after a **sub‑minute familiarization period** (e.g., a brief guided exposure where each pattern is presented and named). This is not “zero training”; it is a minimal onboarding step. The system includes an optional quick calibration to identify the user's most sensitive frequency and location, which further improves discrimination. The lite mode is designed for immediate practical use, and users can remain in it indefinitely.

### 10.2 Progressive Complexity (Optional)

A staged curriculum (Appendix D) gradually introduces richer parameter variations. Progression is gated by accuracy thresholds (>90%).

### 10.3 Individual Calibration

A 2‑minute calibration maps the user's most sensitive skin locations and remaps spatial parameters accordingly.

### 10.4 Phenomenological Learning Model

As an illustrative model, we represent the user's identification accuracy as:

\[
P_{t+1}(s) = P_t(s) + \alpha \cdot (1 - P_t(s)) \cdot \text{exposure}(s) - \beta \cdot P_t(s) \cdot \text{forgetting\_rate}
\]

This is consistent with perceptual learning literature [14].

---

## 11. Reference Implementation: Perceptual Symbolic Interface

Perceptual Symbolic Interface instantiates the four‑layer architecture as a haptic wristband.

### 11.1 Layer Mapping

- **Layer 1 (Symbolic Computation):** Lean 4 kernel [17], Z3 [20], or domain‑specific rule engines.
- **Layer 2 (SSAL):** A Rust service that produces standardized state vectors.
- **Layer 3 (Perceptual Encoding):** Adaptive vector quantizer implementing the confidence‑aware behavioral intent mapping.
- **Layer 4 (Modality Rendering):** Custom wristband with 4 LRAs, 50 Hz scheduler.

### 11.2 Phased Rollout

**Phase 1 (3–6 months):** Domain‑specific corpora; lite mode; <20 ms latency.
**Phase 2 (9–12 months):** Semi‑structured text; WAIT during extraction.
**Phase 3 (12+ months – Research):** Open‑domain via LLM + formal guard.
**Conservative Mode:** Emits signal only if verification completes within user‑set latency; default for safety‑critical applications.

### 11.3 Error Budget

| Error Source | Allocated (Phase 1) | Mitigation |
|--------------|---------------------|------------|
| Parser error | <1% | Restricted grammar, confidence threshold |
| Formalization error | <0.5% | Pre‑verified models |
| Solver error | <0.01% | Trusted kernel, proof certificates |
| Encoding error | <5% | Discriminable patterns, familiarization |
| Human perception error | <10% | Adaptive salience, catch trials |
| **Total false negative (critical)** | <1% | Layered defenses |

### 11.4 Aggregation and Arbitration

When multiple claims exist simultaneously:
- REJECT signals suppress all others.
- LOW_CONFIDENCE_REJECT is treated as REJECT for prioritization but uses the ALERT pattern.
- WAIT claims are queued by user focus.

---

## 12. Human Factors and Ergonomics

### 12.1 Real‑World Interference

Motion triggers automatic fallback to simpler encoding (frequency‑only CONFIRM/REJECT). Stationary periods restore richer patterns.

### 12.2 Habituation Management

Constant vibration causes rapid habituation. To combat this, the system implements a concrete **adaptive silence and novelty injection** protocol:

- **Baseline shift:** Every 5–10 minutes, the CONFIRM frequency is subtly altered (±3 Hz) while remaining within the CONFIRM class. This prevents sensory adaptation without altering semantic meaning.
- **Adaptive silence:** If the CONFIRM state has persisted continuously for more than 15 minutes, the vibration amplitude is gradually reduced to a sub‑threshold level over 60 seconds. The system remains in a “quiet watch” mode; the first change to any other intent class immediately restores full amplitude, ensuring transitions are not missed.
- **Novelty injection:** Approximately every 30 minutes, a brief (200 ms) non‑semantic “chirp” is inserted, which does not correspond to any intent class. This is designed to momentarily reset the user's tactile attention. The chirp is low‑salience and distinct from all semantic patterns.
- **Periodic reset:** After 2 hours of continuous use, the system performs a brief self‑test (actuator sweep) and prompts the user (via a soft vibration sequence) to consider a short break or recalibration.

These measures are designed to maintain long‑term perceptual sensitivity. They are initial heuristics; empirical tuning will be necessary.

### 12.3 Trust Calibration and Explainability

Trust calibration is a central challenge. The system provides adaptive salience for ignored WAIT/UNCERTAIN, transparent catch trials, conservative mode as default, and a companion app showing corpus scope and freshness. The **explainability layer** allows the user to tap the wristband or glance at the app to retrieve the witness associated with the current percept, using provenance metadata.

### 12.4 Accessibility

- **Blind programmers:** Haptic stream for parallel structural information.
- **Deaf users:** Visual overlays or haptic feedback.
- **ADHD:** Peripheral, low‑attention haptic monitor.
- **Autism:** Predictable, structured sensory input.
- **Low vision:** High‑contrast visual modes or haptics.
- **Skin sensitivity variations:** Personalized calibration.

---

## 13. Error Taxonomy

| Error Class | Haptic Signature (Lite Mode) | Visual Equivalent |
|-------------|------------------------------|-------------------|
| Logical contradiction (high conf.) | Sharp double pulse, alternating actuators | Red border flash |
| Logical contradiction (low conf.) | Rapid triple pulse (ALERT) | Amber flashing border |
| Type mismatch | Rapid flutter on right side | Amber highlight |
| Missing premise | Two slow pulses, front | Dashed underline |
| Incomplete proof | Wavering hum | Pulsing icon |
| Unsupported assumption | Short chirp, back | Question‑mark overlay |
| Outdated corpus | Intermittent soft tick | Grayed‑out indicator |
| Parser uncertainty | Soft irregular taps | Faded text |
| Knowledge gap (UNCERTAIN) | Silence (lite mode) or gentle hum | Neutral icon |
| WAIT (PENDING) | Distinct intermittent tick | Spinning indicator |
| Confidence failure | Amplitude tremolo | Flickering opacity |

---

## 14. Engineering Requirements

| Requirement | Target |
|-------------|--------|
| End‑to‑end latency (Phase 1) | <20 ms |
| Update frequency | 20–100 Hz (default 50 Hz) |
| Lite mode discrimination | >90% after sub‑minute familiarization (hypothesized) |
| Advanced mode accuracy | >85% for 8‑bit codebook (hypothesized) |
| False positive rate (critical) | <1% within corpus scope |
| Corpus integrity | Merkle‑hashed, cryptographically signed |
| Local processing | 100% for sensitive domains |
| User calibration | <2 minutes |
| Motion‑adaptive encoding | Automatic fallback |
| Hardware fault detection | Self‑test every 10 min |

---

## 15. Evaluation Plan

### 15.1 Central Hypotheses (Sharpened)

1. **H1 (Detection Speed):** Users with lite mode haptic feedback will detect high‑confidence INVALID signals faster than unaided users on domain‑specific verification tasks.
2. **H2 (Dual‑Task Interference):** The haptic channel will produce less interference with a primary visual task than text‑based verification feedback, as measured by performance drop in the primary task.
3. **H3 (Peripheral Awareness):** During a sustained code‑reading task, users will detect infrequent (low‑probability) REJECT signals with minimal re‑orienting (as measured by eye‑tracking dwell time on the signal source). We hypothesize detection rates >80% and that most users report the haptic channel as “background” after 30 minutes.
4. **H4 (Learning and Retention):** Users undergoing the progressive curriculum will show increasing information transfer rate (bits/stimulus) over 4 weeks, with retention above baseline after 1 month.
5. **H5 (Confidence‑Aware Mapping Benefit):** The LOW_CONFIDENCE_REJECT → ALERT mapping will result in fewer false‑alarm startle responses compared to a naive mapping that treats all INVALID as REJECT, as measured by subjective annoyance ratings and trust calibration over time.

### 15.2 Pilot Study Design

We propose a two‑phase pilot:

**Phase A – Discrimination Validation:**
Before building the full wristband, a low‑fidelity study using a smartphone app that plays vibration patterns (or uses existing wearable actuators) will test whether users can discriminate the five lite mode patterns under dual‑task conditions (e.g., reading text while responding to haptic signals). Metrics: classification accuracy, reaction time, confusion matrix. This will validate the bandwidth assumptions and refine the encoding.

**Phase B – Full System Evaluation:**
Within‑subjects crossover (n=24–48), developers performing code review. Three conditions: (1) unaided IDE, (2) IDE with textual static analysis warnings, (3) IDE with Perceptual Symbolic Interface haptic feedback. Order counterbalanced with washout. Primary measures:
- Time to detect planted contradictions.
- NASA‑TLX workload.
- Eye‑tracking metrics: dwell time on non‑code regions after a haptic signal, saccade patterns.
- Subjective “peripheral awareness” questionnaire (adapted from peripheral display evaluation scales).
- 1‑month retention test.

### 15.3 Falsification Criteria

The system is considered ineffective if:
- H1: No significant difference in detection time between Perceptual Symbolic Interface and unaided condition.
- H3: Detection rate of infrequent signals <70% or users report the signal as “distracting” rather than “background.”
- H5: Annoyance ratings for LOW_CONFIDENCE_REJECT are not significantly lower than for the naive mapping.

---

## 16. Risks, Limitations, and Ethical Considerations

- **Automation bias:** Mitigated by UNCERTAIN/WAIT states, adaptive salience, conservative mode default, and provenance‑backed explainability. The confidence‑aware mapping reduces false REJECTs that could erode trust.
- **Incomplete corpora:** Completeness indicator warns of partial coverage.
- **Habituation:** The concrete habituation‑reset protocol (Section 12.2) is designed to combat this.
- **Adversarial content:** Input sanitization, ambiguity signaling.
- **Filter bubbles:** Annotation only; no content filtering.
- **Social asymmetry:** Shared visual overlays for teams; open‑source implementations.
- **High‑stakes domains:** Aid only; domain‑specific validation mandatory.
- **Failure cascade:** Multi‑layer checks, UNCERTAIN on low confidence.

---

## 17. Future Research Directions

1. Adaptive encoding via reinforcement learning
2. Multimodal integration (haptic + spatial audio + visual)
3. EEG‑assisted personalization
4. Closed‑loop perceptual training games
5. Multi‑user synchronization with shared perceptual grammar
6. Formal education applications
7. Longitudinal expertise acquisition studies
8. Robot teleoperation and AI alignment monitoring
9. AR glasses integration with spatialized signals
10. Corpus crowdsourcing and community maintenance
11. Emotion‑aware adaptive intensity
12. Cross‑domain transfer of perceptual learning
13. Hardware miniaturization (skin‑like patches)
14. Information bottleneck optimization for encoding
15. Rate‑distortion theory applied to perceptual codebooks
16. Formal verification of the closed‑loop augmentation system
17. Standardization of symbolic sensory encoding vocabulary
18. Calibration of epistemic confidence estimates
19. Long‑term habituation field studies
20. Peripheral awareness with dynamic task loads

---

## 18. Conclusion

We have presented a reference architecture for **perceptual interfaces to symbolic computation**-a new interface category that treats the output of formal reasoning engines as a perceivable information source. The architecture's central innovation is the **Symbolic State Abstraction Layer (SSAL)**, which decouples symbolic computation from perceptual rendering by producing a standardized state vector with separate formal, epistemic, and meta‑state components. The encoding layer maps this state to a small set of behaviorally defined intent classes, now refined with confidence‑aware thresholds to prevent false alarms. A concrete habituation‑reset protocol and a sharper evaluation plan with peripheral awareness metrics ensure that the system is designed for real‑world robustness.

Perceptual Symbolic Interface, a haptic wristband, serves as a reference implementation. A lite mode provides walk‑up‑and‑use utility after sub‑minute familiarization; a progressive curriculum unlocks deeper dimensions. All cognitive benefit claims are testable hypotheses. The broader contribution is the architectural pattern itself-a principled approach to making the state of symbolic computation peripherally perceivable.

---

## References

1. Bach‑y‑Rita, P., & Kercel, S. W. (2003). Sensory substitution and the human–machine interface. *Trends Cogn. Sci.*, 7(12), 541‑546. DOI: [10.1016/j.tics.2003.10.013](https://doi.org/10.1016/j.tics.2003.10.013)
2. Reed, C. M., et al. (1985). Research on the Tadoma method. *J. Acoust. Soc. Am.*, 77(1), 247‑257. DOI: [10.1121/1.392267](https://doi.org/10.1121/1.392267)
3. *The Duotronics Framework.* Internal draft 4.3, July 2026. GitHub.
4. Weiser, M. (1991). The computer for the 21st century. *Scientific American*, 265(3), 94‑104. DOI: [10.1038/scientificamerican0991-94](https://doi.org/10.1038/scientificamerican0991-94)
5. Matthews, T. (2006). Designing and evaluating glanceable peripheral displays. *ACM DIS 2006*. DOI: [10.1145/1142405.1142457](https://doi.org/10.1145/1142405.1142457)
6. Vicente, K. J., & Rasmussen, J. (1992). Ecological interface design. *IEEE Trans. Syst. Man Cybern.*, 22(4), 589‑606. DOI: [10.1109/21.156574](https://doi.org/10.1109/21.156574)
7. Bakker, S., et al. (2012). Peripheral interaction. *Pers. Ubiquitous Comput.*, 16(3), 239‑254. DOI: [10.1007/s00779-011-0388-4](https://doi.org/10.1007/s00779-011-0388-4)
8. Ford, K. M., & Hayes, P. J. (1998). On computational wings. *IEEE Intell. Syst.*, 13(2), 78‑81.
9. Sweller, J. (1988). Cognitive load during problem solving. *Cogn. Sci.*, 12(2), 257‑285. DOI: [10.1207/s15516709cog1202_4](https://doi.org/10.1207/s15516709cog1202_4)
10. Wilson, M. (2002). Six views of embodied cognition. *Psychon. Bull. Rev.*, 9(4), 625‑636. DOI: [10.3758/BF03196322](https://doi.org/10.3758/BF03196322)
11. Noë, A. (2004). *Action in Perception*. MIT Press.
12. Amedi, A., et al. (2007). The plastic human brain cortex. *Nat. Rev. Neurosci.*, 8(10), 768‑778. DOI: [10.1038/nrn2156](https://doi.org/10.1038/nrn2156)
13. Bach‑y‑Rita, P. (2004). Tactile sensory substitution studies. *Ann. N. Y. Acad. Sci.*, 1013, 83‑91. DOI: [10.1196/annals.1305.006](https://doi.org/10.1196/annals.1305.006)
14. Goldstone, R. L. (1998). Perceptual learning. *Annu. Rev. Psychol.*, 49, 585‑612. DOI: [10.1146/annurev.psych.49.1.585](https://doi.org/10.1146/annurev.psych.49.1.585)
15. Clark, A., & Chalmers, D. (1998). The extended mind. *Analysis*, 58(1), 7‑19. DOI: [10.1093/analys/58.1.7](https://doi.org/10.1093/analys/58.1.7)
16. Hutchins, E. (1995). *Cognition in the Wild*. MIT Press.
17. de Moura, L., et al. (2015). The Lean theorem prover. *CADE‑25*, LNCS 9195, 378‑388. DOI: [10.1007/978-3-319-21401-6_26](https://doi.org/10.1007/978-3-319-21401-6_26)
18. Bertot, Y., & Castéran, P. (2004). *Coq'Art*. Springer.
19. Nipkow, T., et al. (2002). *Isabelle/HOL*. LNCS 2283. DOI: [10.1007/3-540-45949-9](https://doi.org/10.1007/3-540-45949-9)
20. de Moura, L., & Bjørner, N. (2008). Z3. *TACAS 2008*, LNCS 4963, 337‑340. DOI: [10.1007/978-3-540-78800-3_24](https://doi.org/10.1007/978-3-540-78800-3_24)
21. Lamport, L. (2002). *Specifying Systems*. Addison‑Wesley.
22. Miller, G. A. (1956). The magical number seven. *Psychol. Rev.*, 63(2), 81‑97. DOI: [10.1037/h0043158](https://doi.org/10.1037/h0043158)
23. Tan, H. Z., et al. (1999). Information transmission with a multi‑finger tactual display. *Percept. Psychophys.*, 61(6), 993‑1008. DOI: [10.3758/BF03207613](https://doi.org/10.3758/BF03207613)
24. Goff, G. D. (1967). Frequency discrimination of cutaneous vibration. *J. Exp. Psychol.*, 74(2), 294‑299. DOI: [10.1037/h0024764](https://doi.org/10.1037/h0024764)
25. Verrillo, R. T. (1992). Vibration sensation in humans. *Music Perception*, 9(3), 281‑302. DOI: [10.2307/40285532](https://doi.org/10.2307/40285532)
26. Tishby, N., et al. (1999). The information bottleneck method. *Proc. 37th Allerton Conf.*
27. Sparrow, B., et al. (2011). Google effects on memory. *Science*, 333(6043), 776‑778. DOI: [10.1126/science.1207745](https://doi.org/10.1126/science.1207745)
28. Garcez, A. d'Avila, & Lamb, L. C. (2020). Neurosymbolic AI: the 3rd wave. *arXiv:2012.05876*.
29. Sun, R. (2023). A survey of neuro‑symbolic reasoning. *J. Artif. Intell. Res.*, 77, 1231‑1293. DOI: [10.1613/jair.1.14235](https://doi.org/10.1613/jair.1.14235)
30. Mueller, S. T., et al. (2020). Principles of augmented cognition. *Front. Hum. Neurosci.*, 14, 569. DOI: [10.3389/fnhum.2020.569844](https://doi.org/10.3389/fnhum.2020.569844)

---

## Appendix A: MIT License

```
MIT License

Copyright (c) 2026 The Blob Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
```

## Appendix B: Implementation Details (Perceptual Symbolic Interface)

Hardware specifications, BOM, actuator specifications, and detailed pseudocode for the haptic scheduler. See companion repository.

---

## Appendix C: Expanded Use Cases

1–20 as previously described (programming, mathematics, medicine, law, cybersecurity, finance, content moderation, education, etc.)

---

## Appendix D: Training Curriculum Details

Stage 0 (Lite Mode familiarization) through Stage 5, with session counts, durations, and gating criteria.

---

## Appendix E: Glossary

- **Symbolic State Abstraction Layer (SSAL):** The architecture component that decouples symbolic computation from perceptual rendering by producing a standardized state vector.
- **Deterministic Anchor:** A symbolic engine whose output is reproducible, auditable, and externally verifiable. Formally, a tuple (D, W, C, T, P).
- **Formal State:** What the verifier has determined about the logical status of the claim.
- **Epistemic State:** What is known about the quality of the pipeline that produced the formal state.
- **Meta‑State:** Contextual information about the claim and verification process.
- **Peripheral Processing:** Sensory processing hypothesized to occur with low attentional demand.
- **Lite Mode:** Immediate‑value encoding requiring only sub‑minute familiarization.
- **Behavioral Intent Class:** A small set of action‑oriented categories (CONFIRM, REJECT, LOW_CONFIDENCE_REJECT, WAIT, UNCERTAIN, ALERT) that abstract the SSAL state for perceptual encoding.
- **Conditional Entropy \(H(S|\hat{H})\):** The remaining uncertainty about the symbolic state after receiving the percept.

---

## Appendix F: Formal Foundations (Optional)

Full mathematical specification of the SSAL, the deterministic anchor, the information‑theoretic treatment of encoding loss, and the closed‑loop cognitive dynamics model.

---

## Appendix G: SSAL JSON Schema (Example)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SymbolicState",
  "type": "object",
  "properties": {
    "formal": {
      "type": "object",
      "properties": {
        "validity": { "enum": ["VALID", "INVALID", "UNKNOWN", "AMBIGUOUS", "PENDING"] },
        "proof_depth": { "type": "integer", "minimum": 0, "maximum": 3 },
        "conflict_count": { "type": "integer", "minimum": 0 },
        "conflict_type": { "type": "string" }
      },
      "required": ["validity"]
    },
    "epistemic": {
      "type": "object",
      "properties": {
        "parser_confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "formalization_confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "solver_confidence": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },
    "meta": {
      "type": "object",
      "properties": {
        "is_novel": { "type": "boolean" },
        "ambiguity_score": { "type": "number", "minimum": 0, "maximum": 1 },
        "temporal_change": { "enum": ["UNCHANGED", "CHANGED", "TRANSITION_TO_VALID", "TRANSITION_TO_INVALID"] },
        "resource_exhausted": { "type": "boolean" }
      }
    },
    "provenance": {
      "type": "object",
      "properties": {
        "corpus_hash": { "type": "string" },
        "engine_id": { "type": "string" },
        "timestamp": { "type": "integer" },
        "signature": { "type": "string" }
      },
      "required": ["corpus_hash", "engine_id", "timestamp"]
    }
  },
  "required": ["formal", "provenance"]
}
```

---

*This document is a living engineering architecture and research blueprint. All cognitive benefit claims are hypotheses to be tested. The architecture (Sections 3–5, 7) is the reusable contribution; Perceptual Symbolic Interface (Section 11, Appendix B) is one reference implementation. Feedback and contributions are welcome under the MIT license.*
```