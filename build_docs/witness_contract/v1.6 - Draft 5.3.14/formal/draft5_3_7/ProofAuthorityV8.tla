-------------------------- MODULE ProofAuthorityV8 --------------------------
EXTENDS Naturals, TLC

VARIABLES invocationSealed, domainLimitBound, requestedControls,
          emittedControls, runtimeStarted, acceptedControls, appliedControls,
          measuredControls, derivedControls, allExternalGates,
          theoremAuthority

vars == <<invocationSealed, domainLimitBound, requestedControls,
          emittedControls, runtimeStarted, acceptedControls, appliedControls,
          measuredControls, derivedControls, allExternalGates,
          theoremAuthority>>

Init ==
  /\ invocationSealed = FALSE /\ domainLimitBound = FALSE
  /\ requestedControls = FALSE /\ emittedControls = FALSE
  /\ runtimeStarted = FALSE /\ acceptedControls = FALSE
  /\ appliedControls = FALSE /\ measuredControls = FALSE
  /\ derivedControls = FALSE /\ allExternalGates = FALSE
  /\ theoremAuthority = FALSE

SealInvocation ==
  /\ invocationSealed' = TRUE /\ domainLimitBound' = TRUE
  /\ requestedControls' = TRUE /\ emittedControls' = TRUE
  /\ UNCHANGED <<runtimeStarted, acceptedControls, appliedControls,
       measuredControls, derivedControls, allExternalGates, theoremAuthority>>

StartRuntime ==
  /\ invocationSealed /\ domainLimitBound /\ requestedControls /\ emittedControls
  /\ runtimeStarted' = TRUE /\ acceptedControls' = TRUE
  /\ UNCHANGED <<invocationSealed, domainLimitBound, requestedControls,
       emittedControls, appliedControls, measuredControls, derivedControls,
       allExternalGates, theoremAuthority>>

ObserveRuntime ==
  /\ runtimeStarted /\ acceptedControls
  /\ appliedControls' = TRUE /\ measuredControls' = TRUE
  /\ UNCHANGED <<invocationSealed, domainLimitBound, requestedControls,
       emittedControls, runtimeStarted, acceptedControls, derivedControls,
       allExternalGates, theoremAuthority>>

DeriveTopology ==
  /\ invocationSealed /\ runtimeStarted
  /\ derivedControls' = TRUE
  /\ UNCHANGED <<invocationSealed, domainLimitBound, requestedControls,
       emittedControls, runtimeStarted, acceptedControls, appliedControls,
       measuredControls, allExternalGates, theoremAuthority>>

CompleteExternalActivation ==
  /\ measuredControls /\ derivedControls
  /\ allExternalGates' = TRUE
  /\ UNCHANGED <<invocationSealed, domainLimitBound, requestedControls,
       emittedControls, runtimeStarted, acceptedControls, appliedControls,
       measuredControls, derivedControls, theoremAuthority>>

Authorize ==
  /\ invocationSealed /\ domainLimitBound /\ requestedControls
  /\ emittedControls /\ acceptedControls /\ appliedControls
  /\ measuredControls /\ derivedControls /\ allExternalGates
  /\ theoremAuthority' = TRUE
  /\ UNCHANGED <<invocationSealed, domainLimitBound, requestedControls,
       emittedControls, runtimeStarted, acceptedControls, appliedControls,
       measuredControls, derivedControls, allExternalGates>>

Stutter == UNCHANGED vars
Next == SealInvocation \/ StartRuntime \/ ObserveRuntime \/ DeriveTopology
        \/ CompleteExternalActivation \/ Authorize \/ Stutter

TypeOK == /\ invocationSealed \in BOOLEAN /\ domainLimitBound \in BOOLEAN
          /\ requestedControls \in BOOLEAN /\ emittedControls \in BOOLEAN
          /\ runtimeStarted \in BOOLEAN /\ acceptedControls \in BOOLEAN
          /\ appliedControls \in BOOLEAN /\ measuredControls \in BOOLEAN
          /\ derivedControls \in BOOLEAN /\ allExternalGates \in BOOLEAN
          /\ theoremAuthority \in BOOLEAN

AcceptedRequiresRuntime == acceptedControls => runtimeStarted
AppliedRequiresAcceptance == appliedControls => acceptedControls
MeasuredRequiresRuntime == measuredControls => runtimeStarted
DerivedRequiresSealedTopology == derivedControls => invocationSealed
AuthorityRequiresDomainLimit == theoremAuthority => domainLimitBound
AuthorityRequiresEvidence == theoremAuthority =>
  acceptedControls /\ appliedControls /\ measuredControls /\ derivedControls
AuthorityRequiresExternalActivation == theoremAuthority => allExternalGates

Spec == Init /\ [][Next]_vars
=============================================================================
