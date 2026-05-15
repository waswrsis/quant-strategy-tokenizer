"""Signature hash framework for Token System v2."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.hash_v2.common import hash_v2_payload


def signature_hash_v2(payload: Any | None = None) -> str:
    """Hash token or callable signature material."""

    return hash_v2_payload("signature", {} if payload is None else payload)
