-------------------------- MODULE ProofAuthorityV3 --------------------------
EXTENDS Naturals, Sequences, TLC

VARIABLES statementBound, axiomClean, signaturesVerified, keyState,
          gateRecorded, authoritative, claimStatus, gateHistory

vars == <<statementBound, axiomClean, signaturesVerified, keyState,
          gateRecorded, authoritative, claimStatus, gateHistory>>

Conjecture == "conjecture"
Theorem == "theorem"
Active == "active"
Revoked == "revoked"
Superseded == "superseded"

Init ==
  /\ statementBound = FALSE
  /\ axiomClean = FALSE
  /\ signaturesVerified = FALSE
  /\ keyState = Active
  /\ gateRecorded = FALSE
  /\ authoritative = FALSE
  /\ claimStatus = Conjecture
  /\ gateHistory = <<>>

BindStatement ==
  /\ ~statementBound
  /\ statementBound' = TRUE
  /\ UNCHANGED <<axiomClean, signaturesVerified, keyState, gateRecorded,
                 authoritative, claimStatus, gateHistory>>

InspectCleanAxioms ==
  /\ statementBound
  /\ ~axiomClean
  /\ axiomClean' = TRUE
  /\ UNCHANGED <<statementBound, signaturesVerified, keyState, gateRecorded,
                 authoritative, claimStatus, gateHistory>>

VerifySignatures ==
  /\ statementBound
  /\ axiomClean
  /\ ~signaturesVerified
  /\ signaturesVerified' = TRUE
  /\ UNCHANGED <<statementBound, axiomClean, keyState, gateRecorded,
                 authoritative, claimStatus, gateHistory>>

Promote ==
  /\ statementBound
  /\ axiomClean
  /\ signaturesVerified
  /\ keyState = Active
  /\ ~gateRecorded
  /\ gateRecorded' = TRUE
  /\ authoritative' = TRUE
  /\ claimStatus' = Theorem
  /\ gateHistory' = Append(gateHistory, "allowed")
  /\ UNCHANGED <<statementBound, axiomClean, signaturesVerified, keyState>>

RevokeKey ==
  /\ keyState = Active
  /\ keyState' = Revoked
  /\ authoritative' = FALSE
  /\ UNCHANGED <<statementBound, axiomClean, signaturesVerified, gateRecorded,
                 claimStatus, gateHistory>>

SupersedeKey ==
  /\ keyState = Active
  /\ keyState' = Superseded
  /\ authoritative' = FALSE
  /\ UNCHANGED <<statementBound, axiomClean, signaturesVerified, gateRecorded,
                 claimStatus, gateHistory>>

Stutter == UNCHANGED vars

Next == BindStatement \/ InspectCleanAxioms \/ VerifySignatures \/ Promote
        \/ RevokeKey \/ SupersedeKey \/ Stutter

TypeOK ==
  /\ statementBound \in BOOLEAN
  /\ axiomClean \in BOOLEAN
  /\ signaturesVerified \in BOOLEAN
  /\ keyState \in {Active, Revoked, Superseded}
  /\ gateRecorded \in BOOLEAN
  /\ authoritative \in BOOLEAN
  /\ claimStatus \in {Conjecture, Theorem}
  /\ gateHistory \in Seq({"allowed"})

AuthorityRequiresStatementBinding == authoritative => statementBound
AuthorityRequiresCleanAxioms == authoritative => axiomClean
AuthorityRequiresVerifiedSignatures == authoritative => signaturesVerified
AuthorityRequiresActiveKey == authoritative => keyState = Active
AuthorityRequiresGate == authoritative => gateRecorded
TheoremRequiresRecordedGate == claimStatus = Theorem => gateRecorded
GateIsAppendOnly == gateRecorded => Len(gateHistory) >= 1

Spec == Init /\ [][Next]_vars
=============================================================================
