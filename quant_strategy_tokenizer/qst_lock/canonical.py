"""Canonical JSON bytes for P3a-0 lock files."""

from __future__ import annotations

import hashlib
from typing import Any

from quant_strategy_tokenizer.canonical_json import stable_json_bytes


def canonical_lock_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for a lock-compatible value."""

    return stable_json_bytes(value)


def sha256_bytes(payload: bytes) -> str:
    """Return a qst-standard sha256 hash string for raw bytes."""

    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def hash_json_value(value: Any) -> str:
    """Return the sha256 hash for canonical JSON bytes of ``value``."""

    return sha256_bytes(canonical_lock_bytes(value))
