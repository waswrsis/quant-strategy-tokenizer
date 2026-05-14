"""Canonical JSON bytes for P3a-0 lock files."""

from __future__ import annotations

import hashlib
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


def canonical_lock_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for a lock-compatible value."""

    canonical = _canonicalize_value(value, depth=0)
    return json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    """Return a qst-standard sha256 hash string for raw bytes."""

    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def hash_json_value(value: Any) -> str:
    """Return the sha256 hash for canonical JSON bytes of ``value``."""

    return sha256_bytes(canonical_lock_bytes(value))
