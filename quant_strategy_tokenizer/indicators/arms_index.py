"""
quant_strategy_tokenizer.indicators.arms_index
===============================================
Purpose: calculate the Arms Index from advance/decline and volume breadth as an atomic breadth token.
Core idea: Divide advance/decline ratio by up-volume/down-volume ratio. Assumes mismatches between count breadth and volume breadth identify pressure extremes.
Inputs: caller-supplied long panel rows, wide close matrix, or aggregate breadth
rows, optional DataFrameSpec field mapping, optional ExtractorSpec,
ArmsIndexParams, and ModuleRunContext.
Outputs: ArmsIndexReport with quality, last values, breadth direction/state,
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


INDICATOR = 'arms_index'


@dataclass
class ArmsIndexParams(BreadthParams):
    """Configuration for the arms_index breadth token.

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
class ArmsIndexRequest:
    data: Any
    params: ArmsIndexParams = field(default_factory=ArmsIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ArmsIndexReport = BreadthReport


def normalize_input(request: ArmsIndexRequest):
    return normalize_breadth_input(request)


def run(request: ArmsIndexRequest) -> ModuleResult[ArmsIndexReport]:
    return run_breadth_indicator(INDICATOR, request, module_name=INDICATOR)


__all__ = ["ArmsIndexParams", "ArmsIndexRequest", "ArmsIndexReport", "normalize_input", "run"]
