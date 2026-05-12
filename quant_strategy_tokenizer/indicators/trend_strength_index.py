"""
quant_strategy_tokenizer.indicators.trend_strength_index
========================================================
Purpose: Composite trend strength index token.
Core idea: Combine rolling regression slope, average absolute movement, and R-squared into a signed strength score. The implementation assumes clean directional linear movement deserves higher trend confidence than noisy movement.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, TrendStrengthIndexParams, and ModuleRunContext.
Outputs: TrendStrengthIndexReport with quality, last values, trend direction, signal,
optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .trend_common import TrendParams, TrendReport, normalize_trend_input, run_trend_indicator


INDICATOR = 'trend_strength_index'
INPUT_KIND = 'price'


@dataclass
class TrendStrengthIndexParams(TrendParams):
    """Configuration for the trend_strength_index trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class TrendStrengthIndexRequest:
    data: Any
    params: TrendStrengthIndexParams = field(default_factory=TrendStrengthIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


TrendStrengthIndexReport = TrendReport


def normalize_input(request: TrendStrengthIndexRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: TrendStrengthIndexRequest) -> ModuleResult[TrendStrengthIndexReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["TrendStrengthIndexParams", "TrendStrengthIndexRequest", "TrendStrengthIndexReport", "normalize_input", "run"]
