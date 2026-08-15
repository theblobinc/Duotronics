from duotronic_runtime.evidence import nla_activation_witness_contract_v1
from duotronic_runtime.prompting import build_runtime_prompt


def test_runtime_prompt_anchors_duotronic_non_collapse():
    prompt = build_runtime_prompt("Explain Duotronic non-collapse.")
    assert "Xavi Runtime" in prompt
    assert "Model output is evidence, not truth" in prompt
    assert "not Xavi Hernández" in prompt
    assert "Duotronic non-collapse" in prompt


def test_nla_contract_projection_has_required_v1_fields():
    projected = nla_activation_witness_contract_v1(
        nla_witness={
            "witness_id": "nla_test",
            "loop_id": "loop-main",
            "created_at_ms": 1778541085829,
            "activation": {
                "activation_digest": "shake256-512:" + "a" * 64,
                "activation_vector_ref": "inline:test",
                "norm": 0.5,
            },
            "verbalizer": {
                "av_model": "deterministic-av-shim-v1",
                "prompt_integrity": "shake256-512:" + "b" * 64,
                "response_integrity": "shake256-512:" + "c" * 64,
                "explanation_text": "diagnostic explanation",
                "parser_status": "parsed",
            },
            "reconstructor": {"mse": 0.1, "cosine": 0.8},
            "fidelity": {
                "fidelity_status": "low",
                "cosine_similarity": 0.8,
                "repeat_stability": 0.9,
                "parser_status": "passed",
            },
            "lifecycle": {"state": "quarantined"},
            "policy": {
                "mode": "audit_only",
                "may_influence_response": False,
                "may_write_memory": False,
                "may_promote_witness": False,
                "human_review_required": True,
            },
        },
        source_model={"provider": "ollama", "model": "llama3.2:1b"},
        loop_id="loop-main",
        node_id="dev-xavi-app",
        policy_mode="audit_only",
    )

    assert projected["schema_version"] == "nla-activation-witness/v1"
    assert projected["source_model"]["backend"] == "ollama"
    assert projected["activation"]["retention_class"] == "audit_artifact"
    assert projected["fidelity"]["parser_valid"] is True
    assert projected["policy"]["may_trigger_mutation"] is False
    assert projected["lifecycle"]["current_state"] == "quarantined"
