"""P2b-0 strategy diff wrapper."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.ir.compare import compare_ir
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import StrategyIR


class DiffResult(BaseModel):
    """Hash and param diff result for two strategies."""

    model_config = ConfigDict(extra="forbid")

    graph_equal: bool
    param_equal: bool
    instance_equal: bool
    left_hashes: dict[str, str]
    right_hashes: dict[str, str]
    param_diffs: list[dict[str, Any]] = Field(default_factory=list)


def diff_strategies(left: StrategyIR, right: StrategyIR) -> DiffResult:
    compare = compare_ir(left, right)
    return DiffResult(
        graph_equal=compare.graph_equal,
        param_equal=compare.param_equal,
        instance_equal=compare.instance_equal,
        left_hashes=compute_hashes(left).as_dict(),
        right_hashes=compute_hashes(right).as_dict(),
        param_diffs=[
            {"path": diff.path, "left": diff.left, "right": diff.right}
            for diff in compare.param_diffs
        ],
    )
