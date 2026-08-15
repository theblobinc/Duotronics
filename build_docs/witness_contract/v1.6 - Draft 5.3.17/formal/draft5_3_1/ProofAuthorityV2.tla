--------------------------- MODULE ProofAuthorityV2 ---------------------------
EXTENDS Naturals, Sequences, TLC

VARIABLES evidenceReady, gateAllowed, claimStatus, gateHistory

vars == <<evidenceReady, gateAllowed, claimStatus, gateHistory>>

Conjecture == "conjecture"
Theorem == "theorem"

Init ==
  /\ evidenceReady = FALSE
  /\ gateAllowed = FALSE
  /\ claimStatus = Conjecture
  /\ gateHistory = <<>>

BindEvidence ==
  /\ evidenceReady = FALSE
  /\ evidenceReady' = TRUE
  /\ UNCHANGED <<gateAllowed, claimStatus, gateHistory>>

Promote ==
  /\ evidenceReady = TRUE
  /\ gateAllowed = FALSE
  /\ gateAllowed' = TRUE
  /\ claimStatus' = Theorem
  /\ gateHistory' = Append(gateHistory, "allowed")
  /\ UNCHANGED evidenceReady

RefuseUnboundPromotion ==
  /\ evidenceReady = FALSE
  /\ gateAllowed = FALSE
  /\ UNCHANGED vars

Stutter == UNCHANGED vars

Next == BindEvidence \/ Promote \/ RefuseUnboundPromotion \/ Stutter

TypeOK ==
  /\ evidenceReady \in BOOLEAN
  /\ gateAllowed \in BOOLEAN
  /\ claimStatus \in {Conjecture, Theorem}
  /\ gateHistory \in Seq({"allowed"})

GateRequiresBoundEvidence == gateAllowed => evidenceReady
TheoremRequiresGate == claimStatus = Theorem => gateAllowed
GateIsAppendOnly == gateAllowed => Len(gateHistory) >= 1

Spec == Init /\ [][Next]_vars

=============================================================================
