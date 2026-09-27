# DUO-MATH, Witness Contracts, and Witness-Gated Recurrent Neural Networks

## A Zeroless Architecture for Auditable Augmented Intelligence

**Status:** Research and architecture paper  
**Related specifications:** DUO-MATH; Duotronics Witness Contract v1.6 Draft 5.3.18; Witness-Gated Recurrent Cell architecture  
**Project:** Duotronics  
**Date:** 2026

---

## Abstract

This paper describes an integrated computational architecture combining three distinct but complementary ideas:

1. **DUO-MATH**, a zeroless signed bijective-alphanumeric numerical and symbolic state system;
2. **the Duotronics Witness Contract**, a deterministic provenance, evidence, validation, and authority framework; and
3. **a Witness-Gated Recurrent Neural Network (WG-RNN)** whose recurrent state is influenced by admitted witnessed evidence rather than unconstrained model activation alone.

DUO-MATH eliminates the numeral `0` from its native mathematical domain. Its canonical shared origin is `1`, its multiplicative identity is `2`, and its positive and negative branches extend outward from a single shared origin. The attached DUO-MATH specification defines the system as zeroless, bijective, signed, alphanumeric, and based on symbolic successor/predecessor transitions rather than requiring conventional positional arithmetic in its native execution model.

The Witness Contract solves a different problem. It determines what was observed, how an observation was produced, what provenance and cryptographic evidence accompany it, how it was revalidated, what authority domain it belongs to, and whether it may participate in authoritative operations. Draft 5.3.18 explicitly prevents recurrence, tensor adjacency, model confidence, similarity, or graph proximity from creating authority on their own. The deterministic evidence graph and authority verifier remain separate from neural or heuristic cognition. 

The WG-RNN connects these domains. Valid witness objects may be projected into DUO-native cognitive state. The recurrent system accumulates, remembers, compares, contradicts, reinforces, decays, and predicts using exact symbolic states. It may generate hypotheses, action proposals, classifications, future-state predictions, retrieval requests, or requests for additional witnesses. It may not independently convert those predictions into canonical truth.

The resulting architecture is therefore not:

```text
input
→ neural network
→ answer
```

but:

```text
observation
→ witness
→ validation
→ DUO projection
→ recurrent witnessed memory
→ inference
→ proposal
→ new witness acquisition
→ deterministic verification
→ canonical result
```

This produces a closed epistemic loop in which cognition can be adaptive without allowing adaptation itself to become proof.

---

# 1. Introduction

Most contemporary machine-learning systems begin with numerical tensors, transform those tensors through many layers of positional binary or floating-point arithmetic, and eventually produce another numerical tensor from which an output is decoded.

That model works well for statistical prediction, but it introduces several architectural difficulties when the desired system must also provide:

- explicit provenance;
- replayability;
- long-term recurrent memory;
- semantic distinction between absence and neutrality;
- contradictory evidence tracking;
- deterministic evidence acceptance;
- auditable learning;
- exact state transitions;
- offline operation;
- multi-agent or multi-model observation;
- and human-inspectable explanations for why state changed.

The central problem is not merely numeric representation.

It is **semantic collapse**.

Conventional software frequently overloads one numeric value—usually zero—to represent many unrelated conditions:

```text
zero quantity
no measurement
missing field
false
unset
padding
empty vector
invalid result
uninitialized memory
no contribution
no confidence
unknown
```

DUO-MATH deliberately eliminates that possibility from its native numeral space. The specification states that zero must not be used as a mathematical value, origin, sentinel, placeholder, default numeric state, indexing convention, or internal DUO numeral.

This does not magically solve epistemology.

Instead, it forces the architecture to represent different semantic states explicitly.

Thus:

```text
DUO origin 1
```

cannot silently mean:

```text
UNKNOWN
ABSENT
UNOBSERVED
INVALID
REJECTED
```

Those concepts remain outside the numerical domain. The DUO-MATH draft makes this distinction explicit.

That property makes DUO-MATH particularly compatible with the Witness Contract.

---

# 2. The Three-Layer Architecture

The proposed architecture separates three fundamentally different kinds of state.

## 2.1 Observational state

This answers:

> What was actually observed, measured, computed, received, or attested?

This belongs to the **Witness Contract**.

Examples include:

```text
camera frame
audio segment
temperature measurement
document passage
database row
API response
model observation
tool execution
compiler result
proof checker result
sensor event
human statement
network event
```

The observational layer preserves the actual source information.

---

## 2.2 Cognitive state

This answers:

> Given everything witnessed so far, what internal state should the system presently hold?

This belongs to the **WG-RNN and DUO recurrent memory system**.

Examples include:

```text
support
contradiction
novelty
persistence
story continuity
causal expectation
source consistency
regime evidence
confidence
relevance
prediction state
memory activation
```

These are learned or accumulated cognitive states.

They are not automatically facts.

---

## 2.3 Authoritative state

This answers:

> Which derived objects or claims may become part of the canonical evidence or authority graph?

This belongs to the **deterministic Witness Contract verifier**.

Authority therefore does not arise from:

```text
high neural confidence
large recurrent activation
nearest vector
majority model agreement
strong attention
long persistence
graph proximity
```

unless a registered deterministic policy explicitly evaluates admissible evidence and creates the corresponding authority-bearing object.

Draft 5.3.18 expressly preserves this distinction: heuristic, analog, neural, or reservoir processes may propose relations and probes, but deterministic verification controls admission to the authority graph. 

---

# 3. DUO-MATH as the Cognitive State Algebra

## 3.1 Canonical number line

The basic DUO line is:

```text
... -5 -4 -3 -2 1 2 3 4 5 ...
```

There is no `0`.

The negative branch ends at `-2`.

The positive branch begins at `2`.

