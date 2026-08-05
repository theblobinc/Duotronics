---- MODULE EvidenceClaimGraph ----
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Claims, Policies, MaxClaims

Operators == {"and", "or", "implies", "equivalent", "not", "xor", "temporal_since", "sequence", "aggregate_any", "aggregate_all"}
Statuses == {"unknown", "absent", "invalid", "draft", "observed", "computed", "proposed", "asserted", "deferred", "vetoed", "conjecture", "theorem", "replay_verified", "proof_verified", "policy_approved", "released"}
ProofRefs == {"", "proof_ref"}
UnaryPremises == {<<c>> : c \in Claims}
BinaryPremises == {<<c1, c2>> : c1 \in Claims, c2 \in Claims}
CandidatePremises == UnaryPremises \cup BinaryPremises
ClaimGraphRecord == [op : Operators, premises : CandidatePremises, policy : Policies]

VARIABLES claimGraph, witnesses, claimStatus
vars == <<claimGraph, witnesses, claimStatus>>

Init ==
  /\ claimGraph = {}
  /\ witnesses = {}
  /\ claimStatus = [c \in Claims |-> "unknown"]

ArityOk(op, premises) ==
  /\ op \in Operators
  /\ CASE op = "not" -> Len(premises) = 1
        [] op \in {"implies", "equivalent", "xor", "temporal_since"} -> Len(premises) = 2
        [] OTHER -> Len(premises) >= 2

Compose(premises, op, policy) ==
  /\ policy \in Policies
  /\ premises \in CandidatePremises
  /\ ArityOk(op, premises)
  /\ Cardinality(claimGraph) < MaxClaims
  /\ claimGraph' = claimGraph \cup {[op |-> op, premises |-> premises, policy |-> policy]}
  /\ witnesses' = witnesses \cup {<<"composition", op, premises, policy>>}
  /\ UNCHANGED claimStatus

Promote(c, source, target, policy, proofRef) ==
  /\ c \in Claims
  /\ source \in Statuses
  /\ target \in Statuses
  /\ policy \in Policies
  /\ proofRef \in ProofRefs
  /\ claimStatus[c] = source
  /\ (target \in {"theorem", "proof_verified"} => proofRef # "")
  /\ claimStatus' = [claimStatus EXCEPT ![c] = target]
  /\ witnesses' = witnesses \cup {<<"status_transition", c, source, target, policy, proofRef>>}
  /\ UNCHANGED claimGraph

Next ==
  \/ \E premises \in CandidatePremises, op \in Operators, p \in Policies : Compose(premises, op, p)
  \/ \E c \in Claims, s \in Statuses, t \in Statuses, p \in Policies, proof \in ProofRefs : Promote(c, s, t, p, proof)

Spec == Init /\ [][Next]_vars

TypeOk ==
  /\ claimGraph \subseteq ClaimGraphRecord
  /\ DOMAIN claimStatus = Claims
  /\ \A c \in Claims : claimStatus[c] \in Statuses

CompositionHasWitness ==
  \A g \in claimGraph :
    \E w \in witnesses :
      /\ Len(w) = 4
      /\ w[1] = "composition"
      /\ w[2] = g.op
      /\ w[3] = g.premises
      /\ w[4] = g.policy

TheoremPromotionHasProof ==
  \A c \in Claims :
    claimStatus[c] \in {"theorem", "proof_verified"} =>
      \E w \in witnesses :
        /\ Len(w) = 6
        /\ w[1] = "status_transition"
        /\ w[2] = c
        /\ w[4] \in {"theorem", "proof_verified"}
        /\ w[6] # ""

====
