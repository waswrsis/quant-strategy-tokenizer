"""
quant_strategy_tokenizer.filters.status_filter
======================================
Module purpose: accept candidates whose caller-supplied trading status is OK.
Core idea: status is external data; this module only interprets supplied flags.
Inputs: candidates and status_by_symbol mapping.
Outputs: StatusFilterReport with accepted/rejected rows.
Failure semantics: unknown symbols are rejected when fail_closed is True.
Market generalization: statuses are caller-defined strings/booleans and work
for equities, futures, crypto, or custom venues.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping

from ..contracts import ModuleEvent, ModuleResult, ModuleRunContext
from ..reporting import write_module_report
from ..row_utils import coerce_row


@dataclass
class StatusFilterParams:
    """Accepted status policy.

    Configuration:
    - `accepted_values`: caller-defined status values treated as tradable/OK.
      Defaults to only `True` so venue-specific strings must be explicit.
    - `fail_closed`: when True, missing status rejects the candidate.
    """

    accepted_values: tuple = (True,)
    fail_closed: bool = True


@dataclass
class StatusFilterRequest:
    candidates: Iterable[Any]
    status_by_symbol: Mapping[str, Any]
    params: StatusFilterParams = field(default_factory=StatusFilterParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="status_filter"))


@dataclass
class StatusFilterReport:
    accepted: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: StatusFilterRequest) -> ModuleResult[StatusFilterReport]:
    accepted_values = {_norm_status(x) for x in request.params.accepted_values}
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item)
        sym = str(row.get("symbol") or "")
        if sym not in request.status_by_symbol:
            if request.params.fail_closed:
                row.update({"accepted": False, "reason": "status_unknown"})
                rejected.append(row)
            else:
                row.update({"accepted": True, "reason": "status_unknown_allowed"})
                accepted.append(row)
            continue
        status = request.status_by_symbol.get(sym)
        if _norm_status(status) in accepted_values:
            row.update({"accepted": True, "reason": "", "status": status})
            accepted.append(row)
        else:
            row.update({"accepted": False, "reason": "status_not_accepted", "status": status})
            rejected.append(row)
    report = StatusFilterReport(accepted=accepted, rejected=rejected, summary={"accepted": len(accepted), "rejected": len(rejected)})
    result = ModuleResult.success(report, events=[ModuleEvent(event="status_filter.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("status_filter", result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _norm_status(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value).strip().upper()


__all__ = ["StatusFilterParams", "StatusFilterRequest", "StatusFilterReport", "run"]