The central shared state is:

```text
1
```

The specification defines `1` as the shared origin and prohibits `-1` and `+1` as distinct canonical numerals.

Thus:

```text
origin = 1
```

---

## 3.2 Successor topology

The number line is fundamentally an ordered graph:

```text
... ↔ -4 ↔ -3 ↔ -2 ↔ 1 ↔ 2 ↔ 3 ↔ 4 ↔ ...
```

with:

```text
S(-2) = 1
S(1)  = 2
S(8)  = 9
S(9)  = 1a
```

and:

```text
P(2) = 1
P(1) = -2
```

The DUO specification explicitly defines this successor/predecessor model.

For machine cognition, this graph interpretation is at least as important as the textual notation.

---

# 4. Modular-10 Placeholder Cycling

DUO uses numeral symbols:

```text
1 2 3 4 5 6 7 8 9
```

followed by:

```text
1a 2a 3a ... 9a
1b 2b 3b ... 9b
...
```

The attached specification defines a modular cycle in terms of canonical states rather than conventional zero-containing digit glyphs.

Conceptually:

```text
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 1a
```

There are nine successor transitions between these ten endpoint-inclusive canonical states.

This distinction matters because the computational primitive is not:

```text
increment a base-10 positional register
```

but:

```text
apply successor(state)
```

The transition:

```text
9 → 1a
```

is simply another edge in the canonical state graph.

Similarly:

```text
9z → 1aa
```

can be executed by the suffix automaton rather than by evaluating positional powers. The DUO specification explicitly describes this suffix successor machine.

---

# 5. Algebraic Identities

DUO defines:

```text
x ⊕ 1 = x
```

therefore:

```text
1 = additive identity
```

It also defines:

```text
x ⊗ 2 = x
```

therefore:

```text
2 = multiplicative identity
```

and:

```text
x ⊗ 1 = 1
```

making the origin an annihilating state under multiplication.

Cancellation returns to the origin:

```text
x ⊕ N(x) = 1

x ⊖ x = 1
```

These properties are documented in the current DUO draft.

This has direct implications for neural computation.

---

# 6. Neural Gates in DUO State

A very useful DUO gate convention is:

```text
1  = closed
2  = pass-through
3  = amplification level 1
4  = amplification level 2
5  = amplification level 3
...

-2 = inhibitory/opposing influence
-3 = stronger inhibition
...
```

This convention is already described in the DUO neural-network section.

Suppose:

```text
g = neural witness gate
e = evidence state
```

Then define:

```text
r = g ⊗ e
```

If:

```text
g = 1
```

then:

```text
r = 1
```

because:

```text
1 ⊗ e = 1
```

And because:

```text
h ⊕ 1 = h
```

the gated evidence produces no state change.

This creates a native closed gate without requiring a semantic zero.

---

# 7. Two Different Kinds of Gate

This architecture must distinguish two entirely different meanings of the word **gate**.

## 7.1 Authority gates

These belong to the Witness Contract.

They determine whether evidence satisfies a deterministic policy requirement.

They must be:

```text
deterministic
auditable
domain-bound
policy-bound
replayable
cryptographically verifiable where required
```

Draft 5.3.18 defines a twelve-gate activation graph and requires all registered gates to be valid, fresh, policy-compatible, and in the same authority domain before activation. 

---

## 7.2 Neural witness gates

These belong to the WG-RNN.

They determine:

> How strongly should a valid observation influence cognitive state?

They may depend upon:

```text
source reliability
novelty
temporal relevance
contradiction
recurrence
semantic similarity
previous witness trajectory
expected state
current regime
task context
```

These gates are adaptive.

They do not create authority.

Recommended terminology is therefore:

```text
AuthorityGateResult
```

versus:

```text
WitnessNeuralGateState
```

---

# 8. Witness Contract Input Pipeline

The full input architecture begins before anything enters the neural system.

## 8.1 Raw inputs

Inputs may include:

```text
text
images
video
audio
documents
structured records
database objects
sensor streams
CAD
source code
terminal output
network telemetry
model outputs
human statements
API results
proof results
simulation results
```

The input must initially remain in its native observable form.

For example:

```text
temperature = 23.71 °C
```

must remain available as:

```text
23.71 °C
```

The system must not destroy the raw measurement merely because the cognitive runtime later maps it into a DUO state.

---

# 9. Witness Envelopes

The raw observation becomes part of a witness object.

Conceptually:

```text
WitnessEnvelope
{
    witness_id
    source_id
    subject_id
    modality
    observation
    timestamp
    chronology
    environment
    toolchain
    authority_domain
    schema_id
    provenance
    content_hash
    signatures
    policy_binding
}
```

The precise fields depend upon the witness family.

The important property is that the original observation remains independently identifiable.

---

# 10. Measurement and Revalidation

Draft 5.3.18 distinguishes the original measurement from a later revalidation measurement.

They are not interchangeable.

Conceptually:

```text
OriginalMeasurement
        │
        ▼
RevalidationMeasurement
```

does **not** mean:

```text
OriginalMeasurement = overwritten
```

Instead both remain available.

This is essential for temporal reasoning.

The cognitive system may therefore observe:

```text
original result
fresh result
difference
time elapsed
source drift
policy state
```

and project their relationship into DUO recurrent state.

---

# 11. Evidence Graph

The 5.3.18 authority graph follows the approximate logical path:

```text
contract subject
      ↓
probe challenge
      ↓
original measurement
      ↓
external attestation
      ↓
fresh revalidation
      ↓
gate result
      ↓
aggregate
      ↓
domain activation
```

The edges are explicit typed objects.

Graph proximity by itself does not constitute evidence.

This property is extremely important for the WG-RNN because it prevents learned graph embeddings from being mistaken for verified relationships. 

