from __future__ import annotations

import base64
import json
import math
import struct
import zlib
from typing import Any, Iterable

GEOMETRY_INFORMATION_STREAM_VERSION = "duotronic_geometry_information_stream/v1"
GEOMETRY_DEPTH_FRAME_VERSION = "duotronic_geometry_depth_frame/v1"
GEOMETRY_CARRIER_VERSION = "duotronic_geometry_carrier/v1"
FRACTAL_BRANCH = "fractal_branch"
POLYGON_RINGS = "polygon_rings"
GEOMETRY_CARRIER_FAMILIES = (FRACTAL_BRANCH, POLYGON_RINGS)

STREAM_MAGIC = b"DGIS"
DEPTH_MAGIC = b"DGD1"
CARRIER_MAGIC = b"DGC1"
STREAM_HEADER_BYTES = 32
DEPTH_HEADER_BYTES = 32
CARRIER_HEADER_BYTES = 14
STREAM_VERSION = 1
DEPTH_VERSION = 1
CARRIER_FRAME_VERSION = 1
RESERVED_PRIMITIVES = 12
FAMILY_IDS = {FRACTAL_BRANCH: 1, POLYGON_RINGS: 2}
FAMILY_NAMES = {1: FRACTAL_BRANCH, 2: POLYGON_RINGS}
TAU = math.pi * 2.0


def crc32(data: bytes | bytearray | memoryview) -> int:
    return zlib.crc32(bytes(data)) & 0xFFFFFFFF


def _stable(value: Any) -> Any:
    if isinstance(value, list):
        return [_stable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _stable(value[k]) for k in sorted(value)}
    return value


