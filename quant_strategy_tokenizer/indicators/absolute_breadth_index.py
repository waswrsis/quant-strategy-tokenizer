"""
quant_strategy_tokenizer.indicators.absolute_breadth_index
===========================================================
Purpose: measure the absolute size of market breadth imbalance as an atomic breadth token.
Core idea: Take the absolute value of net advances. Assumes unusually one-sided participation can matter regardless of direction.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
AbsoluteBreadthIndexParams, and ModuleRunContext.
Outputs: AbsoluteBreadthIndexReport with quality, last values, breadth direction/state,
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


INDICATOR = 'absolute_breadth_index'


@dataclass
class AbsoluteBreadthIndexParams(BreadthParams):
    """Configuration for the absolute_breadth_index breadth token.

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
class AbsoluteBreadthIndexRequest:
    data: Any
    params: AbsoluteBreadthIndexParams = field(default_factory=AbsoluteBreadthIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AbsoluteBreadthIndexReport = BreadthReport


def normalize_input(request: AbsoluteBreadthIndexRequest):
    return normalize_breadth_input(request)


def run(request: AbsoluteBreadthIndexRequest) -> ModuleResult[AbsoluteBreadthIndexReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["AbsoluteBreadthIndexParams", "AbsoluteBreadthIndexRequest", "AbsoluteBreadthIndexReport", "normalize_input", "run"]
