namespace Duotronic

inductive PolicyDecision where
  | allow
  | deny
  | escalate
  deriving DecidableEq, Repr

inductive TaskState where
  | pending
  | delegated
  | completed
  | failed
  deriving DecidableEq, Repr

structure PolicyDecisionRecord where
  decision : PolicyDecision
  conditionsChecked : Bool
  delegationDepth : Nat
  deriving Repr

structure Task where
  state : TaskState
  policy : PolicyDecisionRecord
  delegationDepth : Nat
  deriving Repr

def IsTerminal (s : TaskState) : Prop :=
  s = TaskState.completed ∨ s = TaskState.failed

def DepthPolicy (maxDepth : Nat) (depth : Nat) : PolicyDecision :=
  if depth < maxDepth then PolicyDecision.allow else PolicyDecision.deny

theorem depth_policy_default_deny
    (maxDepth depth : Nat)
    (h : depth ≥ maxDepth) :
    DepthPolicy maxDepth depth = PolicyDecision.deny := by
  unfold DepthPolicy
  have hnot : ¬ depth < maxDepth := Nat.not_lt.mpr h
  simp [hnot]

theorem completed_requires_allow
    (task : Task)
    (hComplete : task.state = TaskState.completed)
    (hInvariant : task.state = TaskState.completed -> task.policy.decision = PolicyDecision.allow) :
    task.policy.decision = PolicyDecision.allow := by
  exact hInvariant hComplete

theorem denied_task_not_completed_under_invariant
    (task : Task)
    (hDeny : task.policy.decision = PolicyDecision.deny)
    (hInvariant : task.state = TaskState.completed -> task.policy.decision = PolicyDecision.allow) :
    task.state ≠ TaskState.completed := by
  intro hCompleted
  have hAllow := hInvariant hCompleted
  rw [hDeny] at hAllow
  contradiction

end Duotronic
