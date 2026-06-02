---- MODULE BayesianKnotFirstClassPromotion ----
EXTENDS Naturals, Sequences

CONSTANTS BayesianModel, Prior, Likelihood, Posterior, UpdateWitness, ReplayWitness,
          KnotDiagram, KnotBraid, KnotTrace, KnotInvariant, KnotAuthorityPath, KnotEquivalence

VARIABLES state

Init == state = "boot"

BayesFirstClass ==
  /\ BayesianModel # Prior
  /\ Prior # Posterior
  /\ Likelihood # Posterior
  /\ UpdateWitness # ReplayWitness

KnotFirstClass ==
  /\ KnotDiagram # KnotBraid
  /\ KnotInvariant # KnotEquivalence
  /\ KnotAuthorityPath # KnotEquivalence
  /\ KnotTrace # KnotEquivalence

NoCollapse == BayesFirstClass /\ KnotFirstClass

Next == state' \in {"boot", "validated", "rejected"}

Spec == Init /\ [][Next]_state

Invariant == NoCollapse
====
