from __future__ import annotations

import re
from typing import Any, Iterable

from .crypto_primitives import contract_canonical_bytes, framed_shake256_duoid, semantic_content_id

U64_MAX = (1 << 64) - 1
_DIMENSION_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")


def _normalize_schema(schema: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Normalize a schema-declared integer aggregate vector.

    Keys are semantic dimensions such as red_pixels, duration_ms, object_count.
    Values may be a unit string or an object with unit/description fields.
    """
    out: dict[str, dict[str, Any]] = {}
    for raw_name, raw_spec in sorted((schema or {}).items()):
        name = str(raw_name)
        if not _DIMENSION_RE.fullmatch(name):
            raise ValueError(f"invalid aggregate dimension: {name!r}")
        if isinstance(raw_spec, str):
            spec = {"unit": raw_spec}
        elif isinstance(raw_spec, dict):
            spec = {
                "unit": str(raw_spec.get("unit") or "count"),
                "description": str(raw_spec.get("description") or ""),
            }
        else:
            raise ValueError(f"invalid aggregate schema for {name}")
        out[name] = spec
    return out


def _checked_u64(value: Any, *, dimension: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"boolean aggregate contribution is invalid for {dimension}")
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"aggregate contribution for {dimension} is not an integer") from exc
    if integer < 0 or integer > U64_MAX:
        raise OverflowError(f"aggregate contribution for {dimension} is outside u64")
    return integer


def _zero_vector(schema: dict[str, dict[str, Any]]) -> dict[str, int]:
    return {name: 0 for name in schema}


def normalize_sum_vector(vector: dict[str, Any] | None, schema: dict[str, dict[str, Any]]) -> dict[str, int]:
    vector = dict(vector or {})
    unknown = sorted(set(vector) - set(schema))
    if unknown:
        raise ValueError(f"aggregate contribution contains undeclared dimensions: {unknown}")
    return {name: _checked_u64(vector.get(name, 0), dimension=name) for name in schema}


def add_sum_vectors(left: dict[str, int], right: dict[str, int], schema: dict[str, dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for name in schema:
        value = int(left.get(name, 0)) + int(right.get(name, 0))
        if value > U64_MAX:
            raise OverflowError(f"aggregate overflow for dimension {name}")
        out[name] = value
    return out


def _leaf_id(occurrence_id: str, sum_vector: dict[str, int]) -> str:
    return framed_shake256_duoid(
        "DUOTRONIC/MEDIA-PROFILE-LEAF/v1",
        str(occurrence_id).encode("utf-8"),
        contract_canonical_bytes(sum_vector),
    )


def _node_id(left_id: str, left_sum: dict[str, int], right_id: str, right_sum: dict[str, int]) -> str:
    return framed_shake256_duoid(
        "DUOTRONIC/MEDIA-PROFILE-NODE/v1",
        str(left_id).encode("utf-8"),
        contract_canonical_bytes(left_sum),
        str(right_id).encode("utf-8"),
        contract_canonical_bytes(right_sum),
    )


def build_merkle_sum_dag(
    occurrences: Iterable[dict[str, Any]],
    *,
    aggregate_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an ordered SHAKE256-512 Merkle-sum DAG over occurrence witnesses.

    Leaves commit to exact occurrence IDs plus their explicitly declared aggregate
    contributions. Parents commit to both child IDs and both child sum vectors.
    The tree order follows occurrence ordinal/locator order from the composition.
    """
    schema = _normalize_schema(aggregate_schema)
    ordered = sorted(
        [dict(row) for row in occurrences],
        key=lambda row: (int(row.get("ordinal") or 0), str(row.get("occurrence_id") or "")),
    )
    nodes: dict[str, dict[str, Any]] = {}
    level: list[dict[str, Any]] = []
    for ordinal, occurrence in enumerate(ordered):
        occurrence_id = str(occurrence.get("occurrence_id") or "")
        if not occurrence_id:
            raise ValueError("occurrence_id is required for media profile leaf")
        vector = normalize_sum_vector(occurrence.get("sum_contribution") or {}, schema)
        node_id = _leaf_id(occurrence_id, vector)
        node = {
            "schema_version": "duotronic_media_profile_leaf/v1",
            "node_id": node_id,
            "occurrence_id": occurrence_id,
            "ordinal": ordinal,
            "sum_vector": vector,
        }
        nodes[node_id] = node
        level.append(node)

    if not level:
        zero = _zero_vector(schema)
        root_id = framed_shake256_duoid(
            "DUOTRONIC/MEDIA-PROFILE-EMPTY/v1",
            contract_canonical_bytes(schema),
            contract_canonical_bytes(zero),
        )
        nodes[root_id] = {
            "schema_version": "duotronic_media_profile_empty/v1",
            "node_id": root_id,
            "sum_vector": zero,
        }
        return {
            "schema_version": "duotronic_merkle_sum_dag/v1",
            "aggregate_schema": schema,
            "root_node_id": root_id,
            "sum_vector": zero,
            "leaf_count": 0,
            "node_count": 1,
            "nodes": [nodes[root_id]],
        }

    while len(level) > 1:
        next_level: list[dict[str, Any]] = []
        for index in range(0, len(level), 2):
            left = level[index]
            if index + 1 >= len(level):
                # Carry an unpaired subtree unchanged. The root still commits to
                # it through the parent above; this avoids inventing duplicate leaves.
                next_level.append(left)
                continue
            right = level[index + 1]
            parent_sum = add_sum_vectors(left["sum_vector"], right["sum_vector"], schema)
            parent_id = _node_id(left["node_id"], left["sum_vector"], right["node_id"], right["sum_vector"])
            parent = {
                "schema_version": "duotronic_media_profile_node/v1",
                "node_id": parent_id,
                "left_node_id": left["node_id"],
                "right_node_id": right["node_id"],
                "left_sum_vector": left["sum_vector"],
                "right_sum_vector": right["sum_vector"],
                "sum_vector": parent_sum,
            }
            nodes[parent_id] = parent
            next_level.append(parent)
        level = next_level

    root = level[0]
    return {
        "schema_version": "duotronic_merkle_sum_dag/v1",
        "aggregate_schema": schema,
        "root_node_id": root["node_id"],
        "sum_vector": root["sum_vector"],
        "leaf_count": len(ordered),
        "node_count": len(nodes),
        "nodes": [nodes[node_id] for node_id in sorted(nodes)],
    }


def build_media_profile(
    graph: dict[str, Any],
    *,
    aggregate_schema: dict[str, Any] | None = None,
    extractor_versions: dict[str, str] | None = None,
    perceptual_refs: dict[str, str] | None = None,
    key_manager: Any | None = None,
) -> dict[str, Any]:
    """Build a deterministic reconstructible media-profile commitment.

    The recursive meta-object graph contains the descriptive data. This profile
    commits to its composition plus an ordered Merkle-sum DAG over occurrences.
    Optional perceptual/vector references are integrity-bound here but are not
    treated as canonical truth or cryptographic similarity measures.
    """
    dag = build_merkle_sum_dag(graph.get("occurrences") or [], aggregate_schema=aggregate_schema)
    profile_body = {
        "schema_version": "duotronic_media_profile/v1",
        "contract_version": str(graph.get("contract_version") or "v1.6-draft-5.3.18"),
        "information_ref": str(graph.get("information_ref") or ""),
        "root_content_id": str(graph.get("root_content_id") or ""),
        "composition_content_id": str(graph.get("composition_content_id") or ""),
        "merkle_sum_root_node_id": dag["root_node_id"],
        "aggregate_schema": dag["aggregate_schema"],
        "sum_vector": dag["sum_vector"],
        "leaf_count": int(dag["leaf_count"]),
        "extractor_versions": {str(k): str(v) for k, v in sorted((extractor_versions or {}).items())},
        "perceptual_refs": {str(k): str(v) for k, v in sorted((perceptual_refs or {}).items())},
    }
    profile_id = semantic_content_id("duotronic_media_profile/v1", profile_body)
    result = {
        "schema_version": "duotronic_media_profile_bundle/v1",
        "profile_id": profile_id,
        "profile": profile_body,
        "dag": dag,
    }
    if key_manager is not None:
        envelope = key_manager.sign({"profile_id": profile_id, "profile": profile_body}, purpose="manifest")
        if not key_manager.verify(envelope):
            raise RuntimeError("media profile ML-DSA signature failed immediate verification")
        result["signed_manifest"] = envelope
        result["signature_verified"] = True
    return result


def verify_merkle_sum_dag(dag: dict[str, Any]) -> bool:
    schema = _normalize_schema(dag.get("aggregate_schema") or {})
    raw_nodes = list(dag.get("nodes") or [])
    nodes = {str(row.get("node_id") or ""): dict(row) for row in raw_nodes if row.get("node_id")}
    if str(dag.get("root_node_id") or "") not in nodes:
        return False
    try:
        for node_id, node in nodes.items():
            kind = str(node.get("schema_version") or "")
            if kind == "duotronic_media_profile_leaf/v1":
                vector = normalize_sum_vector(node.get("sum_vector") or {}, schema)
                if node_id != _leaf_id(str(node.get("occurrence_id") or ""), vector):
                    return False
            elif kind == "duotronic_media_profile_node/v1":
                left_id = str(node.get("left_node_id") or "")
                right_id = str(node.get("right_node_id") or "")
                left = nodes.get(left_id)
                right = nodes.get(right_id)
                if not left or not right:
                    return False
                left_sum = normalize_sum_vector(node.get("left_sum_vector") or {}, schema)
                right_sum = normalize_sum_vector(node.get("right_sum_vector") or {}, schema)
                if left_sum != normalize_sum_vector(left.get("sum_vector") or {}, schema):
                    return False
                if right_sum != normalize_sum_vector(right.get("sum_vector") or {}, schema):
                    return False
                expected_sum = add_sum_vectors(left_sum, right_sum, schema)
                if expected_sum != normalize_sum_vector(node.get("sum_vector") or {}, schema):
                    return False
                if node_id != _node_id(left_id, left_sum, right_id, right_sum):
                    return False
            elif kind == "duotronic_media_profile_empty/v1":
                if normalize_sum_vector(node.get("sum_vector") or {}, schema) != _zero_vector(schema):
                    return False
            else:
                return False
        root_sum = normalize_sum_vector(nodes[str(dag["root_node_id"])].get("sum_vector") or {}, schema)
        return root_sum == normalize_sum_vector(dag.get("sum_vector") or {}, schema)
    except Exception:
        return False


def verify_media_profile(bundle: dict[str, Any], *, key_manager: Any | None = None) -> bool:
    profile = dict(bundle.get("profile") or {})
    profile_id = str(bundle.get("profile_id") or "")
    if profile_id != semantic_content_id("duotronic_media_profile/v1", profile):
        return False
    dag = dict(bundle.get("dag") or {})
    if not verify_merkle_sum_dag(dag):
        return False
    if profile.get("merkle_sum_root_node_id") != dag.get("root_node_id"):
        return False
    if profile.get("sum_vector") != dag.get("sum_vector"):
        return False
    envelope = bundle.get("signed_manifest")
    if envelope is not None:
        if key_manager is None or not key_manager.verify(dict(envelope)):
            return False
        payload = dict(envelope.get("payload") or {})
        if payload.get("profile_id") != profile_id or payload.get("profile") != profile:
            return False
    return True



def generate_merkle_sum_proof(dag: dict[str, Any], *, occurrence_id: str) -> dict[str, Any]:
    """Generate an inclusion + aggregate-contribution proof for one occurrence."""
    schema = _normalize_schema(dag.get("aggregate_schema") or {})
    nodes = {str(row.get("node_id") or ""): dict(row) for row in (dag.get("nodes") or []) if row.get("node_id")}
    root_id = str(dag.get("root_node_id") or "")
    if root_id not in nodes:
        raise ValueError("media profile root node is missing")
    leaf = next(
        (
            node for node in nodes.values()
            if node.get("schema_version") == "duotronic_media_profile_leaf/v1"
            and str(node.get("occurrence_id") or "") == str(occurrence_id)
        ),
        None,
    )
    if leaf is None:
        raise KeyError(f"occurrence is not a media-profile leaf: {occurrence_id}")

    parent_by_child: dict[str, tuple[dict[str, Any], str]] = {}
    for node in nodes.values():
        if node.get("schema_version") != "duotronic_media_profile_node/v1":
            continue
        left_id = str(node.get("left_node_id") or "")
        right_id = str(node.get("right_node_id") or "")
        if left_id:
            parent_by_child[left_id] = (node, "left")
        if right_id:
            parent_by_child[right_id] = (node, "right")

    current_id = str(leaf["node_id"])
    steps: list[dict[str, Any]] = []
    seen: set[str] = set()
    while current_id != root_id:
        if current_id in seen:
            raise ValueError("cycle detected in media-profile proof path")
        seen.add(current_id)
        parent_info = parent_by_child.get(current_id)
        if parent_info is None:
            raise ValueError(f"no path from leaf to root for {occurrence_id}")
        parent, current_side = parent_info
        if current_side == "left":
            sibling_side = "right"
            sibling_id = str(parent.get("right_node_id") or "")
        else:
            sibling_side = "left"
            sibling_id = str(parent.get("left_node_id") or "")
        sibling = nodes.get(sibling_id)
        if sibling is None:
            raise ValueError(f"missing sibling node in proof path: {sibling_id}")
        steps.append({
            "sibling_side": sibling_side,
            "sibling_node_id": sibling_id,
            "sibling_sum_vector": normalize_sum_vector(sibling.get("sum_vector") or {}, schema),
        })
        current_id = str(parent["node_id"])

    return {
        "schema_version": "duotronic_merkle_sum_proof/v1",
        "occurrence_id": str(occurrence_id),
        "leaf_node_id": str(leaf["node_id"]),
        "leaf_sum_vector": normalize_sum_vector(leaf.get("sum_vector") or {}, schema),
        "aggregate_schema": schema,
        "root_node_id": root_id,
        "root_sum_vector": normalize_sum_vector(dag.get("sum_vector") or {}, schema),
        "steps": steps,
    }


def verify_merkle_sum_proof(proof: dict[str, Any]) -> bool:
    """Verify one occurrence's inclusion and aggregate contribution against a root."""
    try:
        schema = _normalize_schema(proof.get("aggregate_schema") or {})
        occurrence_id = str(proof.get("occurrence_id") or "")
        current_sum = normalize_sum_vector(proof.get("leaf_sum_vector") or {}, schema)
        current_id = _leaf_id(occurrence_id, current_sum)
        if current_id != str(proof.get("leaf_node_id") or ""):
            return False
        for step in proof.get("steps") or []:
            sibling_id = str(step.get("sibling_node_id") or "")
            sibling_sum = normalize_sum_vector(step.get("sibling_sum_vector") or {}, schema)
            side = str(step.get("sibling_side") or "")
            if side == "left":
                current_id = _node_id(sibling_id, sibling_sum, current_id, current_sum)
                current_sum = add_sum_vectors(sibling_sum, current_sum, schema)
            elif side == "right":
                current_id = _node_id(current_id, current_sum, sibling_id, sibling_sum)
                current_sum = add_sum_vectors(current_sum, sibling_sum, schema)
            else:
                return False
        return (
            current_id == str(proof.get("root_node_id") or "")
            and current_sum == normalize_sum_vector(proof.get("root_sum_vector") or {}, schema)
        )
    except Exception:
        return False
