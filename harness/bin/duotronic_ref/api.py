"""Reference-impl operation dispatch.

`run_operation(op_name, given) -> dict` is the contract surface that the
harness loader uses to drive every fixture row. External implementations
plug in by exposing a module that defines the same callable; the harness
selects the impl via `--impl <module>` or the `DUOTRONIC_IMPL` env var.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from . import (
    audit,
    canonicalizer,
    dbp,
    dpfc,
    normalizer,
    policy_shield,
    replay,
    retention,
    spectral,
    witness8,
    wsb2,
)
from .registries import (
    FAMILY_REGISTRY,
    GEOMETRY_REGISTRY,
    MIGRATION_REGISTRY,
    NORMALIZER_REGISTRY,
    POLICY_REGISTRY,
    RETENTION_REGISTRY,
    SCHEMA_REGISTRY,
    TRANSPORT_REGISTRY,
)


__all__ = ["run_operation", "OPERATIONS", "register_operation"]


def _family(family_id: str) -> dpfc.Family:
    fam = normalizer.get_family(family_id)
    if fam is None:
        raise KeyError(f"unknown family {family_id}")
    return fam


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _coerce_utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    raise TypeError(f"unsupported datetime value: {value!r}")


def _resolve_transport_profile(profile_ref: str) -> tuple[str, str]:
    if "@" in profile_ref:
        profile_id, version = profile_ref.split("@", 1)
        return profile_id, version
    return profile_ref, "v1"


def _resource_witness_validity(witness: Mapping[str, Any]) -> tuple[bool, Mapping[str, Any]]:
    freshness = witness.get("freshness", {})
    policy = witness.get("policy", {})
    valid = (
        witness.get("trust_status") == "canonicalized"
        and not bool(freshness.get("stale", False))
        and float(witness.get("confidence", 0.0)) >= 0.5
        and float(witness.get("effective_capacity_score", 0.0)) > 0.0
        and bool(policy.get("runtime_mode"))
    )
    return valid, policy


def _resource_satisfies_requirements(
    witness: Mapping[str, Any],
    required: Mapping[str, Any],
) -> bool:
    return (
        float(witness.get("cpu_available_cores", 0.0)) >= float(required.get("cpu_cores", 0.0))
        and float(witness.get("ram_free_bytes", 0.0)) >= float(required.get("ram_bytes", 0.0))
        and float(witness.get("gpu_free_bytes", 0.0)) >= float(required.get("gpu_bytes", 0.0))
        and float(witness.get("disk_io_bandwidth", 0.0)) >= float(required.get("disk_io_bandwidth", 0.0))
        and float(witness.get("network_bandwidth", 0.0)) >= float(required.get("network_bandwidth", 0.0))
        and float(witness.get("max_containers", 0.0) - witness.get("containers_running", 0.0))
        >= float(required.get("containers", 0.0))
    )


def _wgrnn_authority_inputs(feature_vector: Mapping[str, Any]) -> tuple[float, bool, bool]:
    authority_inputs = feature_vector.get("authority_inputs", {})
    transport_validated = bool(authority_inputs.get("transport_validated", True))
    canonicalization_validated = bool(
        authority_inputs.get("canonicalization_validated", True)
    )
    if not transport_validated or not canonicalization_validated:
        return 0.0, transport_validated, canonicalization_validated
    authority = min(
        _clamp_unit(authority_inputs.get("profile_requested_authority", 1.0)),
        _clamp_unit(
            authority_inputs.get(
                "normalizer_confidence",
                feature_vector.get("confidence_score", 1.0),
            )
        ),
        _clamp_unit(authority_inputs.get("policy_limit", 1.0)),
    )
    return authority, transport_validated, canonicalization_validated


# ---------------------------------------------------------------------------
# DPFC operations
# ---------------------------------------------------------------------------

def _op_evaluate_family_word(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    value = dpfc.evaluate_family_word(list(given["word"]), family)
    return {"value": value, "core_magnitude": f"mu_{value}"}


def _op_family_successor(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    return {"successor": dpfc.family_successor(list(given["word"]), family)}


def _op_encode_core_to_family(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    word = dpfc.encode_core_to_family(int(given["core_index"]), family)
    return {"word": word}


def _op_family_conversion(given: Mapping[str, Any]) -> dict[str, Any]:
    src = _family(given["source_family"])
    tgt = _family(given["target_family"])
    return dpfc.convert_family(list(given["word"]), src, tgt)


def _op_canonicalize_family_object(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    return dpfc.canonicalize_family_object(list(given["word"]), family)


def _op_canonical_storage(given: Mapping[str, Any]) -> dict[str, Any]:
    family = _family(given["family_id"])
    return {"canonical_storage": dpfc.canonical_storage(list(given["word"]), family)}


def _op_exported_nonneg_add_with_correction(given: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "value": dpfc.exported_nonnegative_add_with_correction(
            int(given["left"]), int(given["right"])
        )
    }


def _op_exported_nonneg_add_without_correction(given: Mapping[str, Any]) -> dict[str, Any]:
    """Reference impl returns the deliberately-wrong value AND emits a
    policy-mismatch flag so the suite can verify external impls expose
    the same affine-correction failure mode."""
    wrong = dpfc.exported_nonnegative_add_without_correction(
        int(given["left"]), int(given["right"])
    )
    correct = dpfc.exported_nonnegative_add_with_correction(
        int(given["left"]), int(given["right"])
    )
    return {
        "value": wrong,
        "expected_correct_value": correct,
        "required_correction": correct - wrong,
        "failure_code": "export_policy_mismatch",
        "trusted_arithmetic_use": False,
    }


def _op_detect_export_policy_mismatch(given: Mapping[str, Any]) -> dict[str, Any]:
    return dpfc.detect_export_policy_mismatch(
        dpfc.Mu(int(given["left_core"])),
        dpfc.Mu(int(given["right_core"])),
        int(given["declared_left_export"]),
        int(given["declared_right_export"]),
    )


# ---------------------------------------------------------------------------
# Witness8 / WSB2 / DBP
# ---------------------------------------------------------------------------

def _op_decode_witness8(given: Mapping[str, Any]) -> dict[str, Any]:
    return witness8.decode_witness8(
        given["row"],
        profile_id=given.get("profile_id", "witness8-minsafe@v1"),
        profile_declares_numeric_zero=bool(
            given.get("profile_declares_numeric_zero", False)
        ),
    )


def _op_decode_wsb2(given: Mapping[str, Any]) -> dict[str, Any]:
    return wsb2.decode_wsb2_rows(
        given["payload"],
        profile_declares_numeric_zero=bool(
            given.get("profile_declares_numeric_zero", False)
        ),
    )


def _op_dbp_ingress(given: Mapping[str, Any]) -> dict[str, Any]:
    return dbp.validate_dbp_frame(given["frame"])


def _op_ingress_frame(given: Mapping[str, Any]) -> dict[str, Any]:
    """Composite end-to-end ingress: DBP → (WSB2 | Witness8) → canonicalize."""
    frame = given["frame"]
    transport = dbp.validate_dbp_frame(frame)
    if not transport.get("semantic_decode_allowed"):
        return {"transport": transport, "decoded": None, "canonical": None}
    profile_id = transport.get("profile_id")
    profile = TRANSPORT_REGISTRY.resolve(*profile_id.split("@"))
    payload_kind = frame.get("payload_kind")
    payload = frame.get("payload", {})
    if payload_kind == "wsb2":
        decoded = wsb2.decode_wsb2_rows(
            payload, profile_declares_numeric_zero=profile.declares_numeric_zero
        )
    elif payload_kind == "witness8":
        decoded = witness8.decode_witness8(
            payload.get("row"),
            profile_id=profile_id,
            profile_declares_numeric_zero=profile.declares_numeric_zero,
        )
    else:
        decoded = {"failure_code": "unknown_payload_kind"}
    canonical: dict[str, Any] | None = None
    bundle = frame.get("witness_key_bundle")
    if bundle is not None:
        canonical = canonicalizer.canonicalize_witness_key_bundle(bundle)
    return {"transport": transport, "decoded": decoded, "canonical": canonical}


def _op_canonicalize_witness_key_bundle(given: Mapping[str, Any]) -> dict[str, Any]:
    return canonicalizer.canonicalize_witness_key_bundle(given["bundle"])


def _op_validate_resource_availability_witness(given: Mapping[str, Any]) -> dict[str, Any]:
    witness = given["resource_witness"]
    valid, policy = _resource_witness_validity(witness)
    allowed_task_classes = set(policy.get("allowed_task_classes", []))
    cpu_schedulable = (
        valid
        and float(witness.get("cpu_available_cores", 0.0)) > 0.0
        and float(witness.get("ram_free_bytes", 0.0)) > 0.0
        and bool(allowed_task_classes)
    )
    gpu_schedulable = (
        valid
        and float(witness.get("gpu_free_bytes", 0.0)) > 0.0
        and "run_model_inference" in allowed_task_classes
    )
    return {
        "valid": valid,
        "schedulable_for_cpu_task": cpu_schedulable,
        "schedulable_for_gpu_task": gpu_schedulable,
        "authority": policy.get("runtime_mode") if valid else 0,
        "trust_status": witness.get("trust_status"),
    }


def _op_validate_cluster_task_delegation(given: Mapping[str, Any]) -> dict[str, Any]:
    task_payload = given["task_payload"]
    resource_witness = given["resource_witness"]
    resource_status = _op_validate_resource_availability_witness(
        {"resource_witness": resource_witness}
    )
    policy = resource_witness.get("policy", {})
    replay = task_payload.get("replay", {})
    transport_profile_id, transport_version = _resolve_transport_profile(
        replay.get("transport_profile_id", "dbp-cluster-full-duplex-v1")
    )
    transport = TRANSPORT_REGISTRY.resolve(transport_profile_id, transport_version)
    task_allowed = task_payload.get("task_type") in set(policy.get("allowed_task_classes", []))
    resources_fit = _resource_satisfies_requirements(
        resource_witness,
        task_payload.get("required_resources", {}),
    )
    action_allowed = bool(resource_status["valid"] and task_allowed and resources_fit)
    return {
        "action_allowed": action_allowed,
        "delegated_task_record_created": action_allowed,
        "command_lane": 3 if action_allowed else None,
        "task_result_lane": 5 if action_allowed else None,
        "transport_profile_id": transport.profile_id,
        "transport_requires_replay_key": transport.requires_replay_key,
        "target_node_id": task_payload.get("target_node_id"),
        "failure_code": None if action_allowed else "task_delegation_denied",
    }


def _op_invalidate_stale_resource_heartbeat(given: Mapping[str, Any]) -> dict[str, Any]:
    last_heartbeat = _coerce_utc_datetime(given["last_heartbeat_time"])
    current_time = _coerce_utc_datetime(given["current_time"])
    heartbeat_timeout = float(given["heartbeat_timeout_seconds"])
    elapsed_seconds = max(0.0, (current_time - last_heartbeat).total_seconds())
    stale = elapsed_seconds > heartbeat_timeout
    return {
        "node_id": given.get("node_id"),
        "elapsed_seconds": elapsed_seconds,
        "node_schedulable": not stale,
        "resource_authority": 0 if stale else 1,
        "pending_tasks_reassigned": stale,
        "trigger_kind": "resource_heartbeat_timeout" if stale else None,
        "required_action": "reassign_tasks" if stale else None,
    }


def _op_evaluate_wgrnn_policy_gates(given: Mapping[str, Any]) -> dict[str, Any]:
    feature_vector = given["witness_feature_vector"]
    policy = given.get("policy", {})
    authority_t, transport_validated, canonicalization_validated = _wgrnn_authority_inputs(
        feature_vector
    )
    confidence_score = _clamp_unit(feature_vector.get("confidence_score", authority_t or 1.0))
    invalidation_score = _clamp_unit(feature_vector.get("invalidation_score", 0.0))
    novelty_score = _clamp_unit(feature_vector.get("novelty_score", 0.0))
    g_write = min(authority_t, confidence_score) if feature_vector.get("policy_allow_write", True) else 0.0
    g_promote = authority_t if feature_vector.get("policy_allow_promote", False) else 0.0
    g_quarantine = 0.0

    if invalidation_score >= _clamp_unit(policy.get("threshold_invalidate", 0.5)):
        g_write = 0.0
        g_promote = 0.0

    if authority_t == 0.0:
        g_write = 0.0
        g_promote = 0.0

    if (
        novelty_score >= _clamp_unit(policy.get("high_novelty_threshold", 0.8))
        and confidence_score <= _clamp_unit(policy.get("low_confidence_threshold", 0.5))
    ):
        g_quarantine = 1.0

    if feature_vector.get("human_review_required", False):
        g_promote = 0.0
        g_write = min(g_write, _clamp_unit(policy.get("candidate_write_upper_bound", g_write)))

    persistent_memory_changed = g_write > 0.0
    if persistent_memory_changed and g_quarantine == 1.0:
        update_kind = "quarantine_write"
        slot_status = "quarantined"
    elif persistent_memory_changed:
        update_kind = "candidate_write"
        slot_status = "candidate"
    else:
        update_kind = "no_op"
        slot_status = "unchanged"

    promotion_allowed = g_promote > 0.0 and g_quarantine == 0.0
    return {
        "authority_t": round(authority_t, 6),
        "g_write_after_clamp": round(g_write, 6),
        "g_promote_after_clamp": round(g_promote, 6),
        "g_quarantine_after_clamp": round(g_quarantine, 6),
        "update_kind": update_kind,
        "persistent_memory_changed": persistent_memory_changed,
        "slot_status": slot_status,
        "promotion_allowed": promotion_allowed,
        "stable_write_allowed": bool(persistent_memory_changed and promotion_allowed),
        "transport_validated": transport_validated,
        "canonicalization_validated": canonicalization_validated,
    }


def _op_evaluate_wgrnn_slot_promotion(given: Mapping[str, Any]) -> dict[str, Any]:
    request = given["slot_promotion_request"]
    policy_decision = given.get("policy_decision", {})
    promotion_gate_value = float(request.get("promotion_gate_value", 0.0))
    promotion_threshold = float(request.get("promotion_threshold", 1.0))
    replay_trace_verified = bool(request.get("replay_trace_set_id"))
    retention_ready = bool(request.get("retention_metric_ids"))
    purge_lineage_clear = bool(request.get("purge_check_refs"))
    contradiction_clear = not bool(request.get("contradiction_review_refs"))
    policy_allows = policy_decision.get("decision") == "allow"
    approved = (
        promotion_gate_value >= promotion_threshold
        and replay_trace_verified
        and retention_ready
        and purge_lineage_clear
        and contradiction_clear
        and policy_allows
    )
    return {
        "promotion_request_approved": approved,
        "slot_status_after": "stable" if approved else request.get("status", "candidate"),
        "canonical_witness_fact_created": approved,
        "replay_trace_verified": replay_trace_verified,
        "retention_ready": retention_ready,
        "purge_lineage_clear": purge_lineage_clear,
        "policy_decision": policy_decision.get("decision"),
    }


def _op_evaluate_wgrnn_contradiction_split(given: Mapping[str, Any]) -> dict[str, Any]:
    slot = given["memory_slot"]
    policy = given.get("policy", {})
    contradiction_score = _clamp_unit(slot.get("contradiction_score", 0.0))
    split_threshold = _clamp_unit(policy.get("split_contradiction_threshold", 1.0))
    split_required = contradiction_score > split_threshold
    new_slot_status = "quarantined" if policy.get("quarantine_on_split", False) else "candidate"
    return {
        "SlotSplitRecord_created": split_required,
        "original_slot_unchanged": split_required,
        "new_slot_status": new_slot_status if split_required else None,
        "source_slot_id": slot.get("slot_id"),
        "new_slot_id": (int(slot.get("slot_id", 0)) + 1) if split_required else None,
    }


def _op_evaluate_wgrnn_purge_cascade(given: Mapping[str, Any]) -> dict[str, Any]:
    purge_event = given["evidence_purge_event"]
    slot = given["memory_slot"]
    purged_hashes = set(purge_event.get("purged_provenance_hashes", []))
    slot_hashes = set(slot.get("provenance_hashes", []))
    impacted = bool(purged_hashes.intersection(slot_hashes))
    tombstone_required = impacted and slot.get("trust_status") == "stable"
    return {
        "MemoryPurgeImpactRecord_created": impacted,
        "slot_status_after": "tombstoned" if tombstone_required else slot.get("trust_status"),
        "stable_authority_after": 0 if tombstone_required else 1,
        "purge_event_id": purge_event.get("purge_event_id"),
        "impacted_hashes": sorted(purged_hashes.intersection(slot_hashes)),
    }


def _op_evaluate_cluster_task_conflict(given: Mapping[str, Any]) -> dict[str, Any]:
    conflict = given["task_delegation_conflict"]
    default_resolution = conflict.get("default_resolution", "queue_or_no_action")
    if default_resolution == "least_loaded_node_gets_task":
        alternate_resolution = "reassign_lower_priority_or_second_task"
    else:
        alternate_resolution = default_resolution
    return {
        "task_delegation_conflict_id": conflict.get("task_delegation_conflict_id"),
        "policy_mode": "restricted",
        "if_alternate_node_available": alternate_resolution,
        "if_no_alternate_node": "queue_or_no_action",
        "conflict_type": conflict.get("conflict_type"),
    }


def _op_validate_cluster_authority_frame(given: Mapping[str, Any]) -> dict[str, Any]:
    frame = given["frame"]
    security_mode = frame.get("security_mode")
    authority_bearing = bool(frame.get("authority_bearing", False))
    accepted = not authority_bearing or security_mode == "S2"
    return {
        "accepted": accepted,
        "rejection_reason": None if accepted else "authority_bearing_s1_frame",
        "action": "allow" if accepted else "reject_and_alarm",
        "security_mode": security_mode,
    }


def _op_evaluate_node_hello(given: Mapping[str, Any]) -> dict[str, Any]:
    node_hello = given["node_hello"]
    transport = node_hello.get("transport", {})
    supported_security_modes = set(transport.get("supported_security_modes", []))
    profile_id, version = _resolve_transport_profile(
        transport.get("dbp_profile_id", "dbp-cluster-full-duplex-v1")
    )
    transport_profile = TRANSPORT_REGISTRY.resolve(profile_id, version)
    if "S2" not in supported_security_modes:
        return {
            "accepted": False,
            "rejection_reason": "unsupported_security",
            "retry_allowed": False,
            "transport_profile_id": transport_profile.profile_id,
        }
    return {
        "accepted": True,
        "admission_status": "restricted",
        "lane_layout": "dbp-cluster-full-duplex-v1-layout-a",
        "heartbeat_timeout_seconds": 30,
        "runtime_mode": "restricted",
        "transport_profile_id": transport_profile.profile_id,
    }


def _op_evaluate_cluster_replay_direction_binding(given: Mapping[str, Any]) -> dict[str, Any]:
    payload_hash = given["payload_hash"]
    lane_layout_id = given["lane_layout_id"]
    direction_a = given["direction_a"]
    direction_b = given["direction_b"]
    base_payload = {
        "transport_profile_id": "dbp-cluster-full-duplex-v1",
        "lane_layout_id": lane_layout_id,
        "payload_hash": payload_hash,
    }
    digest_a = replay.normal_form_hash({**base_payload, "direction": direction_a})
    digest_b = replay.normal_form_hash({**base_payload, "direction": direction_b})
    return {
        "replay_digest_a": digest_a,
        "replay_digest_b": digest_b,
        "replay_digest_a_equals_b": digest_a == digest_b,
        "reason": "direction_is_identity_affecting",
    }


def _op_evaluate_cluster_learning_mode_gate(given: Mapping[str, Any]) -> dict[str, Any]:
    task_payload = given["task_payload"]
    cluster_policy = given["cluster_policy"]
    required_learning_mode = (
        task_payload.get("policy", {}).get("learning_mode_required", "not_applicable")
    )
    cluster_learning_mode = cluster_policy.get("cluster_learning_mode", "blocked")
    action_allowed = not (
        required_learning_mode == "active" and cluster_learning_mode != "active"
    )
    return {
        "action_allowed": action_allowed,
        "reason": None if action_allowed else "cluster_learning_mode_insufficient",
        "required_learning_mode": required_learning_mode,
        "cluster_learning_mode": cluster_learning_mode,
    }


def _op_select_cluster_node_for_task(given: Mapping[str, Any]) -> dict[str, Any]:
    nodes = list(given["nodes"])
    selected = min(
        nodes,
        key=lambda node: (
            float(node.get("effective_queue_pressure", 1.0)),
            -float(node.get("effective_capacity_score", 0.0)),
            str(node.get("node_id", "")),
        ),
    )
    return {
        "expected_selected_node": selected.get("node_id"),
        "reason": "sufficient_capacity_lowest_queue_pressure",
        "selected_queue_pressure": selected.get("effective_queue_pressure"),
        "selected_capacity_score": selected.get("effective_capacity_score"),
    }


def _op_evaluate_cluster_node_schedulability(given: Mapping[str, Any]) -> dict[str, Any]:
    task_payload = given.get("task_payload", {})
    candidate_node = given.get("candidate_node", {})
    required_resources = task_payload.get("required_resources", {})
    required_gpu_bytes = float(required_resources.get("gpu_bytes", 0.0))
    available_gpu_bytes = float(candidate_node.get("gpu_free_bytes", 0.0))
    schedulable = available_gpu_bytes >= required_gpu_bytes
    return {
        "schedulable": schedulable,
        "reason": None if schedulable else "gpu_requirement_not_met",
        "required_gpu_bytes": required_gpu_bytes,
        "available_gpu_bytes": available_gpu_bytes,
    }


def _op_evaluate_task_outcome_transport_authority(given: Mapping[str, Any]) -> dict[str, Any]:
    outcome = given.get("task_outcome_witness", {})
    transport = given.get("transport", {})
    policy = given.get("policy", {})
    if not bool(transport.get("dbp_s2_valid", False)):
        return {
            "eta_t": 0.0,
            "authority": 0.0,
            "reason": "transport_failed",
        }

    eta_before_policy = float(outcome.get("normalizer_confidence", 0.0)) * float(outcome.get("h_J_t", 0.0))
    authority = min(eta_before_policy, float(policy.get("l5_limit", eta_before_policy)))
    return {
        "eta_t_before_policy": round(eta_before_policy, 6),
        "eta_t_after_policy": round(authority, 6),
        "eta_t": round(authority, 6),
        "authority": round(authority, 6),
        "reason": None,
    }


def _op_evaluate_node_disconnect_reassignment(given: Mapping[str, Any]) -> dict[str, Any]:
    disconnect_event = given.get("node_disconnect_event", {})
    affected_tasks = list(disconnect_event.get("affected_delegated_task_ids", []))
    disconnect_kind = disconnect_event.get("disconnect_kind")
    reassigned = bool(affected_tasks) and disconnect_kind == "heartbeat_timeout"
    return {
        "node_id": disconnect_event.get("node_id"),
        "node_resource_authority": 0,
        "task_status": "reassigned" if reassigned else "unchanged",
        "self_model_invalidated": True,
        "affected_task_count": len(affected_tasks),
    }


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

def _op_normalize_family_word(given: Mapping[str, Any]) -> dict[str, Any]:
    return normalizer.normalize_family_word(given)


def _op_normalize_reflection_path(given: Mapping[str, Any]) -> dict[str, Any]:
    return normalizer.normalize_reflection_path(given)


def _op_normalize_witness8_row(given: Mapping[str, Any]) -> dict[str, Any]:
    return normalizer.normalize_witness8_row(given)


# ---------------------------------------------------------------------------
# Spectral / EDO
# ---------------------------------------------------------------------------

def _op_infer_missing_fundamental(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.infer_missing_fundamental(list(given["components_hz"]))


def _op_transpose_retention(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.transpose_retention(
        list(given["values"]),
        int(given["transposition"]),
        int(given["modulus"]),
    )


def _op_collapse_to_12edo(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.enharmonic_collapse_policy(
        given.get("source_family", "edo31"),
        given.get("target_family", "edo12"),
        int(given["left_step"]),
        int(given["right_step"]),
    )


def _op_validate_fourier_provenance(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.validate_fourier_provenance(given["witness"])


def _op_temperament_error_witness(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.temperament_error_witness(given["ratio"], given["target_family"])


def _op_approximate_ratio_in_edo(given: Mapping[str, Any]) -> dict[str, Any]:
    return spectral.approximate_ratio_in_edo(given["ratio"], int(given["steps"]))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

def _op_resolve_schema(given: Mapping[str, Any]) -> dict[str, Any]:
    entry = SCHEMA_REGISTRY.resolve(given["schema_id"], given["version"])
    return {
        "schema_id": entry.schema_id,
        "version": entry.version,
        "owner": entry.owner,
        "status": entry.status,
    }


def _op_resolve_family(given: Mapping[str, Any]) -> dict[str, Any]:
    e = FAMILY_REGISTRY.resolve(given["family_id"])
    return {
        "family_id": e.family_id,
        "base": e.base,
        "digit_alphabet": list(e.digit_alphabet),
        "is_bijective_base": e.is_bijective_base,
    }


def _op_resolve_geometry(given: Mapping[str, Any]) -> dict[str, Any]:
    e = GEOMETRY_REGISTRY.resolve(given["geometry_id"])
    return {
        "geometry_id": e.geometry_id,
        "family_id": e.family_id,
        "n_sides": e.n_sides,
        "chirality": e.chirality,
    }


def _op_resolve_transport(given: Mapping[str, Any]) -> dict[str, Any]:
    e = TRANSPORT_REGISTRY.resolve(given["profile_id"], given.get("version", "v1"))
    return {
        "profile_id": e.profile_id,
        "version": e.version,
        "declares_numeric_zero": e.declares_numeric_zero,
        "requires_replay_key": e.requires_replay_key,
    }


def _op_resolve_normalizer(given: Mapping[str, Any]) -> dict[str, Any]:
    e = NORMALIZER_REGISTRY.resolve(given["normalizer_id"], given["version"])
    return {
        "normalizer_id": e.normalizer_id,
        "version": e.version,
        "target_family": e.target_family,
        "has_migration_plan": e.has_migration_plan,
    }


def _op_resolve_retention(given: Mapping[str, Any]) -> dict[str, Any]:
    e = RETENTION_REGISTRY.resolve(given["metric_id"])
    return {
        "metric_id": e.metric_id,
        "version": e.version,
        "baseline_required": e.baseline_required,
        "frozen_on_bypass": e.frozen_on_bypass,
    }


def _op_resolve_policy(given: Mapping[str, Any]) -> dict[str, Any]:
    e = POLICY_REGISTRY.resolve(given["event"])
    return {
        "event": e.event,
        "mode": e.mode,
        "freeze_metrics": e.freeze_metrics,
        "trust_status": e.trust_status,
        "escalation_chain": list(e.escalation_chain),
    }


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

def _op_freeze_retention_baseline(given: Mapping[str, Any]) -> dict[str, Any]:
    retention.LEDGER.freeze_baseline(
        given["metric_id"],
        value=float(given["value"]),
        sample_count=int(given["sample_count"]),
        profile=given.get("profile", "reference-default"),
    )
    return {"frozen": True, "metric_id": given["metric_id"]}


def _op_record_retention_sample(given: Mapping[str, Any]) -> dict[str, Any]:
    return retention.LEDGER.record_sample(
        metric_id=given["metric_id"],
        value=float(given["value"]),
        policy_mode=given.get("policy_mode", "normal"),
    )


def _op_seed_retention_default_baselines(given: Mapping[str, Any]) -> dict[str, Any]:
    retention.seed_default_baselines()
    return {"seeded": True}


# ---------------------------------------------------------------------------
# Policy / Migration / Replay
# ---------------------------------------------------------------------------

def _op_policy_decide(given: Mapping[str, Any]) -> dict[str, Any]:
    return policy_shield.SHIELD.decide(
        event=given["event"], context=given.get("context", {})
    )


def _op_reset_policy_shield(given: Mapping[str, Any]) -> dict[str, Any]:
    policy_shield.reset_shield()
    return {"reset": True}


def _op_migration_resolve_plan(given: Mapping[str, Any]) -> dict[str, Any]:
    try:
        plan = MIGRATION_REGISTRY.resolve(
            component=given["component"],
            from_version=given["from_version"],
            to_version=given["to_version"],
        )
    except KeyError as exc:
        return {"resolved": False, "failure_code": "missing_migration_plan", "error": str(exc)}
    return {
        "resolved": True,
        "plan_id": plan.plan_id,
        "component": plan.component,
        "from_version": plan.from_version,
        "to_version": plan.to_version,
        "strategy": plan.strategy,
        "requires_replay_pin_update": plan.requires_replay_pin_update,
    }


def _op_register_migration_plan(given: Mapping[str, Any]) -> dict[str, Any]:
    from .registries.migration import MigrationPlan

    plan = MigrationPlan(
        plan_id=given["plan_id"],
        from_version=given["from_version"],
        to_version=given["to_version"],
        component=given["component"],
        strategy=given.get("strategy", "bijective"),
        requires_replay_pin_update=bool(given.get("requires_replay_pin_update", True)),
        notes=given.get("notes", ""),
    )
    MIGRATION_REGISTRY.register(plan)
    return {"registered": True, "plan_id": plan.plan_id}


def _op_replay_compute_normal_form_hash(given: Mapping[str, Any]) -> dict[str, Any]:
    return {"normal_form_hash": replay.normal_form_hash(given["object"])}


def _op_replay_compute_input_hash(given: Mapping[str, Any]) -> dict[str, Any]:
    return {"input_hash": replay.input_hash(given["object"])}


def _op_replay_compare(given: Mapping[str, Any]) -> dict[str, Any]:
    expected = given["expected"]
    identity = replay.ReplayIdentity(**expected)
    return replay.compare_replay(
        identity,
        given["observed"],
        expected_mismatch=bool(given.get("expected_mismatch", False)),
    )


# ---------------------------------------------------------------------------
# Family-conversion + retention report (composite)
# ---------------------------------------------------------------------------

def _op_family_conversion_with_retention_report(given: Mapping[str, Any]) -> dict[str, Any]:
    src = _family(given["source_family"])
    tgt = _family(given["target_family"])
    conversion = dpfc.convert_family(list(given["word"]), src, tgt)
    # convert back to verify core-magnitude preservation
    round_trip = dpfc.convert_family(conversion["target_word"], tgt, src)
    return {
        **conversion,
        "round_trip_word": round_trip["target_word"],
        "round_trip_core_magnitude": round_trip["target_core_magnitude"],
        "core_magnitude_preserved": (
            conversion["source_core_magnitude"]
            == conversion["target_core_magnitude"]
            == round_trip["target_core_magnitude"]
        ),
    }


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

OPERATIONS: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    # DPFC core
    "evaluate_family_word": _op_evaluate_family_word,
    "family_successor": _op_family_successor,
    "encode_core_to_family": _op_encode_core_to_family,
    "family_conversion": _op_family_conversion,
    "canonicalize_family_object": _op_canonicalize_family_object,
    "canonical_storage": _op_canonical_storage,
    "exported_nonnegative_add_with_correction": _op_exported_nonneg_add_with_correction,
    "exported_nonnegative_add_without_correction": _op_exported_nonneg_add_without_correction,
    "detect_export_policy_mismatch": _op_detect_export_policy_mismatch,
    "family_conversion_with_retention_report": _op_family_conversion_with_retention_report,
    # Witness / WSB2 / DBP
    "decode_witness8": _op_decode_witness8,
    "decode_wsb2": _op_decode_wsb2,
    "dbp_ingress": _op_dbp_ingress,
    "ingress_dbp_frame": _op_dbp_ingress,
    "ingress_frame": _op_ingress_frame,
    "canonicalize_witness_key_bundle": _op_canonicalize_witness_key_bundle,
    "validate_resource_availability_witness": _op_validate_resource_availability_witness,
    "validate_cluster_task_delegation": _op_validate_cluster_task_delegation,
    "invalidate_stale_resource_heartbeat": _op_invalidate_stale_resource_heartbeat,
    "evaluate_wgrnn_policy_gates": _op_evaluate_wgrnn_policy_gates,
    "evaluate_wgrnn_slot_promotion": _op_evaluate_wgrnn_slot_promotion,
    "evaluate_wgrnn_contradiction_split": _op_evaluate_wgrnn_contradiction_split,
    "evaluate_wgrnn_purge_cascade": _op_evaluate_wgrnn_purge_cascade,
    "evaluate_cluster_task_conflict": _op_evaluate_cluster_task_conflict,
    "validate_cluster_authority_frame": _op_validate_cluster_authority_frame,
    "evaluate_node_hello": _op_evaluate_node_hello,
    "evaluate_cluster_replay_direction_binding": _op_evaluate_cluster_replay_direction_binding,
    "evaluate_cluster_learning_mode_gate": _op_evaluate_cluster_learning_mode_gate,
    "select_cluster_node_for_task": _op_select_cluster_node_for_task,
    "evaluate_cluster_node_schedulability": _op_evaluate_cluster_node_schedulability,
    "evaluate_task_outcome_transport_authority": _op_evaluate_task_outcome_transport_authority,
    "evaluate_node_disconnect_reassignment": _op_evaluate_node_disconnect_reassignment,
    # Normalizer
    "normalize_family_word": _op_normalize_family_word,
    "normalize_reflection_path": _op_normalize_reflection_path,
    "normalize_witness8_row": _op_normalize_witness8_row,
    # Spectral / EDO
    "infer_missing_fundamental": _op_infer_missing_fundamental,
    "transpose_and_measure_interval_retention": _op_transpose_retention,
    "collapse_to_12edo": _op_collapse_to_12edo,
    "validate_fourier_provenance": _op_validate_fourier_provenance,
    "temperament_error_witness": _op_temperament_error_witness,
    "approximate_ratio_in_edo": _op_approximate_ratio_in_edo,
    # Registries
    "resolve_schema": _op_resolve_schema,
    "resolve_family": _op_resolve_family,
    "resolve_geometry": _op_resolve_geometry,
    "resolve_transport": _op_resolve_transport,
    "resolve_normalizer": _op_resolve_normalizer,
    "resolve_retention": _op_resolve_retention,
    "resolve_policy": _op_resolve_policy,
    # Retention
    "freeze_retention_baseline": _op_freeze_retention_baseline,
    "record_retention_sample": _op_record_retention_sample,
    "seed_retention_default_baselines": _op_seed_retention_default_baselines,
    # Policy
    "policy_decide": _op_policy_decide,
    "reset_policy_shield": _op_reset_policy_shield,
    # Migration
    "migration_resolve_plan": _op_migration_resolve_plan,
    "register_migration_plan": _op_register_migration_plan,
    # Replay
    "replay_compute_normal_form_hash": _op_replay_compute_normal_form_hash,
    "replay_compute_input_hash": _op_replay_compute_input_hash,
    "replay_compare": _op_replay_compare,
}


def register_operation(name: str, fn: Callable[[Mapping[str, Any]], dict[str, Any]]) -> None:
    OPERATIONS[name] = fn


def run_operation(op_name: str, given: Mapping[str, Any]) -> dict[str, Any]:
    if op_name not in OPERATIONS:
        raise KeyError(f"unknown operation: {op_name}")
    return OPERATIONS[op_name](given)
