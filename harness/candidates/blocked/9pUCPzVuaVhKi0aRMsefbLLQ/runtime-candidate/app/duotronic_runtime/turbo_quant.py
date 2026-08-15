"""
TurboQuant sidecar for Duotronic Runtime v3.

Ported from srnn_server/srnn/turbo_quant.py. This module implements the
CPU-portable SRNN TurboQuant vector sidecar: structured Hadamard rotation,
dimension-aware Lloyd codebooks, mixed precision MSE quantization, QJL residual
sign coding, binary signatures, batch compression, quality metrics, and an
in-memory approximate similarity index.

This is intentionally a sidecar vector/search backend. It does not patch
Ollama or llama.cpp KV-cache kernels. The model orchestrator can still expose
TurboQuant KV policies, but live model-serving use requires a backend that
implements those kernels.
"""

from __future__ import annotations

import base64
import math
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional, Sequence

import numpy as np

SEED = 20250428
QJL_SEED_OFFSET = 10_000
QJL_SCALE = math.sqrt(math.pi / 2.0)
GROUP_ALIGNMENT = 16
CODEBOOK_GRID_POINTS = 8192
CODEBOOK_EPS = 1e-6


@dataclass
class QuantGroupConfig:
    dim: int
    mse_bits: int
    total_bits: int
    indices: np.ndarray


@dataclass
class QuantConfig:
    original_dim: int
    groups: tuple[QuantGroupConfig, QuantGroupConfig]
    outlier_ratio: float
    recipe: str

    @property
    def compressed_bytes(self) -> int:
        total = 0
        for group in self.groups:
            total += ((group.dim * group.mse_bits + 7) // 8) + ((group.dim + 7) // 8) + 4
        return total

    @property
    def compression_ratio(self) -> float:
        return (self.original_dim * 4) / max(self.compressed_bytes, 1)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "original_dim": self.original_dim,
            "recipe": self.recipe,
            "outlier_ratio": self.outlier_ratio,
            "compressed_bytes": self.compressed_bytes,
            "compression_ratio": self.compression_ratio,
            "groups": [
                {
                    "dim": group.dim,
                    "mse_bits": group.mse_bits,
                    "total_bits": group.total_bits,
                    "indices_count": int(group.indices.size),
                }
                for group in self.groups
            ],
        }


GROUP_BITS = {
    "turbo25": (3, 2),
    "turbo35": (4, 3),
}
OUTLIER_RATIOS = {
    "turbo25": 0.25,
    "turbo35": 0.50,
}


def _fwht_pow2(x: np.ndarray) -> np.ndarray:
    size = x.shape[-1]
    out = x.copy().reshape(-1, size)
    block = 1
    while block < size:
        out = out.reshape(out.shape[0], -1, block * 2)
        left = out[..., :block].copy()
        right = out[..., block : 2 * block].copy()
        out[..., :block] = left + right
        out[..., block : 2 * block] = left - right
        out = out.reshape(-1, size)
        block *= 2
    return out.reshape(x.shape)


def _hadamard_block_sizes(dim: int) -> tuple[int, ...]:
    sizes: list[int] = []
    remaining = int(dim)
    while remaining > 0:
        block = 1 << (remaining.bit_length() - 1)
        sizes.append(block)
        remaining -= block
    return tuple(sizes)