---

# 12. DUO Projection

After evidence becomes eligible for cognitive use, a deterministic or policy-controlled projection converts relevant witness features into DUO states.

Define:

```text
Πᴅ(W_t) = e_t
```

where:

```text
W_t = canonical current witness

e_t = DUO evidence feature vector
```

Example:

```text
e_t =
{
    source_support: 4,
    freshness: 7,
    novelty: 3,
    temporal_alignment: 5,
    contradiction: -2,
    confidence: 6
}
```

The DUO draft itself gives similar interpretable state examples.

The projection must itself be versioned:

```text
projection_policy_id
duo_algebra_version
feature_schema_version
```

so replay remains possible.

---

# 13. Missing Data Must Stay Outside DUO

An essential invariant is:

```text
1 ≠ UNKNOWN
1 ≠ ABSENT
1 ≠ UNOBSERVED
1 ≠ INVALID
1 ≠ REJECTED
```

`1` means:

> a valid DUO state at the shared origin.

Nothing else.

A cognitive feature can therefore be represented conceptually as:

```text
FeatureState =
    DUO(value)
  | UNKNOWN
  | ABSENT
  | UNOBSERVED
  | INVALID
  | REJECTED
```

This is safer than storing every state in one scalar field.

---

# 14. L1 and L2 Witness State

The older witness design already established a useful two-level model:

```text
L1 = current object witness W_t

L2 = recurrent witness state W̃_t
```

The carried-forward WG-RNN documentation explicitly retains witness-gated recurrent state while stating that fast recurrent state does not become mathematical truth. 

That distinction should remain.

The DUO version becomes:

```text
W_t
    canonical witness object

e_t
    DUO projection of W_t

W̃_t
    recurrent DUO witness memory
```

---

# 15. DUO Recurrent Witness State

A future native state object could resemble:

```text
RecurrentWitnessStateDUO
{
    family_support
    family_contradiction
    story_axis
    callback_state
    sector_persistence
    source_consistency
    contradiction_pressure
    coherence_displacement
    regime_evidence
    expected_signature
    freshness
    witness_age
    novelty_state
}
```

Each numerical field is either:

```text
valid DUO state
```

or an explicit external semantic condition.

No field silently defaults to numeric zero.

---

# 16. Initial State

A newly created valid recurrent cell begins at:

```text
1
```

Thus a newly initialized vector may be:

```text
[
    1,
    1,
    1,
    1,
    1
]
```

This means:

> five valid initialized dimensions at their neutral origin.

It does not mean:

> five missing values.

Missing values must be represented separately.

---

# 17. Support and Contradiction Topology

DUO creates a natural signed evidence axis:

```text
strong contradiction

-7
-6
-5
-4
-3
-2

 1

 2
 3
 4
 5
 6
 7

strong support
```

Repeated supporting evidence may move:

```text
1 → 2 → 3 → 4 → 5
```

Repeated contradiction may move:

```text
1 → -2 → -3 → -4 → -5
```

Counterevidence can move a state back toward origin:

```text
5 → 4 → 3 → 2 → 1
```

and then into the opposite branch:

```text
1 → -2 → -3
```

The attached DUO specification already identifies this support/contradiction interpretation for witness-gated recurrent cells.

---

# 18. Provenance-Preserving State Changes

A critical design rule is:

> The aggregate state is not the evidence.

If a state changes:

```text
3 → 4
```

the system must still know why.

For example:

```text
DuoStateTransitionWitness
{
    cell_id
    previous_state: 3
    current_state: 4

    triggering_witness_id
    projection_policy_id
    neural_gate_state
    operator_id

    chronology
    model_version
    duo_version
}
```

This means every important recurrent transition may be reconstructed.

---

# 19. No Evidence Cancellation by Destruction

Consider:

```text
support = 5
contradiction = -5
```

A conventional scalar averaging scheme might collapse both into something numerically near zero.

That can destroy useful information.

The witness architecture should instead preserve:

```text
support_mass = 5
contradiction_mass = -5
aggregate displacement = 1
```

while retaining both witness sets.

Thus:

```text
equilibrium
```

does not necessarily mean:

```text
lack of evidence
```

It may mean:

```text
substantial opposing evidence
```

These conditions should be distinguishable.

---

# 20. Contradiction as a Reason to Observe Again

This produces one of the most important WG-RNN behaviors.

If the system contains:

```text
strong support
+
strong contradiction
```

the preferred result should often be:

```text
REQUEST MORE WITNESSES
```

rather than:

```text
average everything and answer confidently
```

The cognitive system can therefore output:

```text
IndependentWitnessRequest
{
    subject
    unresolved_claim
    desired_source_family
    evidence_gap
}
```

The WG-RNN becomes an **active observer**.

---

# 21. Recurrent Update

The recurrent system can be written abstractly as:

```text
e_t = Πᴅ(W_t)
```

then:

```text
W̃_t =
Ψᴅ(
    W̃_{t-1},
    e_t,
    chronology_t,
    provenance_t,
    context_t
)
```

The neural witness gate becomes:

```text
g_t =
Gᴅ(
    e_t,
    W̃_t,
    contradiction_t,
    freshness_t,
    novelty_t,
    task_t
)
```

Then:

```text
r_t = g_t ⊗ e_t
```

and the recurrent candidate:

```text
c_t =
(U ⊗ᴹ h_{t-1})
⊕
(W ⊗ᴹ r_t)
⊕
b
```

followed by:

```text
h_t = Φᴅ(c_t)
```

where `⊗ᴹ` denotes DUO-native matrix composition.

---

# 22. DUO Matrix Multiplication

The DUO specification defines:

