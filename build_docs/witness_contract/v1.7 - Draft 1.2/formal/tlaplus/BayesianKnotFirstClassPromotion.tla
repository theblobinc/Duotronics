---- MODULE BayesianKnotFirstClassPromotion ----
EXTENDS Naturals, Sequences

CONSTANTS BayesianModel, Prior, Likelihood, Posterior, UpdateWitness, ReplayWitness,
          KnotDiagram, KnotBraid, KnotReidemeisterMove, KnotBraidRelation,
          KnotMarkovMove, KnotAuthorityPath, KnotEquivalence

VARIABLES state

Init == state = "boot"

TypeOk == state \in {"boot", "validated", "rejected"}

BayesianReplaySharesModelAndHypotheses ==
  /\ BayesianModel # Prior
  /\ Prior # Likelihood
  /\ UpdateWitness # ReplayWitness
  /\ Posterior # ReplayWitness

KnotAuthorityPathRequired ==
  /\ KnotAuthorityPath # KnotEquivalence
  /\ KnotDiagram # KnotEquivalence
  /\ KnotBraid # KnotEquivalence

NoReidemeisterBraidMarkovCollapse ==
  /\ KnotReidemeisterMove # KnotBraidRelation
  /\ KnotReidemeisterMove # KnotMarkovMove
  /\ KnotBraidRelation # KnotMarkovMove

Next == state' \in {"boot", "validated", "rejected"}

Spec == Init /\ [][Next]_state
====
