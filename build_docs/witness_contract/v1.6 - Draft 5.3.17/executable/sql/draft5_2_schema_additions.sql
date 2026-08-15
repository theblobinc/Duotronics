-- Draft 5.2.2 completed additive schema
-- Status: completion candidate; additive only; does not weaken Draft 5.1 gates.
-- Dialect: SQLite-compatible core DDL. Production stores may translate types while preserving constraints.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS srnn_evidence_claims (
  claim_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'evidence_claim/v1'),
  claim_kind TEXT NOT NULL CHECK (claim_kind IN ('atomic', 'measurement', 'observation', 'policy_decision', 'proof_claim', 'replay_claim', 'nla_activation_claim', 'delegation_claim', 'human_attestation')),
  subject_ref TEXT NOT NULL,
  predicate TEXT NOT NULL,
  claim_object_json TEXT NOT NULL,
  claim_status TEXT NOT NULL CHECK (claim_status IN ('unknown', 'absent', 'invalid', 'draft', 'observed', 'computed', 'proposed', 'asserted', 'deferred', 'vetoed', 'conjecture', 'theorem', 'replay_verified', 'proof_verified', 'policy_approved', 'released')),
  epistemic_status TEXT NOT NULL CHECK (epistemic_status IN ('unknown', 'absent', 'invalid', 'observed', 'computed', 'conjecture', 'theorem', 'policy_approved', 'synthetic', 'audit_only', 'shadow', 'release_candidate', 'authoritative', 'self_trained', 'external_authority', 'human_attested', 'replay_verified', 'proof_verified')),
  force_indicator TEXT NOT NULL CHECK (force_indicator IN ('observe', 'propose', 'assert', 'defer', 'veto', 'delegate', 'replay_verify')),
  authority_scope TEXT NOT NULL CHECK (authority_scope IN ('none', 'diagnostic', 'local_session', 'tenant', 'repo', 'service', 'cluster', 'system', 'release', 'mathematical_claim', 'nla_training', 'policy', 'memory_write', 'model_promotion', 'truth_observer')),
  runtime_mode TEXT NOT NULL CHECK (runtime_mode IN ('observe', 'test', 'simulation', 'shadow', 'audit', 'migration', 'release_candidate', 'production', 'rollback')),
  evidence_refs_json TEXT NOT NULL CHECK (evidence_refs_json <> '[]'),
  policy_decision_id TEXT NOT NULL,
  pragmatic_context_id TEXT,
  delegation_chain_id TEXT,
  non_collapse_state_id TEXT NOT NULL,
  proof_witness_refs_json TEXT NOT NULL DEFAULT '[]',
  lean_compiler_witness_refs_json TEXT NOT NULL DEFAULT '[]',
  theorem_promotion_gate_id TEXT,
  status_transition_id TEXT,
  inference_witness_id TEXT,
  issuer_principal_id TEXT NOT NULL,
  confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  CHECK (claim_status <> 'theorem' OR epistemic_status = 'theorem'),
  CHECK (
    (claim_status NOT IN ('theorem','proof_verified') AND epistemic_status NOT IN ('theorem','proof_verified'))
    OR (
      proof_witness_refs_json <> '[]' AND proof_witness_refs_json <> ''
      AND lean_compiler_witness_refs_json <> '[]' AND lean_compiler_witness_refs_json <> ''
      AND status_transition_id IS NOT NULL
      AND theorem_promotion_gate_id IS NOT NULL
    )
  ),
  FOREIGN KEY (theorem_promotion_gate_id) REFERENCES srnn_theorem_promotion_gates(theorem_promotion_gate_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS srnn_pragmatic_contexts (
  pragmatic_context_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'pragmatic_context/v1'),
  issuer_principal_id TEXT NOT NULL,
  audience_json TEXT NOT NULL,
  channel TEXT NOT NULL,
  force_indicator TEXT NOT NULL,
  authority_scope TEXT NOT NULL,
  runtime_mode TEXT NOT NULL,
  delegation_chain_id TEXT,
  policy_decision_id TEXT NOT NULL,
  human_review_required INTEGER NOT NULL CHECK (human_review_required IN (0,1)),
  non_collapse_checked INTEGER NOT NULL CHECK (non_collapse_checked = 1),
  constraints_json TEXT,
  created_at TEXT NOT NULL,
  expires_at TEXT
);

CREATE TABLE IF NOT EXISTS srnn_policy_decision_evidence_extensions (
  policy_extension_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'policy_decision_evidence_extension/v1'),
  policy_decision_id TEXT NOT NULL,
  pragmatic_context_id TEXT NOT NULL,
  requested_force TEXT NOT NULL,
  allowed_force TEXT NOT NULL,
  denied_forces_json TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('allow','deny','escalate','defer','veto')),
  authority_scope TEXT NOT NULL,
  runtime_mode TEXT NOT NULL,
  reasons_json TEXT NOT NULL,
  constraints_json TEXT,
  non_collapse_transition_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_non_collapse_states (
  state_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'non_collapse_state/v1'),
  primitive_category TEXT NOT NULL CHECK (primitive_category IN ('zero', 'absence', 'unknown', 'invalid', 'empty', 'null', 'computational_evidence', 'theorem', 'conjectural', 'self_trained', 'authoritative', 'audit_only', 'active', 'observation', 'proof', 'explanation', 'fact', 'policy_approval', 'human_attestation', 'synthetic_witness', 'activation_witness')),
  authority_class TEXT NOT NULL CHECK (authority_class IN ('none', 'diagnostic', 'proposal', 'audit', 'shadow', 'release_candidate', 'authoritative', 'human_authoritative', 'formal_proof')),
  state_kind TEXT NOT NULL CHECK (state_kind IN ('value_state', 'epistemic_state', 'authority_state', 'runtime_state', 'claim_state', 'model_state', 'replay_state')),
  collapse_status TEXT NOT NULL CHECK (collapse_status IN ('not_collapsed', 'collapse_denied', 'transition_requires_witness', 'transition_witnessed', 'transition_allowed', 'transition_forbidden')),
  claim_id TEXT,
  external_witness_ref TEXT,
  may_collapse_to_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  CHECK (may_collapse_to_json = '[]')
);

