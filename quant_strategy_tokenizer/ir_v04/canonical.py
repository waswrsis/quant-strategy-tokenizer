"""Canonicalization for the qst-ir/0.4 shell."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from quant_strategy_tokenizer.canonical_json import stable_json_bytes
from quant_strategy_tokenizer.ir_v04.schema import NodeV04, StrategyBodyV04, StrategyIRV04


def _stable_plain(value: Any) -> Any:
    """Return a JSON-compatible value normalized by the public canonical JSON API."""

    return json.loads(stable_json_bytes(value).decode("utf-8"))


def canonicalize_v04(ir: StrategyIRV04 | Mapping[str, Any]) -> StrategyIRV04:
    """Return the deterministic qst-ir/0.4 canonical shell.

    This function is deliberately independent from the legacy canonicalizer.
    It only sorts and normalizes the minimal v0.4 shell introduced in WP1.
    """

    source = ir if isinstance(ir, StrategyIRV04) else StrategyIRV04.model_validate(ir)

    nodes = [
        NodeV04.model_validate(
            {
                **node.model_dump(mode="json", exclude_none=True),
                "inputs": _stable_plain(node.inputs),
                "params": _stable_plain(node.params),
                "signature": _stable_plain(node.signature.model_dump(mode="json", exclude_none=True)),
                "metadata": _stable_plain(node.metadata),
            }
        )
        for node in sorted(source.strategy.nodes, key=lambda item: item.id)
    ]

    strategy = StrategyBodyV04(
        id=source.strategy.id,
        version=source.strategy.version,
        nodes=nodes,
        outputs=_stable_plain(source.strategy.outputs),
    )

    return StrategyIRV04(
        capabilities=source.capabilities,
        strategy=strategy,
        metadata=_stable_plain(source.metadata),
    )


def canonical_bytes_v04(ir: StrategyIRV04 | Mapping[str, Any]) -> bytes:
    """Return deterministic canonical JSON bytes for qst-ir/0.4."""

    canonical = canonicalize_v04(ir)
    return stable_json_bytes(canonical.model_dump(mode="json"))
