"""Signature hash framework for Token System v2."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quant_strategy_tokenizer.hash_v2.common import hash_v2_payload
from quant_strategy_tokenizer.ports_v2 import PortSignature


def signature_hash_v2(payload: Any | None = None) -> str:
    """Hash token or callable signature material."""

    return hash_v2_payload("signature", {} if payload is None else payload)


def signature_hash_for_ports_v2(signature: PortSignature | Mapping[str, Any]) -> str:
    """Hash structured v2 PortSignature material."""

    parsed = signature if isinstance(signature, PortSignature) else PortSignature.model_validate(signature)
    return signature_hash_v2(parsed.model_dump(mode="json", exclude_none=True))
