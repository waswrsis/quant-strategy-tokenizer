"""Graph hash for qst-ir/0.4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quant_strategy_tokenizer.hash_v2.common import hash_v2_payload
from quant_strategy_tokenizer.ir_v04.canonical import canonicalize_v04
from quant_strategy_tokenizer.ir_v04.schema import StrategyIRV04


def graph_hash_v2(ir: StrategyIRV04 | Mapping[str, Any]) -> str:
    """Hash v0.4 graph structure without params or metadata."""

    canonical = canonicalize_v04(ir)
    payload = {
        "ir_version": canonical.ir_version,
        "canonical_version": canonical.canonical_version,
        "strategy": {
            "id": canonical.strategy.id,
            "version": canonical.strategy.version,
            "nodes": [
                {
                    "id": node.id,
                    "token": node.token,
                    "version": node.version,
                    "inputs": node.inputs,
                }
                for node in canonical.strategy.nodes
            ],
            "outputs": canonical.strategy.outputs,
        },
    }
    return hash_v2_payload("graph", payload)
