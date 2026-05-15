"""Implementation reference hash framework for Token System v2."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.hash_v2.common import hash_v2_payload


def implementation_ref_hash_v2(payload: Any | None = None) -> str:
    """Hash implementation reference material for custom token runtimes."""

    return hash_v2_payload("implementation_ref", {} if payload is None else payload)
