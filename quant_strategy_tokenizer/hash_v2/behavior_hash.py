"""Behavior hash framework for Token System v2."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.hash_v2.common import hash_v2_payload


def behavior_hash_v2(payload: Any | None = None) -> str:
    """Hash behavior material or behavior contract summaries."""

    return hash_v2_payload("behavior", {} if payload is None else payload)
