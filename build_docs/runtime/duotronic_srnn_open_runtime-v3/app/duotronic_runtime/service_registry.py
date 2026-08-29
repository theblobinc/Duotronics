from __future__ import annotations

import ipaddress
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from .crypto_primitives import stable_shake_id


class ServiceRegistry:
    """Offline topology/capability registry for the Xavi backend LAN.

    The registry is configuration and provenance, not a live-discovery oracle.
    Nodes become scheduler-ready only after their private transport has been
    explicitly commissioned. Public management endpoints may be recorded as
    bootstrap/fallback metadata but never make a node LAN-ready.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": "xavi-service-registry-v1",
                "network": {},
                "nodes": [],
                "warnings": [f"registry_missing:{self.path}"],
            }
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {
                "schema_version": "xavi-service-registry-v1",
                "network": {},
                "nodes": [],
                "warnings": [f"registry_invalid:{type(exc).__name__}"],
            }
        if not isinstance(data, dict):
            return {"schema_version": "xavi-service-registry-v1", "network": {}, "nodes": [], "warnings": ["registry_not_object"]}
        data.setdefault("schema_version", "xavi-service-registry-v1")
        data.setdefault("network", {})
        data.setdefault("nodes", [])
        return data

    @staticmethod
    def _normalize_url(value: Any) -> str:
        return str(value or "").strip().rstrip("/")

    def _backend_network(self) -> ipaddress._BaseNetwork | None:
        cidr = str((self.data.get("network") or {}).get("backend_cidr") or "").strip()
        if not cidr:
            return None
        try:
            return ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            return None

    def nodes(self, *, scheduler_ready_only: bool = False, role: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for raw in self.data.get("nodes") or []:
            if not isinstance(raw, dict):
                continue
            row = dict(raw)
            roles = [str(item) for item in (row.get("roles") or [])]
            if role and role not in roles:
                continue
            if scheduler_ready_only and not bool(row.get("scheduler_eligible")):
                continue
            rows.append(row)
        return rows

    def node(self, node_id: str) -> dict[str, Any] | None:
        wanted = str(node_id or "").strip()
        return next((row for row in self.nodes() if str(row.get("id") or "") == wanted), None)

    def endpoint_owner(self, base_url: str) -> tuple[dict[str, Any], str, dict[str, Any]] | None:
        wanted = self._normalize_url(base_url)
        if not wanted:
            return None
        for node in self.nodes():
            services = node.get("services") or {}
            if not isinstance(services, dict):
                continue
            for service_name, raw_service in services.items():
                if not isinstance(raw_service, dict):
                    continue
                service = dict(raw_service)
                for key in ("primary_url", "container_url", "url", "endpoint"):
                    if self._normalize_url(service.get(key)) == wanted:
                        return node, str(service_name), service
        return None

    def annotate_model(self, record: dict[str, Any]) -> dict[str, Any]:
        out = dict(record)
        owner = self.endpoint_owner(str(out.get("base_url") or ""))
        if owner is None:
            return out
        node, service_name, service = owner
        transport = node.get("transport") or {}
        metadata = dict(out.get("metadata") or {})
        metadata.update(
            {
                "node_id": node.get("id"),
                "node_status": node.get("status"),
                "node_roles": list(node.get("roles") or []),
                "scheduler_eligible": bool(node.get("scheduler_eligible")),
                "transport": transport.get("kind") or "dedicated-private-ethernet",
                "private_ipv4": transport.get("private_ipv4"),
                "internet_required": bool(transport.get("internet_required", False)),
                "lan_preferred": bool(service.get("lan_preferred", True)),
                "service_name": service_name,
            }
        )
        out["metadata"] = metadata
        return out

    def _probe_endpoints(self, node: dict[str, Any], service: dict[str, Any]) -> list[str]:
        local_node_id = str((self.data.get("network") or {}).get("local_node_id") or "")
        node_id = str(node.get("id") or "")
        keys = ("container_url", "primary_url", "url", "endpoint") if node_id == local_node_id else ("primary_url", "url", "endpoint", "container_url")
        endpoints: list[str] = []
        for key in keys:
            endpoint = self._normalize_url(service.get(key))
            if not endpoint or endpoint in endpoints:
                continue
            parsed = urlparse(endpoint)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                continue
            endpoints.append(endpoint)
        return endpoints

    def service_health(
        self,
        *,
        node_id: str | None = None,
        service: str | None = None,
        timeout_seconds: float = 2.0,
    ) -> dict[str, Any]:
        """Actively observe configured offline service liveness over loopback/LAN.

        Static commissioning remains separate from this observation. A healthy
        response does not grant authority or commission a node, and public
        bootstrap/management endpoints are never probed by this method.
        """
        wanted_node = str(node_id or "").strip()
        wanted_service = str(service or "").strip()
        timeout_value = max(0.2, min(float(timeout_seconds or 2.0), 10.0))
        observed_at_ms = int(time.time() * 1000)
        observations: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []

        with httpx.Client(timeout=httpx.Timeout(timeout_value, connect=min(timeout_value, 2.0)), trust_env=False) as client:
            for node in self.nodes():
                current_node = str(node.get("id") or "unknown")
                if wanted_node and current_node != wanted_node:
                    continue
                if str(node.get("status") or "") != "commissioned" or not bool(node.get("scheduler_eligible")):
                    skipped.append({"node_id": current_node, "reason": "not_scheduler_ready", "status": node.get("status")})
                    continue
                services = node.get("services") if isinstance(node.get("services"), dict) else {}
                selected_services = services.items() if not wanted_service else [(wanted_service, services.get(wanted_service))]
                for service_name, raw_service in selected_services:
                    if not isinstance(raw_service, dict):
                        skipped.append({"node_id": current_node, "service": str(service_name), "reason": "service_not_configured"})
                        continue
                    service_record = dict(raw_service)
                    if bool(service_record.get("internet_required", False)):
                        skipped.append({"node_id": current_node, "service": str(service_name), "reason": "internet_service_not_probed"})
                        continue
                    endpoints = self._probe_endpoints(node, service_record)
                    if not endpoints:
                        skipped.append({"node_id": current_node, "service": str(service_name), "reason": "no_offline_http_endpoint"})
                        continue

                    health_path = str(service_record.get("health_path") or "/").strip() or "/"
                    if not health_path.startswith("/"):
                        health_path = "/" + health_path
                    attempts: list[dict[str, Any]] = []
                    selected_endpoint: str | None = None
                    selected_status: int | None = None
                    selected_latency_ms: float | None = None
                    healthy = False
                    reachable = False
                    for endpoint in endpoints:
                        url = endpoint + health_path
                        started = time.perf_counter()
                        try:
                            response = client.get(url)
                            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
                            status_code = int(response.status_code)
                            network_reachable = True
                            attempt_healthy = 200 <= status_code < 400
                            attempts.append({
                                "endpoint": endpoint,
                                "status_code": status_code,
                                "latency_ms": latency_ms,
                                "reachable": network_reachable,
                                "healthy": attempt_healthy,
                            })
                            reachable = True
                            if selected_endpoint is None or attempt_healthy:
                                selected_endpoint = endpoint
                                selected_status = status_code
                                selected_latency_ms = latency_ms
                            if attempt_healthy:
                                healthy = True
                                break
                        except Exception as exc:
                            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
                            attempts.append({
                                "endpoint": endpoint,
                                "status_code": None,
                                "latency_ms": latency_ms,
                                "reachable": False,
                                "healthy": False,
                                "error": exc.__class__.__name__,
                            })

                    observations.append({
                        "node_id": current_node,
                        "service": str(service_name),
                        "healthy": healthy,
                        "reachable": reachable,
                        "endpoint": selected_endpoint,
                        "status_code": selected_status,
                        "latency_ms": selected_latency_ms,
                        "transport": (node.get("transport") or {}).get("kind"),
                        "internet_required": False,
                        "attempts": attempts,
                    })

        payload = {
            "schema_version": "xavi-service-health-v1",
            "offline_only": True,
            "observed_at_ms": observed_at_ms,
            "filters": {"node_id": wanted_node or None, "service": wanted_service or None},
            "healthy_count": sum(1 for row in observations if row.get("healthy")),
            "reachable_count": sum(1 for row in observations if row.get("reachable")),
            "observation_count": len(observations),
            "observations": observations,
            "skipped": skipped,
        }
        payload["observation_digest"] = stable_shake_id("service-health", payload, length=32)
        return payload

    def ollama_inventory(
        self,
        *,
        timeout_seconds: float = 2.0,
        health: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Observe installed Ollama model tags on healthy offline/LAN nodes.

        This is inventory evidence, not authority and not a model pull mechanism.
        Only endpoints already admitted by service_health are queried, with public
        proxy inheritance disabled. A healthy service without a requested model is
        therefore distinguishable from an actually executable model route.
        """
        timeout_value = max(0.2, min(float(timeout_seconds or 2.0), 10.0))
        health_payload = health or self.service_health(service="ollama", timeout_seconds=timeout_value)
        rows: list[dict[str, Any]] = []
        with httpx.Client(timeout=httpx.Timeout(timeout_value, connect=min(timeout_value, 2.0)), trust_env=False) as client:
            for observed in health_payload.get("observations") or []:
                if not isinstance(observed, dict) or str(observed.get("service") or "") != "ollama":
                    continue
                node_id = str(observed.get("node_id") or "unknown")
                endpoint = self._normalize_url(observed.get("endpoint"))
                if observed.get("healthy") is not True or not endpoint:
                    rows.append(
                        {
                            "node_id": node_id,
                            "service": "ollama",
                            "endpoint": endpoint or None,
                            "healthy": False,
                            "inventory_observed": False,
                            "models": [],
                            "model_count": 0,
                            "reason": "service_not_healthy",
                        }
                    )
                    continue
                started = time.perf_counter()
                try:
                    response = client.get(f"{endpoint}/api/tags")
                    latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
                    response.raise_for_status()
                    data = response.json()
                    models = sorted(
                        {
                            str(item.get("name") or item.get("model") or "").strip()
                            for item in (data.get("models") or [])
                            if isinstance(item, dict) and str(item.get("name") or item.get("model") or "").strip()
                        }
                    )
                    rows.append(
                        {
                            "node_id": node_id,
                            "service": "ollama",
                            "endpoint": endpoint,
                            "healthy": True,
                            "inventory_observed": True,
                            "models": models,
                            "model_count": len(models),
                            "latency_ms": latency_ms,
                            "status_code": int(response.status_code),
                        }
                    )
                except Exception as exc:
                    rows.append(
                        {
                            "node_id": node_id,
                            "service": "ollama",
                            "endpoint": endpoint,
                            "healthy": True,
                            "inventory_observed": False,
                            "models": [],
                            "model_count": 0,
                            "latency_ms": round((time.perf_counter() - started) * 1000.0, 2),
                            "error": exc.__class__.__name__,
                            "reason": "inventory_probe_failed",
                        }
                    )
        payload = {
            "schema_version": "xavi-ollama-inventory-v1",
            "offline_only": True,
            "observed_at_ms": int(time.time() * 1000),
            "service_health_digest": health_payload.get("observation_digest"),
            "node_count": len(rows),
            "inventory_observed_count": sum(1 for row in rows if row.get("inventory_observed")),
            "observations": rows,
        }
        payload["observation_digest"] = stable_shake_id("ollama-inventory", payload, length=32)
        return payload

    @staticmethod
    def _clamp01(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(number, 1.0))

    def node_pressure(
        self,
        *,
        node_id: str | None = None,
        timeout_seconds: float = 1.5,
    ) -> dict[str, Any]:
        """Observe current compute pressure without granting scheduling authority.

        Host telemetry is accepted only from configured backend-LAN node-metrics
        endpoints. Ollama process pressure is observed independently through
        /api/ps. Missing observations reduce confidence; they never imply an idle
        node, commission a node, or override service/model availability gates.
        """
        wanted_node = str(node_id or "").strip()
        timeout_value = max(0.2, min(float(timeout_seconds or 1.5), 5.0))
        network = self._backend_network()
        observations: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        weights = {
            "cpu": 0.25,
            "memory": 0.20,
            "gpu_utilization": 0.20,
            "vram": 0.15,
            "ollama_loaded_models": 0.08,
            "ollama_vram": 0.12,
        }

        with httpx.Client(timeout=httpx.Timeout(timeout_value, connect=min(timeout_value, 1.5)), trust_env=False) as client:
            for node in self.nodes():
                current_node = str(node.get("id") or "unknown")
                if wanted_node and current_node != wanted_node:
                    continue
                if str(node.get("status") or "") != "commissioned" or not bool(node.get("scheduler_eligible")):
                    skipped.append({"node_id": current_node, "reason": "not_scheduler_ready", "status": node.get("status")})
                    continue

                capacity = node.get("capacity") if isinstance(node.get("capacity"), dict) else {}
                components: dict[str, float] = {}
                sources: list[str] = []
                host_metrics: dict[str, Any] = {"observed": False}
                ollama_process: dict[str, Any] = {"observed": False}

                metrics = node.get("metrics") if isinstance(node.get("metrics"), dict) else {}
                metrics_url = self._normalize_url(metrics.get("primary_url") or metrics.get("url"))
                if metrics_url and not bool(metrics.get("internet_required", False)):
                    allowed = False
                    try:
                        parsed = urlparse(metrics_url)
                        host = parsed.hostname or ""
                        address = ipaddress.ip_address(host)
                        allowed = parsed.scheme in {"http", "https"} and network is not None and address in network
                    except ValueError:
                        allowed = False
                    if allowed:
                        started = time.perf_counter()
                        try:
                            response = client.get(f"{metrics_url}/v1/metrics")
                            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
                            response.raise_for_status()
                            data = response.json()
                            if str(data.get("schema_version") or "") != "xavi-node-metrics-v1":
                                raise ValueError("unexpected_metrics_schema")
                            if str(data.get("node_id") or "") != current_node:
                                raise ValueError("metrics_node_mismatch")
                            cpu = data.get("cpu") if isinstance(data.get("cpu"), dict) else {}
                            memory = data.get("memory") if isinstance(data.get("memory"), dict) else {}
                            gpus = data.get("gpus") if isinstance(data.get("gpus"), list) else []
                            components["cpu"] = self._clamp01(cpu.get("load1_per_thread"))
                            components["memory"] = self._clamp01(memory.get("used_ratio"))
                            gpu_utils = [self._clamp01(float(g.get("utilization_gpu_percent") or 0.0) / 100.0) for g in gpus if isinstance(g, dict)]
                            vram = [
                                self._clamp01(float(g.get("memory_used_mib") or 0.0) / max(float(g.get("memory_total_mib") or 0.0), 1.0))
                                for g in gpus if isinstance(g, dict) and float(g.get("memory_total_mib") or 0.0) > 0.0
                            ]
                            if gpu_utils:
                                components["gpu_utilization"] = max(gpu_utils)
                            if vram:
                                components["vram"] = max(vram)
                            host_metrics = {
                                "observed": True,
                                "endpoint": metrics_url,
                                "latency_ms": latency_ms,
                                "cpu": cpu,
                                "memory": memory,
                                "gpus": gpus,
                                "observed_at_ms": data.get("observed_at_ms"),
                            }
                            sources.append("xavi-node-metrics")
                        except Exception as exc:
                            host_metrics = {
                                "observed": False,
                                "endpoint": metrics_url,
                                "error": exc.__class__.__name__,
                                "latency_ms": round((time.perf_counter() - started) * 1000.0, 2),
                            }
                    else:
                        host_metrics = {"observed": False, "endpoint": metrics_url, "reason": "metrics_endpoint_not_backend_lan"}

                services = node.get("services") if isinstance(node.get("services"), dict) else {}
                ollama = services.get("ollama") if isinstance(services.get("ollama"), dict) else None
                if ollama is not None and not bool(ollama.get("internet_required", False)):
                    attempts: list[dict[str, Any]] = []
                    for endpoint in self._probe_endpoints(node, ollama):
                        started = time.perf_counter()
                        try:
                            response = client.get(f"{endpoint}/api/ps")
                            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
                            response.raise_for_status()
                            data = response.json()
                            models = [item for item in (data.get("models") or []) if isinstance(item, dict)]
                            total_vram_bytes = sum(max(int(item.get("size_vram") or 0), 0) for item in models)
                            configured_gpu_bytes = int(sum(
                                float(gpu.get("memory_mib") or 0.0) * 1024 * 1024
                                for gpu in (capacity.get("gpus") or []) if isinstance(gpu, dict)
                            ))
                            components["ollama_loaded_models"] = self._clamp01(len(models) / 4.0)
                            components["ollama_vram"] = self._clamp01(total_vram_bytes / max(configured_gpu_bytes, 1)) if configured_gpu_bytes else 0.0
                            ollama_process = {
                                "observed": True,
                                "endpoint": endpoint,
                                "latency_ms": latency_ms,
                                "loaded_model_count": len(models),
                                "resident_bytes": sum(max(int(item.get("size") or 0), 0) for item in models),
                                "resident_vram_bytes": total_vram_bytes,
                            }
                            sources.append("ollama-api-ps")
                            break
                        except Exception as exc:
                            attempts.append({"endpoint": endpoint, "error": exc.__class__.__name__, "latency_ms": round((time.perf_counter() - started) * 1000.0, 2)})
                    if not ollama_process.get("observed") and attempts:
                        ollama_process = {"observed": False, "attempts": attempts}

                observed_weight = sum(weights[name] for name in components)
                weighted = sum(components[name] * weights[name] for name in components)
                pressure = self._clamp01(weighted / observed_weight) if observed_weight else 0.0
                row = {
                    "node_id": current_node,
                    "observed": bool(components),
                    "pressure": round(pressure, 6),
                    "confidence": round(min(observed_weight, 1.0), 6),
                    "components": {name: round(value, 6) for name, value in components.items()},
                    "sources": sources,
                    "host_metrics": host_metrics,
                    "ollama_process": ollama_process,
                    "transport": (node.get("transport") or {}).get("kind"),
                    "internet_required": False,
                }
                row["observation_digest"] = stable_shake_id("node-pressure-observation", row, length=32)
                observations.append(row)

        payload = {
            "schema_version": "xavi-node-pressure-v1",
            "offline_only": True,
            "authority": "observation-only",
            "observed_at_ms": int(time.time() * 1000),
            "node_count": len(observations),
            "observed_count": sum(1 for row in observations if row.get("observed")),
            "observations": observations,
            "skipped": skipped,
        }
        payload["observation_digest"] = stable_shake_id("node-pressure", payload, length=32)
        return payload

    def scheduler_candidates(
        self,
        *,
        node_id: str | None = None,
        role: str | None = None,
        service: str | None = None,
        prefer_gpu: bool = False,
        minimum_memory_gib: float = 0.0,
        require_live: bool = False,
        live_timeout_seconds: float = 2.0,
        observe_pressure: bool = False,
        pressure_timeout_seconds: float = 1.5,
        limit: int = 8,
    ) -> dict[str, Any]:
        """Return static, offline scheduler candidates from commissioned LAN state.

        This intentionally does not claim that a node is healthy merely because
        it is configured. Dynamic load/liveness is a separate observer. The
        scheduler gate here answers the narrower question: which nodes are
        commissioned and eligible to be considered without public Internet?
        """
        wanted_node_id = str(node_id or "").strip()
        wanted_role = str(role or "").strip()
        wanted_service = str(service or "").strip()
        minimum_bytes = max(float(minimum_memory_gib or 0.0), 0.0) * (1024 ** 3)
        max_results = max(1, min(int(limit), 64))
        candidates: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []

        for node in self.nodes():
            node_id = str(node.get("id") or "unknown")
            roles = [str(item) for item in (node.get("roles") or [])]
            services = node.get("services") if isinstance(node.get("services"), dict) else {}
            capacity = node.get("capacity") if isinstance(node.get("capacity"), dict) else {}
            transport = node.get("transport") if isinstance(node.get("transport"), dict) else {}
            reasons: list[str] = []
            if wanted_node_id and node_id != wanted_node_id:
                reasons.append("different_node")
            if str(node.get("status") or "") != "commissioned":
                reasons.append("not_commissioned")
            if not bool(node.get("scheduler_eligible")):
                reasons.append("scheduler_ineligible")
            if wanted_role and wanted_role not in roles:
                reasons.append("missing_role")
            if wanted_service and wanted_service not in services:
                reasons.append("missing_service")

            memory_bytes = float(capacity.get("memory_bytes") or 0.0)
            memory_gib_up_to = float(capacity.get("memory_gib_up_to") or 0.0)
            effective_memory_bytes = memory_bytes or (memory_gib_up_to * (1024 ** 3))
            if minimum_bytes and effective_memory_bytes < minimum_bytes:
                reasons.append("insufficient_memory")

            if reasons:
                excluded.append({"node_id": node_id, "reasons": reasons, "status": node.get("status")})
                continue

            gpus = capacity.get("gpus") if isinstance(capacity.get("gpus"), list) else []
            gpu_memory_mib = sum(
                float(gpu.get("memory_mib") or 0.0)
                for gpu in gpus
                if isinstance(gpu, dict)
            )
            logical_threads = float(capacity.get("logical_cpu_threads") or capacity.get("cpu_threads_up_to") or 0.0)
            score = 20.0
            if wanted_role:
                score += 30.0
            if wanted_service:
                score += 24.0
            if transport.get("internet_required") is False:
                score += 12.0
            if gpus:
                score += 18.0
                if prefer_gpu:
                    score += 20.0
                    score += min(gpu_memory_mib / 512.0, 20.0)
            elif prefer_gpu:
                score -= 20.0
            if "preferred-accelerator" in roles:
                score += 15.0
            score += min(logical_threads / 4.0, 20.0)
            if effective_memory_bytes:
                score += min(effective_memory_bytes / float(8 * (1024 ** 3)), 16.0)

            service_record = services.get(wanted_service) if wanted_service else None
            preferred_endpoints = self._probe_endpoints(node, service_record) if isinstance(service_record, dict) else []
            host_endpoint = self._normalize_url((service_record or {}).get("primary_url")) if isinstance(service_record, dict) else ""
            service_endpoint = preferred_endpoints[0] if preferred_endpoints else (host_endpoint or None)
            candidates.append(
                {
                    "node_id": node_id,
                    "score": round(score, 2),
                    "status": node.get("status"),
                    "roles": roles,
                    "transport": transport.get("kind"),
                    "private_ipv4": transport.get("private_ipv4"),
                    "internet_required": bool(transport.get("internet_required", False)),
                    "capacity": capacity,
                    "service": wanted_service or None,
                    "service_endpoint": service_endpoint,
                    "service_host_endpoint": host_endpoint or None,
                    "service_endpoint_scope": "runtime-internal" if service_endpoint and service_endpoint != host_endpoint else ("host-or-lan" if service_endpoint else None),
                }
            )

        live_observation: dict[str, Any] | None = None
        if require_live:
            if not wanted_service:
                for row in candidates:
                    excluded.append({
                        "node_id": row.get("node_id"),
                        "reasons": ["live_probe_requires_service"],
                        "status": row.get("status"),
                    })
                candidates = []
            else:
                live_observation = self.service_health(
                    node_id=wanted_node_id or None,
                    service=wanted_service,
                    timeout_seconds=live_timeout_seconds,
                )
                health_by_node = {
                    str(row.get("node_id") or ""): row
                    for row in live_observation.get("observations") or []
                    if isinstance(row, dict)
                }
                live_candidates: list[dict[str, Any]] = []
                for row in candidates:
                    current_node = str(row.get("node_id") or "")
                    health = health_by_node.get(current_node)
                    if health is None or not bool(health.get("healthy")):
                        excluded.append({
                            "node_id": current_node,
                            "reasons": ["service_unhealthy_or_unobserved"],
                            "status": row.get("status"),
                            "live_health": health,
                        })
                        continue
                    row = dict(row)
                    row["live_health"] = health
                    observed_endpoint = self._normalize_url(health.get("endpoint"))
                    if observed_endpoint:
                        row["service_endpoint"] = observed_endpoint
                        row["service_endpoint_scope"] = "observed-live"
                    row["score"] = round(float(row.get("score") or 0.0) + 10.0, 2)
                    live_candidates.append(row)
                candidates = live_candidates

        pressure_observation: dict[str, Any] | None = None
        if observe_pressure and candidates:
            pressure_observation = self.node_pressure(
                node_id=wanted_node_id or None,
                timeout_seconds=pressure_timeout_seconds,
            )
            pressure_by_node = {
                str(item.get("node_id") or ""): item
                for item in pressure_observation.get("observations") or []
                if isinstance(item, dict)
            }
            for row in candidates:
                current_node = str(row.get("node_id") or "")
                observation = pressure_by_node.get(current_node)
                row["base_score"] = round(float(row.get("score") or 0.0), 2)
                if observation is None or not bool(observation.get("observed")):
                    row["pressure_observed"] = False
                    row["pressure_penalty"] = 0.0
                    continue
                pressure_value = self._clamp01(observation.get("pressure"))
                penalty = round(35.0 * pressure_value, 2)
                row["pressure_observed"] = True
                row["pressure"] = pressure_value
                row["pressure_confidence"] = self._clamp01(observation.get("confidence"))
                row["pressure_penalty"] = penalty
                row["pressure_observation_digest"] = observation.get("observation_digest")
                row["score"] = round(float(row.get("score") or 0.0) - penalty, 2)

        candidates.sort(key=lambda row: (-float(row.get("score") or 0.0), str(row.get("node_id") or "")))
        return {
            "schema_version": "xavi-service-candidates-v1",
            "offline_only": True,
            "filters": {
                "node_id": wanted_node_id or None,
                "role": wanted_role or None,
                "service": wanted_service or None,
                "prefer_gpu": bool(prefer_gpu),
                "minimum_memory_gib": float(minimum_memory_gib or 0.0),
                "require_live": bool(require_live),
                "live_timeout_seconds": float(live_timeout_seconds or 2.0),
                "observe_pressure": bool(observe_pressure),
                "pressure_timeout_seconds": float(pressure_timeout_seconds or 1.5),
            },
            "count": min(len(candidates), max_results),
            "candidates": candidates[:max_results],
            "excluded": excluded,
            "live_observation": live_observation,
            "pressure_observation": pressure_observation,
        }

    def validate(self) -> list[str]:
        warnings = list(self.data.get("warnings") or [])
        network = self._backend_network()
        for node in self.nodes():
            node_id = str(node.get("id") or "unknown")
            transport = node.get("transport") or {}
            private = str(transport.get("private_ipv4") or "").strip()
            if bool(node.get("scheduler_eligible")) and str(node.get("status") or "") != "commissioned":
                warnings.append(f"scheduler_node_not_commissioned:{node_id}")
            if private and network is not None:
                try:
                    address = ipaddress.ip_interface(private).ip
                    if address not in network:
                        warnings.append(f"private_address_outside_backend_cidr:{node_id}:{private}")
                except ValueError:
                    warnings.append(f"invalid_private_address:{node_id}:{private}")
            for service_name, service in (node.get("services") or {}).items():
                if not isinstance(service, dict):
                    continue
                endpoint = self._normalize_url(service.get("primary_url") or service.get("url") or service.get("endpoint"))
                if not endpoint:
                    continue
                try:
                    host = urlparse(endpoint).hostname
                    if host and network is not None:
                        ip = ipaddress.ip_address(host)
                        if bool(service.get("lan_preferred", True)) and ip not in network:
                            warnings.append(f"lan_service_outside_backend_cidr:{node_id}:{service_name}:{host}")
                except ValueError:
                    # Named local/container endpoints are valid but cannot be CIDR checked.
                    pass
        return warnings

    def report(self) -> dict[str, Any]:
        nodes = self.nodes()
        scheduler_nodes = [row for row in nodes if row.get("scheduler_eligible")]
        return {
            "schema_version": "xavi-service-registry-report-v1",
            "registry_schema": self.data.get("schema_version"),
            "registry_digest": stable_shake_id("service-registry", self.data, length=32),
            "offline_only": True,
            "network": dict(self.data.get("network") or {}),
            "node_count": len(nodes),
            "scheduler_ready_count": len(scheduler_nodes),
            "nodes": nodes,
            "warnings": self.validate(),
        }
