"""
quant_strategy_tokenizer.candidate_pool
=======================================
Module purpose: combine caller-supplied candidates and external filter decisions into a final ranked pool.
Core idea: Accept candidate rows, attach optional filter state, reject unavailable or failed rows, and optionally sort by a score field. Assumes indicators, votes, and filters have already been computed elsewhere; this module only assembles and ranks.
Inputs: candidate rows, optional filter_state_by_symbol, score/ranking params, and ModuleRunContext.
Outputs: CandidatePoolReport with accepted candidates, rejected candidates, ranked symbols, and summaries.
Failure semantics: missing symbol rejects a row; missing filter state rejects when fail_closed is enabled; unusable candidate iterables fail the request.
Market generalization: candidate rows are generic mappings and symbols are arbitrary caller identifiers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .contracts import ModuleEvent, ModuleResult, ModuleRunContext
from .reporting import write_module_report
from .row_utils import coerce_row, finite_float


@dataclass
class CandidatePoolParams:
    """How to assemble and optionally rank accepted candidates.

    Configuration:
    - `symbol_field`: input row field containing the instrument identifier.
    - `score_field`: optional numeric field used for sorting; `None` preserves
      input order after filtering.
    - `descending`: sort direction when `score_field` is configured.
    - `fail_closed`: when True, missing external filter state rejects a row.
    - `require_filter_state`: when True, an empty filter-state mapping is
      treated as unavailable filter data and rejects all rows.
    """

    symbol_field: str = "symbol"
    score_field: Optional[str] = None
    descending: bool = True
    fail_closed: bool = True
    require_filter_state: bool = False


@dataclass
class CandidatePoolRequest:
    candidates: Iterable[Mapping[str, Any]]
    filter_state_by_symbol: Optional[Mapping[str, Mapping[str, Any]]] = None
    params: CandidatePoolParams = field(default_factory=CandidatePoolParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="candidate_pool"))


@dataclass
class CandidatePoolReport:
    accepted_candidates: List[Dict[str, Any]]
    rejected_candidates: List[Dict[str, Any]]
    ranked_symbols: List[str]
    filter_summary: Dict[str, Any] = field(default_factory=dict)
    vote_summary: Dict[str, Any] = field(default_factory=dict)


def run(request: CandidatePoolRequest) -> ModuleResult[CandidatePoolReport]:
    p = request.params
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item, symbol_field=p.symbol_field)
        sym = str(row.get(p.symbol_field) or row.get("symbol") or "")
        row["symbol"] = sym
        if not sym:
            row.update({"accepted": False, "reason": "missing_symbol"})
            rejected.append(row)
            continue
        filter_state = request.filter_state_by_symbol
        if filter_state is not None and len(filter_state) == 0 and p.require_filter_state and p.fail_closed:
            row.update({"accepted": False, "reason": "filter_state_unavailable"})
            rejected.append(row)
            continue
        fstate = None if filter_state is None else filter_state.get(sym)
        if fstate is None and filter_state is not None and p.fail_closed:
            row.update({"accepted": False, "reason": "filter_state_unknown"})
            rejected.append(row)
            continue
        if fstate:
            row["filters"] = dict(fstate)
            if not bool(fstate.get("accepted", True)):
                row.update({"accepted": False, "reason": str(fstate.get("reason") or "filter_rejected")})
                rejected.append(row)
                continue
        row.update({"accepted": True, "reason": row.get("reason", "")})
        accepted.append(row)
    if p.score_field:
        sortable: List[Dict[str, Any]] = []
        for row in accepted:
            score = finite_float(row.get(p.score_field))
            if score is None:
                row.update({"accepted": False, "reason": "score_invalid"})
                rejected.append(row)
            else:
                row["_sort_score"] = score
                sortable.append(row)
        sortable.sort(key=lambda x: float(x.get("_sort_score", 0.0)), reverse=bool(p.descending))
        accepted = sortable
        for row in accepted:
            row.pop("_sort_score", None)
    report = CandidatePoolReport(
        accepted_candidates=accepted,
        rejected_candidates=rejected,
        ranked_symbols=[str(x.get("symbol")) for x in accepted],
        filter_summary={"accepted": len(accepted), "rejected": len(rejected)},
        vote_summary=_vote_summary(accepted),
    )
    result = ModuleResult.success(report, events=[ModuleEvent(event="candidate_pool.completed", fields=report.filter_summary)])
    if request.context.output_dir:
        result.files = write_module_report("candidate_pool", result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _vote_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for row in rows:
        outcome = str(row.get("outcome") or row.get("vote") or "")
        if outcome:
            counts[outcome] = counts.get(outcome, 0) + 1
    return {"outcomes": counts}


__all__ = ["CandidatePoolParams", "CandidatePoolRequest", "CandidatePoolReport", "run"]
