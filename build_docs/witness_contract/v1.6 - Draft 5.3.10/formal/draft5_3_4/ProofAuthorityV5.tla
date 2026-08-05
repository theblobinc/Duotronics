-------------------------- MODULE ProofAuthorityV5 --------------------------
EXTENDS Naturals, Sequences, TLC

VARIABLES snapshotSealed, artifactFromSnapshot, generatedInputSealed,
          untrustedCanWriteFinal, verifierResultSigned, executionClosureBound,
          governanceScopeExact, eventSequence, snapshotRecorded, snapshotCutoff,
          snapshotEventRootBound, laterBackdatedEvent, releaseGatesPassed,
          theoremAuthority, eventHistory

vars == <<snapshotSealed, artifactFromSnapshot, generatedInputSealed,
          untrustedCanWriteFinal, verifierResultSigned, executionClosureBound,
          governanceScopeExact, eventSequence, snapshotRecorded, snapshotCutoff,
          snapshotEventRootBound, laterBackdatedEvent, releaseGatesPassed,
          theoremAuthority, eventHistory>>

Init ==
  /\ snapshotSealed = FALSE
  /\ artifactFromSnapshot = FALSE
  /\ generatedInputSealed = FALSE
  /\ untrustedCanWriteFinal = FALSE
  /\ verifierResultSigned = FALSE
  /\ executionClosureBound = FALSE
  /\ governanceScopeExact = FALSE
  /\ eventSequence = 0
  /\ snapshotRecorded = FALSE
  /\ snapshotCutoff = 0
  /\ snapshotEventRootBound = FALSE
  /\ laterBackdatedEvent = FALSE
  /\ releaseGatesPassed = FALSE
  /\ theoremAuthority = FALSE
  /\ eventHistory = <<>>

SealSnapshot ==
  /\ ~snapshotSealed
  /\ snapshotSealed' = TRUE
  /\ artifactFromSnapshot' = TRUE
  /\ generatedInputSealed' = TRUE
  /\ UNCHANGED <<untrustedCanWriteFinal, verifierResultSigned,
       executionClosureBound, governanceScopeExact, eventSequence,
       snapshotRecorded, snapshotCutoff, snapshotEventRootBound,
       laterBackdatedEvent, releaseGatesPassed, theoremAuthority, eventHistory>>

VerifyTrustedResult ==
  /\ snapshotSealed /\ artifactFromSnapshot /\ generatedInputSealed
  /\ ~untrustedCanWriteFinal
  /\ verifierResultSigned' = TRUE
  /\ executionClosureBound' = TRUE
  /\ UNCHANGED <<snapshotSealed, artifactFromSnapshot, generatedInputSealed,
       untrustedCanWriteFinal, governanceScopeExact, eventSequence,
       snapshotRecorded, snapshotCutoff, snapshotEventRootBound,
       laterBackdatedEvent, releaseGatesPassed, theoremAuthority, eventHistory>>

AppendGovernedEvent ==
  /\ governanceScopeExact' = TRUE
  /\ eventSequence' = eventSequence + 1
  /\ eventHistory' = Append(eventHistory, eventSequence + 1)
  /\ UNCHANGED <<snapshotSealed, artifactFromSnapshot, generatedInputSealed,
       untrustedCanWriteFinal, verifierResultSigned, executionClosureBound,
       snapshotRecorded, snapshotCutoff, snapshotEventRootBound,
       laterBackdatedEvent, releaseGatesPassed, theoremAuthority>>

RecordLedgerSnapshot ==
  /\ ~snapshotRecorded /\ governanceScopeExact
  /\ snapshotRecorded' = TRUE
  /\ snapshotCutoff' = eventSequence
  /\ snapshotEventRootBound' = TRUE
  /\ UNCHANGED <<snapshotSealed, artifactFromSnapshot, generatedInputSealed,
       untrustedCanWriteFinal, verifierResultSigned, executionClosureBound,
       governanceScopeExact, eventSequence, laterBackdatedEvent,
       releaseGatesPassed, theoremAuthority, eventHistory>>