@lru_cache(maxsize=128)
def _structured_signs(dim: int, seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    return np.where(rng.randint(0, 2, size=dim) > 0, 1.0, -1.0).astype(np.float32)


def hadamard_transform(x: np.ndarray, signs: np.ndarray, normalized: bool = True, inverse: bool = False) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    outputs: list[np.ndarray] = []
    cursor = 0
    for block_size in _hadamard_block_sizes(x.shape[-1]):
        block = x[..., cursor : cursor + block_size].copy()
        block_signs = signs[cursor : cursor + block_size]
        if inverse:
            block = _fwht_pow2(block)
            block = block * block_signs
        else:
            block = block * block_signs
            block = _fwht_pow2(block)
        if normalized:
            block = block / math.sqrt(block_size)
        outputs.append(block)
        cursor += block_size
    return np.concatenate(outputs, axis=-1)


def mse_transform(x: np.ndarray, dim: int, seed_offset: int = 0) -> np.ndarray:
    return hadamard_transform(x, _structured_signs(dim, SEED + seed_offset + dim), normalized=True, inverse=False)


def mse_inverse_transform(x: np.ndarray, dim: int, seed_offset: int = 0) -> np.ndarray:
    return hadamard_transform(x, _structured_signs(dim, SEED + seed_offset + dim), normalized=True, inverse=True)


def qjl_transform(x: np.ndarray, dim: int, seed_offset: int = 0) -> np.ndarray:
    return hadamard_transform(x, _structured_signs(dim, SEED + QJL_SEED_OFFSET + seed_offset + dim), normalized=False, inverse=False)


def qjl_inverse_transform(x: np.ndarray, dim: int, seed_offset: int = 0) -> np.ndarray:
    return hadamard_transform(x, _structured_signs(dim, SEED + QJL_SEED_OFFSET + seed_offset + dim), normalized=False, inverse=True)


def build_binary_signature(vector: np.ndarray, seed_offset: int = 0, max_bits: Optional[int] = 256) -> np.ndarray:
    arr = np.asarray(vector, dtype=np.float32).ravel()
    if arr.size == 0:
        return np.zeros(0, dtype=np.uint8)
    transformed = mse_transform(arr.reshape(1, -1), arr.size, seed_offset).ravel()
    if max_bits is not None:
        transformed = transformed[: max(8, int(max_bits))]
    return np.packbits((transformed >= 0).astype(np.uint8))


def hamming_distance(signature_a: np.ndarray, signature_b: np.ndarray) -> int:
    if signature_a.size == 0 or signature_b.size == 0:
        return 0
    size = min(signature_a.size, signature_b.size)
    return int(np.unpackbits(np.bitwise_xor(signature_a[:size], signature_b[:size])).sum())


def _beta_coordinate_pdf(x: np.ndarray, dim: int) -> np.ndarray:
    exponent = 0.5 * (dim - 3)
    log_norm = math.lgamma(dim / 2.0) - 0.5 * math.log(math.pi) - math.lgamma((dim - 1) / 2.0)
    base = np.clip(1.0 - x**2, CODEBOOK_EPS, None)
    return np.exp(log_norm + exponent * np.log(base))


@lru_cache(maxsize=64)
def build_codebook(dim: int, bits: int) -> np.ndarray:
    if bits <= 0:
        return np.zeros(1, dtype=np.float32)
    levels = 1 << int(bits)
    grid = np.linspace(-1.0 + CODEBOOK_EPS, 1.0 - CODEBOOK_EPS, CODEBOOK_GRID_POINTS, dtype=np.float64)
    weights = _beta_coordinate_pdf(grid, int(dim))
    centroids = np.linspace(-1.0 + 1.0 / (levels + 1), 1.0 - 1.0 / (levels + 1), levels, dtype=np.float64)
    for _ in range(120):
        bounds = np.empty(levels + 1, dtype=np.float64)
        bounds[0] = -1.0
        bounds[-1] = 1.0
        bounds[1:-1] = 0.5 * (centroids[:-1] + centroids[1:])
        assignments = np.searchsorted(bounds[1:-1], grid)
        masses = np.zeros(levels, dtype=np.float64)
        sums = np.zeros(levels, dtype=np.float64)
        np.add.at(masses, assignments, weights)
        np.add.at(sums, assignments, weights * grid)
        new_centroids = sums / np.maximum(masses, 1e-18)
        if np.max(np.abs(new_centroids - centroids)) < 1e-10:
            centroids = new_centroids
            break
        centroids = new_centroids
    return centroids.astype(np.float32)


def compute_outlier_indices(vectors: np.ndarray, outlier_ratio: float) -> np.ndarray:
    vectors = np.asarray(vectors, dtype=np.float32)
    scores = np.mean(vectors.astype(np.float64) ** 2, axis=0)
    dim = vectors.shape[-1]
    aligned_count = int(round(dim * outlier_ratio / GROUP_ALIGNMENT)) * GROUP_ALIGNMENT
    aligned_count = max(GROUP_ALIGNMENT, min(aligned_count, max(GROUP_ALIGNMENT, dim - GROUP_ALIGNMENT)))
    return np.sort(np.argsort(scores)[-aligned_count:])


def build_quant_config(dim: int, recipe: str = "turbo25", calibration_vectors: Optional[np.ndarray] = None) -> QuantConfig:
    if recipe not in GROUP_BITS:
        raise ValueError(f"unknown TurboQuant recipe: {recipe}")
    outlier_ratio = OUTLIER_RATIOS[recipe]
    high_bits, low_bits = GROUP_BITS[recipe]
    dim = int(dim)
    if calibration_vectors is not None and np.asarray(calibration_vectors).size:
        outlier_idx = compute_outlier_indices(np.asarray(calibration_vectors, dtype=np.float32), outlier_ratio)
    else:
        aligned_count = int(round(dim * outlier_ratio / GROUP_ALIGNMENT)) * GROUP_ALIGNMENT
        aligned_count = max(GROUP_ALIGNMENT, min(aligned_count, max(GROUP_ALIGNMENT, dim - GROUP_ALIGNMENT)))
        outlier_idx = np.arange(aligned_count)
    all_idx = np.arange(dim)
    inlier_mask = np.ones(dim, dtype=bool)
    inlier_mask[outlier_idx] = False
    inlier_idx = all_idx[inlier_mask]
    return QuantConfig(
        original_dim=dim,
        groups=(
            QuantGroupConfig(len(outlier_idx), high_bits - 1, high_bits, outlier_idx.astype(np.int64)),
            QuantGroupConfig(len(inlier_idx), low_bits - 1, low_bits, inlier_idx.astype(np.int64)),
        ),
        outlier_ratio=outlier_ratio,
        recipe=recipe,
    )


def _pack_bits(bits: np.ndarray, n_bits: int) -> np.ndarray:
    if n_bits == 0:
        return np.zeros(0, dtype=np.uint8)
    flat = bits.ravel().astype(np.uint32)
    if n_bits == 1:
        pad = (-len(flat)) % 8
        stream = flat.astype(np.uint8)
        if pad:
            stream = np.concatenate([stream, np.zeros(pad, dtype=np.uint8)])
        return np.packbits(stream, bitorder="little")
    shifts = np.arange(n_bits, dtype=np.uint32)
    bit_stream = ((flat[:, None] >> shifts[None, :]) & 1).astype(np.uint8).ravel()
    pad = (-len(bit_stream)) % 8
    if pad:
        bit_stream = np.concatenate([bit_stream, np.zeros(pad, dtype=np.uint8)])
    return np.packbits(bit_stream, bitorder="little")


def _unpack_bits(packed: np.ndarray, count: int, n_bits: int) -> np.ndarray:
    if n_bits == 0:
        return np.zeros(count, dtype=np.uint8)
    all_bits = np.unpackbits(packed.view(np.uint8), bitorder="little")
    if n_bits == 1:
        return all_bits[:count].astype(np.uint8)
    all_bits = all_bits[: count * n_bits]
    matrix = all_bits.reshape(count, n_bits).astype(np.uint32)
    return (matrix * (1 << np.arange(n_bits, dtype=np.uint32))[None, :]).sum(axis=1).astype(np.uint8)


def quantize_vector(vec: np.ndarray, config: QuantConfig, seed_offset: int = 0) -> bytes:
    vec = np.asarray(vec, dtype=np.float32).ravel()
    if vec.size != config.original_dim:
        raise ValueError(f"vector dim {vec.size} does not match config dim {config.original_dim}")
    parts: list[bytes] = []
    for gi, group in enumerate(config.groups):
        group_vec = vec[group.indices]
        vector_norm = float(np.linalg.norm(group_vec))
        if vector_norm < 1e-12:
            vector_norm = 1e-12
        unit = group_vec / vector_norm
        so = seed_offset + gi * 100
        rotated = mse_transform(unit.reshape(1, -1), group.dim, so).ravel()
        if group.mse_bits > 0:
            centroids = build_codebook(group.dim, group.mse_bits)
            indices = np.argmin(np.abs(rotated[:, None] - centroids[None, :]), axis=1).astype(np.uint8)
            rotated_hat = centroids[indices]
        else:
            indices = np.zeros(group.dim, dtype=np.uint8)
            rotated_hat = np.zeros(group.dim, dtype=np.float32)
        mse_hat = mse_inverse_transform(rotated_hat.reshape(1, -1), group.dim, so).ravel()
        residual = unit - mse_hat
        residual_norm = float(np.linalg.norm(residual))
        qjl_signs = (qjl_transform(residual.reshape(1, -1), group.dim, so).ravel() >= 0).astype(np.uint8)
        parts.append(
            _pack_bits(indices, group.mse_bits).tobytes()
            + _pack_bits(qjl_signs, 1).tobytes()
            + np.float16(vector_norm).tobytes()
            + np.float16(residual_norm).tobytes()
        )
    return b"".join(parts)


def dequantize_vector(data: bytes, config: QuantConfig, seed_offset: int = 0) -> np.ndarray:
    result = np.zeros(config.original_dim, dtype=np.float32)
    cursor = 0
    for gi, group in enumerate(config.groups):
        so = seed_offset + gi * 100
        mse_bytes = (group.dim * group.mse_bits + 7) // 8
        qjl_bytes = (group.dim + 7) // 8
        mse_packed = np.frombuffer(data[cursor : cursor + mse_bytes], dtype=np.uint8)
        cursor += mse_bytes
        indices = _unpack_bits(mse_packed, group.dim, group.mse_bits)
        qjl_packed = np.frombuffer(data[cursor : cursor + qjl_bytes], dtype=np.uint8)
        cursor += qjl_bytes
        qjl_signs = _unpack_bits(qjl_packed, group.dim, 1).astype(np.float32) * 2.0 - 1.0
        vector_norm = np.frombuffer(data[cursor : cursor + 2], dtype=np.float16).astype(np.float32)[0]
        cursor += 2
        residual_norm = np.frombuffer(data[cursor : cursor + 2], dtype=np.float16).astype(np.float32)[0]
        cursor += 2
        if group.mse_bits > 0:
            rotated_hat = build_codebook(group.dim, group.mse_bits)[indices.astype(np.intp)]
        else:
            rotated_hat = np.zeros(group.dim, dtype=np.float32)
        mse_hat = mse_inverse_transform(rotated_hat.reshape(1, -1), group.dim, so).ravel()
        qjl_hat = qjl_inverse_transform(qjl_signs.reshape(1, -1), group.dim, so).ravel() * (QJL_SCALE / group.dim)
        result[group.indices] = (mse_hat + qjl_hat * residual_norm) * vector_norm
    return result


def quantize_batch(vectors: np.ndarray, config: QuantConfig, seed_offset: int = 0) -> list[bytes]:
    return [quantize_vector(v, config, seed_offset) for v in np.asarray(vectors, dtype=np.float32)]


def dequantize_batch(data_list: Sequence[bytes], config: QuantConfig, seed_offset: int = 0) -> np.ndarray:
    return np.stack([dequantize_vector(d, config, seed_offset) for d in data_list])


class QuantizedSimilarityIndex:
    def __init__(self, config: QuantConfig, seed_offset: int = 0) -> None:
        self.config = config
        self.seed_offset = seed_offset
        self._compressed: list[bytes] = []
        self._norms: list[float] = []
        self._ids: list[str] = []

    def add(self, item_id: str | int, vec: np.ndarray) -> None:
        vec = np.asarray(vec, dtype=np.float32).ravel()
        self._compressed.append(quantize_vector(vec, self.config, self.seed_offset))
        self._norms.append(float(np.linalg.norm(vec)))
        self._ids.append(str(item_id))

    def add_precompressed(self, item_id: str | int, compressed: bytes, norm: float) -> None:
        self._compressed.append(bytes(compressed))
        self._norms.append(float(norm))
        self._ids.append(str(item_id))

    def approximate_similarity(self, query_vec: np.ndarray, top_k: int = 20) -> list[tuple[str, float]]:
        if not self._compressed:
            return []
        query_vec = np.asarray(query_vec, dtype=np.float32).ravel()
        query_norm = float(np.linalg.norm(query_vec))
        if query_norm < 1e-12:
            return []
        scores = np.array([
            float(np.dot(query_vec, dequantize_vector(blob, self.config, self.seed_offset)) / max(query_norm * norm, 1e-12))
            for blob, norm in zip(self._compressed, self._norms)
        ], dtype=np.float32)
        k = max(1, min(int(top_k), len(scores)))
        top = np.argsort(scores)[-k:][::-1]
        return [(self._ids[i], float(scores[i])) for i in top]

    def __len__(self) -> int:
        return len(self._compressed)


class TurboQuantEmbeddingAccelerator:
    def __init__(self, dim: int = 384, recipe: str = "turbo25") -> None:
        self.dim = int(dim)
        self.recipe = recipe
        self._config: Optional[QuantConfig] = None
        self._index: Optional[QuantizedSimilarityIndex] = None
        self._calibrated = False

    def calibrate(self, vectors: np.ndarray) -> None:
        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[1] != self.dim:
            raise ValueError(f"calibration vectors must be shaped (N, {self.dim})")
        self._config = build_quant_config(self.dim, self.recipe, vectors if vectors.shape[0] >= 10 else None)
        self._index = QuantizedSimilarityIndex(self._config)
        self._calibrated = True

    @property
    def config(self) -> QuantConfig:
        if self._config is None:
            self._config = build_quant_config(self.dim, self.recipe)
        return self._config

    @property
    def similarity_index(self) -> QuantizedSimilarityIndex:
        if self._index is None:
            self._index = QuantizedSimilarityIndex(self.config)
        return self._index

    def compress(self, vec: np.ndarray) -> bytes:
        return quantize_vector(vec, self.config)

    def decompress(self, data: bytes) -> np.ndarray:
        return dequantize_vector(data, self.config)

    def compress_batch(self, vectors: np.ndarray) -> list[bytes]:
        return quantize_batch(vectors, self.config)

    def decompress_batch(self, data_list: Sequence[bytes]) -> np.ndarray:
        return dequantize_batch(data_list, self.config)

    def measure_quality(self, vectors: np.ndarray, sample_size: int = 100) -> dict[str, Any]:
        vectors = np.asarray(vectors, dtype=np.float32)
        sample = vectors[: min(sample_size, vectors.shape[0])]
        if sample.size == 0:
            raise ValueError("no vectors supplied")
        t0 = time.perf_counter()
        compressed = self.compress_batch(sample)
        t_compress = time.perf_counter() - t0
        t0 = time.perf_counter()
        reconstructed = self.decompress_batch(compressed)
        t_decompress = time.perf_counter() - t0
        mse_per_vec = np.mean((sample - reconstructed) ** 2, axis=1)
        cosine_per_vec = np.array([
            float(np.dot(a, b) / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-12))
            for a, b in zip(sample, reconstructed)
        ])
        total_compressed_bytes = sum(len(c) for c in compressed)
        return {
            "recipe": self.recipe,
            "dim": self.dim,
            "sample_size": int(sample.shape[0]),
            "mse_mean": float(np.mean(mse_per_vec)),
            "mse_p95": float(np.percentile(mse_per_vec, 95)),
            "cosine_mean": float(np.mean(cosine_per_vec)),
            "cosine_min": float(np.min(cosine_per_vec)),
            "compression_ratio": float(sample.nbytes / max(total_compressed_bytes, 1)),
            "bytes_per_vector": float(total_compressed_bytes / max(sample.shape[0], 1)),
            "original_bytes_per_vector": int(sample.shape[1] * 4),
            "compress_vectors_per_sec": float(sample.shape[0] / max(t_compress, 1e-9)),
            "decompress_vectors_per_sec": float(sample.shape[0] / max(t_decompress, 1e-9)),
            "config": self.config.to_public_dict(),
        }


def vector_to_b64(vec: np.ndarray) -> str:
    return base64.b64encode(np.asarray(vec, dtype=np.float32).tobytes()).decode("ascii")


def vector_from_b64(value: str, dim: int | None = None) -> np.ndarray:
    arr = np.frombuffer(base64.b64decode(value), dtype=np.float32).copy()
    if dim is not None and arr.size != dim:
        raise ValueError(f"decoded vector dim {arr.size} does not match expected {dim}")
    return arr


def bytes_to_b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def bytes_from_b64(value: str) -> bytes:
    return base64.b64decode(value)
