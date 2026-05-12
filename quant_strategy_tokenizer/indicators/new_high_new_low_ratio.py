"""
quant_strategy_tokenizer.indicators.new_high_new_low_ratio
===========================================================
Purpose: measure the ratio of new highs to new lows as an atomic breadth token.
Core idea: Divide new highs by new lows. Assumes leadership pressure is captured by relative high/low creation.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
NewHighNewLowRatioParams, and ModuleRunContext.
Outputs: NewHighNewLowRatioReport with quality, last values, breadth direction/state,
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


INDICATOR = 'new_high_new_low_ratio'


@dataclass
class NewHighNewLowRatioParams(BreadthParams):
    """Configuration for the new_high_new_low_ratio breadth token.

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
class NewHighNewLowRatioRequest:
    data: Any
    params: NewHighNewLowRatioParams = field(default_factory=NewHighNewLowRatioParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


NewHighNewLowRatioReport = BreadthReport


def normalize_input(request: NewHighNewLowRatioRequest):
    return normalize_breadth_input(request)


def run(request: NewHighNewLowRatioRequest) -> ModuleResult[NewHighNewLowRatioReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["NewHighNewLowRatioParams", "NewHighNewLowRatioRequest", "NewHighNewLowRatioReport", "normalize_input", "run"]
