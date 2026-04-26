"""Sandboxed Duotronic WG-RNN research prototype."""

from importlib import import_module
from typing import Any

__all__ = [
    "MemoryBank",
    "MemorySlot",
    "MemoryUpdateRecord",
    "WGRNNCell",
    "WGRNNPolicy",
    "WGRNNReplayIdentity",
    "WitnessFeatureVector",
]


def __getattr__(name: str) -> Any:
    if name == "WGRNNCell":
        return import_module(".cell", __name__).WGRNNCell
    if name in {"MemoryBank", "MemorySlot"}:
        return getattr(import_module(".memory", __name__), name)
    if name == "WGRNNPolicy":
        return import_module(".policy", __name__).WGRNNPolicy
    if name == "MemoryUpdateRecord":
        return import_module(".records", __name__).MemoryUpdateRecord
    if name == "WGRNNReplayIdentity":
        return import_module(".replay", __name__).WGRNNReplayIdentity
    if name == "WitnessFeatureVector":
        return import_module(".witness", __name__).WitnessFeatureVector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
