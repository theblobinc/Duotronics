-- Duotronic Witness Contract v1.7 Draft 1.1 Bayesian + Knot Theory First-Class Additions
-- Apply after executable/sql/draft5_2_schema_additions.sql.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS srnn_bayesian_models (
  model_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'bayesian_model/v1'),
  model_version TEXT NOT NULL,
  hypotheses_json TEXT NOT NULL,
  observation_space_json TEXT NOT NULL,
  update_method TEXT NOT NULL CHECK (update_method IN ('exact_discrete_bayes','log_space_discrete_bayes','conjugate_closed_form','approximate_monte_carlo','external_verified')),
  assumptions_json TEXT,
  status TEXT NOT NULL CHECK (status IN ('draft','active','deprecated','rejected')),
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_bayesian_priors (
  prior_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'bayesian_prior/v1'),
  model_id TEXT NOT NULL REFERENCES srnn_bayesian_models(model_id),
  hypothesis_distribution_json TEXT NOT NULL,
  normalization_status TEXT NOT NULL CHECK (normalization_status IN ('normalized','unnormalized_rejected','approximate_declared')),
  provenance_refs_json TEXT NOT NULL,
  epistemic_status TEXT NOT NULL CHECK (epistemic_status IN ('candidate','computed','attested','policy_bounded')),
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_bayesian_likelihoods (
  likelihood_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'bayesian_likelihood/v1'),
  model_id TEXT NOT NULL REFERENCES srnn_bayesian_models(model_id),
  observation_id TEXT NOT NULL,
  likelihoods_json TEXT NOT NULL,
  normalization_convention TEXT NOT NULL CHECK (normalization_convention IN ('probability_mass','relative_likelihood','log_likelihood')),
  normalization_convention_id TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_bayesian_posterior_states (
  posterior_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'bayesian_posterior_state/v1'),
  model_id TEXT NOT NULL REFERENCES srnn_bayesian_models(model_id),
  update_witness_id TEXT NOT NULL,
  hypothesis_distribution_json TEXT NOT NULL,
  normalization_status TEXT NOT NULL CHECK (normalization_status IN ('normalized','approximate_declared','rejected')),
  non_collapse_transition_id TEXT NOT NULL,
  posterior_status TEXT NOT NULL CHECK (posterior_status IN ('candidate','computed','calibrated','rejected')),
  approximation_error_bound REAL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_bayesian_update_witnesses (
  update_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'bayesian_update_witness/v1'),
  model_id TEXT NOT NULL REFERENCES srnn_bayesian_models(model_id),
  prior_id TEXT NOT NULL REFERENCES srnn_bayesian_priors(prior_id),
  likelihood_id TEXT NOT NULL REFERENCES srnn_bayesian_likelihoods(likelihood_id),
  observation_evidence_ref TEXT NOT NULL,
  posterior_id TEXT NOT NULL,
  update_method TEXT NOT NULL CHECK (update_method IN ('exact_discrete_bayes','log_space_discrete_bayes','conjugate_closed_form','approximate_monte_carlo','external_verified')),
  normalization_constant REAL NOT NULL CHECK (normalization_constant > 0),
  approximation_used INTEGER NOT NULL CHECK (approximation_used IN (0,1)),
  approximation_error_bound REAL,
  non_collapse_transition_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  replay_grammar_ref TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (posterior_id) REFERENCES srnn_bayesian_posterior_states(posterior_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS srnn_bayesian_update_replay_witnesses (
  replay_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'bayesian_update_replay_witness/v1'),
  model_id TEXT NOT NULL REFERENCES srnn_bayesian_models(model_id),
  update_witness_id TEXT NOT NULL REFERENCES srnn_bayesian_update_witnesses(update_witness_id),
  prior_id TEXT NOT NULL REFERENCES srnn_bayesian_priors(prior_id),
  likelihood_id TEXT NOT NULL REFERENCES srnn_bayesian_likelihoods(likelihood_id),
  posterior_id TEXT NOT NULL REFERENCES srnn_bayesian_posterior_states(posterior_id),
  replay_status TEXT NOT NULL CHECK (replay_status IN ('replayed_exact','replayed_within_tolerance','bounded_approximation','rejected')),
  hypothesis_set_verified INTEGER NOT NULL CHECK (hypothesis_set_verified IN (0,1)),
  model_consistency_verified INTEGER NOT NULL CHECK (model_consistency_verified IN (0,1)),
  computed_normalization_constant REAL NOT NULL CHECK (computed_normalization_constant > 0),
  computed_posterior_distribution_json TEXT NOT NULL,
  tolerance REAL NOT NULL CHECK (tolerance >= 0),
  replay_grammar_ref TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_bayesian_decision_witnesses (
  decision_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'bayesian_decision_witness/v1'),
  model_id TEXT NOT NULL REFERENCES srnn_bayesian_models(model_id),
  posterior_id TEXT NOT NULL REFERENCES srnn_bayesian_posterior_states(posterior_id),
  decision_id TEXT NOT NULL,
  decision_rule TEXT NOT NULL CHECK (decision_rule IN ('maximum_posterior','minimum_expected_loss','maximum_expected_utility','abstain_under_uncertainty','human_review')),
  utility_or_loss_model_json TEXT NOT NULL,
  expected_values_json TEXT,
  policy_decision_required INTEGER NOT NULL CHECK (policy_decision_required IN (0,1)),
  policy_decision_id TEXT,
  non_collapse_transition_id TEXT NOT NULL,
  decision_authority TEXT NOT NULL CHECK (decision_authority IN ('decision_support','policy_approved','human_review_required','rejected')),
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS srnn_bayes_decision_policy_required_guard
BEFORE INSERT ON srnn_bayesian_decision_witnesses
WHEN NEW.policy_decision_required = 1 AND (NEW.policy_decision_id IS NULL OR length(NEW.policy_decision_id) = 0)
BEGIN
  SELECT RAISE(ABORT, 'bayesian decision requiring policy approval must reference policy decision witness');
END;

CREATE TRIGGER IF NOT EXISTS srnn_bayes_decision_not_policy_without_policy
BEFORE INSERT ON srnn_bayesian_decision_witnesses
WHEN NEW.decision_authority = 'policy_approved' AND (NEW.policy_decision_id IS NULL OR length(NEW.policy_decision_id) = 0)
BEGIN
  SELECT RAISE(ABORT, 'bayesian decision support cannot become policy approval without policy decision witness');
END;

CREATE TABLE IF NOT EXISTS srnn_bayesian_calibration_reports (
  calibration_report_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'bayesian_calibration_report/v1'),
  model_id TEXT NOT NULL REFERENCES srnn_bayesian_models(model_id),
  posterior_refs_json TEXT NOT NULL,
  scoring_rule TEXT NOT NULL CHECK (scoring_rule IN ('brier','log_score','expected_calibration_error','custom')),
  score REAL,
  calibration_status TEXT NOT NULL CHECK (calibration_status IN ('uncalibrated','calibrated_candidate','calibrated_reviewed','rejected')),
  limitations_json TEXT NOT NULL,
  non_collapse_transition_id TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS srnn_bayes_no_policyless_update
BEFORE INSERT ON srnn_bayesian_update_witnesses
WHEN NEW.policy_decision_id IS NULL OR length(NEW.policy_decision_id) = 0
BEGIN
  SELECT RAISE(ABORT, 'bayesian update requires policy decision witness');
END;

CREATE TABLE IF NOT EXISTS srnn_knot_diagram_witnesses (
  diagram_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_diagram_witness/v1'),
  diagram_id TEXT NOT NULL UNIQUE,
  encoding_type TEXT NOT NULL CHECK (encoding_type IN ('planar_diagram','gauss_code','dowker_thistlethwaite','grid_diagram','braid_closure','implementation_defined')),
  encoding_payload_json TEXT NOT NULL,
  component_count INTEGER NOT NULL CHECK (component_count >= 1),
  crossing_count INTEGER CHECK (crossing_count >= 0),
  orientation_policy TEXT NOT NULL CHECK (orientation_policy IN ('oriented','unoriented','mixed','unknown_rejected')),
  mirror_policy TEXT CHECK (mirror_policy IN ('distinguish_mirror','identify_mirror','unknown_rejected')),
  canonical_form_hash TEXT,
  canonicalization_status TEXT NOT NULL CHECK (canonicalization_status IN ('not_canonicalized','canonicalized','candidate','rejected')),
  canonicalization_witness_id TEXT,
  normalization_convention_id TEXT,
  non_collapse_transition_id TEXT NOT NULL,
  claim_status TEXT NOT NULL CHECK (claim_status IN ('candidate','computed','verified','rejected')),
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_knot_braid_word_witnesses (
  braid_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_braid_word_witness/v1'),
  braid_id TEXT NOT NULL UNIQUE,
  strand_count INTEGER NOT NULL CHECK (strand_count >= 2),
  generator_sequence_json TEXT NOT NULL,
  closure_convention TEXT NOT NULL CHECK (closure_convention IN ('standard_closure','plat_closure','open_braid','unknown_rejected')),
  orientation_policy TEXT NOT NULL CHECK (orientation_policy IN ('oriented','unoriented','unknown_rejected')),
  source_diagram_id TEXT,
  non_collapse_transition_id TEXT NOT NULL,
  claim_status TEXT NOT NULL CHECK (claim_status IN ('candidate','computed','verified','rejected')),
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_knot_reidemeister_move_witnesses (
  move_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_reidemeister_move_witness/v1'),
  source_diagram_id TEXT NOT NULL,
  target_diagram_id TEXT NOT NULL,
  move_type TEXT NOT NULL CHECK (move_type IN ('R1','R1_inverse','R2','R2_inverse','R3','isotopy_relabeled','braid_relation','markov_move')),
  affected_crossings_json TEXT,
  checked INTEGER NOT NULL CHECK (checked IN (0,1)),
  checker_ref TEXT,
  non_collapse_transition_id TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_knot_reidemeister_trace_witnesses (
  trace_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_reidemeister_trace_witness/v1'),
  source_diagram_id TEXT NOT NULL,
  target_diagram_id TEXT NOT NULL,
  move_witness_refs_json TEXT NOT NULL,
  trace_status TEXT NOT NULL CHECK (trace_status IN ('candidate','replayed','trace_verified','rejected')),
  replay_checker_ref TEXT NOT NULL,
  compression_policy TEXT CHECK (compression_policy IN ('uncompressed','lossless_compressed','summary_only_rejected')),
  non_collapse_transition_id TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_knot_canonicalization_witnesses (
  canonicalization_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_canonicalization_witness/v1'),
  source_object_ref TEXT NOT NULL,
  canonical_form_hash TEXT NOT NULL,
  hash_algorithm TEXT NOT NULL CHECK (hash_algorithm IN ('sha256','sha3_256','blake3','implementation_defined_declared')),
  canonicalization_algorithm_ref TEXT NOT NULL,
  canonical_domain_ref TEXT NOT NULL,
  collision_policy TEXT NOT NULL CHECK (collision_policy IN ('reject_on_collision','require_full_payload_compare','proof_backed_injective_encoding')),
  canonicalization_status TEXT NOT NULL CHECK (canonicalization_status IN ('candidate','canonicalized','canonical_form_verified','rejected')),
  proof_witness_ref TEXT,
  replay_data_ref TEXT,
  non_collapse_transition_id TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_knot_invariant_witnesses (
  invariant_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_invariant_witness/v1'),
  source_object_ref TEXT NOT NULL,
  invariant_kind TEXT NOT NULL CHECK (invariant_kind IN ('crossing_count','component_count','alexander_polynomial','jones_polynomial','signature','fundamental_group_presentation','custom')),
  normalization_convention TEXT NOT NULL,
  normalization_convention_id TEXT NOT NULL,
  invariant_value_json TEXT NOT NULL,
  computation_method TEXT NOT NULL CHECK (computation_method IN ('manual_attestation','deterministic_algorithm','external_tool','lean_proof','unknown_rejected')),
  replay_data_ref TEXT,
  proof_witness_ref TEXT,
  lean_compiler_witness_ref TEXT,
  claim_status TEXT NOT NULL CHECK (claim_status IN ('candidate','computed_support','trace_verified','proof_verified','rejected')),
  complete_for_domain INTEGER NOT NULL CHECK (complete_for_domain IN (0,1)),
  completeness_witness_ref TEXT,
  domain_ref TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_knot_invariant_completeness_witnesses (
  completeness_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_invariant_completeness_witness/v1'),
  invariant_witness_id TEXT NOT NULL REFERENCES srnn_knot_invariant_witnesses(invariant_witness_id),
  invariant_kind TEXT NOT NULL,
  domain_ref TEXT NOT NULL,
  completeness_status TEXT NOT NULL CHECK (completeness_status IN ('domain_limited_complete','incomplete','unknown_rejected','rejected')),
  proof_witness_ref TEXT NOT NULL,
  lean_compiler_witness_ref TEXT NOT NULL,
  limitations_json TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_knot_equivalence_authority_paths (
  authority_path_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_equivalence_authority_path/v1'),
  equivalence_witness_id TEXT,
  source_object_ref TEXT NOT NULL,
  target_object_ref TEXT NOT NULL,
  path_entries_json TEXT NOT NULL,
  authority_status TEXT NOT NULL CHECK (authority_status IN ('candidate','computed_support','trace_verified','canonical_form_verified','proof_verified','rejected')),
  non_collapse_transition_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srnn_knot_equivalence_witnesses (
  equivalence_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'knot_equivalence_witness/v1'),
  source_object_ref TEXT NOT NULL,
  target_object_ref TEXT NOT NULL,
  equivalence_relation TEXT NOT NULL CHECK (equivalence_relation IN ('ambient_isotopy','oriented_ambient_isotopy','link_equivalence','braid_markov_equivalence','mirror_identified_equivalence')),
  authority_level TEXT NOT NULL CHECK (authority_level IN ('candidate','computed_support','trace_verified','canonical_form_verified','proof_verified','rejected')),
  authority_path_id TEXT NOT NULL REFERENCES srnn_knot_equivalence_authority_paths(authority_path_id),
  authority_path_json TEXT,
  invariant_witness_refs_json TEXT,
  proof_witness_ref TEXT,
  lean_compiler_witness_ref TEXT,
  non_collapse_transition_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS srnn_knot_equivalence_requires_authority_path
BEFORE INSERT ON srnn_knot_equivalence_witnesses
WHEN NEW.authority_path_id IS NULL OR length(NEW.authority_path_id) = 0
BEGIN
  SELECT RAISE(ABORT, 'knot equivalence requires first-class authority path');
END;

CREATE TRIGGER IF NOT EXISTS srnn_knot_proof_verified_requires_proof_refs
BEFORE INSERT ON srnn_knot_equivalence_witnesses
WHEN NEW.authority_level = 'proof_verified' AND (NEW.proof_witness_ref IS NULL OR NEW.lean_compiler_witness_ref IS NULL)
BEGIN
  SELECT RAISE(ABORT, 'proof_verified knot equivalence requires proof and Lean compiler witnesses');
END;

CREATE TRIGGER IF NOT EXISTS srnn_knot_invariant_complete_requires_proof
BEFORE INSERT ON srnn_knot_invariant_witnesses
WHEN NEW.complete_for_domain = 1 AND (NEW.proof_witness_ref IS NULL OR NEW.lean_compiler_witness_ref IS NULL OR NEW.completeness_witness_ref IS NULL)
BEGIN
  SELECT RAISE(ABORT, 'complete knot invariant claim requires completeness and proof authority witnesses');
END;
