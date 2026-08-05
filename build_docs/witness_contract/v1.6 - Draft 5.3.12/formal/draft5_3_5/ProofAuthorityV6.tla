-------------------------- MODULE ProofAuthorityV6 --------------------------
EXTENDS Naturals, TLC

VARIABLES commandDispatchExact, controlsRequested, controlsApplied,
          controlsVerified, nonRootIdentity, runtimeVersionMeasured,
          policyResolved, policyBound, snapshotBounded, outputBounded,
          schemaRegistryComplete, sourceProvenanceCommitted,
          externalActivationGates, theoremAuthority

vars == <<commandDispatchExact, controlsRequested, controlsApplied,
          controlsVerified, nonRootIdentity, runtimeVersionMeasured,
          policyResolved, policyBound, snapshotBounded, outputBounded,
          schemaRegistryComplete, sourceProvenanceCommitted,
          externalActivationGates, theoremAuthority>>

Init ==
  /\ commandDispatchExact = FALSE /\ controlsRequested = FALSE
  /\ controlsApplied = FALSE /\ controlsVerified = FALSE
  /\ nonRootIdentity = FALSE /\ runtimeVersionMeasured = FALSE
  /\ policyResolved = FALSE /\ policyBound = FALSE
  /\ snapshotBounded = FALSE /\ outputBounded = FALSE
  /\ schemaRegistryComplete = FALSE /\ sourceProvenanceCommitted = FALSE
  /\ externalActivationGates = FALSE /\ theoremAuthority = FALSE

ConfigureExecution ==
  /\ commandDispatchExact' = TRUE /\ controlsRequested' = TRUE
  /\ nonRootIdentity' = TRUE /\ runtimeVersionMeasured' = TRUE
  /\ UNCHANGED <<controlsApplied, controlsVerified, policyResolved, policyBound,
       snapshotBounded, outputBounded, schemaRegistryComplete,
       sourceProvenanceCommitted, externalActivationGates, theoremAuthority>>

ApplyAndInspect ==
  /\ commandDispatchExact /\ controlsRequested /\ nonRootIdentity
  /\ controlsApplied' = TRUE /\ controlsVerified' = TRUE
  /\ snapshotBounded' = TRUE /\ outputBounded' = TRUE
  /\ UNCHANGED <<commandDispatchExact, controlsRequested, nonRootIdentity,
       runtimeVersionMeasured, policyResolved, policyBound,
       schemaRegistryComplete, sourceProvenanceCommitted,
       externalActivationGates, theoremAuthority>>

ResolvePolicy ==
  /\ policyResolved' = TRUE /\ policyBound' = TRUE
  /\ UNCHANGED <<commandDispatchExact, controlsRequested, controlsApplied,
       controlsVerified, nonRootIdentity, runtimeVersionMeasured,
       snapshotBounded, outputBounded, schemaRegistryComplete,
       sourceProvenanceCommitted, externalActivationGates, theoremAuthority>>

CloseCorpus ==
  /\ schemaRegistryComplete' = TRUE
  /\ UNCHANGED <<commandDispatchExact, controlsRequested, controlsApplied,
       controlsVerified, nonRootIdentity, runtimeVersionMeasured,
       policyResolved, policyBound, snapshotBounded, outputBounded,
       sourceProvenanceCommitted, externalActivationGates, theoremAuthority>>

RecordCommittedProvenance ==
  /\ sourceProvenanceCommitted' = TRUE
  /\ UNCHANGED <<commandDispatchExact, controlsRequested, controlsApplied,
       controlsVerified, nonRootIdentity, runtimeVersionMeasured,
       policyResolved, policyBound, snapshotBounded, outputBounded,
       schemaRegistryComplete, externalActivationGates, theoremAuthority>>

CompleteExternalActivation ==
  /\ sourceProvenanceCommitted /\ externalActivationGates' = TRUE
  /\ UNCHANGED <<commandDispatchExact, controlsRequested, controlsApplied,
       controlsVerified, nonRootIdentity, runtimeVersionMeasured,
       policyResolved, policyBound, snapshotBounded, outputBounded,
       schemaRegistryComplete, sourceProvenanceCommitted, theoremAuthority>>

Authorize ==
  /\ commandDispatchExact /\ controlsRequested /\ controlsApplied /\ controlsVerified
  /\ nonRootIdentity /\ runtimeVersionMeasured /\ policyResolved /\ policyBound
  /\ snapshotBounded /\ outputBounded /\ schemaRegistryComplete
  /\ sourceProvenanceCommitted /\ externalActivationGates
  /\ theoremAuthority' = TRUE
  /\ UNCHANGED <<commandDispatchExact, controlsRequested, controlsApplied,
       controlsVerified, nonRootIdentity, runtimeVersionMeasured,
       policyResolved, policyBound, snapshotBounded, outputBounded,
       schemaRegistryComplete, sourceProvenanceCommitted, externalActivationGates>>

Stutter == UNCHANGED vars
Next == ConfigureExecution \/ ApplyAndInspect \/ ResolvePolicy \/ CloseCorpus
        \/ RecordCommittedProvenance \/ CompleteExternalActivation \/ Authorize \/ Stutter

TypeOK == /\ commandDispatchExact \in BOOLEAN /\ controlsRequested \in BOOLEAN
          /\ controlsApplied \in BOOLEAN /\ controlsVerified \in BOOLEAN
          /\ nonRootIdentity \in BOOLEAN /\ runtimeVersionMeasured \in BOOLEAN
          /\ policyResolved \in BOOLEAN /\ policyBound \in BOOLEAN
          /\ snapshotBounded \in BOOLEAN /\ outputBounded \in BOOLEAN
          /\ schemaRegistryComplete \in BOOLEAN /\ sourceProvenanceCommitted \in BOOLEAN
          /\ externalActivationGates \in BOOLEAN /\ theoremAuthority \in BOOLEAN

AppliedControlsRequireRequest == controlsApplied => controlsRequested
VerifiedControlsRequireApplication == controlsVerified => controlsApplied
PolicyBindingRequiresResolution == policyBound => policyResolved
AuthorityRequiresExactDispatch == theoremAuthority => commandDispatchExact
AuthorityRequiresMeasuredSandbox == theoremAuthority => controlsVerified /\ nonRootIdentity /\ runtimeVersionMeasured
AuthorityRequiresBoundPolicy == theoremAuthority => policyResolved /\ policyBound
AuthorityRequiresBoundedResources == theoremAuthority => snapshotBounded /\ outputBounded
AuthorityRequiresClosedRegistry == theoremAuthority => schemaRegistryComplete
AuthorityRequiresCommittedProvenance == theoremAuthority => sourceProvenanceCommitted
AuthorityRequiresExternalActivation == theoremAuthority => externalActivationGates

Spec == Init /\ [][Next]_vars
=============================================================================
