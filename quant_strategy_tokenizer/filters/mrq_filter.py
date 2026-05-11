"""
quant_strategy_tokenizer.filters.mrq_filter
===================================
Module purpose: filter candidates using precomputed MRQ touch reports.
Core idea: MRQ calculation is separate; this filter only applies pass/fail
policy to supplied diagnostics.
Inputs: candidates and mrq_by_symbol mapping with passed/touch_count/reason.
Outputs: accepted/rejected rows and summary.
Failure semantics: missing MRQ state rejects when fail_closed is True.
Market generalization: MRQ meaning is caller-defined and can represent any
mean-reversion quality criterion across markets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping

from ..contracts import ModuleEvent, ModuleResult, ModuleRunContext
from ..reporting import write_module_report
from ..row_utils import coerce_row


@dataclass
class MRQFilterParams:
    """Policy for supplied mean-reversion-quality diagnostics.

    Configuration:
    - `fail_closed`: when True, missing MRQ diagnostics reject the candidate.
      The pass/fail definition itself must be computed upstream and supplied in
      `mrq_by_symbol`.
    """

    fail_closed: bool = True


@dataclass
class MRQFilterRequest:
    candidates: Iterable[Any]
    mrq_by_symbol: Mapping[str, Mapping[str, Any]]
    params: MRQFilterParams = field(default_factory=MRQFilterParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="mrq_filter"))


@dataclass
class MRQFilterReport:
    accepted: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: MRQFilterRequest) -> ModuleResult[MRQFilterReport]:
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item)
        sym = str(row.get("symbol") or "")
        diag = request.mrq_by_symbol.get(sym)
        if diag is None:
            row.update({"accepted": not request.params.fail_closed, "reason": "mrq_unknown"})
            (rejected if request.params.fail_closed else accepted).append(row)
            continue
        ok = bool(diag.get("passed", False))
        row.update({"accepted": ok, "reason": "" if ok else str(diag.get("reason") or "mrq_rejected"), "mrq": dict(diag)})
        (accepted if ok else rejected).append(row)
    report = MRQFilterReport(accepted=accepted, rejected=rejected, summary={"accepted": len(accepted), "rejected": len(rejected)})
    result = ModuleResult.success(report, events=[ModuleEvent(event="mrq_filter.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("mrq_filter", result, request.context.output_dir, run_id=request.context.run_id)
    return result


__all__ = ["MRQFilterParams", "MRQFilterRequest", "MRQFilterReport", "run"]
