from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from duotronic_runtime.api import (
    MEMORY_PACKET_SCHEMA,
    _memory_packet_projection,
    _validate_external_memory_packet,
    require_memory_packet_key,
)


def witness(*names: tuple[str, str, int]) -> dict:
    tokens = [
        {
            "category": category,
            "object_name": object_name,
            "confidence_q": confidence_q,
            "provenance": {"modality": "text" if "lyrical" in category else "visual"},
        }
        for category, object_name, confidence_q in names
    ]
    sockets = [2, 2, 2, 2, 2, 2]
    return {
        "schema_version": "media_meta_witness/v1",
        "source": {},
        "sockets": sockets,
        "payload_v": sum(sockets),
        "codeword_p": sum(sockets) + 1,
        "tokens": tokens,
    }


def packet() -> dict:
    return {
        "schema_version": MEMORY_PACKET_SCHEMA,
        "status": "unsealed",
        "graph_schema": "media_meta_witness_graph/v1",
        "formal_contract": "Duotronic Witness Contract v1.6 Draft 5.3.18",
        "logical_id": "memory:demo:callback:both:all",
        "anchor_node_id": "demo:callback",
        "anchor_witness": witness(
            ("visual_symbol", "mirror", 800),
            ("lyrical_motif", "return", 1000),
        ),
        "recalled_nodes": [
            {
                "node_id": "demo:first",
                "label": "First Signal",
                "chronology_index": 0,
                "witness": witness(("visual_symbol", "mirror", 1000)),
            },
            {
                "node_id": "demo:later",
                "label": "Reframing",
                "chronology_index": 2,
                "witness": witness(("lyrical_motif", "return", 900)),
            },
        ],
        "relations": [
            {
                "id": "edge:1",
                "source": "demo:first",
                "target": "demo:callback",
                "type": "callback",
                "strength_q": 820,
                "token_overlap_q": 444,
                "explicit": True,
            },
            {
                "id": "edge:2",
                "source": "demo:callback",
                "target": "demo:later",
                "type": "token_overlap",
                "strength_q": 500,
                "token_overlap_q": 500,
                "explicit": False,
            },
        ],
        "recall": {"query": {"direction": "both", "include_inferred": True}},
        "contract_boundary": {"graph_topology": "exploratory"},
        "integrity": {"status": "unsealed", "algorithm": None},
        "portability": {"offline_readable": True, "required_network_access": False},
    }


def test_memory_packet_validates_and_projects_retrievable_evidence() -> None:
    value = packet()
    assert _validate_external_memory_packet(value) is value
    projection = _memory_packet_projection(value)
    assert projection["information_kind"] == "media_meta_witness_memory_packet"
    assert projection["information_ref"] == value["logical_id"]
    assert projection["metadata"]["promotion_eligible"] is False
    assert "return" in projection["text_fields"]["evidence_terms"]
    assert "callback" in projection["text_fields"]["evidence_terms"]
    assert any(row["measurement_kind"] == "media_meta_token" for row in projection["meta_objects"])
    assert any(row["measurement_kind"] == "recurrence_relation" for row in projection["meta_objects"])


@pytest.mark.parametrize("field,value", [
    ("authority", "trusted"),
    ("trust_status", "trusted"),
    ("signature_verified", True),
    ("signed_envelope", {"fake": True}),
])
def test_external_packet_cannot_supply_authority(field: str, value: object) -> None:
    value_packet = packet()
    value_packet[field] = value
    with pytest.raises(HTTPException) as exc:
        _validate_external_memory_packet(value_packet)
    assert exc.value.status_code == 422
    assert "forbidden_authority_field" in str(exc.value.detail)


def test_external_packet_cannot_claim_sealed_algorithm() -> None:
    value = packet()
    value["integrity"] = {"status": "unsealed", "algorithm": "KMAC256"}
    with pytest.raises(HTTPException) as exc:
        _validate_external_memory_packet(value)
    assert exc.value.detail == "external_memory_packet_cannot_claim_sealing_algorithm"


def test_broken_vp_arithmetic_is_rejected() -> None:
    value = packet()
    value["anchor_witness"]["codeword_p"] += 2
    with pytest.raises(HTTPException) as exc:
        _validate_external_memory_packet(value)
    assert exc.value.detail == "anchor_witness_vp_invariant_failed"


def test_relation_cannot_escape_packet_node_set() -> None:
    value = packet()
    value["relations"][0]["source"] = "outside:node"
    with pytest.raises(HTTPException) as exc:
        _validate_external_memory_packet(value)
    assert exc.value.detail == "memory_packet_relation_endpoint_invalid"


def test_memory_packet_dedicated_bearer_is_accepted() -> None:
    settings = SimpleNamespace(runtime_api_key="full-secret", memory_packet_ingest_api_key="memory-secret")
    require_memory_packet_key(settings, "Bearer memory-secret")


def test_memory_packet_full_runtime_bearer_remains_accepted() -> None:
    settings = SimpleNamespace(runtime_api_key="full-secret", memory_packet_ingest_api_key="memory-secret")
    require_memory_packet_key(settings, "Bearer full-secret")


def test_memory_packet_invalid_bearer_is_rejected() -> None:
    settings = SimpleNamespace(runtime_api_key="full-secret", memory_packet_ingest_api_key="memory-secret")
    with pytest.raises(HTTPException) as exc:
        require_memory_packet_key(settings, "Bearer wrong-secret")
    assert exc.value.status_code == 401


def test_memory_packet_auth_is_open_only_when_both_keys_are_unconfigured() -> None:
    settings = SimpleNamespace(runtime_api_key="", memory_packet_ingest_api_key="")
    require_memory_packet_key(settings, None)
