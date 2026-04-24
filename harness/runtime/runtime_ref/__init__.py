"""Standalone SRNN-style meta runtime reference package."""

RUNTIME_REF_VERSION = "runtime-ref@v0.1.0"

from .api import run_meta_operation

__all__ = ["RUNTIME_REF_VERSION", "run_meta_operation"]
