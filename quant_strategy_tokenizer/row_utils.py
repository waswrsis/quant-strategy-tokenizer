"""
quant_strategy_tokenizer.row_utils
==================================
Module purpose: small row-coercion and typed lookup helpers for non-tabular modules.
Core idea: Centralize defensive extraction from mappings, dataclasses, or objects so strategy modules can reject bad rows consistently. Assumes caller data may be imperfect and should be classified rather than silently coerced into false success.
Inputs: dict-like rows, objects with attributes, and scalar values to parse as finite floats or strings.
Outputs: plain dictionaries, optional string values, finite floats, and normalized booleans.
Failure semantics: helpers return None or simple defaults so calling modules can decide whether a row is rejected or the request fails.
Market generalization: row helpers know nothing about instruments or venues and operate on caller-configured field names.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
from typing import Any, Optional


def coerce_row(item: Any, *, symbol_field: str = "symbol") -> dict[str, Any]:
    """Return a dict row without raising for scalar candidate inputs."""

    if isinstance(item, Mapping):
        return dict(item)
    if hasattr(item, "__dict__") and not isinstance(item, (str, bytes)):
        return dict(vars(item))
    return {symbol_field: str(item)}


def finite_float(value: Any) -> Optional[float]:
    """Return a finite float or None for missing/invalid/NaN/inf values."""

    if value is None or value == "":
        return None
    try:
        out = float(value)
    except Exception:
        return None
    if not math.isfinite(out):
        return None
    return out


__all__ = ["coerce_row", "finite_float"]
