from __future__ import annotations

import json
import math
import re
from typing import Any, Iterable

from .crypto_primitives import contract_canonical_bytes, semantic_content_id

CONTRACT_VERSION = "v1.6-draft-5.3.18"
POLICY_ID = "policy:wg-rnn-candidate-meta-observation-v3"
MAX_META_DEPTH = 16
MAX_META_OBJECTS = 16384


def _portable_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        # 5.3.18 canonical identity JSON does not use binary floats. Preserve a
        # deterministic decimal representation until a domain schema provides one.
        return format(value, ".17g")
    if isinstance(value, dict):
        return {str(k): _portable_value(value[k]) for k in sorted(value, key=lambda x: str(x))}
    if isinstance(value, (list, tuple)):
        return [_portable_value(v) for v in value]
    return str(value)


def _content(content_type: str, body: dict[str, Any], *, schema_id: str | None = None) -> dict[str, Any]:
    body = _portable_value(body)
    cid = semantic_content_id(content_type, body)
    return {
        "semantic_content_id": cid,
        "contract_version": CONTRACT_VERSION,
        "content_type": content_type,
        "body": body,
        "canonical_body": contract_canonical_bytes(body),
        "schema_id": schema_id or f"runtime://semantic/{content_type}",
    }


def _children_from_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("children", "meta_objects", "attributes"):
        value = spec.get(key)
        if isinstance(value, list):
            return [dict(row) for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            rows = []
            for name in sorted(value):
                child = value[name]
                if isinstance(child, dict):
                    row = dict(child)
                    row.setdefault("label", str(name))
                else:
                    row = {"label": str(name), "value": child}
                rows.append(row)
            return rows
    return []


def _meta_object_tree(
    spec: dict[str, Any],
    *,
    contents: dict[str, dict[str, Any]],
    depth: int = 0,
    counter: list[int] | None = None,
) -> tuple[str, list[str]]:
    """Create one recursive meta-object witness and all nested child witnesses.

    The parent identity commits to its measured value plus the ordered child
    witness references. Two object instances can therefore have different parent
    identities while sharing many child identities describing common qualities.
    """
    counter = counter if counter is not None else [0]
    if depth > MAX_META_DEPTH:
        raise ValueError("meta_object_max_depth_exceeded")
    counter[0] += 1
    if counter[0] > MAX_META_OBJECTS:
        raise ValueError("meta_object_max_count_exceeded")

    child_refs: list[dict[str, Any]] = []
    closure: list[str] = []
    for ordinal, child in enumerate(_children_from_spec(spec)):
        child_id, child_closure = _meta_object_tree(child, contents=contents, depth=depth + 1, counter=counter)
        child_refs.append({
            "role": str(child.get("role") or child.get("label") or f"child.{ordinal}"),
            "ordinal": int(child.get("ordinal", ordinal)),
            "meta_object_id": child_id,
        })
        closure.extend(child_closure)

    body = {
        "schema_version": "duotronic_meta_object/v2",
        "measurement_kind": str(spec.get("measurement_kind") or "quality"),
        "label": str(spec.get("label") or spec.get("feature_kind") or "measurement"),
        "value": _portable_value(spec.get("value")),
        "unit": str(spec.get("unit")) if spec.get("unit") is not None else None,
        "qualifiers": _portable_value(dict(spec.get("qualifiers") or {})),
        "children": sorted(child_refs, key=lambda row: (row["ordinal"], row["role"], row["meta_object_id"])),
    }
    row = _content("duotronic_meta_object/v2", body)
    cid = row["semantic_content_id"]
    contents[cid] = row
    return cid, [cid, *closure]


def meta_object_content_id(
    *,
    label: str,
    value: Any = None,
    measurement_kind: str = "quality",
    unit: str | None = None,
    qualifiers: dict[str, Any] | None = None,
    children: Iterable[dict[str, Any]] | None = None,
) -> str:
    contents: dict[str, dict[str, Any]] = {}
    cid, _closure = _meta_object_tree({
        "label": label,
        "value": value,
        "measurement_kind": measurement_kind,
        "unit": unit,
        "qualifiers": dict(qualifiers or {}),
        "children": list(children or []),
    }, contents=contents)
    return cid


def _occurrence_content(
    *,
    information_content_id: str,
    meta_object_id: str,
    descendant_meta_object_ids: list[str],
    locator: dict[str, Any] | None,
    ordinal: int,
    channel: str | None = None,
    confidence: Any = None,
    sum_contribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = {
        "schema_version": "duotronic_meta_object_occurrence/v2",
        "information_content_id": str(information_content_id),
        "meta_object_id": str(meta_object_id),
        "descendant_meta_object_ids": sorted(set(descendant_meta_object_ids)),
        "locator": _portable_value(dict(locator or {})),
        "ordinal": int(ordinal),
        "channel": str(channel) if channel is not None else None,
        "confidence": _portable_value(confidence),
        # Optional schema-declared aggregate contributions. These are not inferred
        # from descriptive quantities; the extractor must state them explicitly.
        "sum_contribution": _portable_value(dict(sum_contribution or {})),
    }
    return _content("duotronic_meta_object_occurrence/v2", body)


def _composition_content(*, information_content_id: str, occurrences: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(
        occurrences,
        key=lambda row: (
            int(row.get("ordinal") or 0),
            json.dumps(_portable_value(row.get("locator") or {}), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            str(row.get("occurrence_id") or ""),
        ),
    )
    body = {
        "schema_version": "duotronic_information_composition/v2",
        "information_content_id": str(information_content_id),
        "ordered_occurrence_ids": [str(row["occurrence_id"]) for row in ordered],
    }
    return _content("duotronic_information_composition/v2", body)


def _flatten_structural_measurements(value: Any, *, prefix: str = "", limit: int = 4096) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def walk(current: Any, path: str, locator: dict[str, Any]) -> None:
        if len(out) >= max(1, int(limit)):
            return
        current = _portable_value(current)
        if isinstance(current, dict):
            for key in sorted(current):
                child = f"{path}.{key}" if path else str(key)
                walk(current[key], child, {**locator, "path": child})
            return
        if isinstance(current, list):
            for index, item in enumerate(current):
                child = f"{path}[]" if path else "[]"
                walk(item, child, {**locator, "path": child, "list_index": index})
            return
        if path:
            out.append({"label": path, "value": current, "measurement_kind": "quality", "locator": locator})

    walk(value, prefix, {"scope": "structural"})
    return out[: max(1, int(limit))]


_STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "into", "have", "has", "had", "are", "was", "were",
    "will", "would", "could", "should", "can", "may", "might", "not", "but", "you", "your", "yours", "our", "ours",
    "their", "they", "them", "his", "her", "hers", "its", "it's", "what", "when", "where", "which", "who", "why",
    "how", "about", "than", "then", "there", "here", "also", "just", "some", "more", "most", "very", "been", "being",
    "does", "did", "doing", "get", "got", "make", "made", "like", "using", "use", "used", "via", "per", "each",
}


def _token_occurrences(text: str, *, limit: int = 32) -> list[tuple[int, str]]:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_.'+-]{2,}", str(text or ""))]
    out: list[tuple[int, str]] = []
    for index, token in enumerate(tokens):
        if token in _STOPWORDS:
            continue
        out.append((index, token))
        if len(out) >= max(1, int(limit)):
            break
    return out


def feature_content_ids(text: str, *, limit: int = 32) -> list[str]:
    ids = [meta_object_content_id(label="token", value=token, measurement_kind="lexical") for _i, token in _token_occurrences(text, limit=limit * 2)]
    return list(dict.fromkeys(ids))[: max(1, int(limit))]


def _derive_information_ref(*, information_kind: str, text_fields: dict[str, str], facets: dict[str, Any], metadata: dict[str, Any]) -> str:
    seed = {"information_kind": information_kind, "text_fields": text_fields, "facets": facets, "metadata": metadata}
    return semantic_content_id("duotronic_information_ref_seed/v1", seed)


def build_information_graph(
    *,
    information_kind: str,
    information_ref: str | None = None,
    text_fields: dict[str, str] | None = None,
    facets: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    meta_objects: Iterable[dict[str, Any]] | None = None,
    feature_limit_per_field: int = 24,
    structural_limit: int = 4096,
) -> dict[str, Any]:
    """Build a reconstructible, recursively witnessed description of one information object.

    Exact SHAKE identities are not used as a locality-sensitive similarity metric.
    Similarity is computed from the dereferenceable nested measurements that each
    identity commits to. No arbitrary pairwise links are inferred between unrelated
    qualities that merely coexist in one media object.
    """
    text_fields = {str(k): str(v or "") for k, v in (text_fields or {}).items() if str(v or "").strip()}
    facets = _portable_value(dict(facets or {}))
    metadata = _portable_value(dict(metadata or {}))
    information_ref = str(information_ref or _derive_information_ref(
        information_kind=str(information_kind), text_fields=text_fields, facets=facets, metadata=metadata
    ))

    root_body = {
        "schema_version": "wgrnn_information_object/v3",
        "information_kind": str(information_kind),
        # Stable identity/provenance locator for the information object. Adapter
        # implementation details deliberately do not change the media identity.
        "information_ref": information_ref,
    }
    root = _content("wgrnn_information_object/v3", root_body)
    contents: dict[str, dict[str, Any]] = {root["semantic_content_id"]: root}
    measurements: list[dict[str, Any]] = []
    ordinal = 0

    for field_name in sorted(text_fields):
        text_value = text_fields[field_name]
        measurements.append({
            "label": f"text.{field_name}", "value": text_value, "measurement_kind": "content",
            "locator": {"field": field_name, "scope": "text_field"}, "ordinal": ordinal,
        })
        ordinal += 1
        for token_ordinal, token in _token_occurrences(text_value, limit=feature_limit_per_field):
            measurements.append({
                "label": "token", "value": token, "measurement_kind": "lexical",
                "locator": {"field": field_name, "token_ordinal": token_ordinal, "scope": "token"}, "ordinal": ordinal,
            })
            ordinal += 1

    for row in _flatten_structural_measurements(facets, limit=structural_limit):
        measurements.append({**row, "ordinal": ordinal})
        ordinal += 1

    for supplied in meta_objects or []:
        if not isinstance(supplied, dict):
            continue
        row = dict(supplied)
        row.setdefault("measurement_kind", "quality")
        row.setdefault("label", row.get("feature_kind") or "measurement")
        row.setdefault("locator", {})
        row.setdefault("ordinal", ordinal)
        measurements.append(row)
        ordinal = max(ordinal + 1, int(row.get("ordinal") or 0) + 1)

    occurrences: list[dict[str, Any]] = []
    all_meta_object_ids: list[str] = []
    top_level_meta_object_ids: list[str] = []
    counter = [0]
    for measurement in measurements:
        parent_id, closure = _meta_object_tree(measurement, contents=contents, counter=counter)
        top_level_meta_object_ids.append(parent_id)
        all_meta_object_ids.extend(closure)
        occurrence_content = _occurrence_content(
            information_content_id=root["semantic_content_id"],
            meta_object_id=parent_id,
            descendant_meta_object_ids=closure,
            locator=measurement.get("locator") if isinstance(measurement.get("locator"), dict) else {},
            ordinal=int(measurement.get("ordinal") or 0),
            channel=str(measurement.get("channel")) if measurement.get("channel") is not None else None,
            confidence=measurement.get("confidence"),
            sum_contribution=measurement.get("sum_contribution") if isinstance(measurement.get("sum_contribution"), dict) else {},
        )
        contents[occurrence_content["semantic_content_id"]] = occurrence_content
        body = occurrence_content["body"]
        occurrences.append({
            "occurrence_id": occurrence_content["semantic_content_id"],
            "meta_object_id": parent_id,
            "descendant_meta_object_ids": list(body.get("descendant_meta_object_ids") or []),
            "information_content_id": root["semantic_content_id"],
            "locator": body.get("locator") or {},
            "ordinal": int(body.get("ordinal") or 0),
            "channel": body.get("channel"),
            "confidence": body.get("confidence"),
            "sum_contribution": body.get("sum_contribution") or {},
            "canonical_occurrence": occurrence_content["canonical_body"],
        })

    composition = _composition_content(information_content_id=root["semantic_content_id"], occurrences=occurrences)
    contents[composition["semantic_content_id"]] = composition
    ordered_contents = [contents[key] for key in sorted(contents)]
    ordered_occurrences = sorted(occurrences, key=lambda row: (row["ordinal"], str(row["occurrence_id"])))

    return {
        "schema_version": "wgrnn_meta_object_composition_observation/v3",
        "contract_version": CONTRACT_VERSION,
        "authority": "candidate_observation_only",
        "root_content_id": root["semantic_content_id"],
        "information_ref": information_ref,
        "composition_content_id": composition["semantic_content_id"],
        "contents": ordered_contents,
        "edges": [],
        "content_ids": [row["semantic_content_id"] for row in ordered_contents],
        "edge_ids": [],
        "top_level_meta_object_ids": list(dict.fromkeys(top_level_meta_object_ids)),
        "meta_object_ids": list(dict.fromkeys(all_meta_object_ids)),
        "occurrence_ids": [row["occurrence_id"] for row in ordered_occurrences],
        "occurrences": ordered_occurrences,
        "measurement_count": len(ordered_occurrences),
    }


def _number(value: Any) -> float | None:
    try:
        if isinstance(value, bool) or value is None:
            return None
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _meta_rows(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["semantic_content_id"]): row
        for row in (graph.get("contents") or [])
        if isinstance(row, dict) and row.get("content_type") == "duotronic_meta_object/v2"
    }


def _meta_similarity(left_id: str, right_id: str, left_rows: dict[str, dict[str, Any]], right_rows: dict[str, dict[str, Any]], *, depth: int = 0) -> float:
    if left_id == right_id:
        return 1.0
    if depth > MAX_META_DEPTH:
        return 0.0
    left = left_rows.get(left_id, {}).get("body") or {}
    right = right_rows.get(right_id, {}).get("body") or {}
    if not left or not right:
        return 0.0
    if str(left.get("measurement_kind")) != str(right.get("measurement_kind")):
        return 0.0
    if str(left.get("label")) != str(right.get("label")):
        return 0.0
    if (left.get("unit") or None) != (right.get("unit") or None):
        return 0.0

    lv, rv = left.get("value"), right.get("value")
    ln, rn = _number(lv), _number(rv)
    if ln is not None and rn is not None:
        scale = max(abs(ln), abs(rn), 1.0)
        value_score = max(0.0, 1.0 - abs(ln - rn) / scale)
    else:
        value_score = 1.0 if lv == rv else (0.6 if str(lv).casefold() == str(rv).casefold() else 0.0)

    left_children = list(left.get("children") or [])
    right_children = list(right.get("children") or [])
    if not left_children and not right_children:
        return value_score
    if not left_children or not right_children:
        return 0.55 * value_score

    unmatched = set(range(len(right_children)))
    child_scores: list[float] = []
    for lc in left_children:
        best_i = None
        best = 0.0
        for i in unmatched:
            rc = right_children[i]
            if str(lc.get("role")) != str(rc.get("role")):
                continue
            score = _meta_similarity(str(lc.get("meta_object_id")), str(rc.get("meta_object_id")), left_rows, right_rows, depth=depth + 1)
            if score > best:
                best, best_i = score, i
        if best_i is not None:
            unmatched.remove(best_i)
            child_scores.append(best)
    child_score = sum(child_scores) / max(len(left_children), len(right_children), 1)
    return max(0.0, min(1.0, 0.35 * value_score + 0.65 * child_score))


def compare_information_compositions(left: dict[str, Any], right: dict[str, Any], *, minimum_similarity: float = 0.45) -> dict[str, Any]:
    """Match similar media meta-object occurrences by nested witnessed structure."""
    left_rows, right_rows = _meta_rows(left), _meta_rows(right)
    left_occ, right_occ = list(left.get("occurrences") or []), list(right.get("occurrences") or [])
    available = set(range(len(right_occ)))
    matches: list[dict[str, Any]] = []
    for lo in sorted(left_occ, key=lambda row: (int(row.get("ordinal") or 0), str(row.get("occurrence_id") or ""))):
        best_i = None
        best_score = 0.0
        for i in available:
            ro = right_occ[i]
            score = _meta_similarity(str(lo.get("meta_object_id")), str(ro.get("meta_object_id")), left_rows, right_rows)
            if score > best_score:
                best_score, best_i = score, i
        if best_i is None or best_score < float(minimum_similarity):
            continue
        available.remove(best_i)
        ro = right_occ[best_i]
        matches.append({
            "left_meta_object_id": lo.get("meta_object_id"),
            "right_meta_object_id": ro.get("meta_object_id"),
            "exact_identity": lo.get("meta_object_id") == ro.get("meta_object_id"),
            "similarity": round(best_score, 6),
            "left_occurrence": {"ordinal": lo.get("ordinal"), "locator": lo.get("locator") or {}},
            "right_occurrence": {"ordinal": ro.get("ordinal"), "locator": ro.get("locator") or {}},
        })
    score = sum(float(row["similarity"]) for row in matches) / max(len(left_occ), len(right_occ), 1)
    return {
        "schema_version": "duotronic_composition_match/v2",
        "left_composition_content_id": left.get("composition_content_id"),
        "right_composition_content_id": right.get("composition_content_id"),
        "matched_occurrence_count": len(matches),
        "left_occurrence_count": len(left_occ),
        "right_occurrence_count": len(right_occ),
        "similarity": round(score, 6),
        "matches": matches,
    }


def _descriptor_summary(meta_object_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a compact dereference hint for a witnessed meta-object ID."""
    for item in items:
        for row in item.get("contents") or []:
            if not isinstance(row, dict) or str(row.get("semantic_content_id") or "") != meta_object_id:
                continue
            if row.get("content_type") != "duotronic_meta_object/v2":
                continue
            body = dict(row.get("body") or {})
            return {
                "measurement_kind": body.get("measurement_kind"),
                "label": body.get("label"),
                "value": body.get("value"),
                "unit": body.get("unit"),
                "qualifiers": body.get("qualifiers") or {},
            }
    return {}


def _exact_recurrence_patterns(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positions_by_meta: dict[str, list[int]] = {}
    for position, item in enumerate(items):
        # One descriptor counts once per media/information object even if it occurs
        # many times inside that object. Occurrence multiplicity remains available
        # in the item's occurrence records.
        for meta_object_id in sorted({str(value) for value in (item.get("meta_object_ids") or []) if str(value)}):
            positions_by_meta.setdefault(meta_object_id, []).append(position)

    patterns: list[dict[str, Any]] = []
    for meta_object_id, positions in sorted(positions_by_meta.items()):
        if len(positions) < 2:
            continue
        gaps = [right - left for left, right in zip(positions, positions[1:])]
        period = gaps[0] if gaps and all(gap == gaps[0] for gap in gaps) else None
        pattern = {
            "meta_object_id": meta_object_id,
            "descriptor": _descriptor_summary(meta_object_id, items),
            "positions": positions,
            "gaps": gaps,
            "presence_count": len(positions),
            "period": int(period) if period is not None else None,
            "phase": int(positions[0] % period) if period else None,
            "period_evidence_count": len(gaps) if period is not None else 0,
        }
        patterns.append(pattern)
    return patterns


def _periodic_groups(recurrences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group exact recurring descriptors by period to expose alternation patterns."""
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in recurrences:
        period = row.get("period")
        if not isinstance(period, int) or period <= 1:
            continue
        grouped.setdefault(period, []).append(row)
    result: list[dict[str, Any]] = []
    for period, rows in sorted(grouped.items()):
        phases = sorted({int(row.get("phase") or 0) for row in rows})
        if len(phases) < 2:
            continue
        members = [
            {
                "meta_object_id": row["meta_object_id"],
                "descriptor": row.get("descriptor") or {},
                "phase": int(row.get("phase") or 0),
                "positions": list(row.get("positions") or []),
            }
            for row in sorted(rows, key=lambda value: (int(value.get("phase") or 0), str(value.get("meta_object_id") or "")))
        ]
        result.append({
            "period": period,
            "phases": phases,
            "members": members,
        })
    return result


def build_information_chain(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Witness ordered cross-media recurrence, alternation and near correspondence.

    Cryptographic IDs commit to exact measured descriptions. Similarity itself is
    derived from the dereferenceable descriptions, never from SHAKE digest distance.
    Values committed into the chain witness use integer parts-per-million rather
    than binary floats so the 5.3.18 canonical identity domain remains valid.
    """
    ordered = list(items)
    transitions = [compare_information_compositions(left, right) for left, right in zip(ordered, ordered[1:])]
    recurrences = _exact_recurrence_patterns(ordered)
    periodic_groups = _periodic_groups(recurrences)

    successive_matches: list[list[dict[str, Any]]] = []
    for transition_index, transition in enumerate(transitions):
        rows: list[dict[str, Any]] = []
        for match in transition.get("matches") or []:
            similarity_ppm = max(0, min(1_000_000, int(round(float(match.get("similarity") or 0.0) * 1_000_000))))
            rows.append({
                "transition_index": transition_index,
                "left_meta_object_id": match["left_meta_object_id"],
                "right_meta_object_id": match["right_meta_object_id"],
                "exact_identity": bool(match.get("exact_identity")),
                "similarity_ppm": similarity_ppm,
                "left_locator": match["left_occurrence"]["locator"],
                "right_locator": match["right_occurrence"]["locator"],
            })
        successive_matches.append(rows)

    chain_body = {
        "schema_version": "duotronic_information_chain_pattern/v3",
        "information_refs": [str(item.get("information_ref") or "") for item in ordered],
        "composition_content_ids": [str(item.get("composition_content_id") or "") for item in ordered],
        "profile_ids": [str(item.get("profile_id") or "") for item in ordered],
        "exact_recurrence_patterns": recurrences,
        "periodic_groups": periodic_groups,
        "successive_matches": successive_matches,
    }
    chain_pattern_content_id = semantic_content_id("duotronic_information_chain_pattern/v3", chain_body)
    return {
        **chain_body,
        "chain_pattern_content_id": chain_pattern_content_id,
        # Floating scores are convenient runtime diagnostics but deliberately stay
        # outside the hashed/canonical chain body above.
        "transitions": transitions,
    }


def reconstruct_information_description(graph: dict[str, Any]) -> dict[str, Any]:
    """Dereference a composition into its canonical nested measured description."""
    rows = {str(row.get("semantic_content_id")): row for row in (graph.get("contents") or []) if isinstance(row, dict)}

    def expand(meta_id: str, seen: set[str] | None = None) -> dict[str, Any]:
        seen = set(seen or ())
        if meta_id in seen:
            return {"meta_object_id": meta_id, "cycle": True}
        seen.add(meta_id)
        body = dict((rows.get(meta_id) or {}).get("body") or {})
        children = []
        for child in body.get("children") or []:
            children.append({
                "role": child.get("role"),
                "ordinal": child.get("ordinal"),
                "meta_object": expand(str(child.get("meta_object_id") or ""), seen),
            })
        return {
            "meta_object_id": meta_id,
            "measurement_kind": body.get("measurement_kind"),
            "label": body.get("label"),
            "value": body.get("value"),
            "unit": body.get("unit"),
            "qualifiers": body.get("qualifiers") or {},
            "children": children,
        }

    occurrences = []
    for occurrence in sorted(graph.get("occurrences") or [], key=lambda row: (int(row.get("ordinal") or 0), str(row.get("occurrence_id") or ""))):
        occurrences.append({
            "occurrence_id": occurrence.get("occurrence_id"),
            "ordinal": occurrence.get("ordinal"),
            "locator": occurrence.get("locator") or {},
            "channel": occurrence.get("channel"),
            "confidence": occurrence.get("confidence"),
            "meta_object": expand(str(occurrence.get("meta_object_id") or "")),
        })
    return {
        "schema_version": "duotronic_reconstructed_information_description/v1",
        "information_ref": graph.get("information_ref"),
        "root_content_id": graph.get("root_content_id"),
        "composition_content_id": graph.get("composition_content_id"),
        "occurrences": occurrences,
    }


def build_chat_turn_graph(*, conversation: str, response_text: str, task_frame: dict[str, Any], identity: dict[str, Any], tags: Iterable[str] = ()) -> dict[str, Any]:
    facets: dict[str, Any] = {
        "operation_kind": str(task_frame.get("operation_kind") or "ask"),
        "source": str(identity.get("source") or "openai-compatible"),
    }
    for key in ("user_id", "agent_id", "thread_id"):
        value = identity.get(key)
        if value:
            facets[key] = str(value)
    for index, tag in enumerate(sorted({str(tag) for tag in tags if str(tag)})):
        facets[f"tag.{index}"] = tag
    metadata = {"task_id": str(task_frame.get("task_id") or ""), "task_digest": str(task_frame.get("task_digest") or "")}
    information_ref = str(task_frame.get("task_id") or task_frame.get("task_digest") or "") or None
    return build_information_graph(
        information_kind="wgrnn_chat_turn",
        information_ref=information_ref,
        text_fields={"conversation": conversation, "response": response_text},
        facets=facets,
        metadata=metadata,
    )
