"""
quant_strategy_tokenizer.indicators.percent_above_ma
=====================================================
Purpose: measure the percentage of instruments above a moving average as an atomic breadth token.
Core idea: Compare each constituent close with its rolling simple moving average. Assumes trend participation is visible in how many names hold above their own average.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
PercentAboveMaParams, and ModuleRunContext.
Outputs: PercentAboveMaReport with quality, last values, breadth direction/state,
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


INDICATOR = 'percent_above_ma'


@dataclass
class PercentAboveMaParams(BreadthParams):
    """Configuration for the percent_above_ma breadth token.

    Configuration:
    - field names map caller data into timestamp, symbol, close, volume, weight,
      and optional benchmark/index columns.
    - window fields are measured in rows on the breadth time axis.
    - sample and coverage fields decide whether cross-sectional evidence is
      trustworthy enough to report.
    - this module does not fetch data, read accounts, or execute trades.
    """

    ma_window: int = 50


@dataclass
class PercentAboveMaRequest:
    data: Any
    params: PercentAboveMaParams = field(default_factory=PercentAboveMaParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


PercentAboveMaReport = BreadthReport


def normalize_input(request: PercentAboveMaRequest):
    return normalize_breadth_input(request)


def run(request: PercentAboveMaRequest) -> ModuleResult[PercentAboveMaReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["PercentAboveMaParams", "PercentAboveMaRequest", "PercentAboveMaReport", "normalize_input", "run"]
