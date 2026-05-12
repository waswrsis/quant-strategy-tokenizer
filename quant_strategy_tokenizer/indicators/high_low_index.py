"""
quant_strategy_tokenizer.indicators.high_low_index
===================================================
Purpose: measure new highs as a percentage of new highs plus new lows as an atomic breadth token.
Core idea: Scale new highs by total high/low events. Assumes this percentage is a stable high-low breadth oscillator.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
HighLowIndexParams, and ModuleRunContext.
Outputs: HighLowIndexReport with quality, last values, breadth direction/state,
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


INDICATOR = 'high_low_index'


@dataclass
class HighLowIndexParams(BreadthParams):
    """Configuration for the high_low_index breadth token.

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
class HighLowIndexRequest:
    data: Any
    params: HighLowIndexParams = field(default_factory=HighLowIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


HighLowIndexReport = BreadthReport


def normalize_input(request: HighLowIndexRequest):
    return normalize_breadth_input(request)


def run(request: HighLowIndexRequest) -> ModuleResult[HighLowIndexReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["HighLowIndexParams", "HighLowIndexRequest", "HighLowIndexReport", "normalize_input", "run"]
