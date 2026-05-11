"""
quant_strategy_tokenizer.filters.cooldown_filter
========================================
Module purpose: reject candidates that are still inside a caller-supplied
cooldown window.
Core idea: cooldown state is external; this module only compares current time
with per-symbol until timestamps.
Inputs: candidates, cooldown_until_by_symbol epoch seconds, and current now_ts.
Outputs: accepted/rejected rows with remaining seconds.
Failure semantics: missing cooldown means accepted; invalid timestamps reject
only when fail_closed is True.
Market generalization: works for any symbol namespace and any cooldown reason.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ..contracts import ModuleEvent, ModuleResult, ModuleRunContext
from ..reporting import write_module_report
from ..row_utils import coerce_row, finite_float


@dataclass
class CooldownFilterParams:
    """Invalid cooldown timestamp policy.

    Configuration:
    - `fail_closed_on_invalid`: when True, malformed cooldown timestamps reject
      the candidate; when False, malformed timestamps are ignored.
    """

    fail_closed_on_invalid: bool = True


@dataclass
class CooldownFilterRequest:
    candidates: Iterable[Any]
    cooldown_until_by_symbol: Mapping[str, Any]
    now_ts: Optional[float] = None
    params: CooldownFilterParams = field(default_factory=CooldownFilterParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="cooldown_filter"))


@dataclass
class CooldownFilterReport:
    accepted: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: CooldownFilterRequest) -> ModuleResult[CooldownFilterReport]:
    now = finite_float(request.now_ts if request.now_ts is not None else time.time())
    if now is None:
        return ModuleResult.fail("invalid_parameter", "now_ts must be a finite number", field="now_ts")
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item)
        sym = str(row.get("symbol") or "")
        raw_until = request.cooldown_until_by_symbol.get(sym, 0.0)
        until = finite_float(raw_until or 0.0)
        if until is None:
            row.update({"accepted": not request.params.fail_closed_on_invalid, "reason": "cooldown_invalid", "cooldown_until": raw_until})
            (rejected if request.params.fail_closed_on_invalid else accepted).append(row)
            continue
        if now < until:
            row.update({"accepted": False, "reason": "cooldown_active", "cooldown_until": until, "remaining_sec": until - now})
            rejected.append(row)
        else:
            row.update({"accepted": True, "reason": "", "cooldown_until": until})
            accepted.append(row)
    report = CooldownFilterReport(accepted=accepted, rejected=rejected, summary={"accepted": len(accepted), "rejected": len(rejected), "now_ts": now})
    result = ModuleResult.success(report, events=[ModuleEvent(event="cooldown_filter.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("cooldown_filter", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["CooldownFilterParams", "CooldownFilterRequest", "CooldownFilterReport", "run"]
