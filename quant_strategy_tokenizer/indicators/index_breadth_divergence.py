"""
quant_strategy_tokenizer.indicators.index_breadth_divergence
=============================================================
Purpose: detect divergence between index direction and internal breadth as an atomic breadth token.
Core idea: Compare index momentum with breadth momentum over the same window. Assumes rising index with weakening breadth or falling index with strengthening breadth is meaningful divergence.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
IndexBreadthDivergenceParams, and ModuleRunContext.
Outputs: IndexBreadthDivergenceReport with quality, last values, breadth direction/state,
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


INDICATOR = 'index_breadth_divergence'


@dataclass
class IndexBreadthDivergenceParams(BreadthParams):
    """Configuration for the index_breadth_divergence breadth token.

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
class IndexBreadthDivergenceRequest:
    data: Any
    params: IndexBreadthDivergenceParams = field(default_factory=IndexBreadthDivergenceParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


IndexBreadthDivergenceReport = BreadthReport


def normalize_input(request: IndexBreadthDivergenceRequest):
    return normalize_breadth_input(request)


def run(request: IndexBreadthDivergenceRequest) -> ModuleResult[IndexBreadthDivergenceReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["IndexBreadthDivergenceParams", "IndexBreadthDivergenceRequest", "IndexBreadthDivergenceReport", "normalize_input", "run"]
