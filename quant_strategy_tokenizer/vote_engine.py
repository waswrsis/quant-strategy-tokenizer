"""
quant_strategy_tokenizer.vote_engine
============================
Module purpose: combine independent judge outputs into an allow/reject decision.
Core idea: voting is a small, reusable aggregation step; judges can be trend,
macro, liquidity, risk, or any user-defined evaluator.
Inputs: candidate rows and judge_by_symbol mapping with support/neutral/veto
style fields or numeric scores.
Outputs: VoteEngineReport with outcome, allowed flag, score, and diagnostics.
Failure semantics: missing judge state rejects when fail_closed is True.
Market generalization: judge labels are generic and not tied to any market.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .contracts import ModuleEvent, ModuleResult, ModuleRunContext
from .reporting import write_module_report
from .row_utils import coerce_row, finite_float


@dataclass
class VoteEngineParams:
    """Aggregation rules for supplied judge outputs.

    Configuration:
    - `allowed_outcomes`: outcome labels or booleans that count as accepted.
    - `min_score`: optional numeric score floor; `None` disables score gating.
    - `fail_closed`: when True, missing judge state rejects the candidate.
    """

    allowed_outcomes: tuple = ("allow", "accept", "pass", "support", True)
    min_score: Optional[float] = None
    fail_closed: bool = True


@dataclass
class VoteEngineRequest:
    candidates: Iterable[Mapping[str, Any]]
    judge_by_symbol: Mapping[str, Mapping[str, Any]]
    params: VoteEngineParams = field(default_factory=VoteEngineParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="vote_engine"))


@dataclass
class VoteEngineReport:
    decisions: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: VoteEngineRequest) -> ModuleResult[VoteEngineReport]:
    allowed_set = {_norm_vote(x) for x in request.params.allowed_outcomes}
    min_score = None
    if request.params.min_score is not None:
        min_score = finite_float(request.params.min_score)
        if min_score is None:
            return ModuleResult.fail("invalid_parameter", "min_score must be a finite number", field="min_score")
    decisions: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item)
        sym = str(row.get("symbol") or "")
        judges = (request.judge_by_symbol or {}).get(sym)
        if judges is None:
            row.update({"allowed": not request.params.fail_closed, "outcome": "unknown", "reason": "judge_unknown"})
            (rejected if request.params.fail_closed else decisions).append(row)
            continue
        if not isinstance(judges, Mapping):
            row.update({"allowed": False, "outcome": "unknown", "reason": "judge_invalid", "judges": judges})
            rejected.append(row)
            continue
        outcome = str(judges.get("outcome") or _matrix_outcome(judges))
        raw_score = judges.get("score", row.get("score", None))
        score = finite_float(raw_score)
        if min_score is not None and score is None:
            row.update({"allowed": False, "outcome": outcome, "score": raw_score, "judges": dict(judges), "reason": "score_invalid"})
            rejected.append(row)
            continue
        score_out = 0.0 if score is None else score
        score_ok = True if min_score is None else score_out >= min_score
        allowed = _norm_vote(outcome) in allowed_set and score_ok
        row.update({"allowed": allowed, "outcome": outcome, "score": score_out, "judges": dict(judges), "reason": "" if allowed else "vote_rejected"})
        (decisions if allowed else rejected).append(row)
    report = VoteEngineReport(decisions=decisions, rejected=rejected, summary={"allowed": len(decisions), "rejected": len(rejected)})
    result = ModuleResult.success(report, events=[ModuleEvent(event="vote_engine.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("vote_engine", result, request.context.output_dir, run_id=request.context.run_id)
    return result


def _matrix_outcome(judges: Mapping[str, Any]) -> str:
    if "allowed" in judges:
        return "allow" if bool(judges.get("allowed")) else "reject"
    votes = [str(v).lower() for k, v in judges.items() if k != "score"]
    if votes and all(v == "support" for v in votes):
        return "allow"
    if "veto" in votes:
        return "reject"
    return "neutral"


def _norm_vote(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().lower()


__all__ = ["VoteEngineParams", "VoteEngineRequest", "VoteEngineReport", "run"]
