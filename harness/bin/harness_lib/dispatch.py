"""Implementation dispatch.

Resolves the SUT module to call. Default is `duotronic_ref.api`. Override
via `--impl <module>` (pytest CLI flag added by `conformance/conftest.py`)
or the `DUOTRONIC_IMPL` environment variable.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Callable, Mapping


DEFAULT_IMPL = "duotronic_ref.api"
DEFAULT_META_IMPL = "runtime_ref.api"

RUNTIME_ROOT = Path(__file__).resolve().parent.parent.parent / "runtime"


def _discover_srnn_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "srnn_server"
        if candidate.is_dir():
            return candidate
    return Path(__file__).resolve().parents[3] / "srnn_server"


SRNN_ROOT = _discover_srnn_root()


def _ensure_runtime_path(module_name: str) -> None:
    if not module_name.startswith("runtime_ref"):
        return
    runtime_root = str(RUNTIME_ROOT)
    if runtime_root not in sys.path:
        sys.path.insert(0, runtime_root)


def _ensure_srnn_path(module_name: str) -> None:
    if not module_name.startswith("srnn"):
        return
    srnn_root = str(SRNN_ROOT)
    if srnn_root not in sys.path:
        sys.path.insert(0, srnn_root)


def _ensure_module_path(module_name: str) -> None:
    _ensure_runtime_path(module_name)
    _ensure_srnn_path(module_name)


def resolve_impl_module(name: str | None = None) -> Any:
    if name is None:
        name = os.environ.get("DUOTRONIC_IMPL", DEFAULT_IMPL)
    _ensure_module_path(name)
    return importlib.import_module(name)


def get_run_operation(name: str | None = None) -> Callable[[str, Mapping[str, Any]], dict[str, Any]]:
    mod = resolve_impl_module(name)
    if not hasattr(mod, "run_operation"):
        raise AttributeError(
            f"impl module {mod.__name__} must expose run_operation(op_name, given)"
        )
    return mod.run_operation


def resolve_meta_impl_module(name: str | None = None) -> Any:
    if name is None:
        name = os.environ.get("DUOTRONIC_META_IMPL", DEFAULT_META_IMPL)
    _ensure_module_path(name)
    return importlib.import_module(name)


def get_run_meta_operation(name: str | None = None) -> Callable[[str, Mapping[str, Any]], dict[str, Any]]:
    mod = resolve_meta_impl_module(name)
    if not hasattr(mod, "run_meta_operation"):
        raise AttributeError(
            f"impl module {mod.__name__} must expose run_meta_operation(op_name, given)"
        )
    return mod.run_meta_operation
