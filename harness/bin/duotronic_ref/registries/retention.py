"""Retention registry — surfaces metric specs by id."""

from __future__ import annotations

from ..retention import RETENTION_METRICS, RetentionMetricSpec


class RetentionRegistry:
    def resolve(self, metric_id: str) -> RetentionMetricSpec:
        try:
            return RETENTION_METRICS[metric_id]
        except KeyError as exc:
            raise KeyError(f"unknown retention metric {metric_id}") from exc

    def all(self) -> list[RetentionMetricSpec]:
        return list(RETENTION_METRICS.values())


RETENTION_REGISTRY = RetentionRegistry()
