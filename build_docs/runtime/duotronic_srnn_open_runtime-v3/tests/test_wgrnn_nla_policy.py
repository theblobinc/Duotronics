from duotronic_runtime.nla import NLAWitnessFactory
from duotronic_runtime.policy import PolicyEngine
from duotronic_runtime.wgrnn import WGRNNRuntime


def test_wgrnn_generates_memory_update():
    runtime = WGRNNRuntime(loop_id="test", node_id="node", state_dim=8, slot_dim=8, num_slots=8)
    result = runtime.step(prompt="hello", response_text="world", requested_action="observe")
    update = result["memory_update"]
    assert update["update_id"].startswith("wgrnn_update_")
    assert 0 <= update["authority_t"] <= 1
    assert update["update_kind"] in {"candidate_write", "quarantine_write"}


def test_nla_witness_is_audit_object():
    runtime = WGRNNRuntime(loop_id="test", node_id="node", state_dim=8, slot_dim=8, num_slots=8)
    result = runtime.step(prompt="hello", response_text="world", requested_action="observe")
    factory = NLAWitnessFactory(loop_id="test", node_id="node", min_cosine=0.0, max_mse=2.0, min_repeat_stability=0.0)
    witness = factory.create(
        activation=result["activation_vector"],
        prompt="hello",
        response_text="world",
        source_model={"provider": "echo"},
        policy_flags={"mode": "audit_only", "may_write_memory": False},
        wg_rnn_update_id=result["memory_update"]["update_id"],
    ).to_dict()
    assert witness["witness_id"].startswith("nla_")
    assert witness["policy"]["may_write_memory"] is False
    assert "fidelity_status" in witness["fidelity"]


def test_policy_blocks_nla_memory_write_by_default():
    runtime = WGRNNRuntime(loop_id="test", node_id="node", state_dim=8, slot_dim=8, num_slots=8)
    result = runtime.step(prompt="hello", response_text="world", requested_action="memory_write")
    factory = NLAWitnessFactory(loop_id="test", node_id="node", min_cosine=0.0, max_mse=2.0, min_repeat_stability=0.0)
    witness = factory.create(
        activation=result["activation_vector"],
        prompt="hello",
        response_text="world",
        source_model={"provider": "echo"},
        policy_flags={"mode": "audit_only", "may_write_memory": False},
        wg_rnn_update_id=result["memory_update"]["update_id"],
    ).to_dict()
    policy = PolicyEngine(nla_policy_mode="audit_only", allow_influence=False, allow_memory_write=False, allow_promote=False)
    decision = policy.decide(requested_action="memory_write", wg_rnn_update=result["memory_update"], nla_witness=witness)
    assert decision["allowed"] is False
    assert decision["decision"] == "deny"
