-------------------------- MODULE ProofAuthorityV4 --------------------------
EXTENDS Naturals, Sequences, TLC

VARIABLES registryGoverned, toolchainBound, snapshotImmutable, cleanBuild,
          structuredInspection, governanceAuthorized, keyState, gateRecorded,
          currentAuthority, snapshotAuthority, gateHistory

vars == <<registryGoverned, toolchainBound, snapshotImmutable, cleanBuild,
          structuredInspection, governanceAuthorized, keyState, gateRecorded,
          currentAuthority, snapshotAuthority, gateHistory>>

Active == "active"
Revoked == "revoked"
Superseded == "superseded"
Unrecorded == "unrecorded"
Authoritative == "authoritative"
NonAuthoritative == "non_authoritative"

Init ==
  /\ registryGoverned = FALSE
  /\ toolchainBound = FALSE
  /\ snapshotImmutable = FALSE
  /\ cleanBuild = FALSE
  /\ structuredInspection = FALSE
  /\ governanceAuthorized = FALSE
  /\ keyState = Active
  /\ gateRecorded = FALSE
  /\ currentAuthority = FALSE
  /\ snapshotAuthority = Unrecorded
  /\ gateHistory = <<>>

GovernRegistry ==
  /\ ~registryGoverned
  /\ registryGoverned' = TRUE
  /\ UNCHANGED <<toolchainBound, snapshotImmutable, cleanBuild,
                 structuredInspection, governanceAuthorized, keyState,
                 gateRecorded, currentAuthority, snapshotAuthority, gateHistory>>

BindToolchain ==
  /\ registryGoverned
  /\ ~toolchainBound
  /\ toolchainBound' = TRUE
  /\ UNCHANGED <<registryGoverned, snapshotImmutable, cleanBuild,
                 structuredInspection, governanceAuthorized, keyState,
                 gateRecorded, currentAuthority, snapshotAuthority, gateHistory>>

VerifySnapshotAndBuild ==
  /\ toolchainBound
  /\ ~snapshotImmutable
  /\ snapshotImmutable' = TRUE
  /\ cleanBuild' = TRUE
  /\ UNCHANGED <<registryGoverned, toolchainBound, structuredInspection,
                 governanceAuthorized, keyState, gateRecorded,
                 currentAuthority, snapshotAuthority, gateHistory>>

InspectStructuredResult ==
  /\ snapshotImmutable
  /\ cleanBuild
  /\ ~structuredInspection
  /\ structuredInspection' = TRUE
  /\ UNCHANGED <<registryGoverned, toolchainBound, snapshotImmutable,
                 cleanBuild, governanceAuthorized, keyState, gateRecorded,
                 currentAuthority, snapshotAuthority, gateHistory>>

AuthorizeGovernance ==
  /\ ~governanceAuthorized
  /\ governanceAuthorized' = TRUE
  /\ UNCHANGED <<registryGoverned, toolchainBound, snapshotImmutable,
                 cleanBuild, structuredInspection, keyState, gateRecorded,
                 currentAuthority, snapshotAuthority, gateHistory>>

Promote ==
  /\ registryGoverned /\ toolchainBound /\ snapshotImmutable /\ cleanBuild
  /\ structuredInspection /\ governanceAuthorized /\ keyState = Active
  /\ ~gateRecorded
  /\ gateRecorded' = TRUE
  /\ currentAuthority' = TRUE
  /\ gateHistory' = Append(gateHistory, "allowed")
  /\ UNCHANGED <<registryGoverned, toolchainBound, snapshotImmutable,
                 cleanBuild, structuredInspection, governanceAuthorized,
                 keyState, snapshotAuthority>>

RecordSnapshot ==
  /\ snapshotAuthority = Unrecorded
  /\ snapshotAuthority' = IF currentAuthority THEN Authoritative ELSE NonAuthoritative
  /\ UNCHANGED <<registryGoverned, toolchainBound, snapshotImmutable,
                 cleanBuild, structuredInspection, governanceAuthorized,
                 keyState, gateRecorded, currentAuthority, gateHistory>>

RevokeKey ==
  /\ keyState = Active
  /\ keyState' = Revoked
  /\ currentAuthority' = FALSE
  /\ UNCHANGED <<registryGoverned, toolchainBound, snapshotImmutable,
                 cleanBuild, structuredInspection, governanceAuthorized,
                 gateRecorded, snapshotAuthority, gateHistory>>

SupersedeKey ==
  /\ keyState = Active
  /\ keyState' = Superseded
  /\ currentAuthority' = FALSE
  /\ UNCHANGED <<registryGoverned, toolchainBound, snapshotImmutable,
                 cleanBuild, structuredInspection, governanceAuthorized,
                 gateRecorded, snapshotAuthority, gateHistory>>

Stutter == UNCHANGED vars
Next == GovernRegistry \/ BindToolchain \/ VerifySnapshotAndBuild
        \/ InspectStructuredResult \/ AuthorizeGovernance \/ Promote
        \/ RecordSnapshot \/ RevokeKey \/ SupersedeKey \/ Stutter

TypeOK ==
  /\ registryGoverned \in BOOLEAN /\ toolchainBound \in BOOLEAN
  /\ snapshotImmutable \in BOOLEAN /\ cleanBuild \in BOOLEAN
  /\ structuredInspection \in BOOLEAN /\ governanceAuthorized \in BOOLEAN
  /\ keyState \in {Active, Revoked, Superseded}
  /\ gateRecorded \in BOOLEAN /\ currentAuthority \in BOOLEAN
  /\ snapshotAuthority \in {Unrecorded, Authoritative, NonAuthoritative}
  /\ gateHistory \in Seq({"allowed"})

AuthorityRequiresGovernedRegistry == currentAuthority => registryGoverned
AuthorityRequiresBoundToolchain == currentAuthority => toolchainBound
AuthorityRequiresImmutableCleanBuild == currentAuthority => snapshotImmutable /\ cleanBuild
AuthorityRequiresStructuredInspection == currentAuthority => structuredInspection
AuthorityRequiresGovernanceAuthorization == currentAuthority => governanceAuthorized
AuthorityRequiresActiveKey == currentAuthority => keyState = Active
AuthorityRequiresGate == currentAuthority => gateRecorded
RecordedAuthoritativeSnapshotRequiresGate == snapshotAuthority = Authoritative => gateRecorded
GateIsAppendOnly == gateRecorded => Len(gateHistory) >= 1

Spec == Init /\ [][Next]_vars
=============================================================================