CREATE TABLE IF NOT EXISTS srnn_non_collapse_transitions (
  transition_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'non_collapse_transition/v1'),
  source_state_id TEXT NOT NULL,
  target_state_id TEXT NOT NULL,
  source_primitive_category TEXT NOT NULL CHECK (source_primitive_category IN ('zero', 'absence', 'unknown', 'invalid', 'empty', 'null', 'computational_evidence', 'theorem', 'conjectural', 'self_trained', 'authoritative', 'audit_only', 'active', 'observation', 'proof', 'explanation', 'fact', 'policy_approval', 'human_attestation', 'synthetic_witness', 'activation_witness')),
  target_primitive_category TEXT NOT NULL CHECK (target_primitive_category IN ('zero', 'absence', 'unknown', 'invalid', 'empty', 'null', 'computational_evidence', 'theorem', 'conjectural', 'self_trained', 'authoritative', 'audit_only', 'active', 'observation', 'proof', 'explanation', 'fact', 'policy_approval', 'human_attestation', 'synthetic_witness', 'activation_witness')),
  source_state_kind TEXT NOT NULL CHECK (source_state_kind IN ('value_state', 'epistemic_state', 'authority_state', 'runtime_state', 'claim_state', 'model_state', 'replay_state')),
  target_state_kind TEXT NOT NULL CHECK (target_state_kind IN ('value_state', 'epistemic_state', 'authority_state', 'runtime_state', 'claim_state', 'model_state', 'replay_state')),
  transition_kind TEXT NOT NULL CHECK (transition_kind IN ('identity', 'measurement', 'observation', 'promotion', 'demotion', 'proof_upgrade', 'replay_verification', 'authority_transfer', 'policy_projection', 'runtime_projection', 'invalid_attempt')),
  collapse_status TEXT NOT NULL CHECK (collapse_status IN ('not_collapsed', 'collapse_denied', 'transition_requires_witness', 'transition_witnessed', 'transition_allowed', 'transition_forbidden')),
  transition_status TEXT NOT NULL CHECK (transition_status IN ('allowed', 'denied', 'escalated', 'requires_external_witness', 'requires_proof_witness')),
  external_witness_ref TEXT,
  proof_witness_ref TEXT,
  policy_decision_id TEXT NOT NULL,
  forbidden_without_external_witness INTEGER NOT NULL CHECK (forbidden_without_external_witness = 1),
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (transition_kind <> 'proof_upgrade' OR proof_witness_ref IS NOT NULL),
  CHECK (transition_kind NOT IN ('promotion','authority_transfer') OR external_witness_ref IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS srnn_claim_status_transitions (
  claim_status_transition_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'claim_status_transition/v1'),
  claim_id TEXT NOT NULL,
  source_status TEXT NOT NULL CHECK (source_status IN ('unknown', 'absent', 'invalid', 'draft', 'observed', 'computed', 'proposed', 'asserted', 'deferred', 'vetoed', 'conjecture', 'theorem', 'replay_verified', 'proof_verified', 'policy_approved', 'released')),
  target_status TEXT NOT NULL CHECK (target_status IN ('unknown', 'absent', 'invalid', 'draft', 'observed', 'computed', 'proposed', 'asserted', 'deferred', 'vetoed', 'conjecture', 'theorem', 'replay_verified', 'proof_verified', 'policy_approved', 'released')),
  transition_kind TEXT NOT NULL CHECK (transition_kind IN ('observe', 'compute', 'propose', 'assert', 'defer', 'veto', 'prove', 'replay_verify', 'policy_approve', 'release', 'invalidate', 'mark_absent', 'mark_unknown')),
  allowed INTEGER NOT NULL CHECK (allowed IN (0,1)),
  policy_decision_id TEXT NOT NULL,
  required_witness_refs_json TEXT NOT NULL,
  proof_witness_refs_json TEXT NOT NULL DEFAULT '[]',
  lean_compiler_witness_refs_json TEXT NOT NULL DEFAULT '[]',
  theorem_promotion_gate_id TEXT,
  replay_verification_result_id TEXT,
  non_collapse_transition_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (target_status NOT IN ('theorem','proof_verified') OR (
    transition_kind = 'prove'
    AND proof_witness_refs_json <> '[]' AND proof_witness_refs_json <> ''
    AND lean_compiler_witness_refs_json <> '[]' AND lean_compiler_witness_refs_json <> ''
    AND theorem_promotion_gate_id IS NOT NULL
  )),
  FOREIGN KEY (theorem_promotion_gate_id) REFERENCES srnn_theorem_promotion_gates(theorem_promotion_gate_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS srnn_composition_policies (
  composition_policy_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'composition_policy/v1'),
  operator TEXT NOT NULL,
  composition_mode TEXT NOT NULL,
  premise_claim_ids_json TEXT NOT NULL,
  authority_scope TEXT NOT NULL,
  runtime_mode TEXT NOT NULL,
  output_claim_status TEXT,
  policy_decision_id TEXT NOT NULL,
  scope_bridge_ref TEXT,
  evidence_bundle_union_ref TEXT,
  non_collapse_checked INTEGER NOT NULL CHECK (non_collapse_checked = 1),
  non_collapse_transition_id TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_compound_claim_witnesses (
  compound_claim_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'compound_claim_witness/v1'),
  operator TEXT NOT NULL,
  premise_claim_ids_json TEXT NOT NULL,
  composition_policy_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  evidence_bundle_refs_json TEXT NOT NULL,
  replay_identity_ref TEXT,
  claim_status TEXT NOT NULL,
  authority_scope TEXT NOT NULL,
  runtime_mode TEXT NOT NULL,
  output_claim_id TEXT,
  non_collapse_state_id TEXT,
  non_collapse_checked INTEGER NOT NULL CHECK (non_collapse_checked = 1),
  non_collapse_transition_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_inference_witnesses (
  inference_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'inference_witness/v1'),
  rule_name TEXT NOT NULL CHECK (rule_name IN ('conjunction_elimination', 'modus_ponens_proposal', 'temporal_propagation', 'replay_extension', 'authority_preserving_projection')),
  premise_claim_ids_json TEXT NOT NULL,
  conclusion_claim_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  force_indicator TEXT NOT NULL CHECK (force_indicator IN ('observe', 'propose', 'assert', 'defer', 'veto', 'delegate', 'replay_verify')),
  input_epistemic_status_json TEXT NOT NULL,
  output_epistemic_status TEXT NOT NULL CHECK (output_epistemic_status IN ('unknown', 'absent', 'invalid', 'observed', 'computed', 'conjecture', 'theorem', 'policy_approved', 'synthetic', 'audit_only', 'shadow', 'release_candidate', 'authoritative', 'self_trained', 'external_authority', 'human_attested', 'replay_verified', 'proof_verified')),
  conclusion_status TEXT NOT NULL CHECK (conclusion_status IN ('unknown', 'absent', 'invalid', 'draft', 'observed', 'computed', 'proposed', 'asserted', 'deferred', 'vetoed', 'conjecture', 'theorem', 'replay_verified', 'proof_verified', 'policy_approved', 'released')),
  promotion_status TEXT NOT NULL CHECK (promotion_status IN ('none', 'proposed', 'blocked', 'requires_human_review', 'approved_for_shadow', 'approved_for_audit', 'release_candidate', 'promoted', 'rejected')),
  proof_required INTEGER NOT NULL CHECK (proof_required IN (0,1)),
  proof_witness_ref TEXT,
  lean_compiler_witness_ref TEXT,
  theorem_promotion_gate_id TEXT,
  status_transition_id TEXT,
  non_collapse_checked INTEGER NOT NULL CHECK (non_collapse_checked = 1),
  non_collapse_transition_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (output_epistemic_status NOT IN ('theorem','proof_verified') OR (
    proof_required = 1
    AND proof_witness_ref IS NOT NULL
    AND lean_compiler_witness_ref IS NOT NULL
    AND theorem_promotion_gate_id IS NOT NULL
  )),
  CHECK (conclusion_status NOT IN ('theorem','proof_verified') OR (
    proof_required = 1
    AND proof_witness_ref IS NOT NULL
    AND lean_compiler_witness_ref IS NOT NULL
    AND theorem_promotion_gate_id IS NOT NULL
  )),
  CHECK (promotion_status NOT IN ('promoted','release_candidate') OR status_transition_id IS NOT NULL),
  FOREIGN KEY (lean_compiler_witness_ref) REFERENCES srnn_lean_compiler_witnesses(lean_compiler_witness_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (theorem_promotion_gate_id) REFERENCES srnn_theorem_promotion_gates(theorem_promotion_gate_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS srnn_authority_delegation_chains (
  delegation_chain_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'authority_delegation_chain/v1'),
  delegator_principal_id TEXT NOT NULL,
  delegate_principal_id TEXT NOT NULL,
  scope TEXT NOT NULL,
  force_limit TEXT NOT NULL,
  runtime_mode_limit TEXT,
  channel_authority TEXT,
  delegation_depth INTEGER NOT NULL CHECK (delegation_depth >= 0 AND delegation_depth <= 8),
  parent_delegation_chain_id TEXT,
  delegation_path_json TEXT NOT NULL,
  valid_from TEXT NOT NULL,
  valid_until TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  revoked INTEGER NOT NULL CHECK (revoked IN (0,1)),
  revocation_reason TEXT,
  created_at TEXT NOT NULL,
  CHECK ((revoked = 0 AND revocation_reason IS NULL) OR (revoked = 1 AND revocation_reason IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS srnn_replay_assumption_manifests (
  manifest_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'replay_assumption_manifest/v1'),
  deep_time_intent TEXT NOT NULL,
  required_assumptions_json TEXT NOT NULL,
  failure_mode TEXT NOT NULL,
  manifest_json TEXT NOT NULL,
  manifest_shake256_512 TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_replay_signs (
  replay_sign_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'replay_sign/v1'),
  sign_type TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  description TEXT NOT NULL,
  artifact_ref TEXT,
  shake256_512 TEXT,
  sign_status TEXT NOT NULL,
  verification_result_id TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_verification_grammars (
  grammar_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'verification_grammar/v1'),
  grammar_version TEXT NOT NULL CHECK (grammar_version = 'verification_grammar/v1'),
  deterministic INTEGER NOT NULL CHECK (deterministic = 1),
  allowed_operations_json TEXT NOT NULL,
  instruction_set_json TEXT NOT NULL,
  determinism_profile_json TEXT NOT NULL,
  instructions_json TEXT NOT NULL,
  forbidden_operations_json TEXT NOT NULL,
  grammar_shake256_512 TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_verification_results (
  verification_result_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'verification_result/v1'),
  grammar_id TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pass','fail','inconclusive','error')),
  deterministic INTEGER NOT NULL CHECK (deterministic = 1),
  manifest_id TEXT,
  replay_sign_refs_json TEXT NOT NULL,
  failure_mode TEXT NOT NULL,
  executed_instruction_results_json TEXT NOT NULL,
  verifier_principal_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_temporal_scope_witnesses (
  temporal_scope_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'temporal_scope_witness/v1'),
  claim_id TEXT NOT NULL,
  time_window_json TEXT NOT NULL,
  temporal_granularity TEXT NOT NULL,
  deep_time_replay_required INTEGER NOT NULL CHECK (deep_time_replay_required IN (0,1)),
  replay_witness_ref TEXT NOT NULL,
  replay_assumption_manifest_id TEXT,
  policy_decision_id TEXT NOT NULL,
  extension_of TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_srnn_evidence_claims_status ON srnn_evidence_claims(claim_status, epistemic_status);
CREATE INDEX IF NOT EXISTS idx_srnn_inference_conclusion ON srnn_inference_witnesses(conclusion_claim_id);
CREATE INDEX IF NOT EXISTS idx_srnn_non_collapse_transitions_states ON srnn_non_collapse_transitions(source_state_id, target_state_id);
CREATE INDEX IF NOT EXISTS idx_srnn_verification_results_target ON srnn_verification_results(target_ref, status);


-- Logical Observer Kernel v1.0 additive persistence

CREATE TABLE IF NOT EXISTS srnn_logical_observer_profiles (
  observer_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'logical_observer_profile/v1'),
  observer_kind TEXT NOT NULL CHECK (observer_kind IN ('human','ai_runtime','policy_engine','verifier','replay_agent','kernel_test','service')),
  principal_id TEXT NOT NULL,
  authority_scopes_json TEXT NOT NULL,
  runtime_modes_json TEXT NOT NULL,
  capability_token_refs_json TEXT NOT NULL,
  delegation_chain_id TEXT,
  resource_budget_id TEXT,
  policy_decision_id TEXT NOT NULL,
  non_collapse_state_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','suspended','revoked','audit_only')),
  non_collapse_checked INTEGER NOT NULL CHECK (non_collapse_checked = 1),
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_observer_capability_tokens (
  capability_token_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'observer_capability_token/v1'),
  observer_id TEXT NOT NULL,
  capabilities_json TEXT NOT NULL,
  authority_scopes_json TEXT NOT NULL,
  runtime_modes_json TEXT NOT NULL,
  force_limits_json TEXT NOT NULL,
  delegation_chain_id TEXT,
  resource_budget_id TEXT,
  valid_from TEXT NOT NULL,
  valid_until TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  non_collapse_checked INTEGER NOT NULL CHECK (non_collapse_checked = 1),
  revoked INTEGER NOT NULL CHECK (revoked IN (0,1)),
  revocation_reason TEXT,
  created_at TEXT NOT NULL,
  CHECK ((revoked = 0 AND revocation_reason IS NULL) OR (revoked = 1 AND revocation_reason IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS srnn_resource_budget_witnesses (
  resource_budget_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'resource_budget_witness/v1'),
  scope_ref TEXT NOT NULL,
  max_steps INTEGER NOT NULL CHECK (max_steps > 0),
  max_recursion_depth INTEGER NOT NULL CHECK (max_recursion_depth >= 0),
  max_time_budget_ms INTEGER CHECK (max_time_budget_ms IS NULL OR max_time_budget_ms > 0),
  max_memory_bytes INTEGER NOT NULL CHECK (max_memory_bytes > 0),
  network_allowed INTEGER NOT NULL CHECK (network_allowed = 0),
  randomness_allowed INTEGER NOT NULL CHECK (randomness_allowed = 0),
  wall_clock_allowed INTEGER NOT NULL CHECK (wall_clock_allowed = 0),
  mutation_allowed INTEGER NOT NULL CHECK (mutation_allowed IN (0,1)),
  mutation_requires_transaction INTEGER NOT NULL CHECK (mutation_requires_transaction = 1),
  policy_decision_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_observer_tasks (
  task_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'observer_task/v1'),
  observer_id TEXT NOT NULL,
  task_kind TEXT NOT NULL CHECK (task_kind IN ('observe','compose','infer','verify','replay','delegate','promote','compute','adjudicate','rollback','export','resolve_rule','memory_write')),
  requested_syscall TEXT NOT NULL,
  input_refs_json TEXT NOT NULL,
  capability_token_id TEXT NOT NULL,
  resource_budget_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  pragmatic_context_id TEXT NOT NULL,
  transaction_id TEXT,
  task_frame_id TEXT,
  task_result_witness_id TEXT,
  kernel_error_witness_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending','typechecked','running','committed','denied','deferred','escalated','rolled_back','failed')),
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  CHECK (status <> 'committed' OR task_result_witness_id IS NOT NULL),
  CHECK (status NOT IN ('denied','escalated','failed') OR kernel_error_witness_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS srnn_task_frames (
  task_frame_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'task_frame/v1'),
  task_id TEXT NOT NULL,
  parent_frame_id TEXT,
  step_index INTEGER NOT NULL CHECK (step_index >= 0),
  call_stack_json TEXT NOT NULL,
  local_bindings_json TEXT,
  deterministic INTEGER NOT NULL CHECK (deterministic = 1),
  hidden_state_allowed INTEGER NOT NULL CHECK (hidden_state_allowed = 0),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_task_step_witnesses (
  task_step_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'task_step_witness/v1'),
  task_id TEXT NOT NULL,
  task_frame_id TEXT NOT NULL,
  syscall TEXT NOT NULL,
  instruction TEXT NOT NULL,
  input_refs_json TEXT NOT NULL,
  output_refs_json TEXT NOT NULL,
  witness_refs_json TEXT NOT NULL,
  deterministic INTEGER NOT NULL CHECK (deterministic = 1),
  policy_decision_id TEXT NOT NULL,
  non_collapse_transition_id TEXT,
  claim_status_transition_id TEXT,
  resource_budget_id TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  CHECK (syscall <> 'promote' OR non_collapse_transition_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS srnn_task_result_witnesses (
  task_result_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'task_result_witness/v1'),
  task_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pass','fail','denied','deferred','escalated','rolled_back','inconclusive')),
  step_witness_refs_json TEXT NOT NULL CHECK (step_witness_refs_json <> '[]'),
  output_refs_json TEXT NOT NULL,
  verification_result_id TEXT,
  replay_sign_refs_json TEXT NOT NULL,
  kernel_error_witness_id TEXT,
  policy_decision_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_kernel_transactions (
  kernel_transaction_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'kernel_transaction/v1'),
  task_id TEXT NOT NULL,
  transaction_kind TEXT NOT NULL CHECK (transaction_kind IN ('evidence','memory','promotion','replay','resolution','adjudication','rollback')),
  status TEXT NOT NULL CHECK (status IN ('open','committed','aborted','rolled_back')),
  precondition_refs_json TEXT NOT NULL,
  emitted_witness_refs_json TEXT NOT NULL,
  persisted_witness_refs_json TEXT NOT NULL,
  non_collapse_checked INTEGER NOT NULL CHECK (non_collapse_checked = 1),
  policy_decision_id TEXT NOT NULL,
  kernel_error_witness_id TEXT,
  created_at TEXT NOT NULL,
  committed_at TEXT,
  CHECK (status <> 'committed' OR (emitted_witness_refs_json <> '[]' AND persisted_witness_refs_json <> '[]' AND committed_at IS NOT NULL)),
  CHECK (status NOT IN ('aborted','rolled_back') OR kernel_error_witness_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS srnn_kernel_error_witnesses (
  kernel_error_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'kernel_error_witness/v1'),
  task_id TEXT NOT NULL,
  error_code TEXT NOT NULL CHECK (error_code IN ('missing_witness','authority_denied','non_collapse_violation','replay_assumption_missing','indeterminate_result','human_review_required','schema_validation_failed','resource_budget_exceeded','canonical_rule_ambiguous','capability_denied')),
  severity TEXT NOT NULL CHECK (severity IN ('info','warning','error','fatal')),
  message TEXT NOT NULL,
  denied_syscall TEXT,
  missing_witness_refs_json TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  non_collapse_transition_id TEXT,
  escalation_required INTEGER NOT NULL CHECK (escalation_required IN (0,1)),
  created_at TEXT NOT NULL,
  CHECK (error_code <> 'missing_witness' OR missing_witness_refs_json <> '[]')
);

CREATE TABLE IF NOT EXISTS srnn_corpus_rule_resolution_witnesses (
  corpus_rule_resolution_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'corpus_rule_resolution_witness/v1'),
  concept TEXT NOT NULL,
  requested_rule_ref TEXT,
  active_rule_ref TEXT NOT NULL,
  version_selected TEXT NOT NULL,
  supersession_chain_json TEXT NOT NULL,
  compatibility_exceptions_json TEXT NOT NULL,
  ambiguity_status TEXT NOT NULL CHECK (ambiguity_status IN ('resolved','ambiguous','denied','escalated','forked')),
  kernel_error_witness_id TEXT,
  policy_decision_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (ambiguity_status NOT IN ('ambiguous','denied','escalated') OR kernel_error_witness_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS srnn_conflict_adjudication_witnesses (
  conflict_adjudication_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'conflict_adjudication_witness/v1'),
  conflict_id TEXT NOT NULL,
  claim_refs_json TEXT NOT NULL,
  conflict_class TEXT NOT NULL CHECK (conflict_class IN ('factual','temporal','authority','proof','policy','replay','non_collapse','memory')),
  outcome TEXT NOT NULL CHECK (outcome IN ('merged','forked','denied','unresolved','escalated','superseded')),
  evidence_comparison_refs_json TEXT NOT NULL,
  authority_comparison_refs_json TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  non_collapse_transition_id TEXT,
  kernel_error_witness_id TEXT,
  created_at TEXT NOT NULL,
  CHECK (outcome NOT IN ('unresolved','escalated','denied') OR kernel_error_witness_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS srnn_kernel_states (
  kernel_state_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'kernel_state/v1'),
  corpus_manifest_ref TEXT NOT NULL,
  active_rule_set_ref TEXT NOT NULL,
  schema_registry_ref TEXT NOT NULL,
  authority_registry_ref TEXT NOT NULL,
  observer_registry_ref TEXT NOT NULL,
  task_queue_refs_json TEXT NOT NULL,
  evidence_store_ref TEXT NOT NULL,
  non_collapse_graph_ref TEXT NOT NULL,
  replay_store_ref TEXT NOT NULL,
  policy_engine_ref TEXT NOT NULL,
  audit_log_ref TEXT NOT NULL,
  safe_mode INTEGER CHECK (safe_mode IS NULL OR safe_mode IN (0,1)),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_execution_traces (
  execution_trace_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'execution_trace/v1'),
  task_id TEXT NOT NULL,
  observer_id TEXT NOT NULL,
  step_witness_refs_json TEXT NOT NULL CHECK (step_witness_refs_json <> '[]'),
  transaction_refs_json TEXT NOT NULL,
  error_witness_refs_json TEXT NOT NULL,
  replay_sign_id TEXT,
  deterministic INTEGER NOT NULL CHECK (deterministic = 1),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_logical_memory_cells (
  logical_memory_cell_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'logical_memory_cell/v1'),
  cell_kind TEXT NOT NULL CHECK (cell_kind IN ('observation','cache','candidate_fact','canonical_fact','authority_ref')),
  status TEXT NOT NULL CHECK (status IN ('draft','active','stale','promoted','purged')),
  content_ref TEXT NOT NULL,
  evidence_claim_id TEXT NOT NULL,
  promotion_transition_id TEXT,
  purge_witness_id TEXT,
  snapshot_ref TEXT,
  policy_decision_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (cell_kind NOT IN ('canonical_fact','authority_ref') OR promotion_transition_id IS NOT NULL),
  CHECK (status <> 'purged' OR purge_witness_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_srnn_observer_tasks_status ON srnn_observer_tasks(observer_id, status);
CREATE INDEX IF NOT EXISTS idx_srnn_kernel_errors_task ON srnn_kernel_error_witnesses(task_id, error_code);
CREATE INDEX IF NOT EXISTS idx_srnn_kernel_transactions_task ON srnn_kernel_transactions(task_id, status);
CREATE INDEX IF NOT EXISTS idx_srnn_rule_resolution_concept ON srnn_corpus_rule_resolution_witnesses(concept, ambiguity_status);


-- Draft 5.2.2 Lean proof authority persistence hardening additions.
CREATE TABLE IF NOT EXISTS srnn_lean_compiler_witnesses (
  lean_compiler_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'lean_compiler_witness/v1'),
  toolchain TEXT NOT NULL,
  lakefile_hash TEXT NOT NULL CHECK (length(lakefile_hash) = 128),
  source_tree_hash TEXT NOT NULL CHECK (length(source_tree_hash) = 128),
  command_json TEXT NOT NULL CHECK (command_json <> '[]'),
  result TEXT NOT NULL CHECK (result IN ('passed','failed','advisory_pass_lake_unavailable','strict_fail_lake_unavailable','failed_static_scan','failed_lake_build')),
  contains_sorry INTEGER NOT NULL CHECK (contains_sorry IN (0,1)),
  contains_admit INTEGER NOT NULL CHECK (contains_admit IN (0,1)),
  unapproved_axiom_count INTEGER NOT NULL CHECK (unapproved_axiom_count >= 0),
  compiled_modules_json TEXT NOT NULL CHECK (compiled_modules_json <> '[]'),
  theorem_statuses_json TEXT NOT NULL,
  stdout_ref TEXT,
  stderr_ref TEXT,
  created_at TEXT NOT NULL,
  CHECK (result <> 'passed' OR (contains_sorry = 0 AND contains_admit = 0 AND unapproved_axiom_count = 0))
);

CREATE TABLE IF NOT EXISTS srnn_proof_witnesses (
  proof_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'proof_witness/v1'),
  claim_id TEXT NOT NULL,
  theorem_name TEXT NOT NULL,
  proof_artifact_ref TEXT NOT NULL,
  lean_compiler_witness_id TEXT NOT NULL,
  lean_compiler_result TEXT NOT NULL CHECK (lean_compiler_result IN ('passed','failed','advisory_pass_lake_unavailable','strict_fail_lake_unavailable','failed_static_scan','failed_lake_build')),
  theorem_status TEXT NOT NULL CHECK (theorem_status IN ('proved','failed','sorry_stub','axiom_dependent','source_hash_mismatch')),
  source_hash_matches_claim INTEGER NOT NULL CHECK (source_hash_matches_claim IN (0,1)),
  no_sorry INTEGER NOT NULL CHECK (no_sorry IN (0,1)),
  no_admit INTEGER NOT NULL CHECK (no_admit IN (0,1)),
  no_unapproved_axioms INTEGER NOT NULL CHECK (no_unapproved_axioms IN (0,1)),
  policy_decision_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (theorem_status <> 'proved' OR (lean_compiler_result = 'passed' AND source_hash_matches_claim = 1 AND no_sorry = 1 AND no_admit = 1 AND no_unapproved_axioms = 1)),
  FOREIGN KEY (lean_compiler_witness_id) REFERENCES srnn_lean_compiler_witnesses(lean_compiler_witness_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS srnn_theorem_promotion_gates (
  theorem_promotion_gate_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'theorem_promotion_gate/v1'),
  claim_id TEXT NOT NULL,
  claim_status_transition_id TEXT NOT NULL,
  proof_witness_id TEXT NOT NULL,
  lean_compiler_witness_id TEXT NOT NULL,
  non_collapse_transition_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  allowed INTEGER NOT NULL CHECK (allowed IN (0,1)),
  source_hash_matches_claim INTEGER NOT NULL CHECK (source_hash_matches_claim IN (0,1)),
  rejection_reason TEXT,
  created_at TEXT NOT NULL,
  CHECK (allowed = 0 OR (source_hash_matches_claim = 1 AND rejection_reason IS NULL)),
  FOREIGN KEY (claim_id) REFERENCES srnn_evidence_claims(claim_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (claim_status_transition_id) REFERENCES srnn_claim_status_transitions(claim_status_transition_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (proof_witness_id) REFERENCES srnn_proof_witnesses(proof_witness_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (lean_compiler_witness_id) REFERENCES srnn_lean_compiler_witnesses(lean_compiler_witness_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (non_collapse_transition_id) REFERENCES srnn_non_collapse_transitions(transition_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TRIGGER IF NOT EXISTS trg_srnn_theorem_gate_allowed_insert_guard
BEFORE INSERT ON srnn_theorem_promotion_gates
WHEN NEW.allowed = 1
BEGIN
  SELECT CASE WHEN NEW.source_hash_matches_claim <> 1 THEN RAISE(ABORT, 'allowed theorem gate requires source_hash_matches_claim=1') END;
  SELECT CASE WHEN NEW.rejection_reason IS NOT NULL THEN RAISE(ABORT, 'allowed theorem gate must not carry rejection_reason') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_lean_compiler_witnesses lc
    WHERE lc.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND lc.result = 'passed'
      AND lc.contains_sorry = 0
      AND lc.contains_admit = 0
      AND lc.unapproved_axiom_count = 0
  ) THEN RAISE(ABORT, 'allowed theorem gate requires passing LeanCompilerWitness') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_proof_witnesses pw
    WHERE pw.proof_witness_id = NEW.proof_witness_id
      AND pw.claim_id = NEW.claim_id
      AND pw.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND pw.lean_compiler_result = 'passed'
      AND pw.theorem_status = 'proved'
      AND pw.source_hash_matches_claim = 1
      AND pw.no_sorry = 1
      AND pw.no_admit = 1
      AND pw.no_unapproved_axioms = 1
  ) THEN RAISE(ABORT, 'allowed theorem gate requires proved ProofWitness') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_claim_status_transitions st
    WHERE st.claim_status_transition_id = NEW.claim_status_transition_id
      AND st.claim_id = NEW.claim_id
      AND st.target_status IN ('theorem','proof_verified')
      AND st.transition_kind = 'prove'
      AND st.allowed = 1
      AND st.proof_witness_refs_json <> '[]'
      AND st.proof_witness_refs_json <> ''
      AND st.lean_compiler_witness_refs_json <> '[]'
      AND st.lean_compiler_witness_refs_json <> ''
      AND st.theorem_promotion_gate_id = NEW.theorem_promotion_gate_id
      AND json_valid(st.proof_witness_refs_json) = 1
      AND json_valid(st.lean_compiler_witness_refs_json) = 1
      AND json_valid(st.required_witness_refs_json) = 1
      AND EXISTS (SELECT 1 FROM json_each(st.proof_witness_refs_json) WHERE value = NEW.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(st.lean_compiler_witness_refs_json) WHERE value = NEW.lean_compiler_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(st.required_witness_refs_json) WHERE value = NEW.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(st.required_witness_refs_json) WHERE value = NEW.lean_compiler_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(st.required_witness_refs_json) WHERE value = NEW.theorem_promotion_gate_id)
  ) THEN RAISE(ABORT, 'allowed theorem gate requires matching prove transition with exact proof/Lean/gate witness IDs') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_evidence_claims c
    WHERE c.claim_id = NEW.claim_id
      AND (c.claim_status IN ('theorem','proof_verified') OR c.epistemic_status IN ('theorem','proof_verified'))
      AND c.status_transition_id = NEW.claim_status_transition_id
      AND c.theorem_promotion_gate_id = NEW.theorem_promotion_gate_id
      AND json_valid(c.proof_witness_refs_json) = 1
      AND json_valid(c.lean_compiler_witness_refs_json) = 1
      AND EXISTS (SELECT 1 FROM json_each(c.proof_witness_refs_json) WHERE value = NEW.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(c.lean_compiler_witness_refs_json) WHERE value = NEW.lean_compiler_witness_id)
  ) THEN RAISE(ABORT, 'allowed theorem gate requires matching theorem claim with exact proof/Lean witness IDs') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_srnn_theorem_gate_allowed_update_guard
BEFORE UPDATE ON srnn_theorem_promotion_gates
WHEN NEW.allowed = 1
BEGIN
  SELECT CASE WHEN NEW.source_hash_matches_claim <> 1 THEN RAISE(ABORT, 'allowed theorem gate requires source_hash_matches_claim=1') END;
  SELECT CASE WHEN NEW.rejection_reason IS NOT NULL THEN RAISE(ABORT, 'allowed theorem gate must not carry rejection_reason') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_lean_compiler_witnesses lc
    WHERE lc.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND lc.result = 'passed'
      AND lc.contains_sorry = 0
      AND lc.contains_admit = 0
      AND lc.unapproved_axiom_count = 0
  ) THEN RAISE(ABORT, 'allowed theorem gate requires passing LeanCompilerWitness') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_proof_witnesses pw
    WHERE pw.proof_witness_id = NEW.proof_witness_id
      AND pw.claim_id = NEW.claim_id
      AND pw.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND pw.lean_compiler_result = 'passed'
      AND pw.theorem_status = 'proved'
      AND pw.source_hash_matches_claim = 1
      AND pw.no_sorry = 1
      AND pw.no_admit = 1
      AND pw.no_unapproved_axioms = 1
  ) THEN RAISE(ABORT, 'allowed theorem gate requires proved ProofWitness') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_claim_status_transitions st
    WHERE st.claim_status_transition_id = NEW.claim_status_transition_id
      AND st.claim_id = NEW.claim_id
      AND st.target_status IN ('theorem','proof_verified')
      AND st.transition_kind = 'prove'
      AND st.allowed = 1
      AND st.proof_witness_refs_json <> '[]'
      AND st.proof_witness_refs_json <> ''
      AND st.lean_compiler_witness_refs_json <> '[]'
      AND st.lean_compiler_witness_refs_json <> ''
      AND st.theorem_promotion_gate_id = NEW.theorem_promotion_gate_id
      AND json_valid(st.proof_witness_refs_json) = 1
      AND json_valid(st.lean_compiler_witness_refs_json) = 1
      AND json_valid(st.required_witness_refs_json) = 1
      AND EXISTS (SELECT 1 FROM json_each(st.proof_witness_refs_json) WHERE value = NEW.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(st.lean_compiler_witness_refs_json) WHERE value = NEW.lean_compiler_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(st.required_witness_refs_json) WHERE value = NEW.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(st.required_witness_refs_json) WHERE value = NEW.lean_compiler_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(st.required_witness_refs_json) WHERE value = NEW.theorem_promotion_gate_id)
  ) THEN RAISE(ABORT, 'allowed theorem gate requires matching prove transition with exact proof/Lean/gate witness IDs') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_evidence_claims c
    WHERE c.claim_id = NEW.claim_id
      AND (c.claim_status IN ('theorem','proof_verified') OR c.epistemic_status IN ('theorem','proof_verified'))
      AND c.status_transition_id = NEW.claim_status_transition_id
      AND c.theorem_promotion_gate_id = NEW.theorem_promotion_gate_id
      AND json_valid(c.proof_witness_refs_json) = 1
      AND json_valid(c.lean_compiler_witness_refs_json) = 1
      AND EXISTS (SELECT 1 FROM json_each(c.proof_witness_refs_json) WHERE value = NEW.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(c.lean_compiler_witness_refs_json) WHERE value = NEW.lean_compiler_witness_id)
  ) THEN RAISE(ABORT, 'allowed theorem gate requires matching theorem claim with exact proof/Lean witness IDs') END;
END;

CREATE INDEX IF NOT EXISTS idx_srnn_lean_compiler_witnesses_result ON srnn_lean_compiler_witnesses(result, toolchain);
CREATE INDEX IF NOT EXISTS idx_srnn_proof_witnesses_claim ON srnn_proof_witnesses(claim_id, theorem_status);
CREATE INDEX IF NOT EXISTS idx_srnn_theorem_promotion_gates_claim ON srnn_theorem_promotion_gates(claim_id, allowed);


-- Draft 5.2.2 corrective hardening: exact JSON witness-ID membership checks.
-- These triggers close the gap where arrays were only checked for non-emptiness.
-- SQLite JSON1 is required because theorem/proof promotion arrays are JSON.

CREATE TRIGGER IF NOT EXISTS trg_srnn_evidence_claim_theorem_refs_exact_update_guard
BEFORE UPDATE ON srnn_evidence_claims
WHEN (NEW.claim_status IN ('theorem','proof_verified') OR NEW.epistemic_status IN ('theorem','proof_verified'))
BEGIN
  SELECT CASE WHEN NEW.theorem_promotion_gate_id IS NULL THEN RAISE(ABORT, 'theorem claim update requires theorem_promotion_gate_id') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_theorem_promotion_gates g
    WHERE g.theorem_promotion_gate_id = NEW.theorem_promotion_gate_id
      AND g.claim_id = NEW.claim_id
      AND g.claim_status_transition_id = NEW.status_transition_id
      AND g.allowed = 1
      AND json_valid(NEW.proof_witness_refs_json) = 1
      AND json_valid(NEW.lean_compiler_witness_refs_json) = 1
      AND EXISTS (SELECT 1 FROM json_each(NEW.proof_witness_refs_json) WHERE value = g.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(NEW.lean_compiler_witness_refs_json) WHERE value = g.lean_compiler_witness_id)
  ) THEN RAISE(ABORT, 'theorem claim update must retain exact proof/Lean witness IDs required by gate') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_srnn_claim_status_transition_theorem_refs_exact_update_guard
BEFORE UPDATE ON srnn_claim_status_transitions
WHEN NEW.target_status IN ('theorem','proof_verified')
BEGIN
  SELECT CASE WHEN NEW.theorem_promotion_gate_id IS NULL THEN RAISE(ABORT, 'theorem transition update requires theorem_promotion_gate_id') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_theorem_promotion_gates g
    WHERE g.theorem_promotion_gate_id = NEW.theorem_promotion_gate_id
      AND g.claim_id = NEW.claim_id
      AND g.claim_status_transition_id = NEW.claim_status_transition_id
      AND g.allowed = 1
      AND json_valid(NEW.proof_witness_refs_json) = 1
      AND json_valid(NEW.lean_compiler_witness_refs_json) = 1
      AND json_valid(NEW.required_witness_refs_json) = 1
      AND EXISTS (SELECT 1 FROM json_each(NEW.proof_witness_refs_json) WHERE value = g.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(NEW.lean_compiler_witness_refs_json) WHERE value = g.lean_compiler_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(NEW.required_witness_refs_json) WHERE value = g.proof_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(NEW.required_witness_refs_json) WHERE value = g.lean_compiler_witness_id)
      AND EXISTS (SELECT 1 FROM json_each(NEW.required_witness_refs_json) WHERE value = g.theorem_promotion_gate_id)
  ) THEN RAISE(ABORT, 'theorem transition update must retain exact proof/Lean/gate witness IDs required by gate') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_srnn_inference_witness_theorem_refs_exact_insert_guard
BEFORE INSERT ON srnn_inference_witnesses
WHEN NEW.output_epistemic_status IN ('theorem','proof_verified') OR NEW.conclusion_status IN ('theorem','proof_verified')
BEGIN
  SELECT CASE WHEN NEW.theorem_promotion_gate_id IS NULL THEN RAISE(ABORT, 'theorem inference requires theorem_promotion_gate_id') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_theorem_promotion_gates g
    WHERE g.theorem_promotion_gate_id = NEW.theorem_promotion_gate_id
      AND g.claim_id = NEW.conclusion_claim_id
      AND g.allowed = 1
      AND NEW.proof_witness_ref = g.proof_witness_id
      AND NEW.lean_compiler_witness_ref = g.lean_compiler_witness_id
  ) THEN RAISE(ABORT, 'theorem inference witness must reference exact proof/Lean witness IDs required by gate') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_srnn_inference_witness_theorem_refs_exact_update_guard
BEFORE UPDATE ON srnn_inference_witnesses
WHEN NEW.output_epistemic_status IN ('theorem','proof_verified') OR NEW.conclusion_status IN ('theorem','proof_verified')
BEGIN
  SELECT CASE WHEN NEW.theorem_promotion_gate_id IS NULL THEN RAISE(ABORT, 'theorem inference update requires theorem_promotion_gate_id') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM srnn_theorem_promotion_gates g
    WHERE g.theorem_promotion_gate_id = NEW.theorem_promotion_gate_id
      AND g.claim_id = NEW.conclusion_claim_id
      AND g.allowed = 1
      AND NEW.proof_witness_ref = g.proof_witness_id
      AND NEW.lean_compiler_witness_ref = g.lean_compiler_witness_id
  ) THEN RAISE(ABORT, 'theorem inference witness update must retain exact proof/Lean witness IDs required by gate') END;
END;