```text
Cᵢⱼ =
(Aᵢ₁ ⊗ B₁ⱼ)
⊕
(Aᵢ₂ ⊗ B₂ⱼ)
⊕
...
⊕
(Aᵢₙ ⊗ Bₙⱼ)
```

with the accumulator initialized to:

```text
1
```

rather than zero.

The corresponding identity matrix is:

```text
Iᴅ =

[ 2 1 1 ]
[ 1 2 1 ]
[ 1 1 2 ]
```

because:

```text
2 = multiplicative identity
1 = additive identity
```

---

# 23. Native DUO Computation

The DUO specification proposes a native API based on:

```text
successor
predecessor
mirror
compare
add
subtract
multiply
activation
gradient_transition
compose
```

rather than requiring the core engine to continually convert states to conventional integers or floating point.

For bounded state spaces, operations can be implemented using canonical tables:

```text
ADD
MUL
SUCCESSOR
PREDECESSOR
MIRROR
ACTIVATION
ACTIVATION_DERIVATIVE
```

This makes each state transition exact.

---

# 24. Recurrent Decay Without Floating Multipliers

The earlier witness-state design used fractional decay factors.

A more native DUO approach is transition decay.

Define:

```text
toward_origin(x)
```

such that:

```text
7  → 6
6  → 5
5  → 4
4  → 3
3  → 2
2  → 1

-7 → -6
-6 → -5
-5 → -4
-4 → -3
-3 → -2
-2 → 1
```

A decay profile controls **when** a transition occurs.

For example:

```text
short-lived evidence:
    move one state toward origin frequently

persistent autobiographical evidence:
    move one state toward origin rarely

unreliable evidence:
    decay quickly

strong repeatedly revalidated evidence:
    persistence timer refreshed
```

This replaces:

```text
x = λx
```

with:

```text
if decay_transition_due:
    x = toward_origin(x)
```

---

# 25. Exact Persistence

Floating decay might produce:

```text
7
6.3
5.67
5.103
4.5927
...
```

A discrete witnessed system might instead produce:

```text
7
7
7
6
6
6
5
5
4
...
```

depending on persistence policy.

The important interpretation is:

> The state remains exactly what it is until an authorized state-transition condition occurs.

This is highly compatible with audit-oriented recurrent memory.

---

# 26. Deterministic Replay

Given:

```text
initial state
ordered witness sequence
projection policy
gate policy
DUO operator definitions
decay schedule
```

the cognitive trajectory can be replayed.

Example:

```text
initial = 4

Witness A:
    supporting transition
    4 → 5

No witness:
    state remains 5

Decay:
    5 → 4

Witness B:
    contradictory transition
    4 → 3
```

Final:

```text
3
```

The complete trajectory can be independently reconstructed.

---

# 27. WG-RNN Input Types

The WG-RNN should not have one monolithic “input tensor.”

Inputs can be divided into categories.

## 27.1 Primary witnessed observations

```text
text witness
image witness
audio witness
video witness
sensor witness
database witness
document witness
code witness
CAD witness
external model witness
```

---

## 27.2 Historical witness state

```text
previous recurrent state
previous predictions
previous contradictions
open callbacks
long-term concepts
source history
subject history
```

---

## 27.3 Environmental state

```text
task context
current authority domain
current workspace
current time relation
source availability
runtime health
network availability
model availability
```

---

## 27.4 Policy state

```text
allowed actions
allowed sources
authority restrictions
privacy constraints
verification requirements
freshness requirements
```

---

## 27.5 Memory retrieval

Retrieved memories should themselves arrive through witnessed objects or witnessed references.

Similarity search can answer:

```text
what might be relevant?
```

It cannot answer:

```text
what is authoritative?
```

---

# 28. Multimodal Input

A multimodal witness architecture can use modality-specific encoders:

```text
text encoder
image encoder
audio encoder
video encoder
CAD encoder
sensor encoder
structured-data encoder
```

but all encoders should ultimately produce:

```text
candidate semantic features
+
source references
```

rather than free-floating facts.

For example:

```text
ImageObservation
{
    detected_object: "vehicle"
    source_region: bbox(...)
    frame_id
    confidence_feature
}
```

The fact that a visual model detected something is itself a witnessable observation.

---

# 29. Models as Evidence Observers

External neural networks, language models, computer-vision models, classical algorithms, and statistical systems can participate as **observers**.

Their output becomes:

```text
ModelObservationWitness
```

not:

```text
truth
```

This means the WG-RNN can wrap many kinds of models without giving any one of them epistemic authority.

---

# 30. Output Architecture

The WG-RNN should also have multiple output families.

## 30.1 Cognitive-state output

Internal recurrent state:

```text
DUO state vectors
concept states
memory states
support trajectories
contradiction trajectories
regime states
novelty states
```

---

## 30.2 Prediction output

```text
PredictedWitness
PredictedEvent
PredictedStateTransition
ExpectedObservation
```

These predictions are hypotheses.

---

## 30.3 Candidate relation output

For example:

```text
CandidateEvidenceRelation
{
    subject_a
    proposed_relation
    subject_b
    supporting_witnesses
}
```

This does not become a canonical evidence edge until verified.

---

# 31. Witness Request Output

The WG-RNN may determine that it lacks sufficient evidence.

It then generates:

```text
WitnessRequest
```

For example:

```text
Need:
    independent confirmation of object identity

Preferred sources:
    image
    structured identity record

Reason:
    current evidence contradictory
```

This transforms uncertainty into observation planning.

---

# 32. Tool or Action Proposal

The network may generate:

```text
ActionProposal
```

Examples:

```text
run diagnostic
query database
inspect file
capture sensor reading
re-run test
ask user
search corpus
invoke proof checker
run compiler
```

Policy must still determine whether the action is permitted.

---

# 33. Natural-Language Output

