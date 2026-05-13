"""Lightweight P0 IR comparison."""

from __future__ import annotations

from dataclasses import dataclass

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import StrategyIR


@dataclass(frozen=True)
class CompareResult:
    """Hash-level comparison result."""

    graph_equal: bool
    param_equal: bool
    instance_equal: bool


def compare_ir(left: StrategyIR, right: StrategyIR) -> CompareResult:
    """Compare two Strategy IR instances by P0 hash layers."""

    left_hashes = compute_hashes(left)
    right_hashes = compute_hashes(right)
    return CompareResult(
        graph_equal=left_hashes.graph_hash == right_hashes.graph_hash,
        param_equal=left_hashes.param_hash == right_hashes.param_hash,
        instance_equal=left_hashes.instance_hash == right_hashes.instance_hash,
    )
