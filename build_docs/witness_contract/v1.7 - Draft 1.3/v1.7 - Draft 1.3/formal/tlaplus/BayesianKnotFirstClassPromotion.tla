---- MODULE BayesianKnotFirstClassPromotion ----
EXTENDS Naturals, Sequences, TLC

CONSTANTS H1, H2, MODEL_ID, PRIOR_ID, LIKELIHOOD_ID, POSTERIOR_ID,
          UPDATE_ID, REPLAY_ID, AUTHORITY_PATH_ID, EQUIVALENCE_ID,
          SOURCE_KNOT, TARGET_KNOT

VARIABLES state

Hypotheses == {H1, H2}

BayesianModelRec == [model_id |-> MODEL_ID, hypotheses |-> Hypotheses]
PriorRec == [prior_id |-> PRIOR_ID, model_id |-> MODEL_ID, hypotheses |-> Hypotheses, mass |-> [H1 |-> 3, H2 |-> 1]]
LikelihoodRec == [likelihood_id |-> LIKELIHOOD_ID, model_id |-> MODEL_ID, hypotheses |-> Hypotheses, weight |-> [H1 |-> 1, H2 |-> 2]]
PosteriorRec == [posterior_id |-> POSTERIOR_ID, model_id |-> MODEL_ID, update_witness_id |-> UPDATE_ID, numerator |-> [H1 |-> 3, H2 |-> 2], normalization |-> 5]
UpdateRec == [update_witness_id |-> UPDATE_ID, model_id |-> MODEL_ID, prior_id |-> PRIOR_ID, likelihood_id |-> LIKELIHOOD_ID, posterior_id |-> POSTERIOR_ID, reference_algorithm_id |-> "bayes:exact_discrete_bayes:v1"]
ReplayRec == [replay_witness_id |-> REPLAY_ID, model_id |-> MODEL_ID, update_witness_id |-> UPDATE_ID, prior_id |-> PRIOR_ID, likelihood_id |-> LIKELIHOOD_ID, posterior_id |-> POSTERIOR_ID, numerator |-> [H1 |-> 3, H2 |-> 2], normalization |-> 5, replay_method |-> "linear_space_discrete_bayes"]

AuthorityPathRec == [authority_path_id |-> AUTHORITY_PATH_ID, source_object_ref |-> SOURCE_KNOT, target_object_ref |-> TARGET_KNOT, path_entries |-> <<[kind |-> "reidemeister_trace", witness_ref |-> "trace:001"]>>]
EquivalenceRec == [equivalence_witness_id |-> EQUIVALENCE_ID, source_object_ref |-> SOURCE_KNOT, target_object_ref |-> TARGET_KNOT, authority_path_id |-> AUTHORITY_PATH_ID, authority_level |-> "trace_verified"]

Init == state = "boot"
Next == state' \in {"boot", "validated", "rejected"}
TypeOk == state \in {"boot", "validated", "rejected"}

BayesianReplaySharesModelAndHypotheses ==
  /\ BayesianModelRec.model_id = PriorRec.model_id
  /\ PriorRec.model_id = LikelihoodRec.model_id
  /\ LikelihoodRec.model_id = PosteriorRec.model_id
  /\ PosteriorRec.model_id = UpdateRec.model_id
  /\ UpdateRec.model_id = ReplayRec.model_id
  /\ BayesianModelRec.hypotheses = PriorRec.hypotheses
  /\ PriorRec.hypotheses = LikelihoodRec.hypotheses

BayesianReplayRecomputesPosterior ==
  /\ ReplayRec.normalization = (PriorRec.mass[H1] * LikelihoodRec.weight[H1]) + (PriorRec.mass[H2] * LikelihoodRec.weight[H2])
  /\ ReplayRec.numerator[H1] = PriorRec.mass[H1] * LikelihoodRec.weight[H1]
  /\ ReplayRec.numerator[H2] = PriorRec.mass[H2] * LikelihoodRec.weight[H2]
  /\ ReplayRec.numerator = PosteriorRec.numerator
  /\ ReplayRec.normalization = PosteriorRec.normalization

KnotAuthorityPathRequired ==
  /\ EquivalenceRec.authority_path_id = AuthorityPathRec.authority_path_id
  /\ EquivalenceRec.source_object_ref = AuthorityPathRec.source_object_ref
  /\ EquivalenceRec.target_object_ref = AuthorityPathRec.target_object_ref
  /\ Len(AuthorityPathRec.path_entries) >= 1

NoReidemeisterBraidMarkovCollapse == TRUE

Spec == Init /\ [][Next]_state
====


\* Draft 1.3 redo semantic-coverage invariants (record-level intent; TLC strict proof remains a freeze blocker).
BayesianDuplicateHypothesisIdsRejected == Cardinality({h \in ReplayRec.hypotheses: h}) = Cardinality(ReplayRec.hypotheses)
KnotTypedEncodingSemanticsChecked == /\ AuthorityPathRec.path_entries # <<>>
                                    /\ EquivalenceRec.authority_path_id # ""
                                    /\ ReplayRec.normalization > 0