Human-facing responses are another output surface.

The response generator should receive:

```text
candidate response
supporting witness references
confidence state
contradiction state
unresolved uncertainty
authority status
```

This permits output such as:

```text
Supported by witnesses A, B, and C.

Witness D contradicts one portion.

The unresolved portion requires additional observation.
```

instead of hiding uncertainty inside a probability distribution.

---

# 34. Canonical Authority Output

Only the deterministic authority path may produce objects such as:

```text
AcceptedEvidenceGraphEdge
VerifiedGateResult
AggregateResult
ActivationRecord
CanonicalDerivedObject
```

A recurrent cell cannot emit these directly.

The allowed flow is:

```text
WG-RNN proposal
      ↓
deterministic verifier
      ↓
accepted or rejected
```

---

# 35. Input/Output Loop

The complete I/O loop becomes:

```text
                    EXTERNAL WORLD
                          │
                          ▼
                    raw observation
                          │
                          ▼
                   witness capture
                          │
                          ▼
                  schema validation
                          │
                          ▼
               provenance / attestation
                          │
                          ▼
                    revalidation
                          │
                  ┌───────┴────────┐
                  │                │
               reject            admit
                  │                │
                  ▼                ▼
          rejection object    DUO projection
                                   │
                                   ▼
                            WG-RNN recurrent
                                memory
                                   │
                     ┌─────────────┼─────────────┐
                     │             │             │
                     ▼             ▼             ▼
                 prediction     proposal      memory
                     │             │
                     └──────┬──────┘
                            ▼
                     witness request
                            │
                            ▼
                      EXTERNAL WORLD
                            │
                            ▼
                       new witness
```

This is an **observation-driven cognitive loop**.

---

# 36. Learning

Learning itself should be treated as a first-class witnessed process.

A weight transition should not be an unexplained mutation.

Conceptually:

```text
WeightTransitionWitness
{
    weight_id
    previous_state
    proposed_state
    resulting_state

    training_example_ids
    gradient_or_transition_state
    learning_gate
    optimizer_policy
    model_version
    duo_version
    chronology
}
```

This creates provenance not merely for inputs, but for **learning itself**.

---

# 37. DUO Gradient Concepts

The attached DUO draft defines a transition derivative:

```text
D⁺f(x) = f(S(x)) ⊖ f(x)
```

and a symmetric transition gradient:

```text
G(w) = L(S(w)) ⊖ L(P(w))
```

with a simple discrete optimization procedure:

```text
evaluate current
evaluate successor
evaluate predecessor

if successor improves loss:
    move successor

if predecessor improves loss:
    move predecessor

otherwise:
    remain unchanged
```



This naturally fits a symbolic state system.

---

# 38. Minimum Loss

If:

```text
prediction = target
```

then:

```text
error = prediction ⊖ target = 1
```

and:

```text
loss = 1 ⊗ 1 = 1
```

Thus minimum loss is:

```text
1
```

not zero.

Again:

```text
1
```

is not absence.

It is a valid optimum/origin state.

---

# 39. Witness-Gated Learning

Not every training observation should be allowed to modify the model.

A learning gate could evaluate:

```text
source provenance
freshness
revalidation
contradiction
novelty
quality
domain relevance
poisoning indicators
policy
```

Only admitted examples produce learning transitions.

If a training example is rejected:

```text
weight_before = 4
weight_after  = 4
```

because:

```text
no authorized transition occurred
```

not because:

```text
gradient = zero
```

This distinction is semantically important.

---

# 40. Weight State Provenance

Suppose:

```text
weight state = 3
```

A witnessed update moves:

```text
3 → 4
```

The runtime can retain:

```text
why?
```

Answer:

```text
training witness set: ...
loss comparison: ...
learning policy: ...
transition rule: successor
model version: ...
```

Thus neural parameters become historically auditable objects.

---

# 41. Model Evolution

A trained model version can itself be represented as a witness-linked object:

```text
ModelVersion
{
    parent_model
    training_run
    witness_corpus
    transition_log_root
    benchmark_results
    safety_results
    model_hash
}
```

Model promotion then becomes a witnessed governance event rather than simply overwriting weights.

---

# 42. Continuous Quantities

DUO-MATH does not automatically eliminate the need to observe continuous quantities.

A sensor may legitimately produce:

```text
23.714 °C
```

A scientific measurement may legitimately contain conventional decimals.

A source document may contain:

```text
0.001
```

The Witness Contract must preserve those observations faithfully.

DUO should not rewrite history.

Instead:

```text
raw observation:
    23.714 °C

DUO cognitive projection:
    thermal_state = 4
```

The projection rule must be explicit.

---

# 43. Exact Observation vs Cognitive Interpretation

This distinction is essential:

```text
Observed value
        ≠
Cognitive state
```

Example:

```text
sensor reading:
    23.714 °C

historical baseline:
    18.0–20.0 °C

derived DUO deviation:
    4
```

The system can later modify its interpretation without modifying the original observation.

---

# 44. Binary Hardware Does Not Define DUO Arithmetic

Commodity CPUs and GPUs physically store data in binary.

That is unavoidable with existing hardware.

But binary storage does not require the semantic computation model to be binary positional arithmetic.

The DUO specification proposes representing states as:

```text
opaque handles
enum-like values
one-hot states
table indices
```

and executing operations through transition tables.

Thus binary becomes a **transport encoding**, not the mathematical definition of the state.

---

# 45. GPU Kernel

A DUO matrix kernel can execute:

```text
accumulator = 1

for each term:
    product =
        DUO_MUL[a][b]

    accumulator =
        DUO_ADD[accumulator][product]
```

The current DUO draft describes this DUO-GEMM model directly.

For bounded domains, operator tables can reside in fast GPU memory.

