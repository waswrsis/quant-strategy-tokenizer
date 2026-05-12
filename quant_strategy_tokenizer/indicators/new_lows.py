"""
quant_strategy_tokenizer.indicators.new_lows
=============================================
Purpose: count instruments making rolling new lows as an atomic breadth token.
Core idea: Count constituents at their rolling low. Assumes broad new-low participation confirms downside market stress.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
NewLowsParams, and ModuleRunContext.
Outputs: NewLowsReport with quality, last values, breadth direction/state,
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


INDICATOR = 'new_lows'


@dataclass
class NewLowsParams(BreadthParams):
    """Configuration for the new_lows breadth token.

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
class NewLowsRequest:
    data: Any
    params: NewLowsParams = field(default_factory=NewLowsParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


NewLowsReport = BreadthReport


def normalize_input(request: NewLowsRequest):
    return normalize_breadth_input(request)


def run(request: NewLowsRequest) -> ModuleResult[NewLowsReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["NewLowsParams", "NewLowsRequest", "NewLowsReport", "normalize_input", "run"]
