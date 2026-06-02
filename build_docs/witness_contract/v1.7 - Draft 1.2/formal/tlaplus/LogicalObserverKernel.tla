---- MODULE LogicalObserverKernel ----
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Observers, Tasks, Capabilities, MaxTasks, MaxDelegationDepth

TaskStates == {"absent", "pending", "authorized", "running", "committed", "failed", "rolled_back"}
PolicyDecisions == {"allow", "deny", "escalate"}

VARIABLES activeTasks, taskState, policyDecision, capabilityToken, delegationDepth, witnesses, effects, auditLog
vars == <<activeTasks, taskState, policyDecision, capabilityToken, delegationDepth, witnesses, effects, auditLog>>

Init ==
  /\ activeTasks = {}
  /\ taskState = [t \in Tasks |-> "absent"]
  /\ policyDecision = [t \in Tasks |-> "deny"]
  /\ capabilityToken = [t \in Tasks |-> CHOOSE c \in Capabilities : TRUE]
  /\ delegationDepth = [t \in Tasks |-> 0]
  /\ witnesses = {}
  /\ effects = {}
  /\ auditLog = <<>>

CreateTask(t, o, c) ==
  /\ t \in Tasks
  /\ o \in Observers
  /\ c \in Capabilities
  /\ t \notin activeTasks
  /\ Cardinality(activeTasks) < MaxTasks
  /\ activeTasks' = activeTasks \cup {t}
  /\ taskState' = [taskState EXCEPT ![t] = "pending"]
  /\ policyDecision' = [policyDecision EXCEPT ![t] = "deny"]
  /\ capabilityToken' = [capabilityToken EXCEPT ![t] = c]
  /\ delegationDepth' = [delegationDepth EXCEPT ![t] = 0]
  /\ witnesses' = witnesses \cup {<<"task", t, o, c>>}
  /\ effects' = effects
  /\ auditLog' = Append(auditLog, <<"create", t, o>>)

AuthorizeTask(t) ==
  /\ t \in activeTasks
  /\ taskState[t] = "pending"
  /\ LET depthOk == delegationDepth[t] < MaxDelegationDepth IN
     /\ policyDecision' = [policyDecision EXCEPT ![t] = IF depthOk THEN "allow" ELSE "deny"]
     /\ delegationDepth' = [delegationDepth EXCEPT ![t] = delegationDepth[t] + 1]
     /\ taskState' = [taskState EXCEPT ![t] = IF depthOk THEN "authorized" ELSE "failed"]
     /\ witnesses' = witnesses \cup {<<"policy", t, IF depthOk THEN "allow" ELSE "deny">>}
     /\ auditLog' = Append(auditLog, <<"policy", t, IF depthOk THEN "allow" ELSE "deny">>)
     /\ UNCHANGED <<activeTasks, capabilityToken, effects>>

ExecuteStep(t) ==
  /\ t \in activeTasks
  /\ taskState[t] = "authorized"
  /\ policyDecision[t] = "allow"
  /\ taskState' = [taskState EXCEPT ![t] = "running"]
  /\ witnesses' = witnesses \cup {<<"step", t>>}
  /\ effects' = effects \cup {<<"effect", t, "step">>}
  /\ auditLog' = Append(auditLog, <<"step", t>>)
  /\ UNCHANGED <<activeTasks, policyDecision, capabilityToken, delegationDepth>>

CommitResult(t) ==
  /\ t \in activeTasks
  /\ taskState[t] = "running"
  /\ policyDecision[t] = "allow"
  /\ <<"step", t>> \in witnesses
  /\ taskState' = [taskState EXCEPT ![t] = "committed"]
  /\ witnesses' = witnesses \cup {<<"result", t>>}
  /\ effects' = effects \cup {<<"effect", t, "result">>}
  /\ auditLog' = Append(auditLog, <<"commit", t>>)
  /\ UNCHANGED <<activeTasks, policyDecision, capabilityToken, delegationDepth>>

Rollback(t) ==
  /\ t \in activeTasks
  /\ taskState[t] \in {"authorized", "running", "failed"}
  /\ taskState' = [taskState EXCEPT ![t] = "rolled_back"]
  /\ witnesses' = witnesses \cup {<<"rollback", t>>}
  /\ auditLog' = Append(auditLog, <<"rollback", t>>)
  /\ UNCHANGED <<activeTasks, policyDecision, capabilityToken, delegationDepth, effects>>

Next ==
  \/ \E t \in Tasks, o \in Observers, c \in Capabilities : CreateTask(t, o, c)
  \/ \E t \in activeTasks : AuthorizeTask(t)
  \/ \E t \in activeTasks : ExecuteStep(t)
  \/ \E t \in activeTasks : CommitResult(t)
  \/ \E t \in activeTasks : Rollback(t)

Spec == Init /\ [][Next]_vars

TypeOk ==
  /\ activeTasks \subseteq Tasks
  /\ Cardinality(activeTasks) <= MaxTasks
  /\ DOMAIN taskState = Tasks
  /\ DOMAIN policyDecision = Tasks
  /\ DOMAIN capabilityToken = Tasks
  /\ DOMAIN delegationDepth = Tasks
  /\ \A t \in Tasks : taskState[t] \in TaskStates
  /\ \A t \in Tasks : policyDecision[t] \in PolicyDecisions
  /\ \A t \in Tasks : capabilityToken[t] \in Capabilities
  /\ \A t \in Tasks : delegationDepth[t] \in Nat

NoEffectBeforeWitness ==
  \A e \in effects :
    \/ /\ e[3] = "step"
       /\ <<"step", e[2]>> \in witnesses
    \/ /\ e[3] = "result"
       /\ <<"result", e[2]>> \in witnesses

CommittedTasksHaveResultWitness ==
  \A t \in activeTasks : taskState[t] = "committed" => <<"result", t>> \in witnesses

CommittedTasksWereAllowed ==
  \A t \in activeTasks : taskState[t] = "committed" => policyDecision[t] = "allow"

FailedTasksAreNotAllowed ==
  \A t \in activeTasks : taskState[t] = "failed" => policyDecision[t] # "allow"

DelegationDepthBounded ==
  \A t \in activeTasks : delegationDepth[t] <= MaxDelegationDepth

RollbackHasWitness ==
  \A t \in activeTasks : taskState[t] = "rolled_back" => <<"rollback", t>> \in witnesses

====
