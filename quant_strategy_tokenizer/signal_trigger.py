"""
quant_strategy_tokenizer.signal_trigger
===============================
Module purpose: turn caller-supplied indicator features into long/short/none
trigger decisions.
Core idea: signal triggering is separate from indicator calculation; this
module consumes caller-supplied price, center, and width fields.
Inputs: feature rows with price, center, width fields; trigger params; optional
output_dir.
Outputs: SignalTriggerReport with per-symbol trigger decisions and reasons.
Failure semantics: missing feature fields reject that row with detailed reason.
Market generalization: "center" and "width" can represent EMA/ATR, moving
average/band, fair value/spread, or any user-defined mean-reversion channel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping

from .contracts import ModuleEvent, ModuleResult, ModuleRunContext
from .reporting import write_module_report
from .row_utils import coerce_row, finite_float


@dataclass
class SignalTriggerParams:
    """Field mapping and band multipliers for trigger generation.

    Configuration:
    - `symbol_field`: row field containing the instrument identifier.
    - `price_field`: current or evaluation price field.
    - `center_field`: caller-supplied fair value/mean/center field.
    - `width_field`: caller-supplied band width or volatility field.
    - `upper_mult`: multiplier applied above center for short triggers.
    - `lower_mult`: multiplier applied below center for long triggers.
    """

    symbol_field: str = "symbol"
    price_field: str = "price"
    center_field: str = "center"
    width_field: str = "width"
    upper_mult: float = 2.0
    lower_mult: float = 2.0


@dataclass
class SignalTriggerRequest:
    rows: Iterable[Mapping[str, Any]]
    params: SignalTriggerParams = field(default_factory=SignalTriggerParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="signal_trigger"))


@dataclass
class SignalTriggerReport:
    signals: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: SignalTriggerRequest) -> ModuleResult[SignalTriggerReport]:
    p = request.params
    signals: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    upper_mult = finite_float(p.upper_mult)
    lower_mult = finite_float(p.lower_mult)
    if upper_mult is None or lower_mult is None:
        return ModuleResult.fail("invalid_parameter", "upper_mult and lower_mult must be finite numbers")
    for item in request.rows or []:
        row = coerce_row(item, symbol_field=p.symbol_field)
        price = finite_float(row.get(p.price_field))
        center = finite_float(row.get(p.center_field))
        width = finite_float(row.get(p.width_field))
        if price is None or center is None or width is None:
            row.update({"trigger": "none", "accepted": False, "reason": "missing_or_invalid_feature"})
            rejected.append(row)
            continue
        upper = center + upper_mult * width
        lower = center - lower_mult * width
        side = "short" if price >= upper else "long" if price <= lower else "none"
        row.update({"trigger": side, "upper": upper, "lower": lower, "distance_from_center": price - center, "accepted": side != "none"})
        (signals if side != "none" else rejected).append(row)
    report = SignalTriggerReport(signals=signals, rejected=rejected, summary={"signals": len(signals), "rejected": len(rejected)})
    result = ModuleResult.success(report, events=[ModuleEvent(event="signal_trigger.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("signal_trigger", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["SignalTriggerParams", "SignalTriggerRequest", "SignalTriggerReport", "run"]
