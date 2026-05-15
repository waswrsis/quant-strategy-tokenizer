"""Token pack hash framework for Token System v2."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.hash_v2.common import hash_v2_payload


def token_pack_hash_v2(payload: Any | None = None) -> str:
    """Hash TokenPack material once WP5 defines it."""

    return hash_v2_payload("token_pack", {} if payload is None else payload)