---

# 46. DMAC

A natural accelerator instruction is:

```text
DMAC accumulator, a, b
```

meaning:

```text
accumulator =
    accumulator
    ⊕
    (a ⊗ b)
```

The accumulator begins at:

```text
1
```

The DUO paper already identifies this as a useful future hardware primitive.

---

# 47. Parallel Reduction

Because the proposed DUO addition inherits associativity through the stated integer isomorphism, a bounded implementation may reduce terms in parallel.

Conceptually:

```text
p1 ⊕ p2
p3 ⊕ p4
p5 ⊕ p6
p7 ⊕ p8
```

then:

```text
r1 ⊕ r2
r3 ⊕ r4
```

then:

```text
s1 ⊕ s2
```

The DUO GPU section already proposes tree reduction on this basis.

For a production witness runtime, associativity and bounded overflow behavior should nevertheless be formally tested for every concrete implementation domain.

---

# 48. Recurrent Memory Cell

A complete memory cell might conceptually resemble:

```text
WitnessMemoryCell
{
    canonical_state: 4

    support_state: 5
    contradiction_state: -2

    freshness: 6
    novelty: 3
    persistence: 7
    confidence: 5

    supporting_witnesses: [...]
    contradicting_witnesses: [...]

    previous_state: 3

    latest_transition:
    {
        witness_id
        gate_state
        operator
        timestamp
        policy_id
    }
}
```

The cell therefore contains both:

```text
state
```

and:

```text
why that state exists
```

---

# 49. Memory as a Witness Graph

Long-term memory can then become a graph of:

```text
base objects
meta objects
witnesses
state transitions
concepts
episodes
relationships
contradictions
supersessions
predictions
revalidations
```

A recurrent memory is not merely a vector.

It is a vector **with a recoverable evidence history**.

---

# 50. Base Objects

Base objects preserve original information:

```text
text
image
audio
video
document
CAD file
database record
sensor event
code artifact
```

They should remain immutable or versioned.

---

# 51. Meta Objects

Meta objects describe identified concepts:

```text
person
object
claim
event
measurement
relationship
location
topic
behavior
motif
code symbol
mathematical object
```

Every meta object should retain references back to the base objects that caused its existence.

---

# 52. Witness Connections

Witness connections record:

```text
supports
contradicts
derived_from
observed_by
revalidated_by
caused_transition
supersedes
temporally_precedes
temporally_overlaps
```

This allows the memory system to reconstruct reasoning pathways.

---

# 53. Prediction vs Observation

The architecture must preserve:

```text
prediction
≠
observation
```

If the WG-RNN predicts:

```text
event X will occur
```

the output becomes:

```text
PredictionObject
```

Later:

```text
WitnessObject
```

records what actually happened.

The two may then be compared.

---

# 54. Recurrent Coherence

The difference between:

```text
expected witness
```

and:

```text
observed witness
```

can generate a DUO coherence-displacement state.

For example:

```text
expected = strong match
observed = contradiction
```

may increase:

```text
coherence_displacement
```

and trigger:

```text
regime change
additional observation
memory reconsideration
model update
```

---

# 55. Authority Activation State

Draft 5.3.18 already introduces a non-authoritative `ActivationStateVector/v1` that may expose the twelve authority gates as a positive ordinal state vector suitable for zero-free tensor work. It may also represent freshness, contradiction pressure, replay status, revalidation, and graph completeness. 

This is an especially natural point of integration.

For example:

```text
ActivationStateVectorDUO
[
    gate_1_state,
    gate_2_state,
    ...
    gate_12_state
]
```

However:

> this vector is a rendering and scheduling interface.

It does not itself create authority.

---

# 56. Interpretability

One of the principal benefits of the design is that recurrent state may become human-readable.

Instead of:

```text
hidden_unit_918 = -0.138492
```

the system may expose:

```text
claim support:
    5

contradiction:
    -3

freshness:
    7

source consistency:
    4

novelty:
    3
```

with witness references beneath every dimension.

The DUO draft explicitly identifies exact, interpretable recurrent state as a primary application.

---

# 57. Explanation Output

An explanation system could reconstruct:

```text
state began at 1

Witness A:
    support
    state 1 → 2

Witness B:
    corroboration
    state 2 → 3

Witness C:
    corroboration
    state 3 → 4

Witness D:
    contradiction
    state 4 → 3

Current state:
    3
```

This is a much stronger explanation than:

```text
the neural network is 72% confident
```

when provenance matters.

---

# 58. Input Validation Invariants

Every input should obey at least the following conceptual rules:

```text
1. Source identity is explicit where available.

2. Original content is preserved.

3. Missing does not equal origin.

4. Invalid does not equal contradiction.

5. Prediction does not equal observation.

6. Neural inference does not equal authority.

7. Revalidation does not overwrite original evidence.

8. Cross-domain evidence cannot silently gain new authority.

9. Every cognitive projection identifies its policy.

10. Every model-changing transition is replayable.
```

---

# 59. Output Invariants

Outputs should similarly obey:

```text
1. Cognitive output is labeled as cognitive output.

2. Predicted facts remain predictions until witnessed.

3. Rejected proposals remain inspectable.

4. Contradictions are retained rather than erased.

5. State origin 1 is never used as a missing-value sentinel.

6. Authority-bearing results originate only from the verifier.

7. Generated actions remain policy-gated.

8. Learning changes retain provenance.
```

---

# 60. Fail-Closed Behavior

The Witness Contract already follows a fail-closed philosophy for unknown schemas, authority domains, cryptographic suites, policies, gates, keys, and related conditions. 

The DUO/WG-RNN layer should follow a similar semantic rule.

For example:

```text
unknown state encoding
```

must not become:

```text
1
```

Instead:

```text
INVALID_STATE
```

Likewise:

```text
missing feature
```

must not become:

```text
1
```

unless a specific projection policy explicitly states that the semantic neutral state was actually observed.

---

# 61. Separation from Cryptography

DUO-MATH must not replace standard cryptographic primitives.

Draft 5.3.18 explicitly states that Duotronic mathematics informs state representation, candidate traversal, visualization, scheduling, and test generation rather than substituting for established cryptography. 

Thus cryptographic operations remain defined by their required suites.

DUO may represent cognitive state *about* a signature.

It does not replace the signature algorithm.

---

# 62. Suggested Schema Family

The integrated architecture would benefit from schemas such as:

```text
DuoState/v1

DuoFeatureVector/v1

WitnessDuoProjection/v1

DuoStateTransitionWitness/v1

RecurrentWitnessStateDuo/v1

WitnessNeuralGateState/v1

DuoLearningTransitionWitness/v1

DuoModelVersionWitness/v1

WitnessRequest/v1

PredictionWitness/v1

CandidateEvidenceRelation/v1
```

Each should be versioned independently.

---

# 63. Recommended State Representation

A DUO state should contain more than a string.

For example:

```text
{
    "symbol": "4a",
    "algebra": "duo-math/v1",
    "domain": "signed",
    "state_kind": "numeric"
}
```

External semantics might instead use:

```text
{
    "state_kind": "unobserved"
}
```

No fake numeric placeholder is required.

---

# 64. Canonical vs Runtime Representation

The canonical form may be:

```text
"1a"
```

while a GPU runtime stores:

```text
enum 9
```

or:

```text
one-hot state handle
```

or another opaque physical representation.

The requirement is:

```text
canonical state
→ runtime state
→ canonical state
```

must round-trip exactly.

---

# 65. Canonical Replay

A replay record should therefore retain:

```text
DUO algebra version
operator-table version
projection version
gate version
model version
witness sequence
execution order where relevant
```

This allows different hardware implementations to reconstruct the same cognitive trajectory.

---

# 66. Offline Operation

The architecture naturally supports offline-first execution because its critical epistemic components can remain local:

```text
witness store
DUO runtime
WG-RNN
memory
policy engine
verifier
model observers
```

External networks may provide additional witnesses, but network availability should not be required for internal state continuity.

An internet outage should therefore reduce available observation sources rather than destroy the cognitive architecture itself.

---

# 67. Multi-Model Augmented Intelligence

A powerful consequence of the witness model is that multiple models need not agree internally.

For example:

```text
vision model A
language model B
symbolic solver C
database query D
human observer E
```

may all produce distinct witnesses.

The WG-RNN can accumulate:

```text
support
contradiction
source history
temporal behavior
```

without turning majority agreement into automatic authority.

---

# 68. Model-Agnostic Observation

This permits an architecture where:

```text
LLM
CNN
RNN
transformer
vision-language model
symbolic engine
search engine
solver
human
sensor
```

are all evidence observers.

The WG-RNN is not required to treat any one model family as the definition of intelligence.

---

# 69. Why This Is Augmented Intelligence

The goal is not simply autonomous prediction.

It is an intelligence system capable of saying:

```text
I observed X.

Witness A supports X.

Witness B contradicts it.

My present recurrent state is Y.

I predict Z.

I do not have enough evidence to canonize Z.

I therefore require another witness.
```

That is fundamentally different from producing the most statistically likely continuation.

---

# 70. What DUO-MATH Contributes

DUO contributes:

```text
zeroless state semantics
exact origin
exact successor/predecessor
signed opposition
symbolic state traversal
exact discrete persistence
auditable transitions
native neutral gate
native multiplicative pass gate
canonical nonzero indexing
```

The attached DUO paper characterizes its intended strength similarly: a coherent symbolic substrate for witness-gated machine learning and augmented intelligence rather than a universal replacement for conventional numerical computation.

---

# 71. What the Witness Contract Contributes

The Witness Contract contributes:

```text
identity
provenance
chronology
attestation
revalidation
typed evidence relationships
authority domains
policy
freshness
revocation
cryptographic binding
deterministic acceptance
fail-closed behavior
```

DUO does not replace these.

---

# 72. What the WG-RNN Contributes

The WG-RNN contributes:

```text
temporal learning
witness accumulation
memory persistence
pattern recognition
prediction
candidate relationship discovery
contradiction detection
contextual gating
active witness seeking
adaptive scheduling
```

Its learned state remains subordinate to deterministic evidence authority.

---

# 73. Combined Architecture

The resulting system can be summarized as:

```text
                ┌───────────────────────┐
                │    EXTERNAL WORLD     │
                └───────────┬───────────┘
                            │
                            ▼
                     RAW OBSERVATION
                            │
                            ▼
                 WITNESS ENCAPSULATION
                            │
                            ▼
                PROVENANCE / VALIDATION
                            │
                ┌───────────┴───────────┐
                │                       │
             REJECT                  ADMIT
                │                       │
                ▼                       ▼
       rejection evidence         DUO PROJECTION
                                        │
                                        ▼
                             WITNESS-GATED RECURRENCE
                                        │
                           ┌────────────┼────────────┐
                           │            │            │
                           ▼            ▼            ▼
                        MEMORY      PREDICTION    PROPOSAL
                           │            │            │
                           └────────────┼────────────┘
                                        │
                                        ▼
                                WITNESS REQUEST
                                        │
                                        ▼
                                 NEW OBSERVATION
                                        │
                                        ▼
                             DETERMINISTIC VERIFIER
                                        │
                                ┌───────┴───────┐
                                │               │
                              reject          accept
                                │               │
                                ▼               ▼
                         retained conflict   AUTHORITY
```

---

# 74. The Core Feedback Cycle

