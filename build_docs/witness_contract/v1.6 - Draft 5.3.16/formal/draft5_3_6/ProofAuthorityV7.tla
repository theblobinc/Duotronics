-------------------------- MODULE ProofAuthorityV7 --------------------------
EXTENDS Naturals, TLC

VARIABLES recursiveDependencyPass, exactExecutedArgv, policyLimitsBound,
          trustBoundarySchemasValid, requestedControls, emittedControls,
          acceptedControls, measuredControls, handoffManifestVerified,
          durableIdempotencyCommitted, trustedArtifactsAttested,
          externalActivationGates, theoremAuthority

vars == <<recursiveDependencyPass, exactExecutedArgv, policyLimitsBound,
          trustBoundarySchemasValid, requestedControls, emittedControls,
          acceptedControls, measuredControls, handoffManifestVerified,
          durableIdempotencyCommitted, trustedArtifactsAttested,
          externalActivationGates, theoremAuthority>>

Init ==
  /\ recursiveDependencyPass = FALSE /\ exactExecutedArgv = FALSE
  /\ policyLimitsBound = FALSE /\ trustBoundarySchemasValid = FALSE
  /\ requestedControls = FALSE /\ emittedControls = FALSE
  /\ acceptedControls = FALSE /\ measuredControls = FALSE
  /\ handoffManifestVerified = FALSE /\ durableIdempotencyCommitted = FALSE
  /\ trustedArtifactsAttested = FALSE /\ externalActivationGates = FALSE
  /\ theoremAuthority = FALSE

SealInvocation ==
  /\ exactExecutedArgv' = TRUE /\ policyLimitsBound' = TRUE
  /\ requestedControls' = TRUE /\ emittedControls' = TRUE
  /\ UNCHANGED <<recursiveDependencyPass, trustBoundarySchemasValid,
       acceptedControls, measuredControls, handoffManifestVerified,
       durableIdempotencyCommitted, trustedArtifactsAttested,
       externalActivationGates, theoremAuthority>>

VerifyExecution ==
  /\ exactExecutedArgv /\ policyLimitsBound /\ requestedControls /\ emittedControls
  /\ acceptedControls' = TRUE /\ measuredControls' = TRUE
  /\ handoffManifestVerified' = TRUE /\ recursiveDependencyPass' = TRUE
  /\ UNCHANGED <<exactExecutedArgv, policyLimitsBound, requestedControls,
       emittedControls, trustBoundarySchemasValid, durableIdempotencyCommitted,
       trustedArtifactsAttested, externalActivationGates, theoremAuthority>>

ValidateAndCommit ==
  /\ trustBoundarySchemasValid' = TRUE
  /\ durableIdempotencyCommitted' = TRUE
  /\ trustedArtifactsAttested' = TRUE
  /\ UNCHANGED <<recursiveDependencyPass, exactExecutedArgv, policyLimitsBound,
       requestedControls, emittedControls, acceptedControls, measuredControls,
       handoffManifestVerified, externalActivationGates, theoremAuthority>>

CompleteExternalActivation ==
  /\ trustedArtifactsAttested /\ externalActivationGates' = TRUE
  /\ UNCHANGED <<recursiveDependencyPass, exactExecutedArgv, policyLimitsBound,
       trustBoundarySchemasValid, requestedControls, emittedControls,
       acceptedControls, measuredControls, handoffManifestVerified,
       durableIdempotencyCommitted, trustedArtifactsAttested, theoremAuthority>>

Authorize ==
  /\ recursiveDependencyPass /\ exactExecutedArgv /\ policyLimitsBound
  /\ trustBoundarySchemasValid /\ requestedControls /\ emittedControls
  /\ acceptedControls /\ measuredControls /\ handoffManifestVerified
  /\ durableIdempotencyCommitted /\ trustedArtifactsAttested
  /\ externalActivationGates /\ theoremAuthority' = TRUE
  /\ UNCHANGED <<recursiveDependencyPass, exactExecutedArgv, policyLimitsBound,
       trustBoundarySchemasValid, requestedControls, emittedControls,
       acceptedControls, measuredControls, handoffManifestVerified,
       durableIdempotencyCommitted, trustedArtifactsAttested,
       externalActivationGates>>

Stutter == UNCHANGED vars
Next == SealInvocation \/ VerifyExecution \/ ValidateAndCommit
        \/ CompleteExternalActivation \/ Authorize \/ Stutter

TypeOK == /\ recursiveDependencyPass \in BOOLEAN /\ exactExecutedArgv \in BOOLEAN
          /\ policyLimitsBound \in BOOLEAN /\ trustBoundarySchemasValid \in BOOLEAN
          /\ requestedControls \in BOOLEAN /\ emittedControls \in BOOLEAN
          /\ acceptedControls \in BOOLEAN /\ measuredControls \in BOOLEAN
          /\ handoffManifestVerified \in BOOLEAN
          /\ durableIdempotencyCommitted \in BOOLEAN
          /\ trustedArtifactsAttested \in BOOLEAN
          /\ externalActivationGates \in BOOLEAN /\ theoremAuthority \in BOOLEAN

EmittedControlsRequireRequest == emittedControls => requestedControls
MeasuredControlsRequireAcceptance == measuredControls => acceptedControls
AuthorityRequiresRecursiveDependencyPass == theoremAuthority => recursiveDependencyPass
AuthorityRequiresExactExecutedArgv == theoremAuthority => exactExecutedArgv
AuthorityRequiresPolicyLimits == theoremAuthority => policyLimitsBound
AuthorityRequiresSchemaValidation == theoremAuthority => trustBoundarySchemasValid
AuthorityRequiresMeasuredControls == theoremAuthority => measuredControls
AuthorityRequiresHandoffManifest == theoremAuthority => handoffManifestVerified
AuthorityRequiresDurableIdempotency == theoremAuthority => durableIdempotencyCommitted
AuthorityRequiresTrustedArtifacts == theoremAuthority => trustedArtifactsAttested
AuthorityRequiresExternalActivation == theoremAuthority => externalActivationGates

Spec == Init /\ [][Next]_vars
=============================================================================
