"""
quant_strategy_tokenizer.indicators.cap_weighted_breadth
=========================================================
Purpose: calculate weight-adjusted net breadth as an atomic breadth token.
Core idea: Weight advancing and declining constituents by caller-supplied weights. Assumes user-provided weights represent portfolio, cap, or index importance.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
CapWeightedBreadthParams, and ModuleRunContext.
Outputs: CapWeightedBreadthReport with quality, last values, breadth direction/state,
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


INDICATOR = 'cap_weighted_breadth'


@dataclass
class CapWeightedBreadthParams(BreadthParams):
    """Configuration for the cap_weighted_breadth breadth token.

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
class CapWeightedBreadthRequest:
    data: Any
    params: CapWeightedBreadthParams = field(default_factory=CapWeightedBreadthParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


CapWeightedBreadthReport = BreadthReport


def normalize_input(request: CapWeightedBreadthRequest):
    return normalize_breadth_input(request)


def run(request: CapWeightedBreadthRequest) -> ModuleResult[CapWeightedBreadthReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["CapWeightedBreadthParams", "CapWeightedBreadthRequest", "CapWeightedBreadthReport", "normalize_input", "run"]
