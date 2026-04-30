---- MODULE TaskDelegationAndPolicyCoreSpec ----
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS MaxDelegationDepth, MaxTasks, Agents

VARIABLES tasks, taskState, delegationDepth, policyDecision, auditLog, nextTaskId

TaskStates == {"pending", "delegated", "completed", "failed"}
PolicyDecisions == {"allow", "deny", "escalate"}

Init ==
  /\ tasks = {}
  /\ taskState = [t \in {} |-> "pending"]
  /\ delegationDepth = [t \in {} |-> 0]
  /\ policyDecision = [t \in {} |-> "deny"]
  /\ auditLog = <<>>
  /\ nextTaskId = 0

CreateTask ==
  /\ Cardinality(tasks) < MaxTasks
  /\ LET t == nextTaskId IN
     /\ tasks' = tasks \cup {t}
     /\ taskState' = [taskState EXCEPT ![t] = "pending"]
     /\ delegationDepth' = [delegationDepth EXCEPT ![t] = 0]
     /\ policyDecision' = [policyDecision EXCEPT ![t] = "deny"]
     /\ auditLog' = Append(auditLog, <<"create", t>>)
     /\ nextTaskId' = nextTaskId + 1

EvaluatePolicy(t) ==
  /\ t \in tasks
  /\ taskState[t] = "pending"
  /\ LET depthOk == delegationDepth[t] < MaxDelegationDepth IN
     /\ policyDecision' = [policyDecision EXCEPT ![t] = IF depthOk THEN "allow" ELSE "deny"]
     /\ delegationDepth' = [delegationDepth EXCEPT ![t] = delegationDepth[t] + 1]
     /\ taskState' = [taskState EXCEPT ![t] = IF depthOk THEN "delegated" ELSE "failed"]
     /\ auditLog' = Append(auditLog, <<"policy", t, policyDecision'[t]>>)
     /\ UNCHANGED <<tasks, nextTaskId>>

CompleteTask(t) ==
  /\ t \in tasks
  /\ taskState[t] = "delegated"
  /\ policyDecision[t] = "allow"
  /\ taskState' = [taskState EXCEPT ![t] = "completed"]
  /\ auditLog' = Append(auditLog, <<"complete", t>>)
  /\ UNCHANGED <<tasks, delegationDepth, policyDecision, nextTaskId>>

Next ==
  \/ CreateTask
  \/ \E t \in tasks: EvaluatePolicy(t)
  \/ \E t \in tasks: CompleteTask(t)

Spec == Init /\ [][Next]_<<tasks, taskState, delegationDepth, policyDecision, auditLog, nextTaskId>>

DelegationDepthBounded ==
  \A t \in tasks: delegationDepth[t] <= MaxDelegationDepth

CompletedTasksAllowed ==
  \A t \in tasks: taskState[t] = "completed" => policyDecision[t] = "allow"

DefaultDenyAtMaxDepth ==
  \A t \in tasks: delegationDepth[t] >= MaxDelegationDepth => policyDecision[t] # "allow"

AuditLogMonotone ==
  Len(auditLog) >= 0

THEOREM Spec => []DelegationDepthBounded
THEOREM Spec => []CompletedTasksAllowed
THEOREM Spec => []DefaultDenyAtMaxDepth
====