AppendBackdatedCorrection ==
  /\ snapshotRecorded /\ governanceScopeExact
  /\ eventSequence' = eventSequence + 1
  /\ eventHistory' = Append(eventHistory, eventSequence + 1)
  /\ laterBackdatedEvent' = TRUE
  /\ UNCHANGED <<snapshotSealed, artifactFromSnapshot, generatedInputSealed,
       untrustedCanWriteFinal, verifierResultSigned, executionClosureBound,
       governanceScopeExact, snapshotRecorded, snapshotCutoff,
       snapshotEventRootBound, releaseGatesPassed, theoremAuthority>>

CompleteReleaseGates ==
  /\ verifierResultSigned /\ executionClosureBound /\ snapshotRecorded
  /\ snapshotEventRootBound /\ governanceScopeExact
  /\ releaseGatesPassed' = TRUE
  /\ UNCHANGED <<snapshotSealed, artifactFromSnapshot, generatedInputSealed,
       untrustedCanWriteFinal, verifierResultSigned, executionClosureBound,
       governanceScopeExact, eventSequence, snapshotRecorded, snapshotCutoff,
       snapshotEventRootBound, laterBackdatedEvent, theoremAuthority, eventHistory>>

AuthorizeTheorem ==
  /\ releaseGatesPassed /\ verifierResultSigned /\ executionClosureBound
  /\ snapshotSealed /\ artifactFromSnapshot /\ ~untrustedCanWriteFinal
  /\ theoremAuthority' = TRUE
  /\ UNCHANGED <<snapshotSealed, artifactFromSnapshot, generatedInputSealed,
       untrustedCanWriteFinal, verifierResultSigned, executionClosureBound,
       governanceScopeExact, eventSequence, snapshotRecorded, snapshotCutoff,
       snapshotEventRootBound, laterBackdatedEvent, releaseGatesPassed, eventHistory>>

Stutter == UNCHANGED vars
Next == SealSnapshot \/ VerifyTrustedResult \/ AppendGovernedEvent
        \/ RecordLedgerSnapshot \/ AppendBackdatedCorrection
        \/ CompleteReleaseGates \/ AuthorizeTheorem \/ Stutter

TypeOK ==
  /\ snapshotSealed \in BOOLEAN /\ artifactFromSnapshot \in BOOLEAN
  /\ generatedInputSealed \in BOOLEAN /\ untrustedCanWriteFinal \in BOOLEAN
  /\ verifierResultSigned \in BOOLEAN /\ executionClosureBound \in BOOLEAN
  /\ governanceScopeExact \in BOOLEAN /\ eventSequence \in Nat
  /\ snapshotRecorded \in BOOLEAN /\ snapshotCutoff \in Nat
  /\ snapshotEventRootBound \in BOOLEAN /\ laterBackdatedEvent \in BOOLEAN
  /\ releaseGatesPassed \in BOOLEAN /\ theoremAuthority \in BOOLEAN
  /\ eventHistory \in Seq(Nat)

ResultChannelIsolation == ~untrustedCanWriteFinal
ArtifactIdentity == artifactFromSnapshot => snapshotSealed
SignedResultRequiresClosure == verifierResultSigned => executionClosureBound
SnapshotCutoffMonotonic == snapshotRecorded => snapshotCutoff <= eventSequence
BackdatedEventCannotMoveCutoff == laterBackdatedEvent => snapshotCutoff < eventSequence
SnapshotBindsEventRoot == snapshotRecorded => snapshotEventRootBound
AuthorityRequiresAllGates == theoremAuthority => releaseGatesPassed
AuthorityRequiresTrustedResult == theoremAuthority => verifierResultSigned /\ executionClosureBound
AuthorityRequiresSnapshotIdentity == theoremAuthority => snapshotSealed /\ artifactFromSnapshot
EventSequenceMatchesHistory == eventSequence = Len(eventHistory)

Spec == Init /\ [][Next]_vars
=============================================================================
