"""Public canonical JSON serialization.

This module intentionally preserves the byte semantics used by the P3 lock
writer. P4 artifacts and future frame hashes use this public API instead of
importing qst_lock internals.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

MAX_CANONICAL_DEPTH = 8


def _canonicalize_value(value: Any, *, depth: int) -> Any:
    if depth > MAX_CANONICAL_DEPTH:
        raise ValueError(f"canonical JSON depth exceeds {MAX_CANONICAL_DEPTH}")

    if value is None or isinstance(value, str | bool | int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON rejects NaN and Infinity")
        return value

    if isinstance(value, bytes | bytearray | tuple):
        raise TypeError(f"canonical JSON rejects {type(value).__name__}")

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            result[key] = _canonicalize_value(value[key], depth=depth + 1)
        return result

    if isinstance(value, Sequence) and not isinstance(value, str):
        return [_canonicalize_value(item, depth=depth + 1) for item in value]

    raise TypeError(f"canonical JSON rejects {type(value).__name__}")


def stable_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes.

    The output must remain byte-compatible with the P3 canonical lock bytes for
    every value accepted by the P3 implementation.
    """

    canonical = _canonicalize_value(value, depth=0)
    return json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
