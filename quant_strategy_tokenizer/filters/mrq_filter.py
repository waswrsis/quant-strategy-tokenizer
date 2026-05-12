"""
quant_strategy_tokenizer.filters.mrq_filter
===========================================
Module purpose: apply precomputed MRQ touch/pass-fail diagnostics to candidate rows.
Core idea: Consume MRQ decisions from an external indicator step and reject candidates with failing or unavailable MRQ state. Assumes MRQ calculation is separate and this filter only enforces its output policy.
Inputs: candidate rows, mrq state by symbol, fail-closed params, and ModuleRunContext.
Outputs: MRQFilterReport with accepted rows, rejected rows, and MRQ reason counts.
Failure semantics: missing MRQ state rejects rows when fail_closed is enabled; unusable candidate input fails the request.
Market generalization: MRQ labels are caller-defined and not tied to a specific venue or instrument type.
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
