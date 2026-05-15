"""Validation shim for the qst-ir/0.4 WP1 shell."""

from __future__ import annotations

from quant_strategy_tokenizer.ir_v04.schema import StrategyIRV04


def validate_ir_v04(ir: StrategyIRV04) -> list[str]:
    """Return validation issues for a qst-ir/0.4 shell.

    WP1 validation is model-level only. A successfully constructed
    ``StrategyIRV04`` has no additional semantic checks yet.
    """

    _ = ir
    return []
