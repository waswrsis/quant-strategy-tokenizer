"""
quant_strategy_tokenizer.row_utils
==========================
Module purpose: shared defensive helpers for row-oriented modules.
Core idea: reusable strategy blocks should treat imperfect caller inputs as
data-quality issues, not unhandled Python exceptions.
Inputs: arbitrary row-like objects, scalar values, and numeric values.
Configuration: callers do not configure this module directly; row-oriented
modules pass their configured symbol field when coercing raw rows.
Outputs: plain dictionaries, normalized finite floats, and small diagnostics.
Failure semantics: helpers return `None` for invalid numeric values and produce
fallback row dictionaries for scalar rows; policy decisions stay in callers.
Market generalization: helpers do not assume venue, asset class, or symbol
format.
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
