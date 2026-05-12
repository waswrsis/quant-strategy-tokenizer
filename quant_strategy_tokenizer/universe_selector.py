"""
quant_strategy_tokenizer.universe_selector
==========================================
Module purpose: select a tradable or research universe from caller-provided candidate snapshots.
Core idea: Filter candidates by blacklist, status, history availability, and optional ranking field, then return selected and rejected rows. Assumes universe construction should be fail-closed when required metadata is missing and should never silently fall back to a default symbol.
Inputs: candidate rows, blacklist, status_by_symbol, history_by_symbol, selection params, and ModuleRunContext.
Outputs: UniverseReport with selected rows, rejected rows, selected symbols, and reason counts.
Failure semantics: bad candidate rows are rejected; missing required metadata rejects rows when configured; unusable candidates fail the request.
Market generalization: selection operates on generic rows and symbols with caller-defined status and history semantics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .contracts import ModuleEvent, ModuleResult, ModuleRunContext
from .reporting import write_module_report
from .row_utils import coerce_row, finite_float


@dataclass
class UniverseSelectorParams:
    """Filtering and ranking policy for a supplied universe snapshot.

    Configuration:
    - `top_n`: optional maximum number of selected rows; `None` keeps all.
    - `rank_field`: numeric input row field used for ranking; empty string
      disables ranking and preserves input order.
    - `descending`: sort direction when `rank_field` is active.
    - `min_rank_value`: optional lower bound for the rank value.
    - `symbol_field`: field containing the instrument identifier.
    - `require_status_ok`: when True, `status_by_symbol` must contain an
      accepted status for each symbol.
    - `accepted_status_values`: caller-defined status values treated as OK.
    - `min_history_value`: optional minimum history value in caller-defined
      units. When history data is supplied, booleans are interpreted directly
      and numeric values use this threshold or `> 0` when it is unset.
    - `fail_closed`: reject rows with missing/invalid rank when ranking is used.
    """

    top_n: Optional[int] = None
    rank_field: str = "score"
    descending: bool = True
    min_rank_value: Optional[float] = None
    symbol_field: str = "symbol"
    require_status_ok: bool = False
    accepted_status_values: tuple = (True,)
    min_history_value: Optional[float] = None
    fail_closed: bool = True


@dataclass
class UniverseSelectorRequest:
    candidates: Iterable[Any]
    status_by_symbol: Mapping[str, Any] = field(default_factory=dict)
    blacklist: Iterable[str] = field(default_factory=list)
    history_by_symbol: Mapping[str, Any] = field(default_factory=dict)
    params: UniverseSelectorParams = field(default_factory=UniverseSelectorParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="universe_selector"))


@dataclass
class UniverseReport:
    selected: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    ranked: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: UniverseSelectorRequest) -> ModuleResult[UniverseReport]:
    p = request.params
    blacklist = {str(x) for x in request.blacklist or []}
    min_rank_value = None
    if p.min_rank_value is not None:
        min_rank_value = finite_float(p.min_rank_value)
        if min_rank_value is None:
            return ModuleResult.fail("invalid_parameter", "min_rank_value must be a finite number", field="min_rank_value")
    top_n = None
    if p.top_n is not None:
        top_n_float = finite_float(p.top_n)
        if top_n_float is None:
            return ModuleResult.fail("invalid_parameter", "top_n must be a finite integer", field="top_n")
        top_n = max(int(top_n_float), 0)
    ranked: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item, symbol_field=p.symbol_field)
        sym = str(row.get(p.symbol_field) or row.get("symbol") or "")
        row["symbol"] = sym
        if not sym:
            row.update({"accepted": False, "reason": "missing_symbol"})
            rejected.append(row)
            continue
        if sym in blacklist:
            row.update({"accepted": False, "reason": "blacklisted"})
            rejected.append(row)
            continue
        if request.history_by_symbol:
            if sym not in request.history_by_symbol:
                if p.fail_closed:
                    row.update({"accepted": False, "reason": "history_unknown"})
                    rejected.append(row)
                    continue
            else:
                history_ok, history_value = _history_ok(request.history_by_symbol.get(sym), p.min_history_value)
                if not history_ok:
                    row.update({"accepted": False, "reason": "history_insufficient", "history": history_value})
                    rejected.append(row)
                    continue
                row["history"] = history_value
        if p.require_status_ok:
            if sym not in request.status_by_symbol:
                row.update({"accepted": False, "reason": "status_unknown"})
                rejected.append(row)
                continue
            st = request.status_by_symbol.get(sym)
            if _norm_status(st) not in {_norm_status(x) for x in p.accepted_status_values}:
                row.update({"accepted": False, "reason": "status_not_ok", "status": st})
                rejected.append(row)
                continue
        score = None
        if p.rank_field:
            if p.rank_field not in row:
                if p.fail_closed:
                    row.update({"accepted": False, "reason": "rank_missing"})
                    rejected.append(row)
                    continue
                score = 0.0
            else:
                score = finite_float(row.get(p.rank_field))
                if score is None:
                    if p.fail_closed:
                        row.update({"accepted": False, "reason": "rank_invalid"})
                        rejected.append(row)
                        continue
                    score = 0.0
        if min_rank_value is not None and (score is None or score < min_rank_value):
            row.update({"accepted": False, "reason": "rank_below_min", "rank_value": score})
            rejected.append(row)
            continue
        row.update({"accepted": True, "rank_value": score})
        ranked.append(row)
    if p.rank_field:
        ranked.sort(key=lambda x: float(x.get("rank_value", 0.0) or 0.0), reverse=bool(p.descending))
    selected = ranked if top_n is None else ranked[:top_n]
    report = UniverseReport(
        selected=selected,
        rejected=rejected,
        ranked=ranked,
        summary={"selected": len(selected), "ranked": len(ranked), "rejected": len(rejected), "top_n": p.top_n},
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="universe_selector.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("universe_selector", result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _norm_status(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value).strip().upper()


def _history_ok(value: Any, minimum: Optional[float]) -> tuple[bool, Any]:
    if isinstance(value, bool):
        return bool(value), value
    numeric = finite_float(value)
    if numeric is None:
        return bool(value), value
    if minimum is None:
        return numeric > 0.0, value
    min_numeric = finite_float(minimum)
    if min_numeric is None:
        return False, value
    return numeric >= min_numeric, value


__all__ = ["UniverseSelectorParams", "UniverseSelectorRequest", "UniverseReport", "run"]
