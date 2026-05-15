from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .turbo_quant import (
    TurboQuantEmbeddingAccelerator,
    build_binary_signature,
    bytes_from_b64,
    bytes_to_b64,
    hamming_distance,
    vector_from_b64,
    vector_to_b64,
)


@dataclass
class TurboQuantSidecar:
    dim: int = 384
    recipe: str = "turbo25"

    def __post_init__(self) -> None:
        self.accelerator = TurboQuantEmbeddingAccelerator(dim=self.dim, recipe=self.recipe)
        self._index_items: dict[str, dict[str, Any]] = {}

    def status(self) -> dict[str, Any]:
        config = self.accelerator.config
        return {
            "status": "ok",
            "backend": "turboquant_sidecar",
            "dim": self.dim,
            "recipe": self.recipe,
            "capabilities": [
                "vector_compress",
                "vector_decompress",
                "binary_signature",
                "approximate_similarity",
                "quality_measurement",
                "sidecar_retrieval",
            ],
            "kv_cache_kernel": False,
            "notes": "This is the SRNN TurboQuant sidecar backend for vectors/search. It does not patch llama.cpp or Ollama KV kernels.",
            "config": config.to_public_dict(),
            "index_size": len(self._index_items),
        }

    def calibrate(self, vectors: list[list[float]]) -> dict[str, Any]:
        arr = self._matrix(vectors)
        self.accelerator.calibrate(arr)
        return {"calibrated": True, "config": self.accelerator.config.to_public_dict(), "vectors": int(arr.shape[0])}

    def compress(self, vector: list[float]) -> dict[str, Any]:
        arr = self._vector(vector)
        compressed = self.accelerator.compress(arr)
        reconstructed = self.accelerator.decompress(compressed)
        cosine = float(np.dot(arr, reconstructed) / max(np.linalg.norm(arr) * np.linalg.norm(reconstructed), 1e-12))
        return {
            "recipe": self.recipe,
            "dim": self.dim,
            "compressed_b64": bytes_to_b64(compressed),
            "compressed_bytes": len(compressed),
            "original_bytes": int(arr.size * 4),
            "compression_ratio": float((arr.size * 4) / max(len(compressed), 1)),
            "roundtrip_cosine": cosine,
        }

    def decompress(self, compressed_b64: str) -> dict[str, Any]:
        compressed = bytes_from_b64(compressed_b64)
        vec = self.accelerator.decompress(compressed)
        return {"dim": int(vec.size), "vector": vec.astype(float).tolist(), "vector_b64": vector_to_b64(vec)}

    def signature(self, vector: list[float], max_bits: int = 256) -> dict[str, Any]:
        sig = build_binary_signature(self._vector(vector), max_bits=max_bits)
        return {"signature_b64": bytes_to_b64(sig.tobytes()), "signature_bytes": int(sig.size), "max_bits": max_bits}

    def signature_distance(self, a_b64: str, b_b64: str) -> dict[str, Any]:
        a = np.frombuffer(bytes_from_b64(a_b64), dtype=np.uint8)
        b = np.frombuffer(bytes_from_b64(b_b64), dtype=np.uint8)
        return {"hamming_distance": hamming_distance(a, b)}

    def quality(self, vectors: list[list[float]], sample_size: int = 100) -> dict[str, Any]:
        arr = self._matrix(vectors)
        return self.accelerator.measure_quality(arr, sample_size=sample_size)

    def index_add(self, item_id: str, vector: list[float]) -> dict[str, Any]:
        arr = self._vector(vector)
        compressed = self.accelerator.compress(arr)
        self.accelerator.similarity_index.add_precompressed(item_id, compressed, float(np.linalg.norm(arr)))
        self._index_items[item_id] = {"compressed_bytes": len(compressed), "norm": float(np.linalg.norm(arr))}
        return {"added": item_id, "index_size": len(self._index_items), "compressed_bytes": len(compressed)}

    def index_search(self, vector: list[float], top_k: int = 20) -> dict[str, Any]:
        results = self.accelerator.similarity_index.approximate_similarity(self._vector(vector), top_k=top_k)
        return {"top_k": top_k, "results": [{"id": item_id, "score": score} for item_id, score in results]}

    def reset_index(self) -> dict[str, Any]:
        self.accelerator = TurboQuantEmbeddingAccelerator(dim=self.dim, recipe=self.recipe)
        self._index_items.clear()
        return {"reset": True, "index_size": 0}

    def _vector(self, vector: list[float]) -> np.ndarray:
        arr = np.asarray(vector, dtype=np.float32).ravel()
        if arr.size != self.dim:
            raise ValueError(f"vector dim {arr.size} does not match TurboQuant sidecar dim {self.dim}")
        return arr

    def _matrix(self, vectors: list[list[float]]) -> np.ndarray:
        arr = np.asarray(vectors, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError(f"vectors must be shaped (N, {self.dim})")
        return arr
