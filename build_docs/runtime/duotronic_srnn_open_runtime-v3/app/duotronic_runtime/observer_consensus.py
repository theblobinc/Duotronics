from __future__ import annotations

from .crypto_primitives import shake256_ref

import json
import time
from collections import defaultdict
from typing import Any


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return shake256_ref(value)


def _clamp01(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return default


class ObserverConsensusEngine:
    """Durable multi-observer consensus over candidate factual claims.

    Observer output is evidence, never truth by itself. Correlated observers are
    collapsed through ``independence_group`` before quorum is calculated, so
    repeated calls to the same model/service do not manufacture consensus.
    """

    def __init__(self, runtime_kernel: Any) -> None:
        self.kernel = runtime_kernel
        self.store = runtime_kernel.store

    @staticmethod
    def claim_key(subject: str, predicate: str, object_value: Any) -> str:
        return _digest({"subject": subject.strip(), "predicate": predicate.strip(), "object": object_value})

    def observe(
        self,
        *,
        subject: str,
        predicate: str,
        object_value: Any,
        observer_id: str,
        observer_kind: str = "unknown",
        independence_group: str | None = None,
        stance: str = "support",
        confidence: float = 0.5,
        source_ref: str | None = None,
        evidence_refs: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        subject = str(subject or "").strip()
        predicate = str(predicate or "").strip()
        observer_id = str(observer_id or "").strip()
        observer_kind = str(observer_kind or "unknown").strip() or "unknown"
        if not subject or not predicate or not observer_id:
            raise ValueError("subject, predicate, and observer_id are required")
        stance = str(stance or "uncertain").strip().lower()
        if stance not in {"support", "contradict", "uncertain"}:
            raise ValueError("stance must be support, contradict, or uncertain")
        confidence = _clamp01(confidence)
        group = str(independence_group or observer_id).strip() or observer_id
        claim_key = self.claim_key(subject, predicate, object_value)
        now_ms = int(time.time() * 1000)
        observation_body = {
            "claim_key": claim_key,
            "subject": subject,
            "predicate": predicate,
            "object": object_value,
            "observer_id": observer_id,
            "observer_kind": observer_kind,
            "independence_group": group,
            "stance": stance,
            "confidence": confidence,
            "source_ref": source_ref,
            "evidence_refs": list(evidence_refs or []),
            "payload": dict(payload or {}),
            "created_at_ms": now_ms,
        }
        observation_id = "obs_" + _digest(observation_body).split(":", 1)[1][:32]
        observation_body["observation_id"] = observation_id

        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT INTO observer_claim_observations
                (observation_id,claim_key,subject,predicate,object,observer_id,observer_kind,
                 independence_group,stance,confidence,source_ref,evidence_refs,payload,created_at_ms)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (observation_id) DO NOTHING
                """,
                (
                    observation_id,
                    claim_key,
                    subject,
                    predicate,
                    json.dumps(object_value),
                    observer_id,
                    observer_kind,
                    group,
                    stance,
                    confidence,
                    source_ref,
                    json.dumps(list(evidence_refs or [])),
                    json.dumps(dict(payload or {})),
                    now_ms,
                ),
            )
            conn.commit()

        witness = self.kernel.evidence.witness(
            "ObserverClaimWitness",
            observation_body,
            force="observe",
            status="recorded",
        )
        self.store.insert_witness(witness)
        result = self.evaluate(claim_key=claim_key)
        return {"observation": observation_body, "witness": witness, "consensus": result}

    def _rows(self, claim_key: str) -> list[dict[str, Any]]:
        with self.store.connect() as conn:
            rows = conn.execute(
                """
                SELECT observation_id,claim_key,subject,predicate,object,observer_id,observer_kind,
                       independence_group,stance,confidence,source_ref,evidence_refs,payload,created_at_ms
                FROM observer_claim_observations
                WHERE claim_key=%s
                ORDER BY created_at_ms ASC, observation_id ASC
                """,
                (claim_key,),
            ).fetchall()
        return [dict(row) for row in rows]

    def evaluate(
        self,
        *,
        claim_key: str,
        min_independent_groups: int = 3,
        min_support_ratio: float = 0.75,
        min_support_weight: float = 1.8,
        max_contradiction_ratio: float = 0.20,
    ) -> dict[str, Any]:
        rows = self._rows(claim_key)
        if not rows:
            return {
                "claim_key": claim_key,
                "status": "no_observations",
                "promotion_recommended": False,
                "independent_observers": 0,
                "independent_groups": 0,
            }

        # Only the latest report from a given observer counts. This avoids one
        # observer amplifying itself through repeated polling.
        latest_by_observer: dict[str, dict[str, Any]] = {}
        for row in rows:
            latest_by_observer[str(row["observer_id"])] = row

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in latest_by_observer.values():
            grouped[str(row.get("independence_group") or row["observer_id"])].append(row)

        support_weight = 0.0
        contradiction_weight = 0.0
        uncertain_weight = 0.0
        groups_summary: list[dict[str, Any]] = []

        for group_id, members in sorted(grouped.items()):
            stance_weight = {"support": 0.0, "contradict": 0.0, "uncertain": 0.0}
            for row in members:
                stance_weight[str(row["stance"])] += _clamp01(row.get("confidence"))
            total_member_weight = sum(stance_weight.values()) or 1.0
            support_fraction = stance_weight["support"] / total_member_weight
            contradict_fraction = stance_weight["contradict"] / total_member_weight
            # Correlated observers collectively contribute at most one unit.
            group_confidence = min(1.0, total_member_weight / max(1, len(members)))
            if abs(support_fraction - contradict_fraction) < 0.10:
                effective_stance = "uncertain"
                uncertain_weight += group_confidence
            elif support_fraction > contradict_fraction:
                effective_stance = "support"
                support_weight += group_confidence
            else:
                effective_stance = "contradict"
                contradiction_weight += group_confidence
            groups_summary.append(
                {
                    "independence_group": group_id,
                    "observer_count": len(members),
                    "effective_stance": effective_stance,
                    "weight": round(group_confidence, 6),
                    "observers": sorted(str(row["observer_id"]) for row in members),
                }
            )

        decisive = support_weight + contradiction_weight
        support_ratio = support_weight / decisive if decisive else 0.0
        contradiction_ratio = contradiction_weight / decisive if decisive else 0.0
        independent_groups = len(grouped)
        independent_observers = len(latest_by_observer)

        if independent_groups < min_independent_groups:
            status = "insufficient_observers"
            promotion_recommended = False
        elif contradiction_ratio > max_contradiction_ratio:
            status = "disputed"
            promotion_recommended = False
        elif support_ratio >= min_support_ratio and support_weight >= min_support_weight:
            status = "promotion_recommended"
            promotion_recommended = True
        elif support_ratio >= 0.67:
            status = "candidate_consensus"
            promotion_recommended = False
        else:
            status = "unresolved"
            promotion_recommended = False

        first = rows[0]
        now_ms = int(time.time() * 1000)
        result = {
            "claim_key": claim_key,
            "subject": first["subject"],
            "predicate": first["predicate"],
            "object": first["object"],
            "support_weight": round(support_weight, 6),
            "contradiction_weight": round(contradiction_weight, 6),
            "uncertain_weight": round(uncertain_weight, 6),
            "support_ratio": round(support_ratio, 6),
            "contradiction_ratio": round(contradiction_ratio, 6),
            "independent_observers": independent_observers,
            "independent_groups": independent_groups,
            "status": status,
            "promotion_recommended": promotion_recommended,
            "observer_summary": {"groups": groups_summary},
            "evaluated_at_ms": now_ms,
        }
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT INTO claim_consensus
                (claim_key,subject,predicate,object,support_weight,contradiction_weight,uncertain_weight,
                 support_ratio,contradiction_ratio,independent_observers,independent_groups,status,
                 promotion_recommended,observer_summary,evaluated_at_ms,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())
                ON CONFLICT (claim_key) DO UPDATE SET
                  support_weight=EXCLUDED.support_weight,
                  contradiction_weight=EXCLUDED.contradiction_weight,
                  uncertain_weight=EXCLUDED.uncertain_weight,
                  support_ratio=EXCLUDED.support_ratio,
                  contradiction_ratio=EXCLUDED.contradiction_ratio,
                  independent_observers=EXCLUDED.independent_observers,
                  independent_groups=EXCLUDED.independent_groups,
                  status=EXCLUDED.status,
                  promotion_recommended=EXCLUDED.promotion_recommended,
                  observer_summary=EXCLUDED.observer_summary,
                  evaluated_at_ms=EXCLUDED.evaluated_at_ms,
                  updated_at=now()
                """,
                (
                    claim_key,
                    first["subject"],
                    first["predicate"],
                    json.dumps(first["object"]),
                    result["support_weight"],
                    result["contradiction_weight"],
                    result["uncertain_weight"],
                    result["support_ratio"],
                    result["contradiction_ratio"],
                    independent_observers,
                    independent_groups,
                    status,
                    promotion_recommended,
                    json.dumps(result["observer_summary"]),
                    now_ms,
                ),
            )
            conn.commit()

        claim_status = "promotion_recommended" if promotion_recommended else status
        evidence_claim = self.kernel.evidence.claim(
            subject=str(first["subject"]),
            predicate=str(first["predicate"]),
            object=first["object"],
            claim_kind="observer_consensus",
            claim_status=claim_status,
            epistemic_status=status,
            force="verify",
            support=[row["observation_id"] for row in latest_by_observer.values()],
        )
        self.store.insert_evidence_claim(evidence_claim)
        result["evidence_claim"] = evidence_claim
        return result

    def get(self, *, claim_key: str) -> dict[str, Any]:
        with self.store.connect() as conn:
            row = conn.execute("SELECT * FROM claim_consensus WHERE claim_key=%s", (claim_key,)).fetchone()
        return dict(row) if row else self.evaluate(claim_key=claim_key)

    def recent(self, *, limit: int = 50, promotion_recommended: bool | None = None) -> list[dict[str, Any]]:
        clauses = []
        params: list[Any] = []
        if promotion_recommended is not None:
            clauses.append("promotion_recommended=%s")
            params.append(bool(promotion_recommended))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(max(1, min(int(limit), 200)))
        with self.store.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM claim_consensus{where} ORDER BY updated_at DESC LIMIT %s",
                tuple(params),
            ).fetchall()
        return [dict(row) for row in rows]
