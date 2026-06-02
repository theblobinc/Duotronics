---- MODULE NonCollapseAxioms ----
EXTENDS Naturals, Sequences

PrimitiveStates ==
  {"zero", "absence", "unknown", "invalid", "empty", "null",
   "computational_evidence", "theorem", "conjectural",
   "self_trained", "authoritative", "audit_only", "active",
   "observation", "proof", "explanation", "fact",
   "policy_approval", "human_attestation", "synthetic_witness",
   "activation_witness",
   "probabilistic_prior", "probabilistic_likelihood", "probabilistic_posterior",
   "bayesian_decision_support", "bayesian_calibration_evidence",
   "knot_diagram_presentation", "knot_braid_presentation",
   "knot_reidemeister_trace", "knot_invariant_evidence",
   "knot_canonical_form", "knot_equivalence_claim"}

ForbiddenPairClasses ==
  {<<"zero", "absence", "value_distinction">>,
   <<"unknown", "invalid", "epistemic_distinction">>,
   <<"empty", "null", "value_distinction">>,
   <<"computational_evidence", "theorem", "formal_promotion">>,
   <<"conjectural", "theorem", "formal_promotion">>,
   <<"self_trained", "authoritative", "authority_distinction">>,
   <<"audit_only", "active", "runtime_distinction">>,
   <<"observation", "proof", "proof_distinction">>,
   <<"explanation", "fact", "epistemic_distinction">>,
   <<"policy_approval", "human_attestation", "authority_distinction">>,
   <<"synthetic_witness", "activation_witness", "model_distinction">>}

ForbiddenPairs == {<<p[1], p[2]>> : p \in ForbiddenPairClasses}
ProofWitnessClasses == {"formal_promotion", "proof_distinction"}
AuthorityWitnessClasses == {"authority_distinction", "model_distinction", "runtime_distinction"}

SameState(s, t) == s = t
ForbiddenCollapse(s, t) == <<s, t>> \in ForbiddenPairs \/ <<t, s>> \in ForbiddenPairs

PairClass(s, t) ==
  CHOOSE c \in {p[3] : p \in ForbiddenPairClasses /\ (<<p[1], p[2]>> = <<s, t>> \/ <<p[2], p[1]>> = <<s, t>>)} : TRUE

ProofWitnessRequired(s, t) == ForbiddenCollapse(s, t) /\ PairClass(s, t) \in ProofWitnessClasses
AuthorityWitnessRequired(s, t) == ForbiddenCollapse(s, t) /\ PairClass(s, t) \in AuthorityWitnessClasses

NoSilentCollapse(s, t, externalWitness, proofWitness, authorityWitness) ==
  IF SameState(s, t) THEN TRUE
  ELSE IF ForbiddenCollapse(s, t) THEN
    /\ externalWitness # ""
    /\ (ProofWitnessRequired(s, t) => proofWitness # "")
    /\ (AuthorityWitnessRequired(s, t) => authorityWitness # "")
  ELSE externalWitness # ""

TransitionAllowed(s, t, externalWitness, proofWitness, authorityWitness) ==
  /\ s \in PrimitiveStates
  /\ t \in PrimitiveStates
  /\ NoSilentCollapse(s, t, externalWitness, proofWitness, authorityWitness)

THEOREM ForbiddenPairsAreDistinct ==
  \A p \in ForbiddenPairs : p[1] # p[2]

====
