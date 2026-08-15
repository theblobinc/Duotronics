---- MODULE NonCollapseRuntime ----
EXTENDS Naturals, Sequences, FiniteSets, NonCollapseAxioms

CONSTANTS MaxTransitions

\* The model observes only absence versus presence; witness identity is
\* content-bound elsewhere and does not change these non-collapse invariants.
WitnessValues == {"", "witness"}
TransitionRecord == [
  source : PrimitiveStates,
  target : PrimitiveStates,
  externalWitness : WitnessValues,
  proofWitness : WitnessValues,
  authorityWitness : WitnessValues
]

VARIABLES transitions, currentState
vars == <<transitions, currentState>>

Init ==
  /\ transitions = {}
  /\ currentState \in PrimitiveStates

ApplyTransition(tr) ==
  /\ tr \in TransitionRecord
  /\ Cardinality(transitions) < MaxTransitions
  /\ tr.source = currentState
  /\ TransitionAllowed(tr.source, tr.target, tr.externalWitness, tr.proofWitness, tr.authorityWitness)
  /\ transitions' = transitions \cup {tr}
  /\ currentState' = tr.target

Next ==
  \E tr \in TransitionRecord : ApplyTransition(tr)

Spec == Init /\ [][Next]_vars

TypeOk ==
  /\ transitions \subseteq TransitionRecord
  /\ currentState \in PrimitiveStates
  /\ Cardinality(transitions) <= MaxTransitions

NoForbiddenCollapseWithoutExternalWitness ==
  \A tr \in transitions :
    ForbiddenCollapse(tr.source, tr.target) => tr.externalWitness # ""

ProofClassTransitionsHaveProofWitness ==
  \A tr \in transitions :
    ProofWitnessRequired(tr.source, tr.target) => tr.proofWitness # ""

AuthorityClassTransitionsHaveAuthorityWitness ==
  \A tr \in transitions :
    AuthorityWitnessRequired(tr.source, tr.target) => tr.authorityWitness # ""

NoSameStateWitnessRequired ==
  \A tr \in transitions : tr.source = tr.target => TRUE

====