def canonical_information_bytes(information: dict[str, Any] | None) -> bytes:
    return json.dumps(_stable(information or {}), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_information_stream(*, source_bytes: bytes = b"", information: dict[str, Any] | None = None) -> bytes:
    source = bytes(source_bytes)
    info = canonical_information_bytes(information)
    body = info + source
    header = bytearray(STREAM_HEADER_BYTES)
    header[0:4] = STREAM_MAGIC
    header[4] = STREAM_VERSION
    header[5] = 0
    struct.pack_into("<H", header, 6, STREAM_HEADER_BYTES)
    struct.pack_into("<I", header, 8, len(info))
    struct.pack_into("<Q", header, 12, len(source))
    struct.pack_into("<I", header, 20, crc32(info))
    struct.pack_into("<I", header, 24, crc32(source))
    struct.pack_into("<I", header, 28, crc32(body))
    return bytes(header) + body


def decode_information_stream(stream_bytes: bytes) -> dict[str, Any]:
    data = bytes(stream_bytes)
    if len(data) < STREAM_HEADER_BYTES:
        raise ValueError("geometry_information_stream_too_short")
    if data[:4] != STREAM_MAGIC:
        raise ValueError("geometry_information_stream_sync_not_found")
    if data[4] != STREAM_VERSION:
        raise ValueError(f"unsupported_geometry_information_stream_version:{data[4]}")
    header_bytes = struct.unpack_from("<H", data, 6)[0]
    information_length = struct.unpack_from("<I", data, 8)[0]
    source_length = struct.unpack_from("<Q", data, 12)[0]
    total = header_bytes + information_length + source_length
    if total != len(data):
        raise ValueError(f"geometry_information_stream_length_mismatch:{len(data)}/{total}")
    information_bytes = data[header_bytes:header_bytes + information_length]
    source = data[header_bytes + information_length:]
    body = data[header_bytes:]
    information_crc_ok = crc32(information_bytes) == struct.unpack_from("<I", data, 20)[0]
    source_crc_ok = crc32(source) == struct.unpack_from("<I", data, 24)[0]
    stream_crc_ok = crc32(body) == struct.unpack_from("<I", data, 28)[0]
    if not (information_crc_ok and source_crc_ok and stream_crc_ok):
        raise ValueError("geometry_information_stream_crc_failed")
    return {
        "schema_version": GEOMETRY_INFORMATION_STREAM_VERSION,
        "information": json.loads(information_bytes.decode("utf-8")),
        "source_bytes": source,
        "information_bytes": information_bytes,
        "information_crc_ok": information_crc_ok,
        "source_crc_ok": source_crc_ok,
        "stream_crc_ok": stream_crc_ok,
        "total_bytes": len(data),
    }


def get_depth_plan(stream_bytes: bytes, payload_capacity: int) -> dict[str, Any]:
    data = bytes(stream_bytes)
    capacity = max(DEPTH_HEADER_BYTES + 1, int(payload_capacity or DEPTH_HEADER_BYTES + 1))
    data_bytes = capacity - DEPTH_HEADER_BYTES
    total_depth = max(1, math.ceil(len(data) / data_bytes))
    return {
        "total_bytes": len(data),
        "payload_capacity": capacity,
        "header_bytes": DEPTH_HEADER_BYTES,
        "data_bytes_per_depth": data_bytes,
        "total_depth": total_depth,
        "stream_crc": crc32(data),
        "logical_depth_unbounded": True,
        "continuation": "same_geometry_information_stream",
    }


def build_depth_frame(stream_bytes: bytes, payload_capacity: int, depth_index: int = 0) -> dict[str, Any]:
    data = bytes(stream_bytes)
    plan = get_depth_plan(data, payload_capacity)
    index = int(depth_index or 0) % plan["total_depth"]
    offset = index * plan["data_bytes_per_depth"]
    chunk = data[offset:offset + plan["data_bytes_per_depth"]]
    out = bytearray(plan["payload_capacity"])
    out[:4] = DEPTH_MAGIC
    out[4] = DEPTH_VERSION
    out[5] = 0
    struct.pack_into("<H", out, 6, DEPTH_HEADER_BYTES)
    struct.pack_into("<I", out, 8, index)
    struct.pack_into("<I", out, 12, plan["total_depth"])
    struct.pack_into("<Q", out, 16, len(data))
    struct.pack_into("<I", out, 24, len(chunk))
    struct.pack_into("<I", out, 28, plan["stream_crc"])
    out[DEPTH_HEADER_BYTES:DEPTH_HEADER_BYTES + len(chunk)] = chunk
    return {
        "schema_version": GEOMETRY_DEPTH_FRAME_VERSION,
        "depth_index": index,
        "total_depth": plan["total_depth"],
        "stream_bytes": len(data),
        "stream_crc": plan["stream_crc"],
        "payload_bytes": bytes(out),
        "chunk_bytes": len(chunk),
        "plan": plan,
    }


def decode_depth_frame(frame_payload: bytes) -> dict[str, Any]:
    data = bytes(frame_payload)
    if len(data) < DEPTH_HEADER_BYTES:
        raise ValueError("geometry_depth_frame_too_short")
    if data[:4] != DEPTH_MAGIC:
        raise ValueError("geometry_depth_sync_not_found")
    if data[4] != DEPTH_VERSION:
        raise ValueError(f"unsupported_geometry_depth_version:{data[4]}")
    header_bytes = struct.unpack_from("<H", data, 6)[0]
    depth_index = struct.unpack_from("<I", data, 8)[0]
    total_depth = struct.unpack_from("<I", data, 12)[0]
    stream_bytes = struct.unpack_from("<Q", data, 16)[0]
    chunk_length = struct.unpack_from("<I", data, 24)[0]
    stream_crc = struct.unpack_from("<I", data, 28)[0]
    if header_bytes + chunk_length > len(data):
        raise ValueError("geometry_depth_chunk_truncated")
    return {
        "schema_version": GEOMETRY_DEPTH_FRAME_VERSION,
        "depth_index": depth_index,
        "total_depth": total_depth,
        "stream_bytes": stream_bytes,
        "stream_crc": stream_crc,
        "chunk_bytes": data[header_bytes:header_bytes + chunk_length],
    }


def reassemble_depth_frames(frames: Iterable[bytes | dict[str, Any]]) -> dict[str, Any]:
    decoded = [f if isinstance(f, dict) and isinstance(f.get("chunk_bytes"), (bytes, bytearray)) else decode_depth_frame(bytes(f)) for f in frames]
    if not decoded:
        return {"complete": False, "received_depth": 0, "total_depth": 0, "bytes": None}
    first = decoded[0]
    by_index: dict[int, dict[str, Any]] = {}
    for frame in decoded:
        if frame["total_depth"] != first["total_depth"] or frame["stream_bytes"] != first["stream_bytes"] or frame["stream_crc"] != first["stream_crc"]:
            raise ValueError("geometry_depth_frames_mixed_streams")
        by_index.setdefault(int(frame["depth_index"]), frame)
    if len(by_index) < first["total_depth"]:
        return {"complete": False, "received_depth": len(by_index), "total_depth": first["total_depth"], "bytes": None}
    out = bytearray(first["stream_bytes"])
    offset = 0
    for index in range(first["total_depth"]):
        frame = by_index.get(index)
        if frame is None:
            raise ValueError(f"missing_geometry_depth:{index}")
        part = bytes(frame["chunk_bytes"])[:len(out) - offset]
        out[offset:offset + len(part)] = part
        offset += len(part)
    if offset != len(out):
        raise ValueError(f"geometry_information_reassembly_length_mismatch:{offset}/{len(out)}")
    if crc32(out) != first["stream_crc"]:
        raise ValueError("reassembled_geometry_information_stream_crc_failed")
    return {"complete": True, "received_depth": len(by_index), "total_depth": first["total_depth"], "bytes": bytes(out), "stream_crc": first["stream_crc"]}


def _hamming74_encode4(nibble: int) -> int:
    d1, d2, d3, d4 = (nibble >> 3) & 1, (nibble >> 2) & 1, (nibble >> 1) & 1, nibble & 1
    p1, p2, p4 = d1 ^ d2 ^ d4, d1 ^ d3 ^ d4, d2 ^ d3 ^ d4
    return (p1 << 6) | (p2 << 5) | (d1 << 4) | (p4 << 3) | (d2 << 2) | (d3 << 1) | d4


def _hamming74_decode7(codeword: int) -> tuple[int, bool]:
    b = [0, (codeword >> 6) & 1, (codeword >> 5) & 1, (codeword >> 4) & 1, (codeword >> 3) & 1, (codeword >> 2) & 1, (codeword >> 1) & 1, codeword & 1]
    syndrome = (b[1] ^ b[3] ^ b[5] ^ b[7]) | ((b[2] ^ b[3] ^ b[6] ^ b[7]) << 1) | ((b[4] ^ b[5] ^ b[6] ^ b[7]) << 2)
    corrected = 1 <= syndrome <= 7
    if corrected:
        b[syndrome] ^= 1
    return (b[3] << 3) | (b[5] << 2) | (b[6] << 1) | b[7], corrected


def _bytes_to_protected_bits(data: bytes) -> list[int]:
    bits: list[int] = []
    for byte in data:
        for nibble in ((byte >> 4) & 0xF, byte & 0xF):
            cw = _hamming74_encode4(nibble)
            bits.extend((cw >> i) & 1 for i in range(6, -1, -1))
    return bits


def _protected_bits_to_bytes(bits: list[int]) -> tuple[bytes, int]:
    nibbles: list[int] = []
    corrected = 0
    for start in range(0, (len(bits) // 7) * 7, 7):
        cw = 0
        for bit in bits[start:start + 7]:
            cw = (cw << 1) | (1 if bit else 0)
        nibble, was_corrected = _hamming74_decode7(cw)
        nibbles.append(nibble)
        corrected += int(was_corrected)
    return bytes((nibbles[i] << 4) | nibbles[i + 1] for i in range(0, (len(nibbles) // 2) * 2, 2)), corrected


def get_carrier_capacity(primitive_budget: int = 3000) -> dict[str, Any]:
    budget = max(RESERVED_PRIMITIVES + 28, int(primitive_budget or 3000))
    protected_bits = max(0, budget - RESERVED_PRIMITIVES)
    frame_bytes = protected_bits // 14
    return {
        "payload_bytes": max(0, frame_bytes - CARRIER_HEADER_BYTES),
        "primitive_budget": budget,
        "reserved_primitives": RESERVED_PRIMITIVES,
        "protected_bits": protected_bits,
        "header_bytes": CARRIER_HEADER_BYTES,
        "ecc": "hamming(7,4)",
        "crc": "crc32/iso-hdlc",
    }


def _build_carrier_frame(payload: bytes, frame_index: int, family: str) -> bytes:
    family = family if family in GEOMETRY_CARRIER_FAMILIES else FRACTAL_BRANCH
    payload = bytes(payload)[:0xFFFF]
    out = bytearray(CARRIER_HEADER_BYTES + len(payload))
    out[:4] = CARRIER_MAGIC
    out[4] = CARRIER_FRAME_VERSION
    out[5] = FAMILY_IDS[family]
    struct.pack_into("<H", out, 6, max(0, int(frame_index)) & 0xFFFF)
    struct.pack_into("<H", out, 8, len(payload))
    struct.pack_into("<I", out, 10, crc32(payload))
    out[CARRIER_HEADER_BYTES:] = payload
    return bytes(out)


def _parse_carrier_frame(data: bytes) -> dict[str, Any]:
    if len(data) < CARRIER_HEADER_BYTES:
        return {"ok": False, "reason": "frame_too_short"}
    if data[:4] != CARRIER_MAGIC:
        return {"ok": False, "reason": "sync_mismatch"}
    if data[4] != CARRIER_FRAME_VERSION:
        return {"ok": False, "reason": "version_mismatch"}
    family = FAMILY_NAMES.get(data[5], "unknown")
    frame_index = struct.unpack_from("<H", data, 6)[0]
    payload_length = struct.unpack_from("<H", data, 8)[0]
    if CARRIER_HEADER_BYTES + payload_length > len(data):
        return {"ok": False, "reason": "payload_truncated"}
    payload = data[CARRIER_HEADER_BYTES:CARRIER_HEADER_BYTES + payload_length]
    expected_crc = struct.unpack_from("<I", data, 10)[0]
    return {"ok": True, "family": family, "frame_index": frame_index, "payload": payload, "expected_crc": expected_crc, "crc_ok": crc32(payload) == expected_crc}


def _fractal_primitive(bit: int, index: int, width: float, height: float) -> dict[str, Any]:
    depth = int(math.floor(math.log2(index + 2)))
    branch_ordinal = index - ((1 << depth) - 2)
    slots = max(1, 1 << depth)
    canonical_angle = -math.pi / 2 + (branch_ordinal / slots) * TAU
    chirality = -1 if ((index + depth) & 1) else 1
    turn = 0.47 if bit else 0.23
    length = 0.89 if bit else 0.72
    radial = 1.085 if bit else 0.945
    base_radius = min(width, height) * (0.105 + min(depth, 9) * 0.041)
    start_radius = max(4.0, base_radius * 0.58)
    end_radius = start_radius + max(3.2, base_radius * 0.22 * length * radial)
    return {"index": index, "depth": depth, "branchOrdinal": branch_ordinal, "chirality": chirality, "centerX": width * 0.5, "centerY": height * 0.5, "startRadius": start_radius, "endRadius": end_radius, "startAngle": canonical_angle - chirality * turn * 0.38, "endAngle": canonical_angle + chirality * turn, "turnMagnitude": turn, "lengthScale": length, "radialScale": radial}


def _ring_primitive(bit: int, index: int, width: float, height: float) -> dict[str, Any]:
    min_dim = min(width, height)
    ring_count = max(4, int(math.floor(math.sqrt(index + 1))) + 4)
    ring = index % ring_count
    slot = index // ring_count
    slots = max(12, int(math.ceil((index + 1) / ring_count)))
    base_radius = min_dim * (0.10 + 0.35 * ((ring + 1) / (ring_count + 1)))
    radial_offset = (1 if bit else -1) * max(1.8, min_dim * 0.0045)
    phase_offset = (1 if bit else -1) * (TAU / max(96, slots * 12))
    angle = -math.pi / 2 + (slot / slots) * TAU + phase_offset
    return {"index": index, "ring": ring, "slot": slot, "slots": slots, "centerX": width * 0.5, "centerY": height * 0.5, "radius": base_radius + radial_offset, "baseRadius": base_radius, "radialOffset": radial_offset, "angle": angle, "phaseOffset": phase_offset, "polygonSides": 8 if bit else 5, "polygonRotation": angle + (math.pi / 16 if bit else -math.pi / 10), "polygonRadius": max(2.4, min_dim * 0.0065)}


def _sync_geometry(width: float, height: float, family: str) -> list[dict[str, Any]]:
    min_dim = min(width, height)
    return [{"index": i, "angle": -math.pi / 2 + (i / RESERVED_PRIMITIVES) * TAU, "radius": min_dim * (0.47 if family == POLYGON_RINGS else 0.055), "notch": i % 3} for i in range(RESERVED_PRIMITIVES)]


def build_carrier(payload_bytes: bytes, frame_index: int = 0, *, family: str = FRACTAL_BRANCH, width: float = 1280, height: float = 720, primitive_budget: int = 3000) -> dict[str, Any]:
    family = family if family in GEOMETRY_CARRIER_FAMILIES else FRACTAL_BRANCH
    width, height = max(64.0, float(width)), max(64.0, float(height))
    capacity = get_carrier_capacity(primitive_budget)
    payload = bytes(payload_bytes)[:capacity["payload_bytes"]]
    frame = _build_carrier_frame(payload, frame_index, family)
    bits = _bytes_to_protected_bits(frame)
    builder = _ring_primitive if family == POLYGON_RINGS else _fractal_primitive
    primitives = [builder(bit, i, width, height) for i, bit in enumerate(bits)]
    return {"schema_version": GEOMETRY_CARRIER_VERSION, "family": family, "frame_index": max(0, int(frame_index)), "width": width, "height": height, "capacity": capacity, "frame_bytes": frame, "payload_bytes": payload, "protected_bits": bits, "sync": _sync_geometry(width, height, family), "primitives": primitives, "authoritative_channels": ["polygon_sides", "radial_offset", "angular_phase"] if family == POLYGON_RINGS else ["branch_turn", "segment_ratio", "radial_scale"], "color_required_for_decode": False}


def decode_carrier(observed: dict[str, Any]) -> dict[str, Any]:
    primitives = observed.get("primitives") if isinstance(observed, dict) else None
    if not isinstance(primitives, list):
        return {"ok": False, "reason": "missing_geometry"}
    family = observed.get("family") or FRACTAL_BRANCH
    bits: list[int] = []
    agreement = 0.0
    for primitive in primitives:
        if family == POLYGON_RINGS:
            votes = [1 if float(primitive.get("polygonSides", 0)) >= 7 else 0, 1 if float(primitive.get("radialOffset", 0)) > 0 else 0, 1 if float(primitive.get("phaseOffset", 0)) > 0 else 0]
        else:
            votes = [1 if float(primitive.get("turnMagnitude", 0)) > 0.35 else 0, 1 if float(primitive.get("lengthScale", 0)) > 0.805 else 0, 1 if float(primitive.get("radialScale", 0)) > 1.015 else 0]
        ones = sum(votes)
        bits.append(1 if ones >= 2 else 0)
        agreement += max(ones, 3 - ones) / 3.0
    decoded_bytes, corrected = _protected_bits_to_bytes(bits)
    parsed = _parse_carrier_frame(decoded_bytes)
    geometry_agreement = agreement / len(primitives) if primitives else 0.0
    if not parsed.get("ok"):
        return {"ok": False, "reason": parsed.get("reason"), "geometry_agreement": geometry_agreement, "corrected_codewords": corrected, "confidence": max(0.0, min(1.0, geometry_agreement * 0.65))}
    family_match = parsed["family"] == family
    confidence = max(0.0, min(1.0, geometry_agreement * 0.55 + (0.30 if parsed["crc_ok"] else 0) + (0.10 if family_match else 0) + (0.05 if corrected == 0 else 0.025)))
    return {"ok": bool(parsed["crc_ok"] and family_match), "reason": "family_mismatch" if not family_match else (None if parsed["crc_ok"] else "crc_mismatch"), "family": family, "frame_index": parsed["frame_index"], "payload_bytes": parsed["payload"], "crc_ok": parsed["crc_ok"], "geometry_agreement": geometry_agreement, "corrected_codewords": corrected, "confidence": confidence, "color_required_for_decode": False}


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def from_b64(value: str, *, field: str = "data") -> bytes:
    try:
        return base64.b64decode(str(value or ""), validate=True)
    except Exception as exc:
        raise ValueError(f"invalid_base64:{field}") from exc


def carrier_to_json(carrier: dict[str, Any]) -> dict[str, Any]:
    out = dict(carrier)
    out["frame_b64"] = b64(out.pop("frame_bytes"))
    out["payload_b64"] = b64(out.pop("payload_bytes"))
    return out


def decode_result_to_json(result: dict[str, Any]) -> dict[str, Any]:
    out = dict(result)
    if isinstance(out.get("payload_bytes"), (bytes, bytearray)):
        out["payload_b64"] = b64(out.pop("payload_bytes"))
    return out
