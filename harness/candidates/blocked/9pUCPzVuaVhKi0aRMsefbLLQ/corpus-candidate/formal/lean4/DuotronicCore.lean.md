# Lean 4 Formal Model — Duotronic Core

Status: formal proof artifact in Markdown wrapper.

```lean
namespace DuotronicCore

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
  conditions_checked : Bool
  delegation_depth : Nat
  deriving Repr

structure Task where
  state : TaskState
  policy : PolicyDecisionRecord
  delegation_depth : Nat
  deriving Repr

def isTerminal (s : TaskState) : Prop :=
  s = TaskState.completed ∨ s = TaskState.failed

def depthPolicy (maxDepth : Nat) (depth : Nat) : PolicyDecision :=
  if depth < maxDepth then PolicyDecision.allow else PolicyDecision.deny

theorem depthPolicy_default_deny
    (maxDepth depth : Nat)
    (h : depth ≥ maxDepth) :
    depthPolicy maxDepth depth = PolicyDecision.deny := by
  unfold depthPolicy
  have hnot : ¬ depth < maxDepth := Nat.not_lt.mpr h
  simp [hnot]

theorem completed_requires_allow
    (task : Task)
    (h_complete : task.state = TaskState.completed)
    (h_invariant : task.state = TaskState.completed -> task.policy.decision = PolicyDecision.allow) :
    task.policy.decision = PolicyDecision.allow := by
  exact h_invariant h_complete

theorem denied_task_not_completed_under_invariant
    (task : Task)
    (h_deny : task.policy.decision = PolicyDecision.deny)
    (h_invariant : task.state = TaskState.completed -> task.policy.decision = PolicyDecision.allow) :
    task.state ≠ TaskState.completed := by
  intro h_completed
  have h_allow := h_invariant h_completed
  rw [h_deny] at h_allow
  contradiction

-- Remaining production proofs should connect the executable policy engine
-- to these pure definitions through extraction or reference tests.

end DuotronicCore
```

