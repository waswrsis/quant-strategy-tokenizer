"""
quant_strategy_tokenizer.indicators.least_squares_moving_average
================================================================
Purpose: Least Squares Moving Average trend token.
Core idea: Use the rolling regression fitted value as a moving average. The implementation assumes the fitted regression endpoint is a smoother trend estimate than raw close.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, LeastSquaresMovingAverageParams, and ModuleRunContext.
Outputs: LeastSquaresMovingAverageReport with quality, last values, trend direction, signal,
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


INDICATOR = 'least_squares_moving_average'
INPUT_KIND = 'price'


@dataclass
class LeastSquaresMovingAverageParams(TrendParams):
    """Configuration for the least_squares_moving_average trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class LeastSquaresMovingAverageRequest:
    data: Any
    params: LeastSquaresMovingAverageParams = field(default_factory=LeastSquaresMovingAverageParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


LeastSquaresMovingAverageReport = TrendReport


def normalize_input(request: LeastSquaresMovingAverageRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: LeastSquaresMovingAverageRequest) -> ModuleResult[LeastSquaresMovingAverageReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["LeastSquaresMovingAverageParams", "LeastSquaresMovingAverageRequest", "LeastSquaresMovingAverageReport", "normalize_input", "run"]
