"""
quant_strategy_tokenizer.filters.history_filter
===============================================
Module purpose: reject candidates without enough caller-supplied historical data coverage.
Core idea: Compare per-symbol history counts or durations against a minimum threshold. Assumes data availability is measured upstream and insufficient or missing history should not be treated as tradable by default.
Inputs: candidate rows, history_by_symbol mapping, minimum history params, and ModuleRunContext.
Outputs: HistoryFilterReport with accepted rows, rejected rows, and reason counts.
Failure semantics: missing history rejects rows when required; unusable candidate input fails the request.
Market generalization: history units are caller-defined and can represent bars, days, samples, or vendor coverage scores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ..contracts import ModuleEvent, ModuleResult, ModuleRunContext
from ..reporting import write_module_report
from ..row_utils import coerce_row, finite_float


@dataclass
class HistoryFilterParams:
    """Minimum data availability policy.

    Configuration:
    - `minimum`: optional numeric threshold in caller-defined units such as
      bars, days, sessions, or ticks. `None` only requires a non-missing value.
    - `fail_closed`: when True, missing history state rejects the candidate.
    """

    minimum: Optional[float] = None
    fail_closed: bool = True


@dataclass
class HistoryFilterRequest:
    candidates: Iterable[Any]
    history_by_symbol: Mapping[str, Any]
    params: HistoryFilterParams = field(default_factory=HistoryFilterParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="history_filter"))


@dataclass
class HistoryFilterReport:
    accepted: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: HistoryFilterRequest) -> ModuleResult[HistoryFilterReport]:
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item)
        sym = str(row.get("symbol") or "")
        if sym not in request.history_by_symbol:
            target = rejected if request.params.fail_closed else accepted
            row.update({"accepted": not request.params.fail_closed, "reason": "history_unknown"})
            target.append(row)
            continue
        val = request.history_by_symbol.get(sym)
        if isinstance(val, bool):
            ok = bool(val)
        elif request.params.minimum is None:
            ok = val is not None
        else:
            numeric = finite_float(val)
            minimum = finite_float(request.params.minimum)
            if numeric is None or minimum is None:
                target = rejected if request.params.fail_closed else accepted
                row.update({"accepted": not request.params.fail_closed, "history": val, "reason": "history_invalid"})
                target.append(row)
                continue
            ok = numeric >= minimum
        row.update({"accepted": ok, "history": val, "reason": "" if ok else "history_insufficient"})
        (accepted if ok else rejected).append(row)
    report = HistoryFilterReport(accepted=accepted, rejected=rejected, summary={"accepted": len(accepted), "rejected": len(rejected), "minimum": request.params.minimum})
    result = ModuleResult.success(report, events=[ModuleEvent(event="history_filter.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("history_filter", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["HistoryFilterParams", "HistoryFilterRequest", "HistoryFilterReport", "run"]
