"""
quant_strategy_tokenizer.filters.blacklist_filter
=================================================
Module purpose: remove candidates whose symbols appear in a caller-supplied blacklist.
Core idea: Normalize symbol strings, compare them against a blacklist set, and return accepted/rejected rows with reasons. Assumes blacklist policy is external and this module should not infer why a symbol is banned.
Inputs: candidate rows, blacklist symbols, symbol field params, and ModuleRunContext.
Outputs: BlacklistFilterReport with accepted rows, rejected rows, and blacklist hit counts.
Failure semantics: missing symbol rejects a row; unusable candidate input fails the request.
Market generalization: symbols are opaque caller identifiers and need not follow exchange notation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from ..contracts import ModuleEvent, ModuleResult, ModuleRunContext
from ..reporting import write_module_report
from ..row_utils import coerce_row


@dataclass
class BlacklistFilterParams:
    """Symbol matching options for blacklist filtering.

    Configuration:
    - `symbol_field`: input row field containing the instrument identifier.
    - `case_sensitive`: when False, symbols and blacklist entries are compared
      after uppercase normalization.
    """

    symbol_field: str = "symbol"
    case_sensitive: bool = True


@dataclass
class BlacklistFilterRequest:
    candidates: Iterable[Any]
    blacklist: Iterable[str]
    params: BlacklistFilterParams = field(default_factory=BlacklistFilterParams)
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module="blacklist_filter"))


@dataclass
class BlacklistFilterReport:
    accepted: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)


def run(request: BlacklistFilterRequest) -> ModuleResult[BlacklistFilterReport]:
    blacklist = set(str(x) for x in request.blacklist or [])
    if not request.params.case_sensitive:
        blacklist = {x.upper() for x in blacklist}
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for item in request.candidates or []:
        row = coerce_row(item, symbol_field=request.params.symbol_field)
        row.setdefault("symbol", row.get(request.params.symbol_field))
        sym = str(row.get("symbol") or "")
        if not sym:
            row.update({"accepted": False, "reason": "missing_symbol"})
            rejected.append(row)
            continue
        key = sym if request.params.case_sensitive else sym.upper()
        if key in blacklist:
            row.update({"accepted": False, "reason": "blacklisted"})
            rejected.append(row)
        else:
            row.update({"accepted": True, "reason": ""})
            accepted.append(row)
    report = BlacklistFilterReport(accepted=accepted, rejected=rejected, summary={"accepted": len(accepted), "rejected": len(rejected)})
    result = ModuleResult.success(report, events=[ModuleEvent(event="blacklist_filter.completed", fields=report.summary)])
    if request.context.output_dir:
        result.files = write_module_report("blacklist_filter", result, request.context.output_dir, run_id=request.context.run_id)
    return result

__all__ = ["BlacklistFilterParams", "BlacklistFilterRequest", "BlacklistFilterReport", "run"]