The architecture therefore follows:

```text
WITNESS
   ↓
VALIDATE
   ↓
REMEMBER
   ↓
INFER
   ↓
QUESTION
   ↓
SEEK WITNESS
   ↓
VERIFY
   ↓
REMEMBER AGAIN
```

This may be more useful as a description of the system than the conventional neural formulation:

```text
INPUT
↓
MODEL
↓
OUTPUT
```

---

# 75. Research Questions

Several areas require further work.

## 75.1 Continuous mathematics

The current DUO draft explicitly recognizes that continuous probability, softmax, and high-precision continuous optimization need extensions.

Research is needed into whether these should use:

```text
DUO rational extensions
ordered interval states
probability witness objects
hybrid numeric kernels
```

rather than forcing all continuous quantities into discrete states.

---

## 75.2 Large-state operator tables

Small DUO domains can use complete lookup tables.

Large or unbounded domains require more efficient symbolic operator implementations.

---

## 75.3 Recurrent decay

Transition-based decay should be benchmarked against conventional exponential decay.

The important question is not whether it perfectly imitates floating-point decay.

The question is:

> Does exact transition decay produce useful and more interpretable recurrent memory?

---

## 75.4 Learning performance

Discrete successor/predecessor training may be slower than conventional gradient descent.

Hybrid training strategies may therefore be appropriate during experimentation, provided the distinction between compatibility computation and native DUO computation remains explicit.

---

## 75.5 Formal verification

Important properties to verify include:

```text
closure
associativity
commutativity where claimed
distributivity
mirror involution
successor/predecessor inverse behavior
canonical encoding uniqueness
bounded-domain overflow behavior
parallel reduction equivalence
CPU/GPU operator parity
```

---

# 76. Recommended Development Sequence

A practical implementation program would proceed in roughly this order:

```text
1. Freeze the DUO canonical grammar.

2. Implement successor, predecessor, mirror, compare.

3. Implement canonical add/subtract/multiply.

4. Build conformance vectors.

5. Define explicit nonnumeric missing-state tokens.

6. Define WitnessDuoProjection/v1.

7. Implement DUO recurrent witness state.

8. Replace zero-initialized witness accumulators.

9. Implement neural witness gates.

10. Implement transition-based decay.

11. Implement state-transition provenance.

12. Implement DUO matrix kernels.

13. Implement witnessed learning transitions.

14. Integrate witness requests and active observation.

15. Connect deterministic authority verification.

16. Benchmark against conventional recurrent baselines.

17. Formalize critical algebraic and replay invariants.

18. Add hardware acceleration only after semantic conformance.
```

---

# 77. Foundational Invariants

The architecture should preserve the following rules permanently:

```text
0 does not exist as a native DUO numeral.

1 is a real state.

1 means origin, not missing.

2 is multiplicative identity.

UNKNOWN is not 1.

ABSENT is not 1.

UNOBSERVED is not 1.

INVALID is not 1.

REJECTED is not 1.

contradiction is not absence.

prediction is not observation.

recurrence is not authority.

confidence is not proof.

similarity is not evidence.

model agreement is not authority.

DUO state is not provenance.

provenance is not cognitive state.

a witness can change cognition.

cognition cannot rewrite its original witness.

a model may propose a fact.

only the authority system may canonize an authoritative fact.
```

---

# 78. Conclusion

DUO-MATH, the Duotronics Witness Contract, and the Witness-Gated Recurrent Neural Network solve three different problems.

DUO-MATH provides the **state algebra**.

The Witness Contract provides the **epistemic and authority structure**.

The WG-RNN provides the **adaptive temporal cognition**.

Together they produce a computational architecture in which a machine can learn without being allowed to confuse learning with proof.

The DUO-MATH specification establishes a system where `0` does not exist, `1` is the shared origin and additive identity, `2` is the multiplicative identity, cancellation returns to `1`, symbolic states have exact predecessors and successors, and missing information remains outside the numeral domain.

The Witness Contract then ensures that observations retain provenance, chronology, revalidation, domain identity, and deterministic authority semantics.

The WG-RNN sits between observation and authority.

Its task is not to declare truth.

Its task is to:

```text
remember witnessed experience,
detect patterns,
retain contradictions,
predict future observations,
propose relationships,
identify missing evidence,
and decide what should be witnessed next.
```

The strongest version of the design therefore does not ask:

```text
How can a neural network produce the best output from an input?
```

It asks:

```text
Given everything that has actually been witnessed,
what state should the system hold,
what should it expect,
what does it still not know,
and what witness should it acquire next?
```

The input to the architecture is therefore not merely data.

It is:

```text
witnessed observation + provenance + context.
```

The internal state is not merely activation.

It is:

```text
witness-conditioned recurrent state + transition history.
```

And the output is not merely an answer.

It may be:

```text
a prediction,
a candidate relation,
a memory update,
an action proposal,
an explanation,
a contradiction,
or a request for another witness.
```

Only after those outputs are externally witnessed, deterministically evaluated, and admitted by policy may they become authoritative evidence.

This produces a fundamentally different machine-learning loop:

```text
OBSERVE
   ↓
WITNESS
   ↓
REMEMBER
   ↓
REASON
   ↓
QUESTION
   ↓
OBSERVE AGAIN
```

The most important consequence of DUO-MATH is therefore not simply that it removes the numeral zero.

It is that it forces the architecture to distinguish:

```text
nothing was observed
```

from:

```text
a valid state was observed at equilibrium.
```

That single distinction propagates through input representation, recurrent memory, gating, learning, contradiction handling, output generation, and evidence authority.

The result is a plausible foundation for a form of augmented intelligence whose primitive unit is not an untraceable floating activation, but a **witnessed transition between canonical states**.