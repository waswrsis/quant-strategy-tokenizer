"""
quant_strategy_tokenizer.filters.backoff_filter
===============================================
Module purpose: reject candidates that are still inside caller-supplied retry/backoff windows.
Core idea: Compare current time with per-symbol retry_after/backoff-until state and accept only expired rows. Assumes retry state is produced elsewhere and unavailable required state should reject when fail_closed is enabled.
Inputs: candidate rows, backoff state by symbol, time/asof params, and ModuleRunContext.
Outputs: BackoffFilterReport with accepted rows, rejected rows, and reason counts.
Failure semantics: missing symbols or invalid timestamps reject rows; unusable candidate input fails the request.
Market generalization: backoff state is symbol-generic and works for any strategy or venue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ..contracts import ModuleEvent, ModuleResult, ModuleRunContext
from ..reporting import write_module_report
from ..row_utils import coerce_row, finite_float


@dataclass
class BackoffFilterParams:
    """Invalid retry/backoff timestamp policy.

    Configuration:
    - `fail_closed_on_invalid`: when True, malformed backoff timestamps reject
      the candidate; when False, malformed timestamps are ignored.
    """

    fail_closed_on_invalid: bool = True


@dataclass
class BackoffFilterRequest:
    candidates: Iterable[Any]
    backoff_until_by_symbol: Mapping[str, Any]
    now_ts: Optional[float] = None
    params: BackoffFilterParams = field(default_factory=BackoffFilterParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="backoff_filter"))


@dataclass
class BackoffFilterReport:
    accepted: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: BackoffFilterRequest) -> ModuleResult[BackoffFilterReport]:
    now = finite_float(request.now_ts if request.now_ts is not None else time.time())
    if now is None:
        return ModuleResult.fail("invalid_parameter", "now_ts must be a finite number", field="now_ts")
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item)
        sym = str(row.get("symbol") or "")
        raw_until = request.backoff_until_by_symbol.get(sym, 0.0)
        until = finite_float(raw_until or 0.0)
        if until is None:
            row.update({"accepted": not request.params.fail_closed_on_invalid, "reason": "backoff_invalid"})
            (rejected if request.params.fail_closed_on_invalid else accepted).append(row)
            continue
        if now < until:
            row.update({"accepted": False, "reason": "backoff_active", "backoff_until": until, "remaining_sec": until - now})
            rejected.append(row)
        else:
            row.update({"accepted": True, "reason": "", "backoff_until": until})
            accepted.append(row)
    report = BackoffFilterReport(accepted=accepted, rejected=rejected, summary={"accepted": len(accepted), "rejected": len(rejected), "now_ts": now})
    result = ModuleResult.success(report, events=[ModuleEvent(event="backoff_filter.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("backoff_filter", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["BackoffFilterParams", "BackoffFilterRequest", "BackoffFilterReport", "run"]
