"""
quant_strategy_tokenizer.filters.vwap_filter
============================================
Module purpose: apply precomputed VWAP pause/pass-fail state to candidate rows.
Core idea: Consume external VWAP diagnostics and reject symbols that are paused, too far from VWAP, or missing required state. Assumes VWAP calculation is handled by indicators.vwap or another upstream module.
Inputs: candidate rows, VWAP state by symbol, fail-closed params, and ModuleRunContext.
Outputs: VWAPFilterReport with accepted rows, rejected rows, and VWAP reason counts.
Failure semantics: missing VWAP state rejects rows when fail_closed is enabled; unusable candidate input fails the request.
Market generalization: VWAP state is caller-provided and can be computed from any market with price and volume data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ..contracts import ModuleEvent, ModuleResult, ModuleRunContext
from ..reporting import write_module_report
from ..row_utils import coerce_row


@dataclass
class VWAPFilterParams:
    """Policy for supplied VWAP diagnostics.

    Configuration:
    - `max_abs_deviation`: optional maximum absolute deviation from VWAP; `None`
      disables deviation filtering.
    - `max_no_touch_run`: optional maximum consecutive no-touch count; `None`
      disables no-touch filtering.
    - `fail_closed`: when True, missing VWAP diagnostics reject the candidate.
    """

    max_abs_deviation: Optional[float] = None
    max_no_touch_run: Optional[int] = None
    fail_closed: bool = True


@dataclass
class VWAPFilterRequest:
    candidates: Iterable[Any]
    vwap_by_symbol: Mapping[str, Mapping[str, Any]]
    params: VWAPFilterParams = field(default_factory=VWAPFilterParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="vwap_filter"))


@dataclass
class VWAPFilterReport:
    accepted: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: VWAPFilterRequest) -> ModuleResult[VWAPFilterReport]:
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item)
        sym = str(row.get("symbol") or "")
        diag = request.vwap_by_symbol.get(sym)
        if diag is None:
            row.update({"accepted": not request.params.fail_closed, "reason": "vwap_unknown"})
            (rejected if request.params.fail_closed else accepted).append(row)
            continue
        reasons: List[str] = []
        dev = _float_or_none(diag.get("last_deviation"))
        if request.params.max_abs_deviation is not None:
            if dev is None:
                if request.params.fail_closed:
                    reasons.append("vwap_deviation_unknown")
            elif abs(dev) > float(request.params.max_abs_deviation):
                reasons.append("vwap_deviation_too_large")
        nt = _float_or_none(diag.get("no_touch_run"))
        if request.params.max_no_touch_run is not None:
            if nt is None:
                if request.params.fail_closed:
                    reasons.append("vwap_no_touch_unknown")
            elif nt > int(request.params.max_no_touch_run):
                reasons.append("vwap_no_touch_run_too_long")
        ok = not reasons
        row.update({"accepted": ok, "reason": ";".join(reasons), "vwap": dict(diag)})
        (accepted if ok else rejected).append(row)
    report = VWAPFilterReport(accepted=accepted, rejected=rejected, summary={"accepted": len(accepted), "rejected": len(rejected)})
    result = ModuleResult.success(report, events=[ModuleEvent(event="vwap_filter.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("vwap_filter", result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _float_or_none(v: Any):
    try:
        return None if v is None else float(v)
    except Exception:
        return None


__all__ = ["VWAPFilterParams", "VWAPFilterRequest", "VWAPFilterReport", "run"]
