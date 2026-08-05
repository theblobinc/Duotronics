---- MODULE TaskDelegationAndPolicyCoreSpec ----
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS MaxDelegationDepth, MaxTasks, Agents, Tasks

TaskStates == {"absent", "pending", "delegated", "completed", "failed"}
PolicyDecisions == {"allow", "deny", "escalate"}

VARIABLES activeTasks, taskState, delegationDepth, policyDecision, witnesses, auditLog
vars == <<activeTasks, taskState, delegationDepth, policyDecision, witnesses, auditLog>>

Init ==
  /\ activeTasks = {}
  /\ taskState = [t \in Tasks |-> "absent"]
  /\ delegationDepth = [t \in Tasks |-> 0]
  /\ policyDecision = [t \in Tasks |-> "deny"]
  /\ witnesses = {}
  /\ auditLog = <<>>

CreateTask(t, a) ==
  /\ t \in Tasks
  /\ a \in Agents
  /\ t \notin activeTasks
  /\ Cardinality(activeTasks) < MaxTasks
  /\ activeTasks' = activeTasks \cup {t}
  /\ taskState' = [taskState EXCEPT ![t] = "pending"]
  /\ delegationDepth' = [delegationDepth EXCEPT ![t] = 0]
  /\ policyDecision' = [policyDecision EXCEPT ![t] = "deny"]
  /\ witnesses' = witnesses \cup {<<"task_created", t, a>>}
  /\ auditLog' = Append(auditLog, <<"create", t, a>>)

EvaluatePolicy(t) ==
  /\ t \in activeTasks
  /\ taskState[t] = "pending"
  /\ LET depthOk == delegationDepth[t] < MaxDelegationDepth IN
     /\ policyDecision' = [policyDecision EXCEPT ![t] = IF depthOk THEN "allow" ELSE "deny"]
     /\ delegationDepth' = [delegationDepth EXCEPT ![t] = delegationDepth[t] + 1]
     /\ taskState' = [taskState EXCEPT ![t] = IF depthOk THEN "delegated" ELSE "failed"]
     /\ witnesses' = witnesses \cup {<<"policy", t, IF depthOk THEN "allow" ELSE "deny">>}
     /\ auditLog' = Append(auditLog, <<"policy", t, IF depthOk THEN "allow" ELSE "deny">>)
     /\ UNCHANGED activeTasks

CompleteTask(t) ==
  /\ t \in activeTasks
  /\ taskState[t] = "delegated"
  /\ policyDecision[t] = "allow"
  /\ taskState' = [taskState EXCEPT ![t] = "completed"]
  /\ witnesses' = witnesses \cup {<<"complete", t>>}
  /\ auditLog' = Append(auditLog, <<"complete", t>>)
  /\ UNCHANGED <<activeTasks, delegationDepth, policyDecision>>

Next ==
  \/ \E t \in Tasks, a \in Agents : CreateTask(t, a)
  \/ \E t \in activeTasks : EvaluatePolicy(t)
  \/ \E t \in activeTasks : CompleteTask(t)

Spec == Init /\ [][Next]_vars

TypeOk ==
  /\ activeTasks \subseteq Tasks
  /\ Cardinality(activeTasks) <= MaxTasks
  /\ DOMAIN taskState = Tasks
  /\ DOMAIN delegationDepth = Tasks
  /\ DOMAIN policyDecision = Tasks
  /\ \A t \in Tasks : taskState[t] \in TaskStates
  /\ \A t \in Tasks : policyDecision[t] \in PolicyDecisions
  /\ \A t \in Tasks : delegationDepth[t] \in Nat

DelegationDepthBounded ==
  \A t \in activeTasks : delegationDepth[t] <= MaxDelegationDepth

CompletedTasksAllowed ==
  \A t \in activeTasks : taskState[t] = "completed" => policyDecision[t] = "allow"

FailedTasksNotAllowed ==
  \A t \in activeTasks : taskState[t] = "failed" => policyDecision[t] # "allow"

CompletedTasksHaveWitness ==
  \A t \in activeTasks : taskState[t] = "completed" => <<"complete", t>> \in witnesses

AuditLogMonotone ==
  Len(auditLog) >= Cardinality(witnesses) - Cardinality(activeTasks)

====
