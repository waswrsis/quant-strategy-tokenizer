"""
quant_strategy_tokenizer.market_freeze
======================================
Module purpose: pure broad-market freeze and new-risk blocking decision token.
Core idea: Count caller-supplied instrument returns above and below thresholds, then trigger block_new_risk when one side dominates enough of the sample. Assumes breadth imbalance is a risk regime signal and insufficient breadth should fail closed when configured.
Inputs: rows with returns, symbol field, threshold params, minimum sample params, and ModuleRunContext.
Outputs: MarketFreezeReport with freeze flag, action, direction, ratios, accepted rows, rejected rows, and reason.
Failure semantics: invalid rows are rejected; too few valid rows can return fail-closed decision or explicit failure depending on params.
Market generalization: works for any universe whose members can be represented by interval returns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .contracts import ModuleEvent, ModuleResult, ModuleRunContext
from .reporting import write_module_report
from .row_utils import finite_float


@dataclass
class MarketFreezeParams:
    """Breadth threshold policy for market freeze decisions.

    Configuration:
    - `ratio_threshold`: fraction of same-direction returns required to freeze;
      `None` disables freeze triggering and only reports breadth.
    - `min_symbols`: minimum usable sample count before the result is trusted.
    - `return_field`: input row field containing signed return values.
    - `fail_closed_on_insufficient`: when True, insufficient samples return a
      block-new-risk action instead of allowing risk.
    """

    ratio_threshold: Optional[float] = None
    min_symbols: int = 1
    return_field: str = "return"
    fail_closed_on_insufficient: bool = True


@dataclass
class MarketFreezeRequest:
    rows: Iterable[Mapping[str, Any]]
    params: MarketFreezeParams = field(default_factory=MarketFreezeParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="market_freeze"))


@dataclass
class MarketFreezeReport:
    freeze: bool
    action: str
    direction: str
    up_ratio: float
    down_ratio: float
    sample_count: int
    reason: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: MarketFreezeRequest) -> ModuleResult[MarketFreezeReport]:
    min_symbols = finite_float(request.params.min_symbols)
    if min_symbols is None or int(min_symbols) <= 0:
        return ModuleResult.fail("invalid_parameter", "min_symbols must be a positive integer", field="min_symbols")
    threshold = None
    if request.params.ratio_threshold is not None:
        threshold = finite_float(request.params.ratio_threshold)
        if threshold is None or threshold < 0.0 or threshold > 1.0:
            return ModuleResult.fail("invalid_parameter", "ratio_threshold must be between 0 and 1", field="ratio_threshold")
    vals: List[float] = []
    invalid_rows = 0
    for row in request.rows or []:
        raw = row.get(request.params.return_field, None) if isinstance(row, Mapping) else row
        val = finite_float(raw)
        if val is None:
            invalid_rows += 1
            continue
        vals.append(val)
    n = len(vals)
    if n < int(min_symbols):
        report = MarketFreezeReport(
            freeze=bool(request.params.fail_closed_on_insufficient),
            action="block_new_risk" if request.params.fail_closed_on_insufficient else "allow",
            direction="unknown",
            up_ratio=0.0,
            down_ratio=0.0,
            sample_count=n,
            reason="insufficient_sample",
            summary={"sample_count": n, "min_symbols": int(min_symbols), "invalid_rows": invalid_rows},
        )
        return ModuleResult.success(report, events=[ModuleEvent(event="market_freeze.insufficient_sample", level="WARNING", fields=report.summary)])
    up = sum(1 for v in vals if v > 0)
    down = sum(1 for v in vals if v < 0)
    up_ratio = up / n
    down_ratio = down / n
    direction = "up" if up_ratio >= down_ratio else "down"
    freeze = False if threshold is None else max(up_ratio, down_ratio) >= threshold
    report = MarketFreezeReport(
        freeze=freeze,
        action="block_new_risk" if freeze else "allow",
        direction=direction if freeze else "none",
        up_ratio=float(up_ratio),
        down_ratio=float(down_ratio),
        sample_count=n,
        reason="breadth_threshold" if freeze else "threshold_not_configured" if threshold is None else "",
        summary={"sample_count": n, "threshold": threshold, "invalid_rows": invalid_rows},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="market_freeze.evaluated", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("market_freeze", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["MarketFreezeParams", "MarketFreezeRequest", "MarketFreezeReport", "run"]
