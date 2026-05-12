"""
quant_strategy_tokenizer.indicators.new_highs
==============================================
Purpose: count instruments making rolling new highs as an atomic breadth token.
Core idea: Count constituents at their rolling high. Assumes broad new-high participation confirms upside market structure.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
NewHighsParams, and ModuleRunContext.
Outputs: NewHighsReport with quality, last values, breadth direction/state,
participation counts, volume breadth fields, signal, regime, optional series,
input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient sample,
insufficient coverage, insufficient history, missing required volume/weight, or
calculation errors return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, index provider, constituent source, broker, or live exchange
access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .breadth_common import BreadthParams, BreadthReport, normalize_breadth_input, run_breadth_indicator


INDICATOR = 'new_highs'


@dataclass
class NewHighsParams(BreadthParams):
    """Configuration for the new_highs breadth token.

    Configuration:
    - field names map caller data into timestamp, symbol, close, volume, weight,
      and optional benchmark/index columns.
    - window fields are measured in rows on the breadth time axis.
    - sample and coverage fields decide whether cross-sectional evidence is
      trustworthy enough to report.
    - this module does not fetch data, read accounts, or execute trades.
    """
    pass


@dataclass
class NewHighsRequest:
    data: Any
    params: NewHighsParams = field(default_factory=NewHighsParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


NewHighsReport = BreadthReport


def normalize_input(request: NewHighsRequest):
    return normalize_breadth_input(request)


def run(request: NewHighsRequest) -> ModuleResult[NewHighsReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["NewHighsParams", "NewHighsRequest", "NewHighsReport", "normalize_input", "run"]
