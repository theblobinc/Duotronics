from __future__ import annotations

import base64

from duotronic_runtime.geometry_codec import (
    FRACTAL_BRANCH, POLYGON_RINGS, build_information_stream, decode_information_stream,
    get_carrier_capacity, build_depth_frame, decode_depth_frame, reassemble_depth_frames,
    build_carrier, decode_carrier, crc32,
)


def test_information_stream_roundtrip_exact_source_and_meta_graph():
    source = bytes(range(256)) * 3
    info = {"schema_version":"media_witness_pattern_packet/v2","meta_objects":[{"label":"disco ball","confidence":0.91},{"label":"red background"}],"relationships":[{"from":"disco ball","to":"red background","kind":"foreground_of"}],"authority":"candidate_observation_only"}
    stream = build_information_stream(source_bytes=source, information=info)
    decoded = decode_information_stream(stream)
    assert decoded["source_bytes"] == source
    assert decoded["information"] == info
    assert decoded["information_crc_ok"] and decoded["source_crc_ok"] and decoded["stream_crc_ok"]


def test_depth_frames_reassemble_same_stream_arbitrary_depth():
    stream = build_information_stream(source_bytes=b"source" * 900, information={"x":"y" * 2000})
    cap = 173
    frames = [build_depth_frame(stream, cap, i)["payload_bytes"] for i in range(build_depth_frame(stream, cap, 0)["total_depth"])]
    decoded = [decode_depth_frame(f) for f in frames]
    result = reassemble_depth_frames(list(reversed(decoded)))
    assert result["complete"] is True
    assert result["bytes"] == stream
    assert result["stream_crc"] == crc32(stream)


def _perturb(carrier, family):
    out = dict(carrier)
    rows=[]
    for i,p in enumerate(carrier["primitives"]):
        q=dict(p); sign=-1 if i & 1 else 1
        if family == POLYGON_RINGS:
            q["radialOffset"] += sign * 0.35
            q["phaseOffset"] += sign * 0.0004
        else:
            q["turnMagnitude"] += sign * 0.025
            q["lengthScale"] += sign * 0.02
        rows.append(q)
    out["primitives"] = rows
    return out


def test_both_geometry_carriers_roundtrip_without_color_even_perturbed():
    payload = b"all-information-in-geometry" * 4
    for family in (FRACTAL_BRANCH, POLYGON_RINGS):
        carrier = build_carrier(payload, 17, family=family, primitive_budget=3000, width=1280, height=720)
        assert carrier["color_required_for_decode"] is False
        decoded = decode_carrier(_perturb(carrier, family))
        assert decoded["ok"] is True
        assert decoded["payload_bytes"] == payload
        assert decoded["frame_index"] == 17
        assert decoded["crc_ok"] is True
        assert decoded["confidence"] >= 0.95


def test_hamming_corrects_one_geometry_vote_bit_per_codeword():
    payload=b"ECC geometry"
    carrier=build_carrier(payload, 2, family=FRACTAL_BRANCH, primitive_budget=1000)
    # Flip all three geometric votes for one primitive: one protected bit error.
    p=carrier["primitives"][3]
    p["turnMagnitude"] = 0.47 if p["turnMagnitude"] < 0.35 else 0.23
    p["lengthScale"] = 0.89 if p["lengthScale"] < 0.805 else 0.72
    p["radialScale"] = 1.085 if p["radialScale"] < 1.015 else 0.945
    decoded=decode_carrier(carrier)
    assert decoded["ok"] is True
    assert decoded["payload_bytes"] == payload
    assert decoded["corrected_codewords"] >= 1


def test_capacity_has_only_one_payload_stream():
    cap=get_carrier_capacity(3000)
    assert cap["payload_bytes"] > 0
    assert cap["ecc"] == "hamming(7,4)"
